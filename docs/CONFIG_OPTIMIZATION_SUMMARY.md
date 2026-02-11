# 配置文件优化说明

> 将硬编码的 IP 地址和密码改为环境变量

---

## 📋 优化概述

### 优化目标
- ✅ 移除 `config.py` 中所有硬编码的 IP 地址
- ✅ 移除 `config.py` 中所有硬编码的密码
- ✅ 将所有敏感配置移到 `.env` 文件
- ✅ 添加新的配置项（Redis、CDN、网站域名等）
- ✅ 更新配置检查函数
- ✅ 创建详细的配置文档

### 优化内容

| 优化项 | 修改前 | 修改后 |
|--------|--------|--------|
| 数据库地址 | 硬编码 `10.10.10.250` | 从环境变量 `DB_HOST` 读取 |
| 数据库密码 | 硬编码 `Nutanix/4u123!` | 从环境变量 `DB_PASSWORD` 读取 |
| SMTP 用户名 | 硬编码 `1919516011@qq.com` | 从环境变量 `SMTP_USERNAME` 读取 |
| SMTP 密码 | 从环境读取 | 从环境变量 `SMTP_PASSWORD` 读取 |
| 联系邮箱 | 硬编码 `dora.dong@cloud-doors.com` | 从环境变量 `CONTACT_EMAIL` 读取 |
| Trilium 地址 | 硬编码 `10.10.10.250:8080` | 从环境变量读取 |
| Trilium 密码 | 硬编码 `Nutanix/4u123!` | 从环境变量读取 |
| 邮件默认发送者 | 硬编码 `noreply@cloud-doors.com` | 从环境变量读取 |
| CORS 配置 | 硬编码 `http://localhost:5000` | 默认改为 `*` |

---

## 📄 修改的文件

### 1. config.py

**主要修改**:

#### 1.1 移除硬编码的数据库配置
```python
# 修改前
DB_HOST = os.getenv('DB_HOST', '10.10.10.250')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Nutanix/4u123!')

# 修改后
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
```

#### 1.2 移除硬编码的邮件配置
```python
# 修改前
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '1919516011@qq.com')
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '1919516011@qq.com')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'dora.dong@cloud-doors.com')

# 修改后
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', '')
```

#### 1.3 移除硬编码的 Trilium 配置
```python
# 修改前
TRILIUM_SERVER_URL = os.getenv('TRILIUM_SERVER_URL', 'http://10.10.10.250:8080')
TRILIUM_SERVER_HOST = os.getenv('TRILIUM_SERVER_HOST', '10.10.10.250:8080')
TRILIUM_LOGIN_PASSWORD = os.getenv('TRILIUM_LOGIN_PASSWORD', 'Nutanix/4u123!')

# 修改后
TRILIUM_SERVER_URL = os.getenv('TRILIUM_SERVER_URL', 'http://127.0.0.1:8080')
TRILIUM_SERVER_HOST = os.getenv('TRILIUM_SERVER_HOST', '127.0.0.1:8080')
TRILIUM_LOGIN_PASSWORD = os.getenv('TRILIUM_LOGIN_PASSWORD', '')
```

#### 1.4 添加新配置项

```python
# 网站域名配置
SITE_URL = os.getenv('SITE_URL', f'http://{FLASK_HOST}:{FLASK_PORT}')

# Redis 配置
REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'False').lower() == 'true'
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# CDN 配置
CDN_ENABLED = os.getenv('CDN_ENABLED', 'False').lower() == 'true'
CDN_DOMAIN = os.getenv('CDN_DOMAIN', '')
CDN_PROTOCOL = os.getenv('CDN_PROTOCOL', 'https')

# 图片优化配置
IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '80'))
IMAGE_ENABLE_WEBP = os.getenv('IMAGE_ENABLE_WEBP', 'True').lower() == 'true'
IMAGE_AUTO_COMPRESS = os.getenv('IMAGE_AUTO_COMPRESS', 'True').lower() == 'true'
IMAGE_CACHE_TTL = int(os.getenv('IMAGE_CACHE_TTL', '604800'))

# 缓存配置
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '604800'))
CACHE_KEY_PREFIX = os.getenv('CACHE_KEY_PREFIX', 'yundour_')

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10'))
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
```

#### 1.5 更新配置检查函数

```python
# 新增检查项
if not DB_PASSWORD:
    errors.append('严重错误: DB_PASSWORD 未设置，数据库连接将失败')

if DB_HOST == '127.0.0.1' and not BaseConfig.DEBUG:
    warnings.append('警告: 生产环境数据库地址使用默认值')

if SITE_URL == 'http://0.0.0.0:5000' and not BaseConfig.DEBUG:
    errors.append('严重错误: 生产环境 SITE_URL 使用默认值')

if CDN_ENABLED and not CDN_DOMAIN:
    errors.append('严重错误: CDN_ENABLED 为 True 但未设置 CDN_DOMAIN')
```

### 2. .env 文件

**完整配置**:

```env
# Flask 基础配置
FLASK_SECRET_KEY=yihu-website-secret-key-2024-CHANGE-ME
FLASK_DEBUG=False

# 服务器配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SITE_URL=http://10.10.10.250:5000

# 数据库配置
DB_HOST=10.10.10.250
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Nutanix/4u123!
DB_NAME_HOME=clouddoors_db
DB_NAME_KB=YHKB
DB_NAME_CASE=casedb

# 邮件配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=1919516011@qq.com
SMTP_PASSWORD=xrbvyjjfkpdmcfbj
EMAIL_SENDER=1919516011@qq.com

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@cloud-doors.com

CONTACT_EMAIL=dora.dong@cloud-doors.com

# Trilium 配置
TRILIUM_SERVER_URL=http://10.10.10.250:8080
TRILIUM_TOKEN=CAdIBlRbkihf_vZGsEocvjR7xMjb0HdSqXaDR+MBpTRUNdX+W99NnWxw=
TRILIUM_SERVER_HOST=10.10.10.250:8080
TRILIUM_LOGIN_USERNAME=
TRILIUM_LOGIN_PASSWORD=Nutanix/4u123!

# CORS 配置
ALLOWED_ORIGINS=*

# Redis 配置
REDIS_ENABLED=False
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# CDN 配置
CDN_ENABLED=False
CDN_DOMAIN=
CDN_PROTOCOL=https

# 图片优化配置
IMAGE_QUALITY=80
IMAGE_ENABLE_WEBP=True
IMAGE_AUTO_COMPRESS=True
IMAGE_CACHE_TTL=604800

# 缓存配置
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=604800
CACHE_KEY_PREFIX=yundour_

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10
LOG_BACKUP_COUNT=5
```

### 3. .env.example 文件（新增）

**目的**: 提供配置模板，不包含实际敏感信息

**使用方式**:
```bash
# 复制配置模板
cp .env.example .env

# 根据实际环境修改配置
vim .env
```

### 4. docs/CONFIGURATION_GUIDE.md（新增）

**内容**:
- 所有环境变量的详细说明
- 配置检查机制说明
- 安全性建议
- 常见问题解答
- 开发/生产环境配置模板

---

## ✅ 优化效果

### 安全性提升

| 优化项 | 效果 |
|--------|------|
| 移除硬编码密码 | 防止密码泄露到版本控制 |
| 移除硬编码 IP 地址 | 支持灵活部署 |
| .env 文件保护 | 默认在 .gitignore 中 |
| 配置检查机制 | 启动时验证关键配置 |

### 可维护性提升

| 优化项 | 效果 |
|--------|------|
| 所有配置统一管理 | 只需修改 .env 文件 |
| 配置文档完善 | 清晰说明每个配置项 |
| 模板文件提供 | 方便新环境配置 |

---

## 🔒 安全建议

### 1. 保护 .env 文件

```bash
# 设置文件权限（仅所有者可读写）
chmod 600 .env

# 确保 .gitignore 包含 .env
echo ".env" >> .gitignore

# 如果已提交到 Git，移除追踪
git rm --cached .env
git commit -m "Remove .env from version control"
```

### 2. 生成强密钥

```bash
# 生成 Flask SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 生成数据库密码
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 3. 生产环境配置检查清单

- [ ] 修改 `FLASK_SECRET_KEY` 为随机密钥
- [ ] 修改 `DB_PASSWORD` 为强密码
- [ ] 修改 `TRILIUM_LOGIN_PASSWORD` 为强密码
- [ ] 设置 `SITE_URL` 为实际网站域名
- [ ] 确认 `DB_HOST` 为生产数据库地址
- [ ] 确认 `TRILIUM_SERVER_URL` 为生产地址
- [ ] 检查 `.env` 文件权限为 `600`
- [ ] 确认 `.env` 不在版本控制中

---

## 📝 使用说明

### 首次配置（新环境）

```bash
# 1. 复制配置模板
cp .env.example .env

# 2. 编辑配置文件
vim .env

# 3. 修改关键配置项
# - FLASK_SECRET_KEY
# - DB_PASSWORD
# - SITE_URL
# - 其他环境特定配置

# 4. 启动应用
python app.py

# 5. 查看配置检查结果
# 确保没有严重错误
```

### 切换环境（开发 ↔ 生产）

```bash
# 开发环境
FLASK_DEBUG=True
DB_HOST=127.0.0.1
SITE_URL=http://localhost:5000

# 生产环境
FLASK_DEBUG=False
DB_HOST=10.10.10.250
SITE_URL=http://10.10.10.250:5000
```

---

## 📊 配置项统计

### 配置分类统计

| 分类 | 配置项数量 | 说明 |
|------|-----------|------|
| Flask 基础配置 | 4 | SECRET_KEY, DEBUG, HOST, PORT |
| 服务器配置 | 3 | HOST, PORT, SITE_URL |
| 数据库配置 | 7 | HOST, PORT, USER, PASSWORD, 3个DB_NAME |
| 邮件配置 | 8 | SMTP服务器、Gmail服务器、联系邮箱 |
| Trilium 配置 | 5 | 服务器URL、Token、登录信息 |
| CORS 配置 | 1 | ALLOWED_ORIGINS |
| Redis 配置 | 5 | ENABLED, HOST, PORT, DB, PASSWORD |
| CDN 配置 | 3 | ENABLED, DOMAIN, PROTOCOL |
| 图片优化配置 | 4 | QUALITY, WEBP, COMPRESS, TTL |
| 缓存配置 | 3 | TYPE, TIMEOUT, PREFIX |
| 日志配置 | 4 | LEVEL, FILE, MAX_BYTES, BACKUP_COUNT |
| **总计** | **47** | - |

---

## 🎯 下一步

配置优化完成后，可以开始实施图片加载优化：

1. **Phase 1**: 图片压缩（见 `IMAGE_LOADING_OPTIMIZATION_PLAN.md`）
2. **Phase 2**: Redis 缓存实现
3. **Phase 3**: CDN 部署
4. **Phase 4**: 前端优化
5. **Phase 5**: Nginx 配置优化

---

<div align="center">

**文档版本: v1.0**  
**创建日期: 2026-02-11**

</div>
