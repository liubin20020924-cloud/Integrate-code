# Trilium 公网访问问题解决方案

> 解决公网环境下 Trilium 附件 429 错误

---

## 🔍 问题分析

### 错误日志

```
Feb 11 16:27:14 VM-16-8-opencloudos python3[1918597]: YOUR_PUBLIC_IP,127.0.0.1 - - [11/Feb/2026 16:27:14] "GET /kb/api/attachments/your-note-id HTTP/1.1" 429 330 0.001117
```

**错误代码**: `429 Too Many Requests`

### 问题原因

1. **内网地址配置**: `.env` 中 `TRILIUM_SERVER_URL=http://YOUR_INTERNAL_IP:8080` 是内网地址
2. **公网无法访问**: Flask 应用运行在公网，无法访问内网的 Trilium 服务器
3. **连接超时**: 连接 `127.0.0.1:51520` 失败（这是 Flask-Caching 使用的端口）
4. **请求积压**: 连接失败导致请求积压，触发 429 错误

---

## ✅ 解决方案

### 方案一：修改 Trilium 地址为公网地址（推荐）

#### 适用场景
- Trilium 服务器有公网 IP 或域名
- Flask 应用和 Trilium 服务器在同一公网环境

#### 修改步骤

**步骤 1**: 获取 Trilium 服务器的公网地址

```bash
# 方法1: 在 Trilium 服务器上查看公网IP
curl ifconfig.me

# 方法2: 查看服务器管理面板
# 获取公网 IP 或域名

# 方法3: 使用域名（如果已配置）
# 例如: trilium.yundour.com
```

**步骤 2**: 修改 `.env` 文件

```env
# ============================================
# Trilium 配置
# ============================================
# Trilium 服务器地址（修改为公网地址）

# 示例1: 使用公网 IP
TRILIUM_SERVER_URL=http://YOUR_PUBLIC_IP:8080
TRILIUM_SERVER_HOST=YOUR_PUBLIC_IP:8080

# 示例2: 使用域名（推荐）
TRILIUM_SERVER_URL=http://trilium.yundour.com:8080
TRILIUM_SERVER_HOST=trilium.yundour.com:8080

# Token 保持不变（使用你自己的 Token）
TRILIUM_TOKEN=your-trilium-token-here

# 登录信息
TRILIUM_LOGIN_USERNAME=
TRILIUM_LOGIN_PASSWORD=your-trilium-password
```

**步骤 3**: 重启 Flask 应用

```bash
# 停止应用
Ctrl+C

# 重新启动
python app.py
```

#### 验证方法

```bash
# 方法1: 查看 Flask 应用日志
# 应该看到类似 "Trilium 连接成功" 的日志

# 方法2: 访问知识库页面
# 浏览器访问: http://YOUR_SERVER_IP:5000/kb
# 检查图片是否正常显示

# 方法3: 测试 Trilium API
curl http://YOUR_PUBLIC_IP:8080/etapi/tree
```

---

### 方案二：配置内网穿透（如果 Trilium 没有公网）

#### 适用场景
- Trilium 服务器只有内网地址
- 不便直接配置公网 IP
- 临时快速解决

#### 选项 1: SSH 端口转发

```bash
# 在 Flask 应用服务器上执行
# 假设 Trilium 在 YOUR_INTERNAL_IP:8080

# 方式1: 本地转发
ssh -L 8080:127.0.0.1:8080 user@YOUR_INTERNAL_IP

# 方式2: 后台转发
ssh -fN -L 8080:127.0.0.1:8080 user@YOUR_INTERNAL_IP

# 然后修改 .env
TRILIUM_SERVER_URL=http://127.0.0.1:8080
TRILIUM_SERVER_HOST=127.0.0.1:8080
```

**缺点**: SSH 断开后转发失效

#### 选项 2: 使用内网代理

**修改 `.env` 文件**:

```env
# 使用内网地址
TRILIUM_SERVER_URL=http://YOUR_INTERNAL_IP:8080
TRILIUM_SERVER_HOST=YOUR_INTERNAL_IP:8080
```

**前提条件**:
- Flask 应用服务器能访问内网 `YOUR_INTERNAL_IP:8080`
- 网络配置允许访问

---

### 方案三：配置反向代理（推荐生产环境）

#### 适用场景
- Trilium 服务器有公网 IP
- 需要统一域名管理
- 需要 HTTPS 支持

#### Nginx 反向代理配置

**在 Trilium 服务器或负载均衡服务器上配置**:

```nginx
server {
    listen 80;
    server_name trilium.yundour.com;

    location / {
        # 代理到 Trilium 服务
        proxy_pass http://127.0.0.1:8080;
        
        # 传递主机信息
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（Trilium 使用）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
```

**修改 Flask 应用的 `.env`**:

```env
# 使用域名访问
TRILIUM_SERVER_URL=http://trilium.yundour.com
TRILIUM_SERVER_HOST=trilium.yundour.com
```

**优点**:
- ✅ 统一域名管理
- ✅ 可以添加 HTTPS
- ✅ 隐藏内网 IP
- ✅ 便于负载均衡

---

### 方案四：关闭 Trilium 集成（临时方案）

#### 适用场景
- 暂时不需要 Trilium 功能
- 快速恢复知识库访问

#### 修改方法

**修改 `.env` 文件**:

```env
# 设置空 Token，系统会跳过 Trilium 功能
TRILIUM_TOKEN=
```

**修改 `routes/kb_bp.py`**:

```python
# 在使用 Trilium 的地方添加检查
if not config.TRILIUM_TOKEN:
    # 使用本地数据库或返回占位内容
    return render_template('kb/content.html', content="Trilium 功能未启用")
```

---

## 🎯 推荐方案

### 生产环境部署

**推荐使用方案三（反向代理）**:

1. **配置域名**: 为 Trilium 配置公网域名（如 `trilium.yundour.com`）
2. **Nginx 代理**: 使用 Nginx 反向代理到内网 Trilium 服务
3. **修改配置**: `.env` 中使用域名访问
4. **添加 HTTPS**: 配置 SSL 证书，启用 HTTPS

**配置示例**:

```env
# Flask 应用 .env
TRILIUM_SERVER_URL=https://trilium.your-domain.com
TRILIUM_SERVER_HOST=trilium.your-domain.com
TRILIUM_TOKEN=your-trilium-token-here

# 网站配置
SITE_URL=https://www.your-domain.com
```

### 测试环境

**推荐使用方案一（直接公网地址）**:

```env
TRILIUM_SERVER_URL=http://YOUR_PUBLIC_IP:8080
TRILIUM_SERVER_HOST=YOUR_PUBLIC_IP:8080
```

---

## 🔧 故障排查

### 检查 1: Trilium 服务是否运行

```bash
# 在 Trilium 服务器上检查
curl http://127.0.0.1:8080

# 应该返回 Trilium 页面
```

### 检查 2: 网络连通性

```bash
# 从 Flask 应用服务器测试内网
curl http://YOUR_INTERNAL_IP:8080

# 如果超时，检查:
# - 防火墙规则
# - 网络连通性
# - Trilium 服务状态
```

### 检查 3: Flask 应用日志

```bash
# 查看日志中的 Trilium 连接信息
tail -f logs/app.log | grep trilium

# 正常应该看到:
# "Trilium 服务器连接成功"
# "获取笔记列表成功"
```

### 检查 4: 429 错误来源

**查看日志中的请求来源**:

```bash
# 日志显示连接的是 127.0.0.1:51520
# 这是 Flask-Caching 的 Redis 端口，不是 Trilium

# 正确应该连接到 Trilium 的端口 8080
```

---

## 📝 修改清单

### 立即修改

- [ ] 修改 `.env` 中的 `TRILIUM_SERVER_URL`
- [ ] 修改 `.env` 中的 `TRILIUM_SERVER_HOST`
- [ ] 确认 `TRILIUM_TOKEN` 正确
- [ ] 修改 `.env` 中的 `SITE_URL` 为公网地址
- [ ] 重启 Flask 应用
- [ ] 测试知识库图片显示

### 可选修改（推荐生产环境）

- [ ] 配置 Trilium 公网域名
- [ ] 配置 Nginx 反向代理
- [ ] 配置 HTTPS 证书
- [ ] 配置防火墙规则
- [ ] 监控 Trilium 服务状态

---

## 📊 配置对比

| 配置项 | 错误配置 | 正确配置（公网） |
|--------|---------|-----------------|
| `TRILIUM_SERVER_URL` | `http://YOUR_INTERNAL_IP:8080` | `http://trilium.your-domain.com` 或 `http://YOUR_PUBLIC_IP:8080` |
| `TRILIUM_SERVER_HOST` | `YOUR_INTERNAL_IP:8080` | `trilium.your-domain.com` 或 `YOUR_PUBLIC_IP:8080` |
| `SITE_URL` | `http://YOUR_INTERNAL_IP:5000` | `https://www.your-domain.com` |
| `ALLOWED_ORIGINS` | `*` | `https://www.yundour.com,https://yundour.com` |

---

## 🚀 快速修复步骤

### 最简单的方法

```bash
# 1. 编辑 .env 文件
vim .env

# 2. 修改以下两行（第 54 和 56 行）
TRILIUM_SERVER_URL=http://YOUR_PUBLIC_IP:8080
TRILIUM_SERVER_HOST=YOUR_PUBLIC_IP:8080

# 3. 修改 SITE_URL（第 71 行）
SITE_URL=http://YOUR_PUBLIC_IP:5000

# 4. 保存并重启应用
python app.py
```

### 验证修复

```bash
# 1. 查看应用启动日志
# 应该没有 Trilium 连接错误

# 2. 访问知识库
curl http://YOUR_PUBLIC_IP:5000/kb

# 3. 检查图片是否加载
# 打开浏览器，访问知识库页面
```

---

<div align="center">

**文档版本: v1.0**  
**创建日期: 2026-02-11**  
**问题**: Trilium 附件 429 错误

</div>
