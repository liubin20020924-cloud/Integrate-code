# 安全优化说明文档

本文档记录了已完成的高优先级安全优化。

## 已完成的优化项

### 1. 删除冗余文件 ✅

已删除以下冗余文件：
- `routes.py` - 已被 `routes_new.py` 替代
- `unified_user_management.html` - 已迁移到 `templates/kb/user_management.html`

**影响**: 减少代码冗余，避免混淆和维护困难。

---

### 2. 增强配置安全检查 ✅

#### 2.1 配置文件修改 (`config.py`)

**修改内容**:
```python
# 默认调试模式改为 False（更安全）
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# 默认管理员密码添加安全警告
DEFAULT_ADMIN_PASSWORD = 'YHKB@2024'  # ⚠️ 安全警告...
```

**增强的配置检查**:
- 生产环境使用默认 SECRET_KEY → **严重错误**
- 数据库密码使用默认值 → **严重错误**
- Trilium密码使用默认值 → **严重错误**
- SMTP_PASSWORD 未设置 → **严重错误**
- 默认管理员密码未修改 → 警告

#### 2.2 创建安全检查工具

新增文件：
- `scripts/check_security.py` - 快速安全配置检查
- `scripts/generate_secure_env.py` - 生成安全的环境变量配置

**使用方法**:
```bash
# 检查配置安全
python scripts/check_security.py

# 生成安全的环境变量
python scripts/generate_secure_env.py
```

---

### 3. 增强密码强度验证 ✅

#### 3.1 密码验证规则升级 (`common/validators.py`)

**普通用户密码要求**:
- 最小长度: 8位
- 必须包含: 字母 + 数字
- 禁止: 常见弱密码、纯数字、纯字母、重复字符过多

**管理员密码要求**（更严格）:
- 最小长度: 10位
- 必须包含: 大写字母 + 小写字母 + 数字 + 特殊字符
- 禁止: 常见弱密码

**禁止的弱密码列表**:
```
123456, password, qwerty, abc123, 111111,
12345678, 123456789, admin123, password123,
YHKB@2024, admin@2024, root123, test123,
1234567890, qwertyuiop, letmein, welcome,
monkey, dragon, sunshine, iloveyou,
admin, root, test, guest, passw0rd
```

#### 3.2 创建密码策略模块 (`common/password_policy.py`)

新增功能：
- `get_password_policy(role)` - 根据角色获取密码策略
- `check_password_strength(password)` - 检查密码强度
- 配置化的密码策略（易于调整）

#### 3.3 更新路由代码 (`routes_new.py`)

修改了密码修改逻辑，根据用户角色应用不同安全级别：
```python
user_role = session.get('role', 'user')
is_admin = user_role == 'admin'
is_valid, msg = validate_password(new_password, is_admin=is_admin)
```

---

### 4. 环境变量检查机制 ✅

已在 `config.py` 中实现：
- 启动时自动检查配置
- 输出警告和错误信息
- 提供 .env 文件检查

---

## 下一步操作建议

### 立即执行（必须）

1. **生成安全的环境变量配置**:
   ```bash
   python scripts/generate_secure_env.py
   ```

2. **修改 .env 文件中的占位符**:
   - SMTP_PASSWORD - 替换为邮箱授权码
   - TRILIUM_TOKEN - 替换为 Trilium ETAPI Token
   - 根据实际情况修改其他配置

3. **运行安全检查确认**:
   ```bash
   python scripts/check_security.py
   ```

4. **修改默认管理员密码**:
   登录知识库系统后，立即修改 admin 用户的密码

### 短期计划（1-2周）

5. 启用 HTTPS
6. 配置防火墙规则
7. 设置定期备份
8. 启用审计日志

### 中期计划（1个月）

9. 实施双因素认证（2FA）
10. 添加密码过期策略
11. 实施会话管理策略
12. 添加安全事件告警

---

## 安全最佳实践

### 密码管理
- ✅ 使用强密码（至少8位，包含字母和数字）
- ✅ 管理员密码使用更严格策略（10位+，包含特殊字符）
- ✅ 定期更换密码
- ❌ 不要使用默认密码
- ❌ 不要在代码中硬编码密码

### 配置管理
- ✅ 使用环境变量存储敏感信息
- ✅ .env 文件不提交到版本控制
- ✅ 生产环境关闭调试模式
- ❌ 不要使用默认 SECRET_KEY

### 访问控制
- ✅ 实施基于角色的访问控制（RBAC）
- ✅ 密码加密存储（werkzeug）
- ✅ Session 超时设置（3小时）
- ✅ 登录失败锁定机制（5次）

---

## 相关文件

| 文件 | 用途 |
|------|------|
| `config.py` | 主配置文件 |
| `.env` | 环境变量配置（需手动创建） |
| `common/validators.py` | 输入验证模块 |
| `common/password_policy.py` | 密码策略配置 |
| `scripts/check_security.py` | 安全检查工具 |
| `scripts/generate_secure_env.py` | 生成安全配置 |

---

## 故障排查

### Q: 配置检查提示错误但应用正常启动？
A: 应用会继续启动，但建议尽快修复配置错误以避免安全风险。

### Q: 如何生成 Trilium Token？
A: 在 Trilium 中进入 设置 → ETAPI，点击"Generate Token"按钮。

### Q: 密码验证失败怎么办？
A: 确保密码符合以下要求：
  - 普通用户：至少8位，包含字母和数字
  - 管理员：至少10位，包含大小写字母、数字和特殊字符

---

## 版本历史

- **2026-02-09**: 完成高优先级安全优化
  - 删除冗余文件
  - 增强配置安全检查
  - 升级密码强度验证
  - 添加环境变量检查机制
