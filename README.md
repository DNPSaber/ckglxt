# 仓库管理系统 (v2.0.0)

## 项目简介

这是一个基于FastAPI和Vue.js开发的仓库管理系统，支持多用户权限管理、库存查询、入库出库管理等功能。系统采用前后端分离架构，使用JWT进行身份验证，RSA加密保障密码安全，支持WebSocket实时通信，同时针对PC端和移动端提供了不同的用户界面。

## 技术栈

### 后端
- **FastAPI**: 高性能的Python Web框架
- **PyMySQL**: MySQL数据库连接库
- **JWT**: 用户身份验证
- **WebSocket**: 实时通信和心跳机制
- **SQLite**: 用户信息存储
- **RSA加密**: 密码安全保障
- **Uvicorn**: ASGI服务器
- **PyCrypto**: 加密算法库

### 前端
- **Vue.js**: 前端MVVM框架
- **Axios**: HTTP请求库
- **JSEncrypt**: RSA加密实现
- **响应式设计**: 同时支持PC端和移动端
- **设备检测**: 自动识别设备类型并提供相应界面

## 系统功能

1. **用户管理**
   - 多级权限控制(1~5级)
   - 注册/登录/登出
   - 访客模式
   - 设备识别与自适应界面

2. **库存管理**
   - 库存查询
   - 物品入库/出库记录
   - 库存状态监控
   - 条码/二维码支持

3. **系统管理**
   - 用户权限管理
   - 系统日志查看与下载
   - 数据备份与导出
   - 批量操作支持

## 系统架构

```
+------------------+      +------------------+      +------------------+
|                  |      |                  |      |                  |
|  用户界面(前端)   <----->   FastAPI(后端)   <----->   数据库(MySQL)    |
|                  |      |                  |      |                  |
+------------------+      +------------------+      +------------------+
        |                         |
        v                         v
+------------------+      +------------------+
|                  |      |                  |
|   PC/移动设备      |      |   日志系统        |
|                  |      |                  |
+------------------+      +------------------+
```

## 权限说明

- **1级**: 访客无权限，只能查看基本信息
- **2级**: 只读权限，可以查看库存和报表
- **3级**: 修改权限，可以进行入库出库操作
- **4级**: 用户管理权限，可以管理普通用户
- **5级**: 管理员，拥有所有权限

## 部署说明

### 环境要求
- Python 3.8+
- MySQL 5.7+
- Node.js 16+ (前端开发)
- 现代浏览器(Chrome, Firefox, Safari, Edge等)

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/ckglxt.git
cd ckglxt
```

2. 安装后端依赖
```bash
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
npm install
```

4. 配置数据库连接
修改环境变量或配置文件，设置MySQL连接信息：

```bash
# Linux/MacOS
export MYSQL_NAME_LIVE2="your_username"
export MYSQL_PASSWD_LIVE2="your_password"
export MYSQL_NAME_LIVE3="your_username"
export MYSQL_PASSWD_LIVE3="your_password"
export MYSQL_NAME_LIVE4="your_username"
export MYSQL_PASSWD_LIVE4="your_password"
export MYSQL_NAME_LIVE5="your_username"
export MYSQL_PASSWD_LIVE5="your_password"

# Windows
set MYSQL_NAME_LIVE2=your_username
set MYSQL_PASSWD_LIVE2=your_password
set MYSQL_NAME_LIVE3=your_username
set MYSQL_PASSWD_LIVE3=your_password
set MYSQL_NAME_LIVE4=your_username
set MYSQL_PASSWD_LIVE4=your_password
set MYSQL_NAME_LIVE5=your_username
set MYSQL_PASSWD_LIVE5=your_password
```

5. 生成RSA密钥对
```bash
mkdir -p generate_rsa_key
python -c "from Crypto.PublicKey import RSA; key = RSA.generate(2048); open('generate_rsa_key/private.pem', 'wb').write(key.export_key()); open('generate_rsa_key/public.pem', 'wb').write(key.publickey().export_key())"
```

6. 初始化用户数据库
```bash
python init_db.py
```

7. 运行服务
```bash
python main.py
```

默认服务将在 http://localhost:8000 启动。

## 开发指南

### 目录结构
```
ckglxt/
├── static/           # 静态资源文件
├── templates/        # HTML模板
├── generate_rsa_key/ # RSA密钥
├── flastweb.py      # FastAPI主应用
├── sql_control.py   # 数据库控制器
├── log_management.py # 日志管理模块
├── main.py          # 程序入口
└── README.md        # 项目说明
```

### API文档
启动服务后，访问 http://localhost:8000/docs 查看API文档。

## 移动端适配

系统自动识别设备类型，对移动设备提供优化的界面:
- 自适应布局
- 简化操作流程
- 触摸友好的界面元素
- 针对不同权限级别提供不同移动端界面

## 安全特性

- **JWT身份验证**: 基于时间的token验证，30分钟过期
- **RSA密码加密**: 前端加密，保护传输安全
- **定时会话清理**: 超时自动登出
- **WebSocket心跳机制**: 保持连接活跃和及时检测断开
- **防XSS设置**: 安全的Cookie策略

## 更新日志

### v2.0.0 (2025-07-11)
- 增加移动端专属界面
- 优化WebSocket连接稳定性
- 添加日志下载功能
- 改进用户权限管理

### v1.0.0 (2025-06-01)
- 初始版本发布
- 基本用户管理功能
- 库存管理系统

## 许可证

本项目采用 GNU通用公共许可证 (GPL v3)。

```
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) 2025 [dnpsaber]

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

完整的GPL v3许可证文本可在[GNU官方网站](https://www.gnu.org/licenses/gpl-3.0.html)查看。

GPL许可证要求：
- 任何使用、修改或分发本软件的作品也必须以GPL许可证发布
- 必须保留源代码的版权和许可证信息
- 必须向用户提供获取源代码的方式
- 对软件的修改必须明确标注并说明修改内容
