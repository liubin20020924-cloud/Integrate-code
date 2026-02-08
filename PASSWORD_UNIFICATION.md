# 密码类型统一化文档

## 概述
将知识库系统的密码类型从支持 `werkzeug` 和 `md5` 两种方式，统一为只使用更安全的 `werkzeug` 加密方式。

## 修改原因
1. **安全性**：MD5 已被证明不安全，容易被彩虹表破解
2. **代码简化**：移除双密码类型支持，降低维护复杂度
3. **一致性**：所有新用户和密码重置都使用 werkzeug
4. **符合现代安全标准**：werkzeug 使用 PBKDF2-HMAC-SHA256 等现代算法

## 修改内容

### 1. `common/unified_auth.py`
- **移除**：`hashlib` 导入（不再需要MD5）
- **移除**：所有 MD5 密码验证逻辑
- **简化**：`authenticate_user()` 函数，只验证 werkzeug 密码
- **简化**：`create_user()` 函数，移除 `use_werkzeug` 参数
- **简化**：`update_user_password()` 函数，移除 `use_werkzeug` 参数

### 2. `routes.py`
- **修改**：密码修改API调用，移除 `use_werkzeug=True` 参数

### 3. `init_database_complete.sql`
- **修改**：`users` 表注释，说明 `password_md5` 已废弃
- **移除**：`real_name` 字段注释中的"兼容旧数据"

### 4. 新增 SQL 脚本
- `unify_password_type.sql`：将所有现有用户统一为 werkzeug 密码类型

## 数据库迁移步骤

### 1. 备份数据库（重要！）
```bash
mysqldump -h 10.10.10.250 -u root -p YHKB > YHKB_backup_$(date +%Y%m%d).sql
```

### 2. 执行密码类型统一脚本
```bash
mysql -h 10.10.10.250 -u root -p YHKB < unify_password_type.sql
```

### 3. 验证结果
脚本执行后会显示：
- 使用 md5 密码的用户列表（需要重置密码）
- 修复后的密码类型统计
- 所有用户状态概览

### 4. 为使用 MD5 的用户重置密码
之前使用 MD5 加密的用户无法直接登录，需要重置密码。可以通过以下方式之一：

**方式1：通过管理后台重置**
- 以 admin 用户登录
- 进入用户管理页面
- 选择需要重置密码的用户
- 重置为新密码

**方式2：通过 SQL 直接重置**
```sql
UPDATE `users`
SET password_hash = 'scrypt:32768:8:1$ZeitszjeQhBOqUJF$dbfa5f57ec9ba38892585302b8ff94cb79a77f9e73644ae32afc12087b2c39d9f3bd254eaff335baca953c4378b8e8b210b5fb9904569fd07b84ca190743b773'
WHERE username = '目标用户名';
```

### 5. 重启应用
```bash
# 停止应用
pkill -f python

# 启动应用
python app.py
# 或使用 start.bat / start.sh
```

## 测试验证

### 1. 管理员登录
```bash
用户名：admin
密码：YHKB@2024
```

### 2. 创建新用户
通过管理后台创建新用户，确认密码类型为 `werkzeug`

### 3. 修改密码
以普通用户登录，修改密码，确认密码更新成功

### 4. 查看用户记录
```sql
SELECT id, username, display_name, role, password_type, status
FROM `users`
ORDER BY id;
```

确认所有用户的 `password_type` 都是 `werkzeug`

## 向后兼容性

### 保留字段
- `password_md5` 字段保留在数据库中，但不再使用
- 这是为了避免破坏性迁移和可能的审计需求

### 已废弃功能
- ❌ 不再支持 MD5 密码加密
- ❌ 不再支持 `use_werkzeug` 参数
- ❌ 不再创建或验证 MD5 密码哈希

## 安全性改进

### Werkzeug 加密特点
- 使用 PBKDF2-HMAC-SHA256 算法
- 可配置的迭代次数（默认 260000）
- 自动加盐处理
- 抗彩虹表攻击
- 抗暴力破解

### 默认密码哈希示例
```
scrypt:32768:8:1$ZeitszjeQhBOqUJF$dbfa5f57ec9ba38892585302b8ff94cb79a77f9e73644ae32afc12087b2c39d9f3bd254eaff335baca953c4378b8e8b210b5fb9904569fd07b84ca190743b773
```

## 注意事项

1. **必须先备份数据库**：以防迁移过程中出现问题
2. **MD5 用户无法登录**：必须重置密码后才能登录
3. **批量重置**：如果有大量 MD5 用户，考虑编写批量重置脚本
4. **测试验证**：在生产环境应用前，先在测试环境验证

## 回滚方案

如果需要回滚到支持两种密码类型：

1. 恢复 `common/unified_auth.py` 的旧版本
2. 恢复 `routes.py` 的旧版本
3. 执行 `fix_password_type.sql` 恢复密码类型判断

## 相关文档

- `fix_admin_password.sql` - 管理员密码修复脚本
- `fix_password_type.sql` - 密码类型修复脚本（旧版）
- `unify_password_type.sql` - 密码类型统一脚本（新版）

## 总结

本次修改将密码系统从双类型支持简化为单一、更安全的 werkzeug 类型。虽然短期内需要为使用 MD5 的用户重置密码，但长期来看：

✅ 提升系统安全性
✅ 简化代码维护
✅ 统一密码验证逻辑
✅ 符合现代安全标准
