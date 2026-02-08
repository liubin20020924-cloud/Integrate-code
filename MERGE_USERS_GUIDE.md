# 知识库用户表和工单系统用户表合并指南

## 概述

本文档说明如何将知识库用户表（YHKB.mgmt_users）和工单系统用户表（casedb.users）合并为一个统一的用户表（YHKB.users）。

## 合并方案

### 1. 统一用户表结构

新的统一用户表 `YHKB.users` 整合了两个系统的字段：

```sql
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'werkzeug加密',
    `password_md5` VARCHAR(64) COMMENT 'MD5加密（兼容旧数据）',
    `display_name` VARCHAR(100) COMMENT '显示名称',
    `real_name` VARCHAR(100) COMMENT '真实姓名',
    `email` VARCHAR(100) COMMENT '邮箱',
    `role` VARCHAR(20) DEFAULT 'user' COMMENT 'admin/user/customer',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT 'active/inactive/locked',
    `last_login` TIMESTAMP NULL,
    `login_attempts` INT DEFAULT 0,
    `password_type` VARCHAR(10) DEFAULT 'werkzeug' COMMENT 'werkzeug/md5',
    `system` VARCHAR(20) DEFAULT 'unified' COMMENT 'unified/kb/case',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `created_by` VARCHAR(50),
    INDEX idx_username (`username`),
    INDEX idx_status (`status`),
    INDEX idx_role (`role`),
    INDEX idx_system (`system`)
);
```

### 2. 密码兼容性

统一认证支持两种密码加密方式：

- **werkzeug**：新用户默认使用（知识库原有用户）
- **md5**：工单系统原有用户（兼容旧数据）

登录时自动判断密码类型进行验证：
- 优先使用 werkzeug 密码验证
- 如果失败，尝试 md5 密码验证
- 登录成功后可自动升级密码类型

### 3. 角色映射

- **admin**：管理员（知识库和工单系统通用）
- **user**：普通用户（知识库系统）
- **customer**：客户（工单系统）

## 执行步骤

### 第一步：备份数据库

在执行迁移前，请务必备份两个数据库：

```bash
mysqldump -u root -p YHKB > YHKB_backup_$(date +%Y%m%d_%H%M%S).sql
mysqldump -u root -p casedb > casedb_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 第二步：执行迁移脚本

运行合并用户表的 SQL 脚本：

```bash
mysql -u root -p < merge_users.sql
```

迁移脚本会：
1. 创建新的统一用户表 `YHKB.users`
2. 迁移知识库用户数据（mgmt_users → users）
3. 迁移工单系统用户数据（casedb.users → users）
4. 创建兼容性视图（v_kb_users, v_case_users）
5. 验证数据迁移结果

### 第三步：更新代码

代码已自动更新为使用统一用户表：

- `common/unified_auth.py`：统一认证工具，支持两种密码类型
- `routes.py`：所有用户管理API已更新为使用 `YHKB.users` 表
- `init_database.sql`：数据库初始化脚本已更新

### 第四步：测试验证

1. **测试知识库登录**
   - 访问 `/kb/auth/login`
   - 使用原有知识库用户名和密码登录

2. **测试工单系统登录**
   - 访问 `/case/` 登录页面
   - 使用原有工单系统用户名和密码登录

3. **测试统一用户管理**
   - 访问 `/unified/users`
   - 添加、编辑、删除用户

4. **验证数据完整性**
   ```sql
   -- 验证用户总数
   SELECT COUNT(*) FROM YHKB.users;

   -- 验证密码类型分布
   SELECT password_type, COUNT(*) as count
   FROM YHKB.users
   GROUP BY password_type;

   -- 验证角色分布
   SELECT role, COUNT(*) as count
   FROM YHKB.users
   GROUP BY role;
   ```

### 第五步：清理旧表（可选）

在确认迁移成功且所有功能正常后，可以保留或删除旧表：

**保留旧表作为备份（推荐）**
```sql
-- 重命名旧表
RENAME TABLE YHKB.mgmt_users TO YHKB.mgmt_users_backup;
RENAME TABLE casedb.users TO casedb.users_backup;
```

**删除旧表**
```sql
-- 删除知识库旧表
DROP TABLE YHKB.mgmt_users;

-- 删除工单系统旧表
DROP TABLE casedb.users;
```

## 兼容性说明

### API 路由兼容

所有原有 API 路由保持兼容：

**知识库用户管理：**
- `/kb/auth/users` - 用户管理页面
- `/auth/api/add-user` - 添加用户
- `/auth/api/update-user/<id>` - 更新用户
- `/auth/api/delete-user/<id>` - 删除用户

**统一用户管理：**
- `/unified/users` - 统一用户管理页面
- `/unified/api/users` - 用户列表/添加用户
- `/unified/api/users/<id>` - 更新/删除用户
- `/unified/api/kb-users` - 知识库用户（兼容）
- `/unified/api/case-users` - 工单系统用户（兼容）

**工单系统登录：**
- `/case/api/login` - 登录（自动使用统一认证）

### 数据库视图兼容

创建的视图用于向后兼容：

```sql
-- 知识库用户视图
CREATE VIEW v_kb_users AS
SELECT id, username, password_hash, display_name, role, status,
       last_login, login_attempts, created_at, updated_at, created_by
FROM `users` WHERE system IN ('unified', 'kb');

-- 工单系统用户视图
CREATE VIEW v_case_users AS
SELECT id, username, password_md5 as password, real_name, role,
       email, created_at as create_time
FROM `users` WHERE system IN ('unified', 'case');
```

## 密码升级策略

### 自动升级

当旧用户（使用 MD5 密码）登录成功后，系统会：
1. 自动将密码升级为 werkzeug 加密
2. 保留 MD5 密码作为备份
3. 更新 `password_type` 为 `werkzeug`

### 手动升级

管理员可以通过用户管理界面手动重置用户密码，重置后自动使用 werkzeug 加密。

## 注意事项

1. **数据备份**：执行迁移前务必备份数据库
2. **测试验证**：迁移后全面测试所有功能
3. **渐进式清理**：建议先保留旧表一段时间
4. **密码安全**：MD5 加密强度较低，建议引导用户重置密码
5. **角色权限**：确保用户角色映射正确，特别是 `customer` 角色用户

## 回滚方案

如果迁移出现问题，可以使用备份进行回滚：

```bash
# 恢复知识库数据库
mysql -u root -p YHKB < YHKB_backup_YYYYMMDD_HHMMSS.sql

# 恢复工单系统数据库
mysql -u root -p casedb < casedb_backup_YYYYMMDD_HHMMSS.sql

# 恢复代码版本
git checkout <previous-commit>
```

## 技术支持

如有问题，请检查：
1. 数据库连接配置（config.py）
2. 日志文件（如有）
3. 数据表结构是否符合预期

---

**执行日期**：建议选择业务低峰期执行
**预估耗时**：5-15分钟（根据数据量）
**影响范围**：知识库和工单系统的用户登录、用户管理功能
