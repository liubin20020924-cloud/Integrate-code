# 云户科技网站 - 整合项目

> 🎯 整合官网、知识库、工单三个系统的统一 Web 应用平台

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 项目简介

云户科技网站是一个全功能的 Web 应用平台，整合了三个独立但相互关联的系统：

- **官网系统** - 企业官网展示、产品介绍、解决方案展示
- **知识库系统** - 文档管理、内容搜索、Trilium 笔记集成
- **工单系统** - 客户服务、实时聊天、问题跟踪

所有系统共享统一的用户管理和认证体系，使用 Flask 框架构建，支持 MySQL/MariaDB 数据库。

---

## ✨ 主要特性

### 🏠 官网系统
- 响应式设计，支持多设备访问
- 产品展示和解决方案介绍
- 客户案例和公司介绍
- 在线联系表单
- 管理后台（留言管理）

### 📚 知识库系统
- 集成 Trilium 笔记服务
- 强大的搜索功能
- 分页浏览和分类管理
- 统一用户认证
- 管理后台（记录管理、批量操作）
- 密码强度验证（用户8位，管理员10位+）

### 🎫 工单系统
- WebSocket 实时聊天
- 工单创建和跟踪
- 邮件通知
- 客户与服务人员实时交流
- 工单状态管理
- **用户需由管理员创建**（已移除自助注册功能）

### 🔒 统一安全特性
- Werkzeug 密码加密（PBKDF2）
- Session 超时管理（3小时）
- 登录失败锁定（5次失败自动锁定）
- 基于角色的访问控制（RBAC）
- 登录日志审计
- 配置安全检查

---

## 📁 项目结构

```
Integrate-code/
├── 🐍 核心文件
│   ├── app.py                    # Flask 应用主入口
│   ├── config.py                 # 统一配置文件
│   ├── routes_new.py             # 统一路由（2155行）
│   └── requirements.txt          # Python 依赖
│
├── 🔧 公共模块 (common/)
│   ├── db_manager.py             # 数据库连接池管理
│   ├── kb_utils.py               # 知识库工具函数
│   ├── logger.py                 # 结构化日志模块
│   ├── password_policy.py         # 密码策略配置
│   ├── response.py               # 统一 API 响应
│   ├── trilium_helper.py         # Trilium 集成
│   ├── unified_auth.py           # 统一认证模块
│   └── validators.py             # 输入验证
│
├── 💼 业务逻辑 (services/)
│   └── user_service.py           # 用户服务层
│
├── 📜 工具脚本 (scripts/)
│   ├── check_config.py           # 配置安全检查
│   ├── check_security.py         # 快速安全检查
│   └── generate_secure_env.py    # 生成安全配置
│
├── 🎨 前端模板 (templates/)
│   ├── home/                     # 官网模板
│   ├── kb/                       # 知识库模板
│   ├── case/                     # 工单模板
│   └── common/                   # 通用模板
│
├── 📦 静态资源 (static/)
│   ├── common.css                # 统一样式
│   ├── home/                     # 官网资源
│   ├── kb/                       # 知识库资源
│   └── case/                     # 工单资源
│
├── 📚 文档 (docs/)
│   ├── README.md                 # 文档索引
│   ├── HOME_SYSTEM_GUIDE.md      # 官网系统说明
│   ├── KB_SYSTEM_GUIDE.md        # 知识库系统说明
│   ├── CASE_SYSTEM_GUIDE.md      # 工单系统说明
│   ├── UNIFIED_SYSTEM_GUIDE.md   # 统一用户管理说明
│   ├── SECURITY_IMPROVEMENTS.md  # 安全改进文档
│   └── CODE_STATISTICS.md        # 代码统计
│
├── 🗄️ 数据库
│   ├── init_database.sql          # 数据库初始化脚本
│   ├── .env                      # 环境变量（本地配置）
│   └── .env.example              # 环境变量示例
│
└── 🚀 启动脚本
    ├── start.bat                 # Windows 启动脚本
    └── start.sh                  # Linux/Mac 启动脚本
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- MySQL/MariaDB 5.7 或更高版本
- Trilium 笔记服务器（用于知识库功能）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- Flask 3.0.3
- Flask-SocketIO 5.3.6
- PyMySQL 1.1.0
- trilium-py 0.8.5
- python-dotenv 1.0.0

### 2. 配置环境

#### 生成安全配置（推荐）

```bash
python scripts/generate_secure_env.py
```

#### 或手动创建 .env 文件

复制 `.env.example` 为 `.env` 并修改配置：

```env
# Flask 配置
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME_HOME=clouddoors_db
DB_NAME_KB=YHKB
DB_NAME_CASE=casedb

# Trilium 配置
TRILIUM_SERVER_URL=http://127.0.0.1:8080
TRILIUM_TOKEN=your-trilium-token

# 邮件配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-email-password
```

### 3. 初始化数据库

```bash
mysql -u root -p < init_database.sql
```

这会创建三个数据库：
- `clouddoors_db` - 官网系统
- `YHKB` - 知识库系统
- `casedb` - 工单系统

### 4. 检查配置安全

```bash
python scripts/check_security.py
```

### 5. 启动应用

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**或直接运行:**
```bash
python app.py
```

### 6. 访问系统

启动成功后，访问以下地址：

| 系统 | 地址 | 说明 |
|------|------|------|
| 官网首页 | http://localhost:5000/ | 企业官网 |
| 知识库系统 | http://localhost:5000/kb | 文档管理 |
| 工单系统 | http://localhost:5000/case | 客户服务 |
| 统一用户管理 | http://localhost:5000/unified/users | 用户管理 |

---

## 🔐 默认账号

### 知识库系统

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | YHKB@2024 | 管理员 |

⚠️ **安全提示**: 生产环境请立即修改默认密码！

### 工单系统

工单系统使用统一的用户管理，**不支持自助注册**。用户账户需由管理员通过以下方式创建：

1. 访问统一用户管理：http://localhost:5000/unified/users
2. 或访问知识库用户管理：http://localhost:5000/kb/auth/users

---

## 📊 项目统计

| 类型 | 数量 | 代码行数 |
|------|------|----------|
| Python 文件 | 17 | ~4,000 行 |
| HTML 模板 | 23 | ~7,000 行 |
| CSS 样式 | 5 | ~2,600 行 |
| JavaScript | 1 | 88 行 |
| Markdown 文档 | 9 | ~3,700 行 |
| SQL 脚本 | 1 | 262 行 |
| **总计** | **105** | **~18,000+ 行** |

---

## 🔧 配置说明

### Flask 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_HOST` | 0.0.0.0 | 监听地址 |
| `FLASK_PORT` | 5000 | 服务端口 |
| `DEBUG` | False | 调试模式 |
| `SECRET_KEY` | - | Flask 密钥（必须设置） |

### 数据库配置

三个系统共用一个数据库服务器，使用三个独立的数据库：

- `clouddoors_db` - 官网系统
- `YHKB` - 知识库系统
- `casedb` - 工单系统

### 连接池配置

```python
DB_POOL_MAX_CONNECTIONS = 20  # 最大连接数
DB_POOL_MIN_CACHED = 5         # 最小缓存连接
DB_POOL_MAX_CACHED = 10        # 最大缓存连接
DB_POOL_MAX_SHARED = 5         # 最大共享连接
```

---

## 🌟 核心功能

### 统一用户认证

所有系统共享用户表和认证逻辑：

- **用户名或邮箱登录**
- **密码强度验证**
  - 普通用户：至少 8 位，包含字母和数字
  - 管理员：至少 10 位，包含大小写字母、数字和特殊字符
- **登录失败锁定**（5 次失败自动锁定）
- **Session 超时**（3 小时）
- **登录日志审计**

### WebSocket 实时通信

工单系统支持 WebSocket 实时聊天：

- 客户与服务人员实时交流
- 工单房间机制（每工单独立房间）
- 消息广播和通知
- 在线状态显示

### Trilium 集成

知识库系统集成 Trilium 笔记：

- 从 Trilium 搜索笔记
- 获取笔记内容（支持克隆笔记）
- HTML 内容清理和格式化
- 图片处理和代理

### 统一 API 响应

所有 API 使用统一的响应格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

---

## 📚 文档

详细文档请查看 [`docs/`](./docs/) 目录：

- [官网系统说明](./docs/HOME_SYSTEM_GUIDE.md)
- [知识库系统说明](./docs/KB_SYSTEM_GUIDE.md)
- [工单系统说明](./docs/CASE_SYSTEM_GUIDE.md)
- [统一用户管理说明](./docs/UNIFIED_SYSTEM_GUIDE.md)
- [安全改进文档](./docs/SECURITY_IMPROVEMENTS.md)
- [代码统计](./docs/CODE_STATISTICS.md)

---

## 🔒 安全特性

### 密码安全

- **Werkzeug PBKDF2 加密**
- **密码强度验证**
  - 普通用户：8+ 位，字母 + 数字
  - 管理员：10+ 位，大小写 + 数字 + 特殊字符
- **禁止常见弱密码**
- **密码修改需验证旧密码**

### 会话安全

- **HttpOnly Cookies**
- **SameSite=Lax**
- **3 小时超时**
- **自动清理过期 Session**

### API 安全

- **登录验证装饰器**
- **角色权限控制**
- **SQL 注入防护**（参数化查询）
- **XSS 防护**（HTML 内容清理）
- **CSRF 保护**

### 审计日志

- 登录成功/失败日志
- 登录 IP 和 User-Agent
- 用户操作日志
- 系统错误日志

---

## 🛠️ 开发指南

### 代码规范

项目遵循 PEP 8 代码规范：

- 使用 4 空格缩进
- 函数和类使用驼峰命名
- 变量使用下划线命名
- 添加类型注解和文档字符串

### 添加新路由

1. 在 `routes_new.py` 中添加路由函数
2. 使用统一响应格式
3. 添加登录验证装饰器（如需要）
4. 记录日志

### 修改配置

1. 编辑 `.env` 文件（推荐）
2. 或修改 `config.py` 中的默认值
3. 运行安全检查确认

### 数据库迁移

修改数据库结构时：

1. 更新 `init_database.sql`
2. 提供数据迁移脚本
3. 更新文档说明

---

## 🐛 故障排除

### 数据库连接失败

```bash
# 检查 MySQL 服务
systemctl status mysql

# 测试连接
mysql -h 127.0.0.1 -u root -p

# 检查防火墙
firewall-cmd --list-all
```

### 端口被占用

```bash
# 查看占用端口的进程
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # Linux/Mac

# 修改端口（编辑 .env）
FLASK_PORT=5001
```

### Trilium 连接失败

1. 确认 Trilium 服务运行中
2. 检查 `TRILIUM_SERVER_URL` 配置
3. 在 Trilium 中生成 ETAPI Token
4. 更新 `.env` 中的 `TRILIUM_TOKEN`

### WebSocket 连接失败

1. 确认安装了 `eventlet` 或 `gevent`
2. 检查防火墙设置
3. 确认使用正确的异步模式

---

## 📝 更新日志

### 2026-02-09 (v2.0)

#### 新功能
- ✅ 工单系统移除自助注册功能
- ✅ 增强密码强度验证（管理员 10 位 + 特殊字符）
- ✅ 添加配置安全检查工具
- ✅ 生成安全环境变量配置脚本
- ✅ 统一 API 响应格式
- ✅ 结构化日志系统
- ✅ 输入验证模块

#### 安全改进
- 🔒 默认调试模式改为 `False`
- 🔒 增强配置安全检查
- 🔒 密码策略配置化
- 🔒 登录失败锁定机制
- 🔒 登录日志审计

#### 文档更新
- 📚 重写所有项目文档
- 📚 添加安全改进文档
- 📚 更新代码统计

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 提交规范

- 功能: `feat: 添加新功能`
- 修复: `fix: 修复 bug`
- 文档: `docs: 更新文档`
- 重构: `refactor: 代码重构`
- 测试: `test: 添加测试`

---

## 📄 许可证

MIT License

---

## 📞 联系方式

- **邮箱**: dora.dong@cloud-doors.com
- **工单系统**: http://your-server:5000/case
- **官网**: http://your-server:5000/

---

## 🙏 致谢

感谢以下开源项目：

- [Flask](https://flask.palletsprojects.com)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io)
- [Bootstrap](https://getbootstrap.com)
- [Trilium Notes](https://github.com/zadam/trilium)

---

<div align="center">

**云户科技 © 2026**

Made with ❤️ by CloudDoors Team

</div>
