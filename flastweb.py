from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sql_control import sql_Management
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from log_management import setup_logger
import logging
import jwt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from pydantic import BaseModel
import base64
from datetime import datetime, timedelta
from fastapi import Request
from typing import Dict, Set
from sqlite3 import connect
import os

# 加载 RSA 私钥
private_key = RSA.import_key(open("generate_rsa_key/private.pem").read())

logger = setup_logger(logger_name="dnpsaber_browserlogger", log_dir_name="browserlogs")

uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.handlers = logger.handlers
uvicorn_logger.setLevel(logging.INFO)

# 加载SECRET_KEY
with open("SECRET_KEY.txt") as f:
    SECRET_KEY = f.read().strip()
app = FastAPI()

# 全局连接池和 WebSocket 连接管理
connection_pool: Dict[str, sql_Management] = {}
active_websockets: Dict[str, Set[WebSocket]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")


# 定义请求体模型
class LoginRequest(BaseModel):
    username: str
    password: str
    deviceID: str  # 新增字段


@app.post("/login")
def login(request: LoginRequest, http_request: Request):
    user_device_key = f"{request.username}_{request.deviceID}"  # 使用 userID+deviceID 作为键

    # 解密密码
    try:
        cipher = PKCS1_v1_5.new(private_key)
        decrypted_password = cipher.decrypt(base64.b64decode(request.password), None).decode('utf-8')
    except Exception as e:
        logger.error(f"密码解密失败: {e}")
        raise HTTPException(status_code=400, detail="密码解密失败")

    # 查询user.db3数据库，校验用户名和密码
    try:
        conn = connect('user.db3')
        cursor = conn.cursor()
        cursor.execute("SELECT passwd, live FROM usernames WHERE name=?", (request.username,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=401, detail="用户名不存在")
        db_passwd, live_level = row
        if db_passwd != decrypted_password:
            raise HTTPException(status_code=401, detail="密码错误")
    except Exception as e:
        logger.error(f"数据库查询失败: {e}")
        raise HTTPException(status_code=500, detail="数据库查询失败")



    # 创建数据库连接并存储到连接池
    sql_manager = sql_control.sql_Management(sql_user=os.environ.get(f'MYSQL_NAME_LIVE{live}'),sql_user_passwd=os.environ.get(f"MYSQL_PASSWD_LIVE{live}"))
    result = sql_manager.sql_connect()
    if "成功" in result:
        connection_pool[user_device_key] = sql_manager
        if user_device_key not in active_websockets:
            active_websockets[user_device_key] = set()
        logger.info(f"用户 {user_device_key} 登录成功，连接已建立")
        logger.info(f"连接池状态: {len(connection_pool)} 个连接")
        # 生成JWT，过期时间30分钟
        payload = {
            "userID": request.username,
            "deviceID": request.deviceID,
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return {"message": result, "token": token}
    else:
        raise HTTPException(status_code=401, detail="登录失败，数据库连接失败")


# 绑定根路径到 index.html
@app.get("/")
def read_root():
    return FileResponse("static/logins.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    x_forwarded_for = websocket.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        client_ip = websocket.headers.get("x-real-ip", websocket.client.host)
    logger.info(f"WebSocket 连接请求来自 IP: {client_ip}")
    await websocket.accept()

    # 1. 等待客户端发送JWT token
    try:
        token = await websocket.receive_text()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("WebSocket认证失败: JWT已过期")
            await websocket.close(code=4001, reason="JWT已过期")
            return
        except jwt.InvalidTokenError as e:
            logger.warning(f"WebSocket认证失败: JWT无效 {e}")
            await websocket.close(code=4002, reason="JWT无效")
            return
        userID = payload["userID"]
        deviceID = payload["deviceID"]
        user_device_key = f"{userID}_{deviceID}"
    except Exception as e:
        logger.warning(f"WebSocket认证失败: {e}")
        await websocket.close(code=4003, reason="认证异常")
        return

    # 2. 验证是否已登录（连接池中有该用户设备的连接）
    if user_device_key not in connection_pool:
        logger.warning(f"未登录用户 {user_device_key} 尝试建立 WebSocket 连接，已拒绝")
        await websocket.close(code=4004, reason="未登录或连接已失效")
        return

    # 3. 将 WebSocket 连接添加到活动连接中
    if user_device_key not in active_websockets:
        active_websockets[user_device_key] = set()
    active_websockets[user_device_key].add(websocket)
    logger.info(f"WebSocket认证通过: {user_device_key} 已加入活动连接池")

    try:
        while True:
            try:
                msg = await websocket.receive_text()
                # 心跳包处理
                if msg == '{"type": "ping"}':
                    await websocket.send_text('{"type": "pong"}')
                    continue
                # 这里可扩展更多消息类型处理
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket消息处理异常: {e}")
                break
    finally:
        # 移除断开的 WebSocket 连接
        active_websockets[user_device_key].discard(websocket)
        logger.info(f"WebSocket 断开: {user_device_key}，当前剩余连接数: {len(active_websockets[user_device_key])}")
        if not active_websockets[user_device_key]:
            # 如果该用户设备的所有 WebSocket 都断开，关闭数据库连接
            sql_manager = connection_pool.pop(user_device_key, None)
            if sql_manager:
                sql_manager.__exit__(None, None, None)
                logger.info(f"用户设备 {user_device_key} 的数据库连接已断开")
            active_websockets.pop(user_device_key, None)


@app.get("/home")
def home():
    return FileResponse("static/home.html")


@app.get("/favicon.ico")
def favicon():
    return FileResponse("static/favicon.png")


def web_run():
    """
    启动Web服务
    :return: None
    """
    uvicorn.run(app,
                host="0.0.0.0",
                port=8000,  # 改为8000端口，去除SSL参数
                log_config=None)
    # uvicorn.run(app,
    #             host="0.0.0.0",
    #             log_config=None)


if __name__ == '__main__':
    # uvicorn.run(app, host="139.196.175.179")
    web_run()
