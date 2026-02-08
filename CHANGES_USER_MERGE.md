# 用户表合并改动说明

## 文件改动清单

### 新增文件

1. **merge_users.sql**
   - 数据库迁移脚本
   - 包含数据迁移和表创建逻辑

2. **common/unified_auth.py**
   - 统一认证工具模块
   - 支持 werkzeug 和 md5 两种密码类型
   - 整合了原来的 `common/kb_auth.py`

3. **MERGE_USERS_GUIDE.md**
   - 详细的合并操作指南
   - 包含执行步骤、回滚方案、注意事项

4. **CHANGES_USER_MERGE.md**（本文件）
   - 改动说明文档

### 修改文件

1. **routes.py**
   - 导入 `unified_auth` 替代 `kb_auth`
   - 工单系统登录使用统一认证
   - 知识库用户管理使用 `users` 表
   - 统一用户管理 API 更新
   - 工单系统用户管理 API 更新
   - 用户统计 API 更新
   - 删除工单系统 users 表创建代码

2. **init_database.sql**
   - 在 YHKB 数据库创建统一用户表 `users`
   - 保留 mgmt_users 表标记为已废弃
   - 删除 casedb 数据库的 users 表创建语句

## 核心改动点

### 1. 统一用户表结构

**位置**：`YHKB.users`

**关键字段**：
- `password_hash`：werkzeug 密码哈希（新用户）
- `password_md5`：MD5 密码（兼容旧用户）
- `password_type`：密码类型标识（werkzeug/md5）
- `display_name` 和 `real_name`：兼容两个系统的显示名称

### 2. 统一认证机制

**文件**：`common/unified_auth.py`

**认证逻辑**：
```python
# 1. 先尝试 werkzeug 密码验证
if password_type == 'werkzeug':
    valid = check_password_hash(password_hash, password)

# 2. 如果失败，尝试 md5 密码验证
elif password_type == 'md5':
    valid = hashlib.md5(password.encode()).hexdigest() == password_md5

# 3. 都失败则认证失败
```

### 3. 工单系统登录

**改动**：`routes.py` 的 `/case/api/login` 路由

**改动前**：
- 查询 `casedb.users` 表
- 使用 MD5 密码验证
- 返回 `real_name` 字段

**改动后**：
- 使用 `authenticate_user()` 统一认证
- 自动识别密码类型
- 返回 `display_name` 或 `real_name`

### 4. 用户管理 API

**知识库用户管理**（/kb/auth/users）：
- 查询 `YHKB.users` 表
- 支持两种密码类型

**统一用户管理**（/unified/users）：
- 新增 `/unified/api/users` 端点
- 所有 CRUD 操作使用统一用户表
- 保留 `/unified/api/kb-users` 和 `/unified/api/case-users` 作为兼容路由

**工单系统用户管理**（/unified/api/case-users）：
- 查询 `YHKB.users` 表（不再查询 casedb.users）
- 筛选 role IN ('admin', 'customer')

### 5. 数据库初始化

**init_database.sql 改动**：
- 创建 `YHKB.users` 统一用户表
- 插入默认管理员到 `users` 表
- 标记 `YHKB.mgmt_users` 为已废弃
- 标记 `casedb.users` 为已废弃

## 数据迁移流程

### 自动迁移脚本

运行 `merge_users.sql` 脚本：

```bash
mysql -u root -p < merge_users.sql
```

### 迁移步骤

1. 创建 `YHKB.users` 表
2. 迁移 `mgmt_users` → `users`
   - 保持 werkzeug 密码
   - 设置 system = 'unified'
   - 设置 password_type = 'werkzeug'
3. 迁移 `casedb.users` → `users`
   - 保持 MD5 密码
   - 设置 system = 'unified'
   - 设置 password_type = 'md5'
4. 创建兼容性视图

## 兼容性说明

### 向后兼容

所有原有 API 路由保持可用：

```
/kb/auth/login           → 知识库登录
/kb/auth/users           → 知识库用户管理
/auth/api/add-user       → 添加用户
/auth/api/update-user/<id> → 更新用户
/auth/api/delete-user/<id> → 删除用户

/case/api/login          → 工单系统登录
/unified/users           → 统一用户管理
/unified/api/kb-users   → 知识库用户（兼容）
/unified/api/case-users  → 工单系统用户（兼容）
```

### 数据库视图

创建的视图保证旧代码可继续使用：

- `v_kb_users`：模拟 mgmt_users 表结构
- `v_case_users`：模拟 casedb.users 表结构

## 部署建议

### 部署顺序

1. **代码部署**
   ```bash
   git pull
   pip install -r requirements.txt  # 如有新增依赖
   ```

2. **数据库迁移**
   ```bash
   # 备份数据库
   mysqldump -u root -p YHKB > backup_YHKB.sql
   mysqldump -u root -p casedb > backup_casedb.sql

   # 执行迁移
   mysql -u root -p < merge_users.sql
   ```

3. **重启服务**
   ```bash
   # 停止服务
   python app.py stop  # 或使用 systemd stop

   # 启动服务
   python app.py start  # 或使用 systemd start
   ```

4. **功能验证**
   - 测试知识库登录
   - 测试工单系统登录
   - 测试用户管理功能

### 回滚方案

如果出现问题：

1. 恢复数据库：
   ```bash
   mysql -u root -p YHKB < backup_YHKB.sql
   mysql -u root -p casedb < backup_casedb.sql
   ```

2. 回退代码：
   ```bash
   git checkout <previous-commit>
   ```

3. 重启服务

## 注意事项

1. **密码安全**：MD5 加密较弱，建议引导用户重置密码
2. **数据备份**：迁移前务必完整备份
3. **测试验证**：迁移后全面测试所有功能
4. **渐进式清理**：旧表建议保留一段时间
5. **用户通知**：如需用户操作（如重置密码），提前通知

## 联系支持

如有问题，请参考：
- `MERGE_USERS_GUIDE.md` - 详细操作指南
- `common/unified_auth.py` - 认证逻辑实现
- `init_database.sql` - 数据库表结构
