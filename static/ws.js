const ws = new WebSocket("wss://dnpsaber.cn/ws");

ws.onopen = function () {
    // 连接建立后，发送JWT token
    const token = localStorage.getItem('jwt_token');
    if (token) {
        ws.send(token);
    } else {
        alert("未检测到登录凭证，请重新登录");
        ws.close();
    }
};

window.addEventListener("beforeunload", () => {
    ws.close();
});