from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sql_control import sql_Management
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from log_management import setup_logger
import logging
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
from fastapi import Request
from typing import Dict, Set

# 加载 RSA 私钥
private_key = RSA.import_key(open("generate_rsa_key/private.pem").read())

logger = setup_logger(logger_name="dnpsaber_browserlogger", log_dir_name="browserlogs")

uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.handlers = logger.handlers
uvicorn_logger.setLevel(logging.INFO)
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


@app.post("/login")
def login(request: LoginRequest, http_request: Request):
    client_ip = http_request.client.host  # 从请求中获取客户端 IP

    # 解密密码
    try:
        cipher = PKCS1_v1_5.new(private_key)
        decrypted_password = cipher.decrypt(base64.b64decode(request.password), None).decode('utf-8')
    except Exception as e:
        logger.error(f"密码解密失败: {e}")
        raise HTTPException(status_code=400, detail="密码解密失败")

    # 创建数据库连接并存储到连接池
    sql_manager = sql_Management(sql_user=request.username, sql_user_passwd=decrypted_password)
    result = sql_manager.sql_connect()
    if "成功" in result:
        connection_pool[client_ip] = sql_manager
        if client_ip not in active_websockets:
            active_websockets[client_ip] = set()
        logger.info(f"IP {client_ip} 登录成功，连接已建立")
        logger.info(f"连接池状态: {len(connection_pool)} 个连接")
        return {"message": result}
    else:
        raise HTTPException(status_code=401, detail="登录失败，用户名或密码错误")


# 绑定根路径到 index.html
@app.get("/")
def read_root():
    return FileResponse("static/logins.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # 优先从 X-Forwarded-For 或 X-Real-IP 获取真实IP
    x_forwarded_for = websocket.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        client_ip = websocket.headers.get("x-real-ip", websocket.client.host)

    # 只允许已登录用户建立 WebSocket 连接
    if client_ip not in connection_pool:
        logger.warning(f"未登录用户 {client_ip} 尝试建立 WebSocket 连接，已拒绝")
        await websocket.close()
        return

    # 将 WebSocket 连接添加到活动连接中
    if client_ip not in active_websockets:
        active_websockets[client_ip] = set()
    active_websockets[client_ip].add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # 移除断开的 WebSocket 连接
        active_websockets[client_ip].remove(websocket)
        logger.info(f"WebSocket 断开: {client_ip}，当前剩余连接数: {len(active_websockets[client_ip])}")
        logger.info(f"当前 active_websockets: {active_websockets}")
        logger.info(f"当前 connection_pool: {connection_pool}")
        if not active_websockets[client_ip]:
            # 如果该 IP 的所有 WebSocket 都断开，关闭数据库连接
            sql_manager = connection_pool.pop(client_ip, None)
            if sql_manager:
                sql_manager.__exit__(None, None, None)
                logger.info(f"IP {client_ip} 的数据库连接已断开")
            else:
                logger.info(f"IP {client_ip} 无数据库连接可关闭")


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
