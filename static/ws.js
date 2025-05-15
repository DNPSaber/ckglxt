const ws = new WebSocket("wss://dnpsaber.cn/ws");

window.addEventListener("beforeunload", () => {
    ws.close();
});