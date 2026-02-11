# Nginx 配置优化指南

## 一、当前配置问题

您的当前配置存在以下可优化的地方：

1. **缺少 Gzip 压缩** - CSS/JS 文件未被压缩
2. **静态文件缓存时间短** - 只有 30 天，可延长到 1 年
3. **未区分文件类型** - 图片、CSS、JS 使用相同的缓存策略
4. **未优化图片传输** - 未启用 sendfile 优化

---

## 二、优化方案对比

| 优化项 | 当前配置 | 优化后配置 | 效果 |
|--------|----------|------------|------|
| Gzip 压缩 | 未启用 | 启用（级别 6） | CSS/JS 减少 70-80% |
| 图片缓存 | 30 天 | 1 年 | 减少重复请求 |
| CSS/JS 缓存 | 30 天 | 30 天 | 不变 |
| 字体缓存 | 30 天 | 1 年 | 减少重复请求 |
| Sendfile | 未设置 | 启用 | 提升传输速度 |

---

## 三、完整优化配置

将以下内容替换您的现有 Nginx 配置：

```nginx
server {
    listen 80;
    server_name _;  # 监听所有域名，可以改为你的域名或IP

    # 客户端上传文件大小限制
    client_max_body_size 10M;

    # ========== 开启 Gzip 压缩 ==========
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/rss+xml
        application/atom+xml
        image/svg+xml
        application/x-font-ttf
        font/opentype
        application/vnd.ms-fontobject;

    location / {
        # 转发到Flask应用
        proxy_pass http://127.0.0.1:5000;

        # 传递客户端信息
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    # ========== 静态文件配置（优化版）==========
    location /static {
        alias /opt/Home-page/static;

        # 图片文件缓存 1 年
        location ~* \.(jpg|jpeg|png|gif|webp|ico|svg)$ {
            alias /opt/Home-page/static;

            # 缓存 1 年
            expires 1y;
            add_header Cache-Control "public, immutable";

            # 启用 sendfile
            sendfile on;
            tcp_nopush on;

            # 不记录访问日志
            access_log off;
        }

        # CSS/JS 文件缓存 30 天
        location ~* \.(css|js)$ {
            alias /opt/Home-page/static;

            expires 30d;
            add_header Cache-Control "public, must-revalidate";
        }

        # 字体文件缓存 1 年
        location ~* \.(woff|woff2|ttf|otf|eot)$ {
            alias /opt/Home-page/static;

            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # 其他静态文件缓存 7 天
        expires 7d;
        add_header Cache-Control "public, must-revalidate";
    }

    # ========== 禁用访问日志的文件 ==========
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location = /robots.txt {
        access_log off;
        log_not_found off;
    }

    # ========== 防止访问隐藏文件 ==========
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

---

## 四、配置说明

### 4.1 Gzip 压缩配置

```nginx
gzip on;                          # 开启 gzip
gzip_vary on;                      # 添加 Vary 头
gzip_min_length 1000;              # 小于 1KB 的文件不压缩
gzip_comp_level 6;                 # 压缩级别（1-9，推荐 6）
gzip_types ...;                     # 压缩的文件类型
```

**效果**：
- CSS 文件压缩 70-80%
- JS 文件压缩 70-80%
- HTML 文件压缩 60-75%

### 4.2 静态文件缓存配置

| 文件类型 | 缓存时间 | 缓存策略 | 说明 |
|---------|---------|---------|------|
| 图片（jpg/png/gif/webp） | 1 年 | immutable | 图片不会频繁变化 |
| CSS/JS | 30 天 | must-revalidate | 可能会更新 |
| 字体（woff/ttf） | 1 年 | immutable | 字体很少变化 |
| 其他静态文件 | 7 天 | must-revalidate | 通用策略 |

**缓存策略说明**：
- `public, immutable`：浏览器不会检查更新，直接使用缓存
- `public, must-revalidate`：浏览器会检查 ETag，有变化才下载

### 4.3 Sendfile 优化

```nginx
sendfile on;           # 启用零拷贝传输
tcp_nopush on;        # 优化数据包发送
```

**效果**：
- 减少内存拷贝
- 降低 CPU 使用率
- 提升传输速度

---

## 五、应用配置步骤

### 步骤 1：备份当前配置

```bash
# 备份配置文件
sudo cp /etc/nginx/sites-available/your-site /etc/nginx/sites-available/your-site.backup

# 或备份主配置
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
```

### 步骤 2：编辑配置文件

```bash
# 编辑站点配置
sudo vi /etc/nginx/sites-available/your-site

# 或编辑主配置
sudo vi /etc/nginx/nginx.conf
```

将上述完整配置粘贴进去。

### 步骤 3：测试配置

```bash
# 测试配置语法
sudo nginx -t
```

如果看到以下输出，说明配置正确：
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 步骤 4：重载 Nginx

```bash
# 优雅重载（不中断服务）
sudo systemctl reload nginx

# 或重启
sudo systemctl restart nginx
```

### 步骤 5：验证配置生效

#### 方法 1：查看响应头

```bash
curl -I http://your-domain.com/static/home/images/sy.jpg
```

应该看到类似输出：
```
HTTP/1.1 200 OK
Content-Type: image/jpeg
Content-Length: 123456
Cache-Control: public, immutable
Expires: Thu, 31 Dec 2026 23:59:59 GMT
```

#### 方法 2：浏览器开发者工具

1. 打开 Chrome 浏览器
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面
5. 点击某个静态文件（如图片）
6. 查看 Response Headers：
   - 应该有 `Cache-Control: public, immutable`
   - 应该有 `Expires` 头（1 年后）
   - 如果是 CSS/JS，应该有 `Content-Encoding: gzip`

---

## 六、快速应用脚本

创建一个快速应用脚本：

```bash
#!/bin/bash
# 快速应用 Nginx 优化配置

echo "开始应用 Nginx 优化配置..."

# 备份当前配置
echo "1. 备份当前配置..."
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)

# 应用新配置
echo "2. 应用新配置..."
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
[在此处粘贴完整的配置]
EOF

# 测试配置
echo "3. 测试配置..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "4. 配置正确，重载 Nginx..."
    sudo systemctl reload nginx
    echo "✓ 配置应用成功！"
else
    echo "✗ 配置有误，请检查"
    echo "恢复备份..."
    sudo cp /etc/nginx/sites-available/default.backup.* /etc/nginx/sites-available/default
    exit 1
fi
```

---

## 七、HTTPS 配置（可选）

如果需要启用 HTTPS，添加以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 将 HTTP 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 其他配置同上...
}
```

---

## 八、性能监控

### 8.1 使用 PageSpeed Insights

访问 https://pagespeed.web.dev/ 输入你的网站 URL，查看优化建议。

### 8.2 使用 GTmetrix

访问 https://gtmetrix.com/ 输入你的网站 URL，查看详细性能报告。

### 8.3 使用 Lighthouse

在 Chrome 开发者工具中运行 Lighthouse 测试。

---

## 九、常见问题

### Q1: 配置后静态文件 404

**原因**：`alias` 路径不正确

**解决**：检查 `/opt/Home-page/static` 是否存在，或改为正确的路径

### Q2: CSS/JS 没有压缩

**原因**：`gzip_types` 未包含相应类型

**解决**：确保 `gzip_types` 包含 `text/css` 和 `application/javascript`

### Q3: 图片更新后不生效

**原因**：浏览器缓存了旧图片

**解决**：
- 添加版本号：`/static/home/images/sy.jpg?v=2`
- 或强制刷新：Ctrl + Shift + R
- 或清除浏览器缓存

### Q4: 如何回滚配置

```bash
# 恢复备份
sudo cp /etc/nginx/sites-available/default.backup /etc/nginx/sites-available/default

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 十、预期效果

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 首页 CSS 大小 | 150 KB | ~45 KB | 70% |
| 首页 JS 大小 | 200 KB | ~60 KB | 70% |
| 重复访问加载时间 | 15 秒 | <1 秒 | 99%* |
| 服务器带宽使用 | 100% | ~40% | 60% |

*启用缓存后

---

## 十一、联系支持

如有问题，请联系：
- 技术支持：dora.dong@cloud-doors.com
- 电话：13454785802

---

**文档版本**：v1.0
**更新日期**：2026-02-11
