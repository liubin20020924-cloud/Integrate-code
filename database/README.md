# 数据库脚本管理文档

## 概述

本文档描述云户科技系统的数据库脚本组织结构和使用方法。系统包含三个数据库:
- `clouddoors_db` - 官网系统
- `YHKB` - 知识库系统
- `casedb` - 工单系统

## 脚本目录结构

```
database/
├── README.md                      # 本文档
├── init_database.sql              # 完整初始化脚本 v2.2 (新建环境,已包含所有补丁)
├── patches/                       # 补丁脚本目录(用于旧版本升级)
│   ├── v2.1_to_v2.2/             # 版本2.1升级到2.2
│   │   ├── 001_add_missing_columns.sql
│   │   ├── 002_extend_kb_name_length.sql
│   │   └── README.md
│   └── v2.2_to_v2.3/             # 版本2.2升级到2.3(预留)
│       └── README.md
└── legacy/                        # 旧版脚本(已废弃)
    ├── migrate_case_db.sql
    ├── patch_kb_name_length.sql
    └── README_KB_NAME_PATCH.md
```

## 使用场景

### 场景1: 全新安装(新环境)

使用 `init_database.sql` 创建所有数据库、表结构和初始数据。

**执行方式:**

```bash
# 方式1: MySQL客户端
mysql -h localhost -u root -p < database/init_database.sql

# 方式2: 登录后执行
mysql -h localhost -u root -p
mysql> source /path/to/database/init_database.sql
```

**注意事项:**
- 此脚本会创建三个新数据库
- 包含完整的表结构和初始数据
- 默认管理员账号: `admin` / `YHKB@2024`
- **版本 v2.2 已包含所有补丁内容，无需额外执行补丁脚本**

### 场景2: 升级现有数据库(已部署环境)

使用 `patches/` 目录下的补丁脚本升级现有数据库。

**版本历史:**

- **v2.0** (初始版本): 基础数据库结构
- **v2.1** (旧版本): 包含统一用户管理和工单系统
- **v2.2** (当前版本): 已合并所有补丁，包含完整字段和索引
  - 工单表新增: assignee, resolution, submit_user, customer_contact_name
  - 知识库名称字段长度: VARCHAR(500)

**升级步骤:**

```bash
# 1. 备份数据库(重要!)
mysqldump -h localhost -u root -p \
  --databases clouddoors_db YHKB casedb > backup_$(date +%Y%m%d).sql

# 2. 依次执行补丁脚本
mysql -h localhost -u root -p < database/patches/v2.1_to_v2.2/001_add_missing_columns.sql
mysql -h localhost -u root -p < database/patches/v2.1_to_v2.2/002_extend_kb_name_length.sql

# 3. 验证升级结果
# (见各补丁README中的验证步骤)
```

**注意事项:**
- 升级前务必备份数据
- 按版本顺序执行补丁
- 每个补丁都是幂等的,可重复执行

### 场景3: 部分补丁修复

如果只需要应用某个特定补丁,可以直接执行对应的SQL文件。

```bash
# 仅修复工单系统缺少字段的问题
mysql -h localhost -u root -p casedb < database/patches/v2.1_to_v2.2/001_add_missing_columns.sql

# 仅扩展知识库名称长度
mysql -h localhost -u root -p YHKB < database/patches/v2.1_to_v2.2/002_extend_kb_name_length.sql
```

## 补丁脚本说明

### v2.1_to_v2.2 升级包

**⚠️ 重要提示**: `init_database.sql` 已升级到 v2.2 版本，包含本升级包的所有内容。
- **全新安装**: 直接使用 `init_database.sql` 即可，无需执行补丁
- **从 v2.1 升级**: 需要执行以下补丁脚本

**包含补丁:**

1. **001_add_missing_columns.sql**
   - 数据库: `casedb`
   - 功能: 添加工单系统缺失的字段(assignee, resolution, submit_user, customer_contact_name)
   - 影响: 修改 `tickets` 表结构,不影响现有数据
   - 预计耗时: < 1秒

2. **002_extend_kb_name_length.sql**
   - 数据库: `YHKB`
   - 功能: 扩展 `KB_Name` 字段长度从 VARCHAR(200) 到 VARCHAR(500)
   - 影响: 修改 `KB-info` 表结构,不影响现有数据
   - 预计耗时: < 1秒

详细说明见各补丁目录下的 `README.md`。

## 数据库结构概览

### clouddoors_db (官网系统)

**表结构:**
- `messages` - 官网留言表

### YHKB (知识库系统)

**表结构:**
- `KB-info` - 知识库信息表
- `users` - 统一用户表(与工单系统共用)
- `mgmt_login_logs` - 知识库登录日志表

### casedb (工单系统)

**表结构:**
- `tickets` - 工单表
- `messages` - 工单聊天消息表

**重要:**
- `casedb.users` 表已废弃,统一使用 `YHKB.users` 表
- 工单系统通过 `submit_user` 字段关联统一用户表

## 版本管理规范

### 命名规范

**初始化脚本:**
- 文件名: `init_database.sql`
- 位置: `database/` 根目录
- 作用: 创建完整的数据库环境

**补丁脚本:**
- 目录名: `vX.Y_to_vZ.Q` (版本范围)
- 文件名: `NNN_description.sql` (序号 + 描述)
  - `NNN`: 三位数字序号(001, 002, 003...)
  - `description`: 简短描述(小写+下划线)
- 必须包含 `README.md` 说明文档

### 补丁开发规范

1. **幂等性**: 补丁可重复执行,不会报错
2. **安全性**: 不会删除数据,只修改结构
3. **可回滚**: 提供回滚SQL(在README中说明)
4. **验证性**: 包含验证SQL,确认修改成功
5. **文档化**: 详细说明变更内容和影响范围

**补丁模板:**

```sql
-- =====================================================
-- 补丁描述: [简短描述]
-- 影响数据库: [数据库名]
-- 创建时间: [YYYY-MM-DD]
-- 版本范围: v2.1 -> v2.2
-- =====================================================

USE `[数据库名]`;

-- 1. 检查是否已应用
-- (使用INFORMATION_SCHEMA检查字段/索引是否存在)

-- 2. 执行修改
-- ALTER TABLE / CREATE INDEX 等

-- 3. 验证结果
-- 查询表结构或数据确认修改成功

-- 4. 完成提示
SELECT '补丁执行完成!' AS status;
```

## 备份与恢复

### 备份

```bash
# 备份所有数据库
mysqldump -h localhost -u root -p \
  --databases clouddoors_db YHKB casedb \
  --single-transaction \
  --routines \
  --triggers \
  > backup_all_$(date +%Y%m%d_%H%M%S).sql

# 备份单个数据库
mysqldump -h localhost -u root -p \
  YHKB > backup_yhkb_$(date +%Y%m%d).sql

# 仅备份数据(不含结构)
mysqldump -h localhost -u root -p \
  --no-create-info \
  YHKB > backup_yhkb_data_$(date +%Y%m%d).sql
```

### 恢复

```bash
# 恢复所有数据库
mysql -h localhost -u root -p < backup_all_20260213.sql

# 恢复单个数据库
mysql -h localhost -u root -p YHKB < backup_yhkb_20260213.sql
```

## 常见问题

### Q1: 执行补丁时报错 "Duplicate column name"
**A:** 补丁已具备幂等性,会自动跳过已存在的字段/索引,可忽略此提示。

### Q2: 升级后数据丢失
**A:** 请立即停止应用,从备份文件恢复,并检查补丁SQL是否有删除操作。

### Q3: 如何知道当前数据库版本
**A:** 查看 `patches/` 目录下已执行的补丁,或查询数据库表结构推断版本。

### Q4: 补丁执行中断怎么办
**A:** 重新执行补丁即可,补丁已设计为幂等操作,不会重复应用变更。

### Q5: 如何回滚补丁
**A:** 查看对应补丁的 `README.md`,其中有详细的回滚SQL脚本。

## 安全建议

1. **定期备份**: 每天至少备份一次数据库
2. **升级前备份**: 执行补丁前必须备份
3. **测试环境验证**: 先在测试环境验证补丁,再应用到生产环境
4. **权限控制**: 生产环境数据库账号应限制为必需的最小权限
5. **审计日志**: 记录所有数据库变更操作

## 联系支持

如有数据库相关问题,请联系技术支持团队。

---

**最后更新**: 2026-02-13
**维护人员**: 云户科技技术团队
**文档版本**: 1.0
