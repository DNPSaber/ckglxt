const deviceId = localStorage.getItem('deviceId') ||
    crypto.randomUUID(); // 或生成指纹
localStorage.setItem('deviceId', deviceId);