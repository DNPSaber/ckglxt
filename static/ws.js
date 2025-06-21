console.log("ws.js 已加载");

function getCookie(name) {
    // 更健壮的cookie获取方式���免空格和大小写问题
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const c = cookies[i].trim();
        if (c.split('=')[0] === name) {
            return decodeURIComponent(c.substring(name.length + 1));
        }
    }
    return null;
}

// 导出一个函数用于连接 WebSocket
defineConnectWebSocket();
function defineConnectWebSocket() {
    window.connectWebSocket = function(token, onOpenCallback) {
        if (!token) {
            console.log("connectWebSocket: token 为空，无法连接 WebSocket");
            return;
        }
        console.log("connectWebSocket: 开始连接 WebSocket，token:", token);
        let ws = new WebSocket("wss://dnpsaber.cn/ws");
        ws.onopen = function () {
            ws.send(token);
            // 启动心跳包定时器，每5秒发送一次
            // console.log("WebSocket已连接，发送token:", token); // 保留关键日志
            ws.heartbeatInterval = setInterval(function () {
                if (ws.readyState === WebSocket.OPEN) {
                    // console.log("发送心跳包"); // 注释掉高频心跳日志
                    ws.send('{\"type\": \"ping\"}');
                }
            }, 5000);
            if (typeof onOpenCallback === 'function') {
                onOpenCallback();
            }
        };
        ws.onclose = function (event) {
            clearInterval(ws.heartbeatInterval);
            console.log("WebSocket已关闭，code:", event.code, event.reason);
            if (event.code === 4001) {
                alert("登录已超过30分钟，请重新登录");
                window.location.href = '/';
            } else if (event.code === 4002 || event.code === 4003 || event.code === 4004) {
                alert("认证失败或会话失效，请重新登录");
                window.location.href = '/';
            }
        };
        ws.onerror = function () {
            console.log("WebSocket连接出错");
            alert("WebSocket连接出错，请重新登录");
            window.location.href = '/';
        };
        window.addEventListener("beforeunload", () => {
            ws.close();
        });
    }
}

// 自动重连WebSocket
function connectWebSocketWithRetry(token, retryDelay = 3000) {
    let ws;
    function connect() {
        ws = new WebSocket("wss://dnpsaber.cn/ws");
        ws.onopen = function () {
            ws.send(token);
            console.log("WebSocket已连接，发送token:", token);
            ws.heartbeatInterval = setInterval(function () {
                if (ws.readyState === WebSocket.OPEN) {
                    console.log("发送心跳包");
                    ws.send('{\"type\": \"ping\"}');
                }
            }, 5000);
        };
        ws.onclose = function (event) {
            clearInterval(ws.heartbeatInterval);
            console.log("WebSocket已关闭，code:", event.code, event.reason);
            setTimeout(connect, retryDelay); // 自动重连
        };
        ws.onerror = function () {
            clearInterval(ws.heartbeatInterval);
            console.log("WebSocket连接出错");
            setTimeout(connect, retryDelay); // 自动重连
        };
        window.addEventListener("beforeunload", () => {
            ws.close();
        });
    }
    connect();
}

// 页面自动连接逻辑保留，改为自动重连
const token = getCookie('jwt_token');
console.log("当前页面:", window.location.pathname, "token:", token);
if (
    window.location.pathname !== '/' &&
    window.location.pathname !== '/static/logins.html' &&
    token
) {
    connectWebSocketWithRetry(token);
}
