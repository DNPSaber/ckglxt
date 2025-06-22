# 仓库管理系统

## 项目简介

这是一个基于FastAPI和Vue.js开发的仓库管理系统，支持多用户权限管理、库存查询、入库出库管理等功能。系统采用前后端分离架构，使用JWT进行身份验证，RSA加密保障密码安全，支持WebSocket实时通信，同时针对PC端和移动端提供了不同的用户界面。

## 技术栈

### 后端
- **FastAPI**: 高性能的Python Web框架
- **PyMySQL**: MySQL数据库连接库
- **JWT**: 用户身份验证
- **WebSocket**: 实时通信
- **SQLite**: 用户信息存储
- **RSA加密**: 密码安全保障

### 前端
- **Vue.js**: 前端MVVM框架
- **Axios**: HTTP请求库
- **JSEncrypt**: RSA加密实现
- **响应式设计**: 同时支持PC端和移动端

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

3. **系统管理**
   - 用户权限管理
   - 系统日志查看与下载
   - 数据备份与导出

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
- 现代浏览器(Chrome, Firefox, Safari, Edge等)

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/ckglxt.git
cd ckglxt
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置数据库连接
修改环境变量或配置文件，设置MySQL连接信息。

4. 生成RSA密钥对
```bash
python generate_keys.py
```

5. 运行服务
```bash
python main.py
```

默认服务将在 http://localhost:8000 启动。


## 移动端适配

系统自动识别设备类型，对移动设备提供优化的界面:
- 自适应布局
- 简化操作流程
- 触摸友好的界面元素

## 安全特性

- **JWT身份验证**: 基于时间的token验证
- **RSA密码加密**: 前端加密，保护传输安全
- **定时会话清理**: 超时自动登出
- **WebSocket心跳机制**: 保持连接活跃和及时检测断开

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
