// 注册逻辑
async function register() {
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value.trim();
    const password2 = document.getElementById('registerPassword2').value.trim();
    if (!username || !password || !password2) {
        alert('请输入用户名和两次密码');
        return;
    }
    if (password !== password2) {
        alert('两次输入的密码不一致');
        return;
    }
    // RSA加密
    const publicKey = `-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAk4XE/umVKmuJCtFxMEuF\nvmxOppgmRL1PZgc1Px+ILXscUVjQgL5xvL7OiKrXg/5ALI+IL80mZ3qEc7Q2c3gC\nyB9U/KhOBfUO1nQGEqKSooAhwCL7N60uoilRCzIV873ynMlpnKSVB+viWoMkICvl\nGALkaDNzBDEShDylzFPobn8Tm2IXmnq6KLam5nC/xKh997gOjmBQViCVxXUn8ClV\nqUgHw/q5LYLRl6QCEomo7SqcRmVfrL1QhXYKcFlmkIUfOEZEQ29JW/8hE+dhgkQO\niXyXzL5udYq/+nS+I2npMta5la50XrgMhDUGLfi4iIGaf2SRDFf4eIQuGp9Nr1pc\nRQIDAQAB\n-----END PUBLIC KEY-----`;
    const encrypt = new JSEncrypt();
    encrypt.setPublicKey(publicKey);
    const encryptedPassword = encrypt.encrypt(password);
    if (!encryptedPassword) {
        alert('密码加密失败，请重试');
        return;
    }
    try {
        const response = await axios.post('/register', {
            username: username,
            password: encryptedPassword
        });
        alert('注册成功，请登录！');
        window.location.href = '/';
    } catch (error) {
        alert(error.response?.data?.detail || '注册失败，请稍后重试');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // 注册按钮弹窗显示
    const registerBtn = document.getElementById('registerBtn');
    const registerModal = document.getElementById('registerModal');
    const registerCloseBtn = document.getElementById('registerCloseBtn');
    if (registerBtn && registerModal) {
        registerBtn.addEventListener('click', () => {
            registerModal.style.display = 'flex';
        });
    }
    if (registerCloseBtn && registerModal) {
        registerCloseBtn.addEventListener('click', () => {
            registerModal.style.display = 'none';
        });
    }
    // 密码显示/隐藏切换
    const pwdToggles = [
        { inputId: 'registerPassword', iconId: 'registerPwdToggle1' },
        { inputId: 'registerPassword2', iconId: 'registerPwdToggle2' }
    ];
    pwdToggles.forEach(({ inputId, iconId }) => {
        const input = document.getElementById(inputId);
        const icon = document.getElementById(iconId);
        if (input && icon) {
            icon.addEventListener('click', function () {
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.src = '/static/display.png';
                    icon.alt = '显示密码';
                } else {
                    input.type = 'password';
                    icon.src = '/static/hide.png';
                    icon.alt = '隐藏密码';
                }
            });
        }
    });
    // 注册确认按钮
    const btn = document.getElementById('registerConfirmBtn');
    if (btn) {
        btn.addEventListener('click', register);
    }
});
