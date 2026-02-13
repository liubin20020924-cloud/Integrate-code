# 快速启动指南

**更新日期**: 2026-02-13
**版本**: v2.3

---

## 📋 前置条件

1. **Python 版本**: Python 3.8 或更高版本
2. **数据库**: MariaDB 或 MySQL 5.7+
3. **操作系统**: Windows / Linux / macOS

---

## 🚀 快速启动步骤

### 1. 安装依赖

```bash
# 安装所有依赖包
pip install -r requirements.txt

# 或者单独安装核心依赖
pip install Flask==3.0.3
pip install flasgger==0.9.7.1
pip install Flask-WTF==1.2.1
pip install bleach==6.0.0
pip install flask-socketio==5.3.6
```

### 2. 配置环境变量

复制示例配置文件：
```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

编辑 `.env` 文件，至少配置以下必需项：
```bash
# 必须修改的安全配置
FLASK_SECRET_KEY=your-secret-key-here
DB_PASSWORD=your-database-password-here
DEFAULT_ADMIN_PASSWORD=your-admin-password-here
```

生成安全密钥和密码：
```bash
# 生成 Flask SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 生成管理员密码
python -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16)))"
```

### 3. 初始化数据库

```bash
# 使用 MySQL 客户端
mysql -u root -p < database/init_database.sql

# 或者使用命令行
mysql -u root -p -e "source database/init_database.sql"
```

### 4. 启动应用

```bash
# Windows
python app.py

# Linux/macOS
python3 app.py
```

### 5. 访问应用

应用启动后，访问以下地址：

- **官网首页**: http://localhost:5000/
- **知识库系统**: http://localhost:5000/kb
- **工单系统**: http://localhost:5000/case
- **API 文档**: http://localhost:5000/api/docs

---

## ⚠️ 常见问题

### 问题 1: ModuleNotFoundError: No module named 'flask_swagger'

**原因**: 导入名称错误

**解决**: 已在 `app.py` 中修复，将 `from flask_swagger import Swagger` 改为 `from flasgger import Swagger`

**验证**:
```bash
python -c "from flasgger import Swagger; print('OK')"
```

### 问题 2: 缺少数据库连接

**原因**: 数据库未启动或配置错误

**解决**:
1. 检查 MySQL/MariaDB 服务是否启动
2. 检查 `.env` 中的数据库配置
3. 验证数据库用户名和密码

**验证**:
```bash
mysql -u root -p -e "SELECT 1"
```

### 问题 3: Session Cookie 错误

**原因**: SECRET_KEY 未设置或使用了默认值

**解决**: 在 `.env` 中设置 `FLASK_SECRET_KEY`

### 问题 4: CSRF Token 错误

**原因**: 表单缺少 CSRF token

**解决**: 确保所有表单都包含 `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`

### 问题 5: Windows 控制台编码错误

**原因**: 控制台不支持 Unicode 字符

**解决**: 在启动脚本中添加编码设置
```bash
# Windows CMD
chcp 65001

# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## 🔧 开发环境配置

### 启用调试模式

编辑 `.env`:
```bash
FLASK_DEBUG=True
```

### 禁用 CSRF 保护（开发环境）

编辑 `app.py`，注释掉以下代码：
```python
try:
    csrf = CSRFProtect(app)
except ImportError:
    csrf = None
```

### 使用 SQLite（开发环境）

编辑 `.env`:
```bash
DB_NAME_HOME=:memory:
```

---

## 📊 健康检查

### 检查依赖安装

```bash
# Windows
python scripts\check_dependencies.py

# Linux/macOS
python3 scripts/check_dependencies.py
```

### 检查配置

```bash
# Windows
python scripts\check_config.py

# Linux/macOS
python3 scripts/check_config.py
```

### 检查安全配置

```bash
# Windows
python scripts\check_security.py

# Linux/macOS
python3 scripts/check_security.py
```

---

## 📝 启动日志示例

**成功启动日志**:
```
预热数据库连接池...
数据库连接池初始化完成
初始化工单系统数据库...
注册路由系统...
注册SocketIO事件...
============================================================
云户科技网站启动完成
============================================================
官网首页: http://0.0.0.0:5000/
知识库系统: http://0.0.0.0:5000/kb
工单系统: http://0.0.0.0:5000/case
统一用户管理: http://0.0.0.0:5000/unified/users
API 文档: http://0.0.0.0:5000/api/docs
============================================================
```

---

## 🔐 安全检查清单

在部署到生产环境前，请确认：

- [ ] `FLASK_SECRET_KEY` 已修改为随机密钥
- [ ] `DB_PASSWORD` 已设置为强密码
- [ ] `DEFAULT_ADMIN_PASSWORD` 已修改
- [ ] `FLASK_DEBUG` 设置为 `False`
- [ ] `HTTPS_ENABLED` 设置为 `True`（如果使用 HTTPS）
- [ ] 数据库用户权限已限制
- [ ] 防火墙规则已配置
- [ ] 日志文件权限已设置

---

## 📚 相关文档

- [安全修复完成报告](SECURITY_FIXES_COMPLETE.md)
- [安全修复总结](SECURITY_FIXES_SUMMARY.md)
- [环境变量配置检查](ENV_VARIABLES_CHECK.md)
- [优化建议文档](OPTIMIZATION_RECOMMENDATIONS.md)
- [项目 README](../README.md)

---

## 💡 提示

1. **首次启动**: 建议使用调试模式，方便查看错误信息
2. **端口占用**: 如果 5000 端口被占用，可以在 `.env` 中修改 `FLASK_PORT`
3. **日志文件**: 应用日志保存在 `logs/app.log`
4. **数据库连接**: 确保数据库服务正在运行
5. **权限问题**: 确保应用有读写日志和上传文件的权限

---

**文档版本**: v1.0
**最后更新**: 2026-02-13
**维护者**: Claude AI Assistant
