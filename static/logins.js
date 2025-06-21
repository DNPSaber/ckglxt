async function logins() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error');

    errorDiv.textContent = ''; // 清空错误信息

    if (!username || !password) {
        errorDiv.textContent = '请输入用户名和密码';
        return;
    }

    // 使用 RSA 公钥加密密码
    const publicKey = `-----BEGIN PUBLIC KEY-----
        MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAk4XE/umVKmuJCtFxMEuF
        vmxOppgmRL1PZgc1Px+ILXscUVjQgL5xvL7OiKrXg/5ALI+IL80mZ3qEc7Q2c3gC
        yB9U/KhOBfUO1nQGEqKSooAhwCL7N60uoilRCzIV873ynMlpnKSVB+viWoMkICvl
        GALkaDNzBDEShDylzFPobn8Tm2IXmnq6KLam5nC/xKh997gOjmBQViCVxXUn8ClV
        qUgHw/q5LYLRl6QCEomo7SqcRmVfrL1QhXYKcFlmkIUfOEZEQ29JW/8hE+dhgkQO
        iXyXzL5udYq/+nS+I2npMta5la50XrgMhDUGLfi4iIGaf2SRDFf4eIQuGp9Nr1pc
        RQIDAQAB
        -----END PUBLIC KEY-----`;
    const encrypt = new JSEncrypt();
    encrypt.setPublicKey(publicKey);
    const encryptedPassword = encrypt.encrypt(password);

    if (!encryptedPassword) {
        errorDiv.textContent = '密码加密失败，请重试';
        return;
    }
    const deviceId = localStorage.getItem('deviceId');
    try {
        const response = await axios.post('https://dnpsaber.cn/login', {
            username: username,
            password: encryptedPassword,
            deviceID: deviceId
        });
        // 登录成功后只跳转，不主动连接 WebSocket
        alert('登录成功: ' + response.data.message);
        window.location.href = '/home';

    } catch (error) {
        errorDiv.textContent = error.response?.data?.detail || '登录失败，请稍后重试';
    }
}

function showModal(message) {
    const modal = document.getElementById("successModal");
    const modalMessage = document.getElementById("modalMessage");
    const closeModal = document.getElementById("closeModal");

    modalMessage.textContent = message;
    modal.style.display = "flex"; // 显示弹窗

    closeModal.addEventListener("click", () => {
        modal.style.display = "none"; // 关闭弹窗
    });
}


document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("button").addEventListener("click", logins);
});