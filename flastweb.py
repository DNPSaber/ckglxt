from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Cookie, Body, Response, Query, Form
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
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
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Set
from sqlite3 import connect
import os
import asyncio
import zipfile
import io

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
        raise HTTPException(status_code=400, detail="密码解码失败")

    decrypted_password = hashlib.md5(decrypted_password.encode('utf-8')).hexdigest()

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

    live = str(live_level)  # 强制转为字符串，确保后续判断正确

    # 创建数据库连接并存储到连接池
    if live > "1":
        sql_manager = sql_Management(sql_user=os.environ.get(f'MYSQL_NAME_LIVE{live}'),
                                     sql_user_passwd=os.environ.get(f"MYSQL_PASSWD_LIVE{live}"))
        result = sql_manager.sql_connect()
    elif live == "1":
        sql_manager = None
        result = "成功"
    if "成功" in result:
        connection_pool[user_device_key] = sql_manager
        if user_device_key not in active_websockets:
            active_websockets[user_device_key] = set()
        logger.info(f"用户 {user_device_key} 等级{live}登录成功，连接已建立")
        logger.info(f"连接池状态: {len(connection_pool)} 个连接")
        # 生成JWT，过期时间30分钟
        payload = {
            "userID": request.username,
            "deviceID": request.deviceID,
            # 使用时区感知的UTC时间
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        response = {"message": result, "token": token}
        from fastapi.responses import JSONResponse
        res = JSONResponse(content=response)
        # 设置SameSite，防止XSS（去掉httponly，前端可读）
        res.set_cookie(key="jwt_token", value=token, samesite="Lax", path="/")
        return res
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

    # 2. 验证是否已登录（连接池该用户设备的连接）且JWT未过期
    if user_device_key not in connection_pool:
        logger.warning(f"未登录用户 {user_device_key} 尝试建立 WebSocket 连接，已拒绝")
        await websocket.close(code=4004, reason="没有登录或连接已失效")
        return
    # 检查JWT是否过期（jwt.decode已做，payload['exp']为过期时间）
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if 'exp' not in payload or now_ts > int(payload['exp']):
        logger.warning(f"JWT已过期: {user_device_key}")
        await websocket.close(code=4001, reason="JWT已过期")
        return

    # 3. 将 WebSocket 连接添加到活动连接中
    if user_device_key not in active_websockets:
        active_websockets[user_device_key] = set()
    active_websockets[user_device_key].add(websocket)
    logger.info(f"WebSocket认证通过: {user_device_key} 已加入活动连接池")

    last_ping = asyncio.get_event_loop().time()

    async def heartbeat_checker():
        nonlocal last_ping
        while True:
            await asyncio.sleep(2)
            if asyncio.get_event_loop().time() - last_ping > 180:
                logger.info(f"heartbeat_checker: 触发断开 {user_device_key}")
                logger.info(f"WebSocket心跳超时: {user_device_key}，自动断开并清理连接池")
                await websocket.close(code=4004, reason="心跳超时，连接已失效")
                break

    heartbeat_task = asyncio.create_task(heartbeat_checker())

    try:
        while True:
            logger.info(f"等待消息: {user_device_key}")
            try:
                msg = await websocket.receive_text()
                logger.info(f"收到消息: {msg}")
                # 心跳包处理
                if msg == '{"type": "ping"}':
                    logger.info(f"用户{user_device_key}的WebSocket心跳包接收: {user_device_key}")
                    last_ping = asyncio.get_event_loop().time()
                    await websocket.send_text('{"type": "pong"}')
                    continue
                # 这里可扩展更多消息类型处理
            except WebSocketDisconnect:
                logger.info(f"WebSocketDisconnect: {user_device_key}")
                break
            except Exception as e:
                logger.error(f"WebSocket消息处理异常: {e}")
                break
    finally:
        # 断开时取消心跳任务，避免资源泄漏
        if not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except Exception:
                pass
        # 移除断开的 WebSocket 连接
        ws_set = active_websockets.get(user_device_key)
        logger.info(f"finally: active_websockets={active_websockets}")
        logger.info(f"finally: connection_pool={connection_pool}")
        if ws_set:
            ws_set.discard(websocket)
            logger.info(
                f"WebSocket 断开: {user_device_key}，当前剩余连接数: {len(ws_set)}，ws_set内容: {[id(ws) for ws in ws_set]}")
            if len(ws_set) == 0:
                # 如果该用户设备的所有 WebSocket 都断开，关闭数据库
                sql_manager = connection_pool.pop(user_device_key, None)
                if sql_manager:
                    sql_manager.__exit__(None, None, None)
                    logger.info(f"用户设备 {user_device_key} 的数据库连接已断开")
                active_websockets.pop(user_device_key, None)
        else:
            logger.info(f"finally: ws_set 不存在，user_device_key={user_device_key}")


@app.get("/home")
def home(request: Request, jwt_token: str = Cookie(None)):
    if not jwt_token:
        # JWT缺失，弹窗提示
        return HTMLResponse('<script>alert("未检测到登录凭证，请重新登录");window.location.href="/";</script>')
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        userID = payload["userID"]
        deviceID = payload["deviceID"]
        user_device_key = f"{userID}_{deviceID}"
        # 校验连接池
        if user_device_key not in connection_pool:
            # 连接池无效，弹窗提示
            return HTMLResponse('<script>alert("会话已失效，请重新登录");window.location.href="/";</script>')
        # 查询用户等级
        conn = connect('user.db3')
        cursor = conn.cursor()
        cursor.execute("SELECT live FROM usernames WHERE name=?", (userID,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return HTMLResponse('<script>alert("用户不存在，请重新登录");window.location.href="/";</script>')
        live = row[0]
        logger.info('用户 %s 等级: %s', userID, live)
        
        # 获取设备类型 (从 User-Agent 判断)
        user_agent = request.headers.get("user-agent", "").lower()
        is_mobile = any(keyword in user_agent for keyword in ["android", "iphone", "ipad", "mobile", "tablet"])
        
        # 根据设备类型和用户等级确定跳转页面
        if is_mobile and live == 5 and os.path.exists("static/live5_mobile.html"):
            # 管理员用户的移动端版本
            logger.info('用户 %s 使用移动设备访问，跳转到移动版管理员页面', userID)
            return FileResponse("static/live5_mobile.html")
        elif is_mobile and os.path.exists(f"static/live{live}_mobile.html"):
            # 如果存在对应权限的移动端页面，则跳转
            logger.info('用户 %s 使用移动设备访问，跳转到移动版页面', userID)
            return FileResponse(f"static/live{live}_mobile.html")
        else:
            # 桌面版或没有专门的移动版页面
            logger.info('用户 %s 使用桌面设备访问或无专用移动页面，跳转到标准页面', userID)
            return FileResponse(f"static/live{live}.html")
    except jwt.ExpiredSignatureError:
        return HTMLResponse('<script>alert("登录已超过30分钟，请重新登录");window.location.href="/";</script>')
    except Exception:
        return HTMLResponse('<script>alert("登录凭证无效，请重新登录");window.location.href="/";</script>')


@app.get("/favicon.ico")
def favicon():
    return FileResponse("static/favicon.png")


# 定义注册请求体模型
class RegisterRequest(BaseModel):
    username: str
    password: str


@app.post("/register")
def register(request: RegisterRequest = Body(...)):
    # 检查用户名是否已存在
    try:
        conn = connect('user.db3')
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM usernames WHERE name=?", (request.username,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="用户已存在")
    except Exception as e:
        logger.error(f"注册-数据库查询失败: {e}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    # 解密密码
    try:
        cipher = PKCS1_v1_5.new(private_key)
        decrypted_password = cipher.decrypt(base64.b64decode(request.password), None).decode('utf-8')
    except Exception as e:
        logger.error(f"注册-密码解密失败: {e}")
        raise HTTPException(status_code=400, detail="密码解码失败")
    # 取md5值
    md5_passwd = hashlib.md5(decrypted_password.encode('utf-8')).hexdigest()
    # 插入新用户
    try:
        cursor.execute("INSERT INTO usernames (name, passwd, live) VALUES (?, ?, ?)",
                       (request.username, md5_passwd, '1'))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"注册-插入用户失败: {e}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")
    return {"message": "注册成功"}


@app.post("/api/clear_conn")
def clear_conn(request: Request, jwt_token: str = Cookie(None)):
    """
    清除当前用户的连接池（登出/访客返回登录页时调用）
    """
    if not jwt_token:
        return {"message": "no token"}
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=["HS256"])
        userID = payload["userID"]
        deviceID = payload["deviceID"]
        user_device_key = f"{userID}_{deviceID}"
        # 移除连接池和websocket
        if user_device_key in connection_pool:
            sql_manager = connection_pool.pop(user_device_key)
            if sql_manager:
                try:
                    sql_manager.__exit__(None, None, None)
                except Exception:
                    pass
        if user_device_key in active_websockets:
            active_websockets.pop(user_device_key)
        # 清除cookie
        res = Response(content='{"message": "ok"}', media_type="application/json")
        res.delete_cookie("jwt_token", path="/")
        return res
    except Exception as e:
        logger.error(f"clear_conn error: {e}")
        return {"message": "error"}


@app.get("/api/users")
def get_users():
    """
    获取所有用户（不返回密码），用于用户管理页面
    """
    try:
        conn = connect('user.db3')
        cursor = conn.cursor()
        cursor.execute("SELECT name, live FROM usernames")
        users = [{"name": row[0], "live": row[1]} for row in cursor.fetchall()]
        conn.close()
        return {"users": users}
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


class UserLiveRequest(BaseModel):
    name: str
    live: str


@app.post("/api/user_live")
def update_user_live(req: UserLiveRequest):
    """
    修改用户 live 等级
    """
    try:
        conn = connect('user.db3')
        cursor = conn.cursor()
        cursor.execute("UPDATE usernames SET live=? WHERE name=?", (req.live, req.name))
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "message": "用户不存在"}
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        logger.error(f"修改用户权限失败: {e}")
        return {"success": False, "message": "修改失败"}


class UserDeleteRequest(BaseModel):
    name: str

@app.post("/api/user_delete")
def delete_user(req: UserDeleteRequest):
    """
    删除用户（根据用户名）
    """
    try:
        conn = connect('user.db3')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usernames WHERE name=?", (req.name,))
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "message": "用户不存在"}
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        return {"success": False, "message": "删除失败"}


@app.get("/api/list_logs")
def list_logs(dir: str = Query(..., pattern="^(logs|browserlogs)$")):
    base_dir = "/root/dnpsaber/" + dir
    try:
        if not os.path.isdir(base_dir):
            return {"success": True, "files": []}
        files = [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
        return {"success": True, "files": files}
    except Exception as e:
        logger.error(f"列出日志文件失败: {e}")
        return {"success": False, "files": [], "message": str(e)}
    

@app.get("/api/download_log")
def download_log(dir: str = Query(..., pattern="^(logs|browserlogs)$"), file: str = Query(...)):
    base_dir = f"/root/dnpsaber/{dir}"
    file_path = os.path.join(base_dir, file)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=file)


@app.post("/api/download_logs_zip")
def download_logs_zip(dir: str = Form(...), files: list[str] = Form(...)):
    # 只允许 logs 或 browserlogs
    if dir not in ("logs", "browserlogs"):
        raise HTTPException(status_code=400, detail="目录不合法")
    base_dir = f"/root/dnpsaber/{dir}"
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in files:
            fpath = os.path.join(base_dir, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, arcname=fname)
    mem_zip.seek(0)
    return StreamingResponse(mem_zip, media_type="application/zip", headers={
        "Content-Disposition": f"attachment; filename={dir}_logs.zip"
    })


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
