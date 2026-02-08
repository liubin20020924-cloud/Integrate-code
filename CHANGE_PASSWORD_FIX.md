# 密码修改功能修复说明

## 问题诊断

日志显示 `/auth/api/change-password` 返回 404 错误，说明缺少后端 API 路由。

## 修复内容

### 1. 后端路由添加（routes.py）

#### 新增路由：

1. **修改密码页面路由** (`/kb/auth/change-password`)
   - 访问路径：`http://localhost:5000/kb/auth/change-password`
   - 功能：显示独立的修改密码页面

2. **修改密码API路由** (`/auth/api/change-password`)
   - 方法：POST
   - 功能：修改当前登录用户的密码
   - 验证：需要登录状态、验证旧密码、新密码长度≥6位

3. **管理员重置密码路由** (`/auth/api/reset-password/<user_id>`)
   - 方法：POST
   - 权限：仅管理员
   - 功能：管理员可以重置其他用户的密码

### 2. 前端功能

#### kb_index.html（已存在）
- 修改密码模态框已集成（第412-468行）
- JavaScript处理逻辑已存在（第930-980行）
- 用户信息栏有"修改密码"按钮

#### kb_change_password.html（新增）
- 独立的修改密码页面
- 完整的表单验证
- 现代化的UI设计

## 使用方法

### 用户修改密码

#### 方式一：通过模态框（推荐）
1. 登录知识库系统
2. 点击右上角"修改密码"按钮
3. 输入旧密码和新密码
4. 点击"保存修改"

#### 方式二：通过独立页面
1. 访问 `http://localhost:5000/kb/auth/change-password`
2. 输入旧密码和新密码
3. 点击"修改密码"

### 管理员重置密码

管理员可以通过以下方式重置用户密码：

1. 访问用户管理页面：`/kb/auth/users` 或 `/unified/users`
2. 在用户管理界面中，编辑用户时可以重置密码
3. 或调用 API：`POST /auth/api/reset-password/<user_id>`

```bash
# API调用示例
curl -X POST http://localhost:5000/auth/api/reset-password/2 \
  -H "Content-Type: application/json" \
  -d '{"password": "new_password123"}'
```

## API 接口说明

### 修改当前用户密码

**请求：**
```
POST /auth/api/change-password
Content-Type: application/json

{
  "old_password": "old_password123",
  "new_password": "new_password456"
}
```

**响应：**
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

**错误响应：**
```json
{
  "success": false,
  "message": "旧密码错误"
}
```

### 管理员重置用户密码

**请求：**
```
POST /auth/api/reset-password/<user_id>
Content-Type: application/json

{
  "password": "new_password123"
}
```

**响应：**
```json
{
  "success": true,
  "message": "用户 username 的密码已重置"
}
```

## 密码策略

- **最小长度**：6位
- **建议**：包含字母和数字
- **不能与旧密码相同**
- **新密码需两次确认**

## 安全特性

1. **旧密码验证**：必须提供正确的旧密码才能修改
2. **登录验证**：用户必须已登录
3. **管理员保护**：不能重置admin用户的密码
4. **密码加密**：使用 werkzeug 的 scrypt 加密算法
5. **登录日志**：密码修改操作会记录在日志中

## 数据库表

密码修改功能使用 `YHKB.users` 表：

```sql
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,  -- werkzeug加密密码
    `password_type` VARCHAR(10) DEFAULT 'werkzeug',
    `last_login` TIMESTAMP NULL,
    `login_attempts` INT DEFAULT 0,
    -- ...其他字段
);
```

## 测试步骤

### 测试用户修改密码
1. 使用 admin / YHKB@2024 登录
2. 点击"修改密码"按钮
3. 输入旧密码：`YHKB@2024`
4. 输入新密码：`new_password123`
5. 点击"保存修改"
6. 使用新密码重新登录验证

### 测试密码验证
1. 尝试使用错误的旧密码 → 应显示"旧密码错误"
2. 尝试使用少于6位的新密码 → 应显示"新密码长度至少为6位"
3. 尝试两次输入不一致的新密码 → 应显示"两次输入的新密码不一致"
4. 尝试使用与旧密码相同的新密码 → 应显示"新密码不能与旧密码相同"

### 测试管理员重置密码
1. 以管理员身份登录
2. 访问用户管理页面
3. 选择一个非admin用户
4. 重置该用户密码
5. 验证该用户可以使用新密码登录

## 相关文件

- **路由文件**：`routes.py`
  - 修改密码API：第221-255行
  - 修改密码页面：第220-222行
  - 管理员重置密码：第1367-1416行

- **模板文件**：
  - `templates/kb_index.html` - 集成的修改密码模态框
  - `templates/kb_change_password.html` - 独立的修改密码页面

- **认证模块**：`common/unified_auth.py`
  - `update_user_password()` 函数

## 常见问题

### Q: 修改密码后无法登录？
A: 请确认：
1. 新密码输入正确
2. 已清除浏览器缓存或使用无痕模式
3. 数据库中密码哈希已正确更新

### Q: 管理员如何重置其他用户密码？
A: 
1. 访问 `/unified/users` 用户管理页面
2. 编辑用户时可以设置新密码
3. 或使用 API `/auth/api/reset-password/<user_id>`

### Q: 如何批量重置用户密码？
A: 需要直接操作数据库或编写自定义脚本：

```sql
-- 批量重置用户密码（慎用）
UPDATE `users` 
SET password_hash = '<生成的密码哈希>',
    password_type = 'werkzeug'
WHERE role = 'user';
```

## 注意事项

1. ⚠️ 生产环境部署前，请修改默认管理员密码
2. ⚠️ 密码重置操作会记录在日志中
3. ⚠️ 建议定期提醒用户修改密码
4. ⚠️ admin用户的密码不能被其他用户重置

## 更新日志

- **2026-02-08**：
  - 添加修改密码API路由
  - 添加修改密码页面路由
  - 添加管理员重置密码功能
  - 更新数据库初始化脚本中的默认密码哈希
  - 修复密码哈希格式（scrypt vs pbkdf2）
