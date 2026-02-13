# v2.1_to_v2.2 升级包说明

## 概述

此升级包包含从 v2.1 版本升级到 v2.2 版本所需的所有数据库补丁。

## 版本信息

- **起始版本**: v2.1
- **目标版本**: v2.2
- **发布日期**: 2026-02-13
- **兼容数据库**: MariaDB/MySQL 5.7+

## 补丁列表

### 1. 001_add_missing_columns.sql

**描述**: 添加工单系统缺失字段

**影响范围**:
- 数据库: `casedb`
- 表: `tickets`
- 新增字段:
  - `assignee` - 处理人(VARCHAR(100))
  - `resolution` - 解决方案(TEXT)
  - `submit_user` - 提交工单的用户名(VARCHAR(100))
  - `customer_contact_name` - 客户联系人姓名(VARCHAR(100))
- 新增索引:
  - `idx_assignee`
  - `idx_submit_user`
  - `idx_customer_contact_name`

**预计耗时**: < 1秒

**数据影响**: 仅修改表结构,不影响现有数据

**详细说明**: 见脚本文件注释

---

### 2. 002_extend_kb_name_length.sql

**描述**: 扩展知识库名称字段长度

**影响范围**:
- 数据库: `YHKB`
- 表: `KB-info`
- 修改字段:
  - `KB_Name` - VARCHAR(200) → VARCHAR(500)

**预计耗时**: < 1秒

**数据影响**: 仅修改字段长度上限,不影响现有数据

**详细说明**: 见脚本文件注释

---

## 升级步骤

### 1. 升级前准备

#### 1.1 备份数据库(必须!)

```bash
# 备份所有数据库
mysqldump -h localhost -u root -p \
  --databases clouddoors_db YHKB casedb \
  --single-transaction \
  --routines \
  --triggers \
  > backup_pre_v2.2_$(date +%Y%m%d_%H%M%S).sql

# 验证备份文件
ls -lh backup_pre_v2.2_*.sql
```

#### 1.2 检查当前版本

查看数据库表结构,确认是否已应用过相关补丁:

```sql
-- 检查 casedb.tickets 表
USE casedb;
SHOW COLUMNS FROM tickets;

-- 检查 YHKB.KB-info 表
USE YHKB;
SHOW COLUMNS FROM `KB-info`;
```

#### 1.3 停止应用服务(推荐)

```bash
# 停止 Flask 应用
# 根据实际部署方式停止服务
# 例如: systemctl stop clouddoors
```

### 2. 执行升级

#### 2.1 方式1: 依次执行补丁

```bash
# 补丁1: 添加工单系统缺失字段
mysql -h localhost -u root -p casedb < 001_add_missing_columns.sql

# 补丁2: 扩展知识库名称长度
mysql -h localhost -u root -p YHKB < 002_extend_kb_name_length.sql
```

#### 2.2 方式2: 使用 MySQL 客户端

```bash
# 登录 MySQL
mysql -h localhost -u root -p

# 在 MySQL 客户端中执行:
mysql> SOURCE /path/to/001_add_missing_columns.sql
mysql> USE YHKB;
mysql> SOURCE /path/to/002_extend_kb_name_length.sql
```

#### 2.3 方式3: 一键执行所有补丁

```bash
# 创建执行脚本
cat > apply_patches.sh << 'EOF'
#!/bin/bash
DB_HOST="${DB_HOST:-localhost}"
DB_USER="${DB_USER:-root}"
DB_PASS="${DB_PASS:-}"

echo "开始执行 v2.1_to_v2.2 升级包..."

# 补丁1
echo "执行补丁1: 添加工单系统缺失字段..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" casedb < 001_add_missing_columns.sql
echo "补丁1执行完成"

# 补丁2
echo "执行补丁2: 扩展知识库名称长度..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" YHKB < 002_extend_kb_name_length.sql
echo "补丁2执行完成"

echo "v2.1_to_v2.2 升级包执行完成!"
EOF

chmod +x apply_patches.sh
./apply_patches.sh
```

### 3. 验证升级结果

#### 3.1 验证工单系统(casedb)

```sql
USE casedb;

-- 检查新增字段
SHOW COLUMNS FROM tickets;

-- 验证字段存在
SELECT COUNT(*) AS assignee_exists 
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='casedb' AND TABLE_NAME='tickets' AND COLUMN_NAME='assignee';

SELECT COUNT(*) AS resolution_exists 
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='casedb' AND TABLE_NAME='tickets' AND COLUMN_NAME='resolution';

SELECT COUNT(*) AS submit_user_exists 
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='casedb' AND TABLE_NAME='tickets' AND COLUMN_NAME='submit_user';

SELECT COUNT(*) AS customer_contact_name_exists 
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='casedb' AND TABLE_NAME='tickets' AND COLUMN_NAME='customer_contact_name';

-- 验证索引存在
SHOW INDEX FROM tickets WHERE Key_name LIKE 'idx_%';
```

预期结果: 所有字段和索引都应存在(查询结果为 1)。

#### 3.2 验证知识库系统(YHKB)

```sql
USE YHKB;

-- 检查 KB_Name 字段长度
SHOW CREATE TABLE `KB-info`;

-- 查询字段信息
SELECT 
    COLUMN_NAME AS '字段名',
    COLUMN_TYPE AS '字段类型',
    CHARACTER_MAXIMUM_LENGTH AS '最大长度',
    IS_NULLABLE AS '可为空',
    COLUMN_COMMENT AS '注释'
FROM 
    INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_SCHEMA = 'YHKB' 
    AND TABLE_NAME = 'KB-info'
    AND COLUMN_NAME = 'KB_Name';

-- 统计知识库名称长度分布
SELECT 
    COUNT(*) AS '总记录数',
    MAX(LENGTH(KB_Name)) AS '最大名称长度',
    MIN(LENGTH(KB_Name)) AS '最小名称长度',
    AVG(LENGTH(KB_Name)) AS '平均名称长度'
FROM 
    `KB-info`;
```

预期结果: `KB_Name` 字段长度应为 `varchar(500)`。

### 4. 重启应用服务

```bash
# 启动 Flask 应用
# 根据实际部署方式启动服务
# 例如: systemctl start clouddoors

# 检查日志确认服务正常启动
tail -f logs/app.log
```

### 5. 功能测试

#### 5.1 工单系统测试

1. 创建新工单,确认可以填写客户联系人姓名
2. 提交工单后,确认 `submit_user` 字段正确记录用户名
3. 分配工单给处理人,确认 `assignee` 字段正确记录
4. 解决工单,确认可以填写解决方案

#### 5.2 知识库系统测试

1. 创建名称超过200字符的知识库,确认可以成功保存
2. 修改现有知识库名称,确认长度限制已扩展到500字符

## 回滚方案

如果升级后出现问题,请按以下步骤回滚:

### 1. 停止应用服务

```bash
# 停止服务
systemctl stop clouddoors
```

### 2. 恢复数据库

```bash
# 从备份恢复
mysql -h localhost -u root -p < backup_pre_v2.2_YYYYMMDD_HHMMSS.sql
```

### 3. 验证恢复结果

```sql
-- 检查 casedb.tickets 表结构
USE casedb;
SHOW COLUMNS FROM tickets;

-- 检查 YHKB.KB-info 表结构
USE YHKB;
SHOW COLUMNS FROM `KB-info`;
```

### 4. 重启应用服务

```bash
# 启动服务
systemctl start clouddoors
```

## 常见问题

### Q1: 补丁执行时报错 "Duplicate column name"

**A**: 这是正常的提示,说明字段已存在。补丁已设计为幂等,可忽略此提示。

### Q2: 升级后发现应用功能异常

**A**: 请立即停止应用,按回滚步骤恢复数据库,然后联系技术支持。

### Q3: 某个补丁执行失败

**A**: 
1. 检查数据库连接是否正常
2. 确认数据库用户权限
3. 查看错误日志获取详细信息
4. 补丁可重复执行,修复问题后重试

### Q4: 升级后性能下降

**A**: 
- 新增的索引会略微降低写入速度,但会提升查询速度
- 如果性能问题严重,可考虑删除不必要的索引
- 联系技术支持进行性能优化

### Q5: 能否跳过某个补丁

**A**: 不建议跳过。所有补丁都是必需的,否则可能导致功能异常。

## 注意事项

1. **必须备份**: 升级前必须备份数据库
2. **顺序执行**: 按补丁编号顺序依次执行
3. **验证结果**: 每个补丁执行后都要验证
4. **测试环境**: 建议先在测试环境验证,再在生产环境执行
5. **停机时间**: 升级期间建议暂停服务,避免数据不一致

## 技术支持

如有问题,请联系技术支持团队。

---

**版本**: 1.0
**发布日期**: 2026-02-13
**维护人员**: 云户科技技术团队
