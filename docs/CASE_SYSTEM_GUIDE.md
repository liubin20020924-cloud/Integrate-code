# 工单系统说明文档

## 概述

工单系统是云户科技的客户服务支持平台，提供完整的工单提交、处理、实时聊天和邮件通知功能。支持客户与客服人员之间的实时沟通，支持附件上传、工单状态跟踪和历史记录查询。

## 技术架构

### 后端技术
- **框架**: Flask (Python Web框架)
- **数据库**: MySQL
- **WebSocket**: Flask-SocketIO
- **邮件**: SMTP
- **密码加密**: MD5（兼容旧系统）

### 前端技术
- **HTML5**: 页面结构
- **CSS3**: 样式设计
- **JavaScript**: 交互和WebSocket
- **jQuery**: DOM操作和AJAX

## 目录结构

```
modules/case/
├── __init__.py                 # 模块初始化
└── routes.py                  # 工单路由（包含所有功能）

static/case/                    # 工单系统前端文件
├── case.css                    # 工单样式
├── logo.png                    # Logo图片
├── login.html                  # 登录页面
├── submit-ticket.html          # 提交工单页面
├── ticket-detail.html          # 工单详情页面
└── ticket-list.html            # 工单列表页面
```

## 功能模块

### 1. 用户认证

#### 1.1 客户登录

**访问路径**: `/case/login`

**功能说明**:
- 客户登录验证
- 密码使用 MD5 加密
- Session 管理

**登录字段**:
- 用户名/邮箱
- 密码

**关键代码位置**:
- 路由: `modules/case/routes.py`

**密码加密**:
```python
import hashlib
md5_password = hashlib.md5(password.encode()).hexdigest()
```

#### 1.2 管理员登录

**访问路径**: `/case/admin/login`

**功能说明**:
- 管理员登录
- 独立的登录界面
- 管理权限验证

**默认管理员账号**:
- 用户名: `admin`
- 密码: `admin123`

### 2. 工单提交

#### 2.1 提交工单页面

**访问路径**: `/case/submit`

**功能说明**:
- 填写工单信息
- 选择工单类型
- 添加详细描述
- 支持附件上传

**表单字段**:
- 客户名称
- 联系邮箱
- 联系电话
- 工单标题
- 工单类型
- 优先级
- 详细描述
- 附件

**关键代码位置**:
- 路由: `modules/case/routes.py`
- 页面: `static/case/submit-ticket.html`

#### 2.2 提交工单接口

**接口**: `POST /case/api/tickets`

**请求示例**:
```json
{
    "customer_name": "张三",
    "customer_email": "zhangsan@example.com",
    "customer_phone": "13800138000",
    "title": "系统无法登录",
    "type": "技术支持",
    "priority": "高",
    "description": "无法登录系统，提示密码错误"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "工单提交成功",
    "ticket_id": 123
}
```

### 3. 工单列表

#### 3.1 客户工单列表

**访问路径**: `/case/my-tickets`

**功能说明**:
- 查看我的工单
- 筛选和搜索
- 查看工单状态

**支持筛选**:
- 工单状态（全部/待处理/处理中/已解决/已关闭）
- 优先级
- 时间范围

**关键代码位置**:
- 路由: `modules/case/routes.py`
- 页面: `static/case/ticket-list.html`

#### 3.2 管理员工单列表

**访问路径**: `/case/admin/tickets`

**功能说明**:
- 查看所有工单
- 工单分配
- 批量操作
- 统计分析

**关键代码位置**:
- 路由: `modules/case/routes.py`

### 4. 工单详情和实时聊天

#### 4.1 工单详情页面

**访问路径**: `/case/ticket/<ticket_id>`

**功能说明**:
- 查看工单详细信息
- 实时聊天
- 查看历史消息
- 下载附件

**主要功能**:
- 实时消息推送（WebSocket）
- 发送文本消息
- 发送附件
- 工单状态更新
- 工单分配
- 邮件通知

**关键代码位置**:
- 路由: `modules/case/routes.py`
- 页面: `static/case/ticket-detail.html`

#### 4.2 实时聊天（WebSocket）

**WebSocket事件**:

**连接工单房间**:
```javascript
socket.emit('join', { ticket_id: 123 });
```

**发送消息**:
```javascript
socket.emit('send_message', {
    ticket_id: 123,
    content: '请帮我看一下这个问题'
});
```

**接收消息**:
```javascript
socket.on('receive_message', function(data) {
    console.log('新消息:', data);
});
```

**关键代码位置**:
- 服务器端: `modules/case/routes.py` (register_socketio_events)
- 客户端: `static/case/ticket-detail.html`

### 5. 工单管理

#### 5.1 更新工单状态

**接口**: `POST /case/api/tickets/<ticket_id>/status`

**请求参数**:
```json
{
    "status": "处理中"
}
```

**状态类型**:
- `待处理` (pending)
- `处理中` (processing)
- `已解决` (resolved)
- `已关闭` (closed)

#### 5.2 分配工单

**接口**: `POST /case/api/tickets/<ticket_id>/assign`

**请求参数**:
```json
{
    "assignee": "客服人员姓名"
}
```

#### 5.3 关闭工单

**接口**: `POST /case/api/tickets/<ticket_id>/close`

**请求参数**:
```json
{
    "resolution": "问题已解决"
}
```

### 6. 邮件通知

#### 6.1 新工单通知

**触发时机**: 客户提交新工单

**通知对象**: 管理员

**邮件内容**:
- 工单编号
- 工单标题
- 客户信息
- 工单描述

#### 6.2 消息通知

**触发时机**: 有新消息发送

**通知对象**: 工单相关用户

**邮件内容**:
- 工单编号
- 发送人
- 消息内容
- 工单链接

#### 6.3 状态变更通知

**触发时机**: 工单状态变更

**通知对象**: 客户

**邮件内容**:
- 工单编号
- 原状态
- 新状态
- 处理人

**关键代码位置**:
- 函数: `modules/case/routes.py` (send_email)

### 7. 附件管理

#### 7.1 上传附件

**接口**: `POST /case/api/upload`

**请求格式**: multipart/form-data

**请求参数**:
- `file`: 附件文件
- `ticket_id`: 工单ID

**限制**:
- 最大文件大小: 10MB
- 支持格式: jpg, png, pdf, doc, docx, txt, zip

**响应示例**:
```json
{
    "success": true,
    "file_url": "/uploads/123456.pdf"
}
```

#### 7.2 下载附件

**接口**: `GET /case/uploads/<filename>`

**功能**: 下载附件文件

### 8. 统计分析

#### 8.1 工单统计

**接口**: `GET /case/api/statistics`

**响应示例**:
```json
{
    "total_tickets": 100,
    "pending": 20,
    "processing": 30,
    "resolved": 40,
    "closed": 10,
    "avg_response_time": "2.5 hours"
}
```

## 数据库设计

### 数据库: casedb

#### 工单表 (tickets)

```sql
CREATE TABLE tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,    -- 工单编号
    customer_name VARCHAR(100) NOT NULL,           -- 客户名称
    customer_email VARCHAR(100) NOT NULL,          -- 客户邮箱
    customer_phone VARCHAR(20),                    -- 客户电话
    title VARCHAR(255) NOT NULL,                   -- 工单标题
    description TEXT NOT NULL,                     -- 工单描述
    type VARCHAR(50),                              -- 工单类型
    priority VARCHAR(20) DEFAULT '普通',            -- 优先级: 高/中/低
    status VARCHAR(20) DEFAULT '待处理',           -- 状态
    assignee VARCHAR(100),                         -- 处理人
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,                    -- 解决时间
    closed_at TIMESTAMP NULL,                       -- 关闭时间
    resolution TEXT                                -- 解决方案
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 消息表 (messages)

```sql
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_id INT NOT NULL,                        -- 工单ID
    sender_id INT NOT NULL,                        -- 发送者ID
    sender_name VARCHAR(100) NOT NULL,             -- 发送者名称
    sender_type ENUM('customer', 'admin') NOT NULL, -- 发送者类型
    content TEXT NOT NULL,                          -- 消息内容
    attachment_url VARCHAR(255),                    -- 附件URL
    is_system BOOLEAN DEFAULT FALSE,                -- 是否系统消息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 发送时间
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 用户表 (users)

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,          -- 用户名
    password VARCHAR(255) NOT NULL,                 -- 密码（MD5）
    email VARCHAR(100) UNIQUE,                      -- 邮箱
    phone VARCHAR(20),                              -- 电话
    full_name VARCHAR(100),                         -- 全名
    role ENUM('admin', 'customer') DEFAULT 'customer',  -- 角色
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    last_login TIMESTAMP NULL,                      -- 最后登录时间
    is_active BOOLEAN DEFAULT TRUE                  -- 是否激活
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**索引优化**:
```sql
CREATE INDEX idx_ticket_status ON tickets(status);
CREATE INDEX idx_ticket_customer ON tickets(customer_email);
CREATE INDEX idx_ticket_created ON tickets(created_at);
CREATE INDEX idx_message_ticket ON messages(ticket_id);
CREATE INDEX idx_message_created ON messages(created_at);
```

## 配置说明

### 数据库配置

在 `config.py` 中配置：

```python
# 工单数据库
DB_NAME_CASE = 'casedb'
DB_HOST = 'your-host'
DB_PORT = 3306
DB_USER = 'your-user'
DB_PASSWORD = 'your-password'
```

### 邮件配置

```python
# SMTP 服务器配置
SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 465
SMTP_USERNAME = 'your-email@qq.com'
SMTP_PASSWORD = 'your-auth-code'  # QQ邮箱授权码
EMAIL_SENDER = 'your-email@qq.com'
```

### WebSocket配置

```python
# WebSocket配置（Flask-SocketIO自动配置）
CORS_ENABLED = True
CORS_ORIGINS = "*"
```

### 附件配置

```python
# 附件上传配置
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
```

## API 接口

### 认证接口

#### 客户登录

**接口**: `POST /case/api/login`

**请求参数**:
```json
{
    "username": "customer",
    "password": "password"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "登录成功",
    "user": {
        "id": 1,
        "username": "customer",
        "email": "customer@example.com",
        "role": "customer"
    }
}
```

#### 管理员登录

**接口**: `POST /case/api/admin/login`

**请求参数**:
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "登录成功",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin"
    }
}
```

### 工单接口

#### 获取工单列表

**接口**: `GET /case/api/tickets`

**参数**:
- `status`: 状态筛选（可选）
- `type`: 类型筛选（可选）
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认20）

**响应示例**:
```json
{
    "success": true,
    "tickets": [
        {
            "id": 1,
            "ticket_number": "TK202602060001",
            "title": "系统无法登录",
            "status": "待处理",
            "priority": "高",
            "created_at": "2026-02-06 10:00:00"
        }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20
}
```

#### 获取工单详情

**接口**: `GET /case/api/tickets/<ticket_id>`

**响应示例**:
```json
{
    "success": true,
    "ticket": {
        "id": 1,
        "ticket_number": "TK202602060001",
        "customer_name": "张三",
        "customer_email": "zhangsan@example.com",
        "title": "系统无法登录",
        "description": "无法登录系统",
        "status": "处理中",
        "assignee": "客服A",
        "created_at": "2026-02-06 10:00:00"
    }
}
```

#### 获取消息列表

**接口**: `GET /case/api/tickets/<ticket_id>/messages`

**响应示例**:
```json
{
    "success": true,
    "messages": [
        {
            "id": 1,
            "sender_name": "张三",
            "sender_type": "customer",
            "content": "请帮我看一下这个问题",
            "created_at": "2026-02-06 10:05:00"
        },
        {
            "id": 2,
            "sender_name": "客服A",
            "sender_type": "admin",
            "content": "收到，我马上处理",
            "created_at": "2026-02-06 10:06:00"
        }
    ]
}
```

### WebSocket 事件

#### 加入工单房间

**客户端发送**:
```javascript
socket.emit('join', { ticket_id: 1 });
```

**服务器响应**:
```javascript
socket.emit('joined', { message: '已加入工单 #1' });
```

#### 发送消息

**客户端发送**:
```javascript
socket.emit('send_message', {
    ticket_id: 1,
    content: '请帮我看一下这个问题'
});
```

**服务器广播**:
```javascript
socket.emit('new_message', {
    ticket_id: 1,
    sender_name: '张三',
    content: '请帮我看一下这个问题',
    created_at: '2026-02-06 10:05:00'
});
```

#### 离开工单房间

**客户端发送**:
```javascript
socket.emit('leave', { ticket_id: 1 });
```

## 默认账号

### 管理员账号
- **用户名**: `admin`
- **密码**: `admin123`
- **角色**: `admin`

### 测试客户账号
- **用户名**: `customer`
- **密码**: `customer123`
- **角色**: `customer`

**注意**: 首次登录后请在统一用户管理中修改密码。

## 部署说明

### 1. 数据库初始化

```sql
-- 创建数据库
CREATE DATABASE casedb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE casedb;

-- 创建工单表
CREATE TABLE tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    type VARCHAR(50),
    priority VARCHAR(20) DEFAULT '普通',
    status VARCHAR(20) DEFAULT '待处理',
    assignee VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    resolution TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建消息表
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_id INT NOT NULL,
    sender_id INT NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    sender_type ENUM('customer', 'admin') NOT NULL,
    content TEXT NOT NULL,
    attachment_url VARCHAR(255),
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    full_name VARCHAR(100),
    role ENUM('admin', 'customer') DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建索引
CREATE INDEX idx_ticket_status ON tickets(status);
CREATE INDEX idx_ticket_customer ON tickets(customer_email);
CREATE INDEX idx_ticket_created ON tickets(created_at);
CREATE INDEX idx_message_ticket ON messages(ticket_id);
CREATE INDEX idx_message_created ON messages(created_at);

-- 创建默认管理员（密码: admin123）
INSERT INTO users (username, password, email, full_name, role)
VALUES ('admin', MD5('admin123'), 'admin@example.com', '系统管理员', 'admin');

-- 创建测试客户
INSERT INTO users (username, password, email, phone, full_name, role)
VALUES ('customer', MD5('customer123'), 'customer@example.com', '13800138000', '测试客户', 'customer');
```

### 2. 创建上传目录

```bash
mkdir -p uploads
chmod 755 uploads
```

### 3. 依赖安装

```bash
pip install flask flask-socketio flask-cors pymysql
```

### 4. 环境变量配置

创建 `.env` 文件：

```env
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME_CASE=casedb

SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-auth-code
```

### 5. 配置QQ邮箱

1. 登录 QQ邮箱
2. 进入"设置" -> "账户"
3. 开启"POP3/SMTP服务"
4. 获取授权码
5. 将授权码填入 `SMTP_PASSWORD`

### 6. 启动应用

```bash
python app.py
```

### 7. 访问工单系统

- 客户登录: `http://localhost:5000/case/login`
- 管理员登录: `http://localhost:5000/case/admin/login`
- 提交工单: `http://localhost:5000/case/submit`

## 自定义配置

### 修改工单类型

在 `static/case/submit-ticket.html` 中修改工单类型选项：

```html
<select name="type">
    <option value="技术支持">技术支持</option>
    <option value="产品咨询">产品咨询</option>
    <option value="售后服务">售后服务</option>
    <!-- 添加自定义类型 -->
</select>
```

### 修改优先级

```html
<select name="priority">
    <option value="高">高</option>
    <option value="中">中</option>
    <option value="低">低</option>
</select>
```

### 自定义邮件模板

在 `modules/case/routes.py` 的 `send_email` 函数中修改邮件内容模板。

### 修改文件上传限制

```python
# 在 config.py 中修改
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'rar'}
```

## 故障排除

### 1. WebSocket 连接失败

**症状**: 无法实时接收消息

**解决方案**:
- 检查 SocketIO 客户端版本
- 确认服务器 SocketIO 服务正常
- 检查防火墙设置
- 查看浏览器控制台错误信息

### 2. 邮件发送失败

**症状**: 无法发送邮件通知

**解决方案**:
- 确认 SMTP 配置正确
- 检查授权码是否有效
- 测试邮件发送: `telnet smtp.qq.com 465`
- 查看服务器日志获取详细错误

### 3. 附件上传失败

**症状**: 无法上传附件

**解决方案**:
- 检查 uploads 目录权限
- 确认文件大小在限制范围内
- 检查文件格式是否允许
- 查看 PHP/Python 上传错误日志

### 4. 工单提交失败

**症状**: 提交工单后无响应

**解决方案**:
- 检查数据库连接
- 确认必填字段已填写
- 查看服务器错误日志
- 测试数据库插入权限

### 5. 消息不显示

**症状**: 发送的消息不显示

**解决方案**:
- 检查 WebSocket 连接状态
- 确认是否加入了正确的房间
- 查看数据库消息是否保存
- 清除浏览器缓存后重试

## 安全建议

1. **密码安全**: 使用强密码，建议改用更安全的加密方式
2. **HTTPS**: 使用 SSL 证书加密通信
3. **输入验证**: 验证所有用户输入，防止SQL注入
4. **XSS防护**: 转义输出内容
5. **CSRF防护**: 为表单添加CSRF Token
6. **文件上传**: 验证文件类型和内容
7. **权限控制**: 严格控制工单访问权限
8. **日志审计**: 记录所有工单操作

## 性能优化

1. **数据库优化**:
   - 添加索引
   - 使用连接池
   - 优化查询语句

2. **WebSocket优化**:
   - 使用Redis作为消息队列
   - 负载均衡
   - 连接数限制

3. **静态资源优化**:
   - 启用CDN
   - 文件压缩
   - 缓存策略

## 扩展功能

### 计划添加的功能

1. **工单模板**: 预设工单模板
2. **批量操作**: 批量处理工单
3. **自动分配**: 根据类型自动分配
4. **SLA管理**: 服务级别协议
5. **知识库集成**: 关联知识库文章
6. **客户门户**: 自助服务门户
7. **报表分析**: 工单统计报表
8. **移动端适配**: 响应式设计

## 相关文档

- [项目总览](../README.md)
- [官网系统说明](./HOME_SYSTEM_GUIDE.md)
- [知识库系统说明](./KB_SYSTEM_GUIDE.md)
- [统一用户管理说明](./UNIFIED_SYSTEM_GUIDE.md)
- [统一用户管理详细指南](./UNIFIED_USER_MANAGEMENT.md)
- [代码风格指南](./STYLE_GUIDE.md)

## 技术支持

如有问题请联系：
- 邮箱: dora.dong@cloud-doors.com
- 工单系统: http://your-server:5000/case

---

**文档版本**: v1.0
**更新日期**: 2026-02-06
