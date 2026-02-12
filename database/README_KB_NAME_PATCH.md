# 知识库名称字段长度补丁说明

## 概述

此补丁用于修改知识库 `KB_Name` 字段的长度，从原来的 `VARCHAR(200)` 增加到 `VARCHAR(500)`，以支持更长的知识库名称。

## 问题描述

- **原始长度**: `VARCHAR(200)` - 最多200个字符
- **问题**: 当从Trilium导入笔记时，某些笔记标题可能超过200字符，导致导入失败或被截断

## 解决方案

将 `KB_Name` 字段长度修改为 `VARCHAR(500)`，支持更长的知识库名称。

## 使用方法

### 方法1: 使用 MySQL 客户端执行补丁

```bash
# 连接到数据库
mysql -h 10.10.10.250 -u root -p

# 执行补丁脚本
source database/patch_kb_name_length.sql
```

### 方法2: 使用命令行执行

```bash
# Windows
mysql -h 10.10.10.250 -u root -p YHKB < database/patch_kb_name_length.sql

# Linux/Mac
mysql -h 10.10.10.250 -u root -p YHKB < database/patch_kb_name_length.sql
```

### 方法3: 使用 Python 脚本执行

```python
import pymysql

# 连接数据库
conn = pymysql.connect(
    host='10.10.10.250',
    port=3306,
    user='root',
    password='Nutanix/4u123!',
    database='YHKB',
    charset='utf8mb4'
)

# 读取并执行补丁脚本
with open('database/patch_kb_name_length.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

cursor = conn.cursor()

# 分割SQL语句并逐个执行
for statement in sql_script.split(';'):
    statement = statement.strip()
    if statement and not statement.startswith('--'):
        try:
            cursor.execute(statement)
            conn.commit()
            print(f"执行成功: {statement[:50]}...")
        except Exception as e:
            print(f"执行失败: {e}")

cursor.close()
conn.close()
print("补丁脚本执行完成！")
```

## 补丁内容说明

### 主修改

```sql
ALTER TABLE `KB-info` 
MODIFY COLUMN `KB_Name` VARCHAR(500) NOT NULL COMMENT '知识库名称';
```

### 备选方案（如果500不够用）

**方案2: VARCHAR(1000)**

```sql
ALTER TABLE `KB-info` 
MODIFY COLUMN `KB_Name` VARCHAR(1000) NOT NULL COMMENT '知识库名称';
```

**方案3: TEXT类型（不推荐）**

```sql
ALTER TABLE `KB-info` 
MODIFY COLUMN `KB_Name` TEXT NOT NULL COMMENT '知识库名称';
```

### 回滚脚本

如果修改后出现问题，可以使用以下SQL回滚到原始长度：

```sql
USE `YHKB`;

ALTER TABLE `KB-info` 
MODIFY COLUMN `KB_Name` VARCHAR(200) NOT NULL COMMENT '知识库名称';
```

## 验证修改结果

### 1. 检查表结构

```sql
USE `YHKB`;
SHOW CREATE TABLE `KB-info`;
```

### 2. 查询字段信息

```sql
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
```

### 3. 统计名称长度分布

```sql
SELECT 
    COUNT(*) AS '总记录数',
    MAX(LENGTH(KB_Name)) AS '最大名称长度',
    MIN(LENGTH(KB_Name)) AS '最小名称长度',
    AVG(LENGTH(KB_Name)) AS '平均名称长度'
FROM 
    `KB-info`;
```

## 代码同步修改

以下文件已同步更新，以支持新的字段长度：

### 1. 数据库初始化脚本
- **文件**: `database/init_database.sql`
- **修改**: `KB_Name` 字段长度从 `VARCHAR(200)` 改为 `VARCHAR(500)`

### 2. 后端代码
- **文件**: `routes/kb_management_bp.py`
- **修改**: 截断长度从 `255` 改为 `500`

```python
# 修改前
kb_name = str(data['KB_Name'])[:255]

# 修改后
kb_name = str(data['KB_Name'])[:500]
```

## 注意事项

1. **数据完整性**: 修改字段长度不会影响现有数据
2. **索引性能**: `VARCHAR(500)` 对索引性能影响很小
3. **回滚能力**: 提供了回滚脚本，可以随时恢复
4. **兼容性**: 修改后的字段长度向下兼容现有代码

## 字段长度建议

| 长度 | 适用场景 | 备注 |
|------|---------|------|
| 200 | 普通知识库标题 | 原始长度 |
| 500 | 较长标题或包含描述 | ✅ 推荐使用 |
| 1000 | 非常长的标题 | 仅在特殊情况下使用 |
| TEXT | 无限制长度 | 不推荐，影响索引性能 |

## 常见问题

### Q: 执行补丁会影响现有数据吗？
A: 不会。修改字段长度只会改变最大长度限制，不会影响现有数据。

### Q: 执行补丁需要停机吗？
A: 不需要。ALTER TABLE 操作会加表级锁，但很快完成。

### Q: 如果修改后出现性能问题怎么办？
A: 使用回滚脚本恢复到原始长度。

### Q: 支持中文字符吗？
A: 支持。使用的是 `utf8mb4` 字符集，可以正确处理中文、emoji等。

## 联系支持

如果在使用此补丁过程中遇到问题，请联系技术支持团队。

---

**创建日期**: 2026-02-12
**版本**: 1.0
**适用数据库**: MariaDB/MySQL 5.7+
**适用系统**: 知识库管理系统 (YHKB)
