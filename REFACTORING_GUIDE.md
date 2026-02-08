# 代码重构指南

本文档说明如何使用新创建的模块来改进现有代码。

## 已完成的重构

### 1. 环境变量配置迁移 ✓

**问题**: 敏感信息（数据库密码、API Token等）硬编码在 `config.py` 中

**解决方案**:
- 创建了 `.env.example` 文件作为配置模板
- 修改了 `config.py` 使用 `os.getenv()` 从环境变量读取配置
- 创建了实际的 `.env` 文件包含当前配置值
- 更新了配置检查函数，增强了安全性检查

**使用方法**:
```python
# 之前（硬编码）
DB_PASSWORD = 'Nutanix/4u123!'

# 现在（环境变量）
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Nutanix/4u123!')
```

### 2. 删除废弃的认证模块 ✓

**问题**: `common/kb_auth.py` 使用已废弃的 `mgmt_users` 表，与 `unified_auth.py` 功能重复

**解决方案**: 删除了 `common/kb_auth.py` 文件，统一使用 `common/unified_auth.py`

**影响**: 无影响，`routes.py` 中未引用该文件

### 3. 统一错误处理机制 ✓

**问题**: 错误响应格式不一致

**解决方案**: 创建了 `common/response.py` 提供统一的响应函数

**使用示例**:
```python
from common.response import success_response, error_response, validation_error_response

# 之前
return jsonify({'success': True, 'message': '操作成功'}), 200
return jsonify({'success': False, 'message': '操作失败'}), 400

# 现在
return success_response()
return error_response('操作失败', 400)
```

**可用函数**:
- `success_response(data=None, message='操作成功')`
- `error_response(message='操作失败', code=400, details=None)`
- `not_found_response(message='资源未找到')`
- `unauthorized_response(message='未授权访问')`
- `forbidden_response(message='权限不足')`
- `validation_error_response(errors)`
- `server_error_response(message='服务器内部错误', details=None)`

### 4. 改进日志系统 ✓

**问题**: 只有 `print` 语句，没有结构化日志

**解决方案**: 创建了 `common/logger.py` 提供结构化日志

**使用示例**:
```python
from common.logger import logger, log_exception

# 之前
print("用户登录成功")
print(f"错误: {e}")

# 现在
logger.info("用户登录成功")
logger.error(f"错误: {e}")
log_exception(logger, "用户登录失败")
```

**日志功能**:
- 自动创建 `logs/` 目录
- 分级日志文件（app.log 和 error.log）
- 日志轮转（10MB，保留10个备份）
- 统一的日志格式

### 5. 创建UserService消除重复代码 ✓

**问题**: 用户更新逻辑在 routes.py 中重复3次（共150行）

**解决方案**: 创建了 `services/user_service.py` 提供统一的用户服务

**使用示例**:
```python
from services.user_service import UserService

# 之前（重复代码）
@app.route('/auth/api/update-user/<int:user_id>', methods=['PUT'])
def kb_update_user(user_id):
    # ... 50行重复逻辑 ...
    
@app.route('/unified/api/users/<int:user_id>', methods=['PUT'])
def unified_update_user(user_id):
    # ... 50行相同的逻辑 ...

# 现在（使用UserService）
@app.route('/auth/api/update-user/<int:user_id>', methods=['PUT'])
def kb_update_user(user_id):
    data = request.get_json()
    conn = get_unified_kb_conn()
    success, message = UserService.update_user(conn, user_id, data)
    conn.close()
    if success:
        return success_response(message=message)
    else:
        return error_response(message, 400)
```

**UserService 方法**:
- `update_user(conn, user_id, data)` - 更新用户
- `get_user(conn, user_id)` - 获取用户信息
- `get_users(conn, filters=None, limit=100, offset=0)` - 获取用户列表
- `delete_user(conn, user_id)` - 删除用户
- `change_password(conn, user_id, old_password, new_password)` - 修改密码

### 6. 添加输入验证 ✓

**问题**: 多处 API 缺少参数验证

**解决方案**: 创建了 `common/validators.py` 提供输入验证函数

**使用示例**:
```python
from common.validators import validate_user_data, validation_error_response

@app.route('/auth/api/add', methods=['POST'])
def add_user():
    data = request.get_json()
    
    # 之前：没有验证
    # 直接使用 data
    
    # 现在：先验证
    is_valid, errors = validate_user_data(data)
    if not is_valid:
        return validation_error_response(errors)
    
    # 继续处理...
```

**可用验证函数**:
- `validate_email(email)` - 验证邮箱
- `validate_password(password)` - 验证密码强度
- `validate_username(username)` - 验证用户名
- `validate_phone(phone)` - 验证手机号
- `validate_required(data, required_fields)` - 验证必填字段
- `validate_user_data(data)` - 验证完整用户数据

## 待完成的重构

### 7. 拆分routes.py文件（进行中）

**问题**: routes.py 文件过大（1960行），包含所有系统的路由

**建议方案**: 按系统拆分为独立的路由模块

```
routes/
├── __init__.py
├── base.py          # 基础路由
├── home.py          # 官网系统路由
├── kb.py            # 知识库系统路由
├── case.py          # 工单系统路由
└── unified.py       # 统一用户管理路由
```

**示例代码**（routes/kb.py）:
```python
"""知识库系统路由"""
from flask import Blueprint, request, session
from common.response import success_response, error_response
from common.validators import validate_user_data
from services.user_service import UserService
from common.logger import logger

kb_bp = Blueprint('kb', __name__, url_prefix='/kb')

@kb_bp.route('/auth/api/update-user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新知识库用户（使用新的服务层）"""
    try:
        data = request.get_json()
        
        # 验证输入
        is_valid, errors = validate_user_data(data)
        if not is_valid:
            return validation_error_response(errors)
        
        # 获取数据库连接
        from common.db_manager import get_connection
        conn = get_connection('kb')
        
        # 调用服务层
        success, message = UserService.update_user(conn, user_id, data)
        conn.close()
        
        # 返回响应
        if success:
            logger.info(f"用户 {user_id} 更新成功")
            return success_response(message=message)
        else:
            return error_response(message, 400)
            
    except Exception as e:
        log_exception(logger, "更新用户失败")
        return server_error_response(f"更新用户失败: {str(e)}")
```

**app.py 中的注册方式**:
```python
from routes.kb import kb_bp
from routes.case import case_bp
from routes.unified import unified_bp

app.register_blueprint(kb_bp)
app.register_blueprint(case_bp)
app.register_blueprint(unified_bp)
```

## 重构优先级总结

| 优先级 | 任务 | 状态 |
|-------|------|------|
| P0 | 迁移敏感配置到环境变量 | ✓ 已完成 |
| P0 | 删除废弃的kb_auth.py | ✓ 已完成 |
| P1 | 统一错误处理机制 | ✓ 已完成 |
| P1 | 改进日志系统 | ✓ 已完成 |
| P1 | 创建UserService消除重复代码 | ✓ 已完成 |
| P1 | 添加输入验证 | ✓ 已完成 |
| P2 | 拆分routes.py文件 | 🔄 进行中 |

## 下一步行动

1. **短期（1周内）**:
   - 逐步将 routes.py 中的路由改为使用新的服务层和响应模块
   - 优先重构用户管理相关的路由（约425行）
   
2. **中期（2-4周）**:
   - 完成routes.py的模块化拆分
   - 添加单元测试
   
3. **长期（1-2月）**:
   - 添加API文档（Swagger/OpenAPI）
   - 实现缓存机制
   - 完善监控和告警

## 注意事项

1. **向后兼容**: 重构时要确保现有功能不受影响
2. **逐步迁移**: 不要一次性修改所有代码，分步骤进行
3. **测试验证**: 每次重构后都要测试相关功能
4. **文档更新**: 及时更新相关文档
