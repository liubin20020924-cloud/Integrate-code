# 快速参考 - 新模块使用指南

## 1. 环境变量配置

```python
import config

# 读取配置
db_password = config.DB_PASSWORD
smtp_password = config.SMTP_PASSWORD
trilium_token = config.TRILIUM_TOKEN
```

**注意**: 所有敏感配置现在从 `.env` 文件读取

---

## 2. 统一响应处理

```python
from common.response import (
    success_response, error_response,
    not_found_response, unauthorized_response,
    forbidden_response, validation_error_response,
    server_error_response
)

# 成功响应
return success_response(data={'id': 1}, message='创建成功')

# 错误响应
return error_response('操作失败', 400)

# 验证错误
return validation_error_response({'username': '用户名太短'})

# 404
return not_found_response('用户不存在')

# 401
return unauthorized_response('请先登录')

# 403
return forbidden_response('权限不足')

# 500
return server_error_response('服务器错误')
```

---

## 3. 日志记录

```python
from common.logger import logger, log_exception, LoggerMixin

# 记录日志
logger.info("用户登录成功")
logger.warning("警告信息")
logger.error("错误信息")

# 记录异常
try:
    # 一些可能出错的代码
    pass
except Exception as e:
    log_exception(logger, "操作失败")

# 在类中使用
class MyService(LoggerMixin):
    def do_something(self):
        self.logger.info("执行操作")
```

---

## 4. 输入验证

```python
from common.validators import (
    validate_email, validate_password,
    validate_username, validate_phone,
    validate_required, validate_user_data
)

# 验证单个字段
is_valid, msg = validate_email('test@example.com')
if not is_valid:
    return error_response(msg, 400)

# 验证必填字段
is_valid, errors = validate_required(data, ['username', 'password', 'email'])
if not is_valid:
    return validation_error_response(errors)

# 验证完整用户数据
is_valid, errors = validate_user_data(data)
if not is_valid:
    return validation_error_response(errors)
```

---

## 5. 用户服务

```python
from services.user_service import UserService
from common.db_manager import get_connection

# 获取连接
conn = get_connection('kb')

# 更新用户
success, message = UserService.update_user(conn, user_id, data)

# 获取用户
user = UserService.get_user(conn, user_id)

# 获取用户列表
users, total = UserService.get_users(
    conn,
    filters={'role': 'admin', 'status': 'active'},
    limit=20,
    offset=0
)

# 删除用户
success, message = UserService.delete_user(conn, user_id)

# 修改密码
success, message = UserService.change_password(
    conn, user_id, old_password, new_password
)

# 关闭连接
conn.close()
```

---

## 6. 完整示例：更新用户API

```python
from flask import request
from common.response import success_response, error_response, validation_error_response
from common.validators import validate_user_data
from services.user_service import UserService
from common.logger import logger
from common.db_manager import get_connection

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        # 获取数据
        data = request.get_json()
        
        # 验证输入
        is_valid, errors = validate_user_data(data)
        if not is_valid:
            return validation_error_response(errors)
        
        # 获取连接
        conn = get_connection('kb')
        if not conn:
            return server_error_response('数据库连接失败')
        
        # 调用服务
        success, message = UserService.update_user(conn, user_id, data)
        conn.close()
        
        # 返回结果
        if success:
            logger.info(f"用户 {user_id} 更新成功")
            return success_response(message=message)
        else:
            return error_response(message, 400)
            
    except Exception as e:
        from common.logger import log_exception
        log_exception(logger, "更新用户失败")
        return server_error_response(f'更新用户失败：{str(e)}')
```

---

## 7. 常见使用模式

### 模式1：带验证的创建操作
```python
data = request.get_json()
is_valid, errors = validate_user_data(data)
if not is_valid:
    return validation_error_response(errors)

# 处理逻辑
return success_response(message='创建成功')
```

### 模式2：带错误处理的操作
```python
try:
    conn = get_connection('kb')
    # 执行操作
    conn.close()
    return success_response()
except Exception as e:
    log_exception(logger, "操作失败")
    return server_error_response(str(e))
```

### 模式3：带权限检查的操作
```python
from common.unified_auth import login_required, get_current_user

@app.route('/api/admin/users', methods=['GET'])
@login_required(roles=['admin'])
def list_users():
    current_user = get_current_user()
    logger.info(f"管理员 {current_user['username']} 查询用户列表")
    # 继续处理...
```

---

## 8. 快速查表

| 任务 | 使用模块 | 函数/方法 |
|------|----------|-----------|
| 读取配置 | config | `config.DB_PASSWORD` 等 |
| 成功响应 | response | `success_response()` |
| 错误响应 | response | `error_response()` |
| 记录日志 | logger | `logger.info()` |
| 记录异常 | logger | `log_exception()` |
| 验证用户 | validators | `validate_user_data()` |
| 更新用户 | user_service | `UserService.update_user()` |
| 获取用户 | user_service | `UserService.get_user()` |
| 获取连接 | db_manager | `get_connection('kb')` |

---

## 9. 迁移检查清单

将旧代码迁移到新架构时，请检查：

- [ ] 是否使用环境变量读取配置？
- [ ] 是否使用统一的响应函数？
- [ ] 是否添加了输入验证？
- [ ] 是否记录了结构化日志？
- [ ] 是否使用了服务层而不是直接操作数据库？
- [ ] 是否正确处理了异常？
- [ ] 是否关闭了数据库连接？

---

## 10. 获取帮助

- 查看详细重构指南：`REFACTORING_GUIDE.md`
- 查看优化总结：`OPTIMIZATION_SUMMARY.md`
- 查看路由示例：`routes_refactored_example.py`
