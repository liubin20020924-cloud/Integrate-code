# Trilium 429 错误解决方案

> 解决知识库图片 429 Too Many Requests 错误

---

## 🔍 问题分析

### 错误现象

```
GET /kb/api/attachments/... HTTP/1.1" 429 330 0.001117
```

### 错误原因

1. **无缓存机制**: 每次访问图片都通过 Flask 代理请求 Trilium
2. **频繁请求**: 浏览器加载页面时会同时请求多张图片
3. **触发限流**: Trilium 服务器检测到高频请求，返回 429 错误
4. **无法复用**: 相同的图片重复请求，没有缓存

### 当前流程

```
浏览器 → Flask (127.0.0.1:5000)
         ↓
    代理转发 requests.get() → Trilium (公网IP:8080)
         ↓
         429 Too Many Requests (频率限制）
```

---

## ✅ 解决方案

### 方案一：添加 Flask 端点缓存（推荐）⭐⭐⭐

#### 原理
在 Flask 层面添加响应缓存，相同图片在 TTL 期内直接返回，不再请求 Trilium。

#### 实施步骤

**步骤 1**: 安装 Flask-Caching

```bash
pip install Flask-Caching
```

**步骤 2**: 修改 `routes/api_bp.py`

```python
# routes/api_bp.py 顶部添加导入
from flask_caching import Cache
from functools import wraps

# 初始化缓存
cache = Cache(config=None, config={'CACHE_TYPE': 'simple'})

# 添加缓存装饰器
def cache_trilium_response(seconds=86400):
    """缓存 Trilium 附件响应 24 小时"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 生成缓存键
            cache_key = f"trilium_attachment:{args[0]}:{request.full_path}"
            
            # 尝试从缓存获取
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"命中缓存: {cache_key}")
                return cached
            
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result, timeout=seconds)
            logger.info(f"设置缓存: {cache_key}")
            
            return result
        return decorated_function
    return decorator
```

**步骤 3**: 修改附件代理路由

```python
@api_bp.route('/attachments/<path:attachment_path>')
@cache_trilium_response(seconds=86400)  # 缓存 24 小时
def proxy_trilium_attachment(attachment_path):
    """代理 Trilium 附件请求，使用 ETAPI"""
    try:
        # 检查 Trilium 配置
        if not hasattr(config, 'TRILIUM_SERVER_URL') or not config.TRILIUM_SERVER_URL:
            logger.error("Trilium 服务未配置")
            return error_response('Trilium 服务未配置', 500)

        server_url = config.TRILIUM_SERVER_URL.rstrip('/')
        # 构建目标 URL
        target_url = f"{server_url}/api/attachments/{attachment_path}"

        logger.info(f"代理 Trilium 附件: {target_url}")

        # 转发请求
        trilium_response = requests.get(
            target_url,
            params=request.args,
            timeout=10
        )

        # 返回响应
        return Response(
            trilium_response.content,
            status=trilium_response.status_code,
            headers={
                'Content-Type': trilium_response.headers.get('Content-Type', 'application/octet-stream'),
                'Content-Disposition': trilium_response.headers.get('Content-Disposition', ''),
                'Cache-Control': 'public, max-age=86400'  # 浏览器缓存 24 小时
            }
        )

    except requests.exceptions.Timeout:
        logger.error(f"Trilium 附件请求超时: {attachment_path}")
        return error_response('请求超时', 504)
    except Exception as e:
        logger.error(f"代理 Trilium 附件失败: {str(e)}")
        return error_response(f'代理失败: {str(e)}', 500)
```

#### 优点
- ✅ 大幅减少 Trilium 请求次数
- ✅ 相同图片只请求一次 Trilium
- ✅ 显著提升加载速度
- ✅ 避免 429 错误

#### 缺点
- ⚠️ 占用 Flask 应用内存
- ⚠️ 需要重启应用清除缓存

---

### 方案二：使用 Redis 缓存（推荐生产环境）⭐⭐⭐⭐

#### 原理
使用 Redis 存储缓存的图片内容，支持分布式和持久化。

#### 实施步骤

**步骤 1**: 安装 Redis 和依赖

```bash
# 安装 Redis
sudo apt-get install redis-server

# 启动 Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 安装 Python 客户端
pip install redis Flask-Caching
```

**步骤 2**: 修改 `.env` 配置

```env
# Redis 配置（用于图片缓存）
# ============================================
REDIS_ENABLED=True
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 缓存配置
# ============================================
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=86400
CACHE_KEY_PREFIX=yundour_
```

**步骤 3**: 修改 `app.py` 初始化缓存

```python
# app.py 顶部添加
from flask_caching import Cache

# 初始化 Redis 缓存
if config.BaseConfig.REDIS_ENABLED:
    cache_config = {
        'CACHE_TYPE': config.BaseConfig.CACHE_TYPE,
        'CACHE_REDIS_HOST': config.BaseConfig.REDIS_HOST,
        'CACHE_REDIS_PORT': config.BaseConfig.REDIS_PORT,
        'CACHE_REDIS_DB': config.BaseConfig.REDIS_DB,
        'CACHE_REDIS_PASSWORD': config.BaseConfig.REDIS_PASSWORD,
        'CACHE_KEY_PREFIX': config.BaseConfig.CACHE_KEY_PREFIX,
        'CACHE_DEFAULT_TIMEOUT': config.BaseConfig.CACHE_DEFAULT_TIMEOUT,
    }
    cache = Cache(app, config=cache_config)
    print(f"✅ Redis 缓存已启用: {config.BaseConfig.REDIS_HOST}:{config.BaseConfig.REDIS_PORT}")
else:
    # 使用内存缓存（回退）
    cache = Cache(app, config={'CACHE_TYPE': 'simple'})
    print("⚠️ 使用内存缓存（Redis 未启用）")
```

**步骤 4**: 修改附件代理路由使用缓存

```python
# routes/api_bp.py
from flask_caching import Cache
from functools import wraps

# 获取全局缓存实例
# 在 app.py 中初始化后通过 current_app 获取
def get_cache():
    from flask import current_app
    return current_app.extensions.get('cache')

# 缓存装饰器
def cache_trilium_response(seconds=86400):
    """缓存 Trilium 附件响应"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache = get_cache()
            if not cache:
                return f(*args, **kwargs)
            
            # 生成缓存键（包含文件路径和查询参数）
            cache_key = f"trilium_attachment:{args[0]}:{request.full_path}"
            
            # 尝试从缓存获取
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"✅ 命中缓存: {cache_key}")
                return cached
            
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 缓存结果（仅成功响应）
            if result.status_code == 200:
                cache.set(cache_key, result, timeout=seconds)
                logger.info(f"💾 设置缓存: {cache_key} (TTL: {seconds}s)")
            else:
                logger.warning(f"❌ 响应失败，不缓存: {result.status_code}")
            
            return result
        return decorated_function
    return decorator
```

#### 优点
- ✅ 分布式缓存支持
- ✅ 持久化存储
- ✅ 内存占用小
- ✅ 支持缓存过期
- ✅ 可查看缓存统计

#### 缺点
- ⚠️ 需要额外安装 Redis
- ⚠️ 增加系统复杂度

---

### 方案三：添加请求间隔控制（快速修复）⭐

#### 原理
添加请求队列和延迟控制，防止同时发送过多请求到 Trilium。

#### 实施步骤

```python
# routes/api_bp.py
import time
from threading import Lock
from collections import deque

# 请求队列
trilium_request_queue = deque()
trilium_request_lock = Lock()
MAX_CONCURRENT_REQUESTS = 3  # 最大并发请求数
REQUEST_INTERVAL = 0.1  # 请求间隔（秒）

def wait_for_trilium_slot():
    """等待可用的 Trilium 请求槽"""
    with trilium_request_lock:
        # 如果队列已满，等待
        while len(trilium_request_queue) >= MAX_CONCURRENT_REQUESTS:
            time.sleep(0.1)  # 等待 100ms
        
        # 添加到队列
        trilium_request_queue.append(time.time())
    
    # 短暂延迟，防止过于频繁请求
    time.sleep(REQUEST_INTERVAL)

@api_bp.route('/attachments/<path:attachment_path>')
def proxy_trilium_attachment(attachment_path):
    """代理 Trilium 附件请求"""
    # 等待可用槽
    wait_for_trilium_slot()
    
    try:
        server_url = config.TRILIUM_SERVER_URL.rstrip('/')
        target_url = f"{server_url}/api/attachments/{attachment_path}"
        logger.info(f"代理 Trilium 附件: {target_url}")
        
        trilium_response = requests.get(
            target_url,
            params=request.args,
            timeout=10
        )
        
        # 返回响应
        result = Response(
            trilium_response.content,
            status=trilium_response.status_code,
            headers={
                'Content-Type': trilium_response.headers.get('Content-Type', 'application/octet-stream'),
                'Content-Disposition': trilium_response.headers.get('Content-Disposition', ''),
                'Cache-Control': 'public, max-age=86400'
            }
        )
        return result
    
    finally:
        # 从队列移除
        with trilium_request_lock:
            if trilium_request_queue:
                trilium_request_queue.popleft()
```

#### 优点
- ✅ 快速实施
- ✅ 立即缓解 429 错误

#### 缺点
- ⚠️ 请求延迟
- ⚠️ 不减少 Trilium 总请求量

---

### 方案四：预热图片缓存（辅助方案）⭐

#### 原理
应用启动时预先请求并缓存常用图片。

#### 实施步骤

```python
# routes/api_bp.py 或 services/preload_service.py
HOT_IMAGES = [
    'KG4pRMe1gA7R/image/files%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%AE%9A%E4%BD%8D%E6%89%8B%E5%86%8C_f6f83bfe35c17.png',
    # ... 添加更多热点图片
]

def preload_hot_images():
    """预热常用图片缓存"""
    print("开始预热 Trilium 图片缓存...")
    
    for attachment_path in HOT_IMAGES:
        try:
            # 模拟请求
            with app.test_request_context():
                proxy_trilium_attachment(attachment_path)
            print(f"✅ 预热: {attachment_path[:50]}...")
            time.sleep(0.5)  # 避免请求过于频繁
        except Exception as e:
            print(f"❌ 预热失败: {attachment_path[:50]} - {e}")
    
    print("预热完成")

# 在 app.py 启动时调用
if __name__ == '__main__':
    # ... 现有代码 ...
    
    # 预热缓存
    if config.BaseConfig.TRILIUM_TOKEN:
        preload_hot_images()
    
    socketio.run(app, ...)
```

---

### 方案五：Nginx 直接代理（最佳方案）⭐⭐⭐⭐⭐

#### 原理
绕过 Flask 应用，使用 Nginx 直接代理到 Trilium，减少一层转发。

#### Nginx 配置

```nginx
# 在 Nginx 配置中添加

location /kb/api/attachments/ {
    # 直接代理到 Trilium，不经过 Flask
    proxy_pass http://YOUR_TRILIUM_IP:8080/api/attachments/;
    
    # 传递路径
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 添加缓存头
    proxy_cache trilium_cache;
    proxy_cache_key "$scheme$proxy_host$request_uri";
    proxy_cache_valid 200 24h;
    proxy_cache_use_stale error timeout updating;
    
    # 添加 Cache-Control
    add_header Cache-Control "public, max-age=86400";
    
    # 超时设置
    proxy_connect_timeout 10;
    proxy_send_timeout 10;
    proxy_read_timeout 10;
}

# 定义缓存路径
proxy_cache_path /var/cache/nginx/trilium levels=1:2 keys_zone=trilium_cache:10m inactive=24h max_size=1g;
```

#### 优点
- ✅ 性能最佳
- ✅ 不占用 Flask 应用内存
- ✅ Nginx 层缓存更高效
- ✅ 减少后端压力

#### 缺点
- ⚠️ 需要修改 Nginx 配置
- ⚠️ 需要重启 Nginx

---

## 🎯 推荐实施方案

### 短期（立即解决）⭐

**使用方案一（Flask 端点缓存）**:

1. 安装依赖：`pip install Flask-Caching`
2. 修改 `routes/api_bp.py` 添加缓存
3. 重启应用测试

**预期效果**: 
- 相同图片只请求一次 Trilium
- 429 错误大幅减少
- 图片加载速度提升 50%

---

### 中期（优化性能）⭐⭐

**使用方案二（Redis 缓存）+ 方案四（预热缓存）**:

1. 安装并配置 Redis
2. 实现缓存装饰器
3. 添加缓存预热逻辑
4. 配置监控和统计

**预期效果**:
- 缓存命中率 > 90%
- 几乎消除 429 错误
- 图片加载速度提升 80%

---

### 长期（最佳性能）⭐⭐⭐⭐⭐

**使用方案五（Nginx 直接代理）**:

1. 修改 Nginx 配置添加代理规则
2. 配置 Nginx 缓存
3. 测试缓存命中
4. 监控缓存效果

**预期效果**:
- Trilium 请求减少 99%
- 图片加载速度提升 90%
- 服务器负载降低 70%

---

## 📊 方案对比

| 方案 | 实施难度 | 性能提升 | 成本 | 推荐度 |
|------|---------|---------|------|--------|
| Flask 端点缓存 | ⭐⭐ 中 | ⬆️ 50% | 低 | ⭐⭐⭐⭐ |
| Redis 缓存 | ⭐⭐⭐ 中高 | ⬆️ 80% | 中 | ⭐⭐⭐⭐⭐ |
| 请求间隔控制 | ⭐ 低 | ⬆️ 20% | 低 | ⭐⭐⭐ |
| 预热缓存 | ⭐⭐ 低 | ⬆️ 30% | 低 | ⭐⭐ |
| Nginx 直接代理 | ⭐⭐ 中 | ⬆️ 90% | 低 | ⭐⭐⭐⭐⭐ |

---

## 🔧 快速修复步骤

### 立即实施（5分钟）

```bash
# 1. 安装 Flask-Caching
pip install Flask-Caching

# 2. 备份原文件
cp routes/api_bp.py routes/api_bp.py.backup

# 3. 添加缓存代码（见方案一）

# 4. 重启应用
python app.py

# 5. 测试
# 访问知识库页面，查看图片是否正常显示
```

---

## 📝 配置检查清单

### 修复前检查

- [ ] 确认 `.env` 中 `TRILIUM_SERVER_URL` 为公网地址
- [ ] 确认 Trilium 服务器可从公网访问
- [ ] 检查当前是否有 429 错误
- [ ] 备份现有配置和代码

### 修复后验证

- [ ] 429 错误是否消失
- [ ] 图片首次加载是否成功
- [ ] 图片再次访问是否从缓存加载
- [ ] 缓存命中率统计是否合理
- [ ] 页面加载速度是否提升

---

<div align="center">

**文档版本: v1.0**  
**创建日期: 2026-02-11**  
**问题**: Trilium 图片 429 错误

</div>
