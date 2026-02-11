# Nginx 配置文件选择指南

## 三个配置文件的区别

### 文件 1: `nginx_image_optimization.conf`
**特点**：
- 这是一个通用模板
- 只包含图片优化和缓存配置
- 没有反向代理配置
- 需要手动添加到现有配置中

**适用场景**：
- 您已经有一个完整的 Nginx 配置
- 只想添加图片优化功能
- 手动修改配置，熟悉 Nginx

**缺点**：
- ❌ 不包含 Flask 反向代理配置
- ❌ 不包含 WebSocket 支持
- ❌ 需要手动合并到现有配置

---

### 文件 2: `nginx_optimized.conf` ⭐ 推荐
**特点**：
- 完整的 server 配置块
- 包含 Flask 反向代理和 WebSocket 支持
- 添加了 Gzip 压缩和静态文件缓存优化
- 使用正则匹配优化不同类型静态资源

**适用场景**：
- 您想直接替换整个 server 配置
- 需要保留 Flask 反向代理
- 需要保留 WebSocket 支持
- 快速部署，无需手动合并

**优点**：
- ✅ 保留 Flask 反向代理（`proxy_pass http://127.0.0.1:5000`）
- ✅ 保留 WebSocket 支持
- ✅ 保留客户端 IP 传递
- ✅ 添加 Gzip 压缩
- ✅ 按文件类型优化缓存策略
- ✅ 使用正则匹配优化静态资源

**注意**：使用 `root` 指令配合正则匹配，路径为 `/opt/Home-page/static`

---

### 文件 3: `nginx_simple_static.conf` 简化版
**特点**：
- 简化的静态文件配置
- 使用 `alias` 指令直接映射
- 适合快速部署和调试

**适用场景**：
- 遇到静态文件 404 问题时使用
- 需要快速验证配置是否正确
- 学习和调试使用

**优点**：
- ✅ 配置简单清晰
- ✅ 使用 `alias` 直接映射，路径问题少
- ✅ 适合排查静态文件问题

**缺点**：
- ⚠️ 未按文件类型区分缓存策略
- ⚠️ 性能优化不如正则匹配版本

---

## 对比表格

| 功能 | nginx_image_optimization.conf | nginx_optimized.conf | nginx_simple_static.conf |
|------|---------------------------|-------------------|---------------------|
| Flask 反向代理 | ❌ | ✅ | ✅ |
| WebSocket 支持 | ❌ | ✅ | ✅ |
| 客户端 IP 传递 | ❌ | ✅ | ✅ |
| 静态文件配置 | - | `root` + 正则匹配 | `alias` 简化映射 |
| Gzip 压缩 | ✅ | ✅ | ✅ |
| 图片缓存（1年） | ✅ | ✅ | ❌ |
| CSS/JS 缓存（30天） | ✅ | ✅ | ❌ |
| 字体缓存（1年） | ✅ | ✅ | ❌ |
| 其他静态缓存（7天） | ❌ | ✅ | ✅ |
| 隐藏文件保护 | ✅ | ✅ | ✅ |
| 文件上传限制 | ❌ | ✅ | ✅ |
| 超时配置 | ❌ | ✅ | ✅ |
| **推荐场景** | 手动添加优化 | ⭐ 生产环境推荐 | 问题排查/调试 |
| **配置复杂度** | 低 | 中 | 低 |
| **性能优化** | 中 | 高 | 低 |

---

## 静态文件路径说明

### 目录结构
```
/opt/Home-page/static/
├── common.css
├── home/
│   ├── images/
│   └── css/
├── kb/
│   ├── images/
│   ├── css/
│   └── js/
└── case/
    ├── images/
    └── css/
```

### 配置对比

#### nginx_optimized.conf（使用 root）
```nginx
location /static/ {
    root /opt/Home-page;
}
# 请求 /static/home/images/Logo.jpg → /opt/Home-page/static/home/images/Logo.jpg
```

#### nginx_simple_static.conf（使用 alias）
```nginx
location /static/ {
    alias /opt/Home-page/static/;
}
# 请求 /static/home/images/Logo.jpg → /opt/Home-page/static/home/images/Logo.jpg
```

---

## 📌 推荐使用 `nginx_optimized.conf`

**原因**：
1. 保留了您所有的现有功能（反向代理、WebSocket）
2. 添加了完整的优化配置
3. 按文件类型优化缓存策略（图片1年、CSS/JS 30天、字体1年）
4. 可以直接替换，无需手动合并

---

## 使用步骤

### 使用 `nginx_optimized.conf`（推荐）

```bash
# 1. 备份当前配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 2. 复制优化配置
sudo cp docs/nginx_optimized.conf /etc/nginx/sites-available/default

# 3. 确认静态文件路径
ls -la /opt/Home-page/static/

# 4. 测试配置
sudo nginx -t

# 5. 重载 Nginx
sudo systemctl reload nginx
```

### 遇到静态文件 404 问题？

使用 `nginx_simple_static.conf` 进行排查：

```bash
# 1. 使用简化版配置
sudo cp docs/nginx_simple_static.conf /etc/nginx/sites-available/default

# 2. 测试配置
sudo nginx -t

# 3. 重载 Nginx
sudo systemctl reload nginx

# 4. 测试静态文件访问
curl -I http://localhost/static/home/images/Logo4.png
curl -I http://localhost/static/kb/images/Logo.jpg
curl -I http://localhost/static/case/images/Logo.jpg
```

### 使用 `nginx_image_optimization.conf`（需要手动合并）

如果您只想添加图片优化功能，需要将配置手动合并：

```nginx
server {
    listen 80;
    server_name _;

    # ========== 添加 Gzip 压缩 ==========
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_comp_level 6;
    gzip_types ...;

    location / {
        # 您现有的反向代理配置
        proxy_pass http://127.0.0.1:5000;
        ...
    }

    location /static {
        alias /opt/Home-page/static;

        # ========== 添加图片缓存优化 ==========
        location ~* \.(jpg|jpeg|png|gif|webp|ico|svg)$ {
            alias /opt/Home-page/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
            sendfile on;
            tcp_nopush on;
            access_log off;
        }

        # ========== 添加 CSS/JS 缓存 ==========
        location ~* \.(css|js)$ {
            alias /opt/Home-page/static;
            expires 30d;
            add_header Cache-Control "public, must-revalidate";
        }

        # ========== 添加字体缓存 ==========
        location ~* \.(woff|woff2|ttf|otf|eot)$ {
            alias /opt/Home-page/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # 其他静态文件
        expires 7d;
        add_header Cache-Control "public, must-revalidate";
    }

    # ========== 添加 favicon/robots 优化 ==========
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location = /robots.txt {
        access_log off;
        log_not_found off;
    }

    # 防止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

---

## 快速决策树

```
是否需要保留 Flask 反向代理？
  │
  ├─ 是 → 使用 nginx_optimized.conf ⭐
  │         （推荐，生产环境最佳）
  │
  └─ 否 → 使用 nginx_simple_static.conf
            （简化版，适合调试）
```

---

## 验证配置是否生效

### 方法 1：查看响应头

```bash
curl -I http://your-domain.com/static/home/images/Logo.jpg
```

应该看到：
```
Cache-Control: public, immutable
Expires: Thu, 31 Dec 2026 23:59:59 GMT
```

### 方法 2：浏览器检查

1. 打开 Chrome 浏览器
2. 按 F12 → Network 标签
3. 刷新页面
4. 点击图片文件
5. 查看 Response Headers：
   - 有 `Cache-Control: public, immutable`
   - 有 `Expires`（1 年后）

### 方法 3：检查 Gzip

访问一个 CSS 或 JS 文件，查看 Response Headers：
```
Content-Encoding: gzip
```

---

## 故障排查

### 静态文件 404 错误

**症状**：浏览器显示图片加载失败，返回 404

**解决方案**：

1. **确认静态文件路径**
```bash
ls -la /opt/Home-page/static/
ls -la /opt/Home-page/static/home/images/
ls -la /opt/Home-page/static/kb/images/
ls -la /opt/Home-page/static/case/images/
```

2. **检查 Nginx 错误日志**
```bash
sudo tail -f /var/log/nginx/error.log
```

3. **使用简化版配置测试**
```bash
sudo cp docs/nginx_simple_static.conf /etc/nginx/sites-available/default
sudo nginx -t
sudo systemctl reload nginx
```

4. **测试直接访问**
```bash
curl -I http://localhost/static/home/images/Logo4.png
```

5. **检查文件权限**
```bash
chmod -R 755 /opt/Home-page/static/
```

### 配置测试失败

```bash
# 查看详细错误
sudo nginx -t

# 常见错误：
# - 缺少分号
# - 大括号不匹配
# - 路径不存在
# - 权限不足
```

---

## 回滚方法

如果配置有问题，快速回滚：

```bash
# 恢复备份
sudo cp /etc/nginx/sites-available/default.backup /etc/nginx/sites-available/default

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 性能优化建议

### 1. 启用 Gzip 压缩

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1000;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;
```

### 2. 设置合适的缓存策略

- 图片资源：1 年（变化少）
- CSS/JS：30 天（可能更新）
- 字体文件：1 年（变化少）
- HTML 文件：不缓存或短缓存

### 3. 禁用不必要的日志

```nginx
location ~* \.(jpg|jpeg|png|gif|webp|ico|svg|woff|woff2|ttf|otf|eot)$ {
    access_log off;
}
```

### 4. 使用 sendfile

```nginx
sendfile on;
tcp_nopush on;
```

---

## 总结

| 使用场景 | 推荐文件 |
|---------|-----------|
| 完整替换配置 | `nginx_optimized.conf` ⭐ |
| 静态文件 404 问题 | `nginx_simple_static.conf` |
| 手动添加优化 | `nginx_image_optimization.conf` |
| 保留现有配置 | `nginx_optimized.conf` ⭐ |
| 快速部署 | `nginx_optimized.conf` ⭐ |

**推荐**：生产环境使用 `nginx_optimized.conf`，它提供了最佳的性能优化和缓存策略。

---

**文档版本**：v2.0
**更新日期**：2026-02-11
**更新内容**：
- 新增 `nginx_simple_static.conf` 简化版配置说明
- 更新静态文件路径说明
- 添加故障排查章节
- 更新对比表格
