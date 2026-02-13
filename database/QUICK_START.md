# 数据库脚本快速参考

## 目录结构

```
database/
├── README.md                          # 详细文档
├── QUICK_START.md                     # 本文件
├── init_database.sql                  # 完整初始化脚本(新环境)
├── apply_patches_v2.1_to_v2.2.bat     # Windows升级脚本
├── apply_patches_v2.1_to_v2.2.sh      # Linux/Mac升级脚本
├── patches/                           # 补丁脚本目录
│   ├── v2.1_to_v2.2/                  # v2.1升级到v2.2
│   │   ├── 001_add_missing_columns.sql
│   │   ├── 002_extend_kb_name_length.sql
│   │   └── README.md
│   └── v2.2_to_v2.3/                  # v2.2升级到v2.3(预留)
│       └── README.md
└── legacy/                            # 旧版脚本归档
    └── README.md
```

## 快速开始

### 场景1: 全新安装(新环境)

```bash
# Windows
mysql -h localhost -u root -p < database\init_database.sql

# Linux/Mac
mysql -h localhost -u root -p < database/init_database.sql
```

**结果**: 创建三个数据库(clouddoors_db, YHKB, casedb)及所有表结构和初始数据

**默认管理员账号**: `admin` / `YHKB@2024`

---

### 场景2: 升级现有数据库(已部署环境)

#### Windows系统

```batch
# 方式1: 使用自动化脚本(推荐)
cd e:\Integrate-code
database\apply_patches_v2.1_to_v2.2.bat

# 方式2: 手动执行
mysql -h localhost -u root -p casedb < database\patches\v2.1_to_v2.2\001_add_missing_columns.sql
mysql -h localhost -u root -p YHKB < database\patches\v2.1_to_v2.2\002_extend_kb_name_length.sql
```

#### Linux/Mac系统

```bash
# 方式1: 使用自动化脚本(推荐)
cd /path/to/Integrate-code
chmod +x database/apply_patches_v2.1_to_v2.2.sh
./database/apply_patches_v2.1_to_v2.2.sh

# 方式2: 手动执行
mysql -h localhost -u root -p casedb < database/patches/v2.1_to_v2.2/001_add_missing_columns.sql
mysql -h localhost -u root -p YHKB < database/patches/v2.1_to_v2.2/002_extend_kb_name_length.sql
```

**结果**: 升级现有数据库到v2.2版本,自动备份到 `database/backups/`

---

## 补丁说明

### v2.1_to_v2.2 升级包

| 补丁编号 | 数据库 | 描述 | 预计耗时 |
|---------|--------|------|----------|
| 001 | casedb | 添加工单系统缺失字段(assignee, resolution, submit_user等) | < 1秒 |
| 002 | YHKB | 扩展知识库名称字段长度(VARCHAR(200) → VARCHAR(500)) | < 1秒 |

详细说明见 `patches/v2.1_to_v2.2/README.md`

---

## 常用命令

### 备份数据库

```bash
# 备份所有数据库
mysqldump -h localhost -u root -p \
  --databases clouddoors_db YHKB casedb \
  --single-transaction --routines --triggers \
  > backup_$(date +%Y%m%d).sql

# 备份单个数据库
mysqldump -h localhost -u root -p YHKB > backup_yhkb.sql
```

### 恢复数据库

```bash
# 恢复所有数据库
mysql -h localhost -u root -p < backup_20260213.sql

# 恢复单个数据库
mysql -h localhost -u root -p YHKB < backup_yhkb.sql
```

### 检查数据库版本

```sql
-- 检查工单系统表结构
USE casedb;
SHOW COLUMNS FROM tickets;

-- 检查知识库表结构
USE YHKB;
SHOW COLUMNS FROM `KB-info`;

-- 验证补丁是否已应用
SELECT COUNT(*) AS assignee_exists
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='casedb' AND TABLE_NAME='tickets' AND COLUMN_NAME='assignee';
-- 结果为1表示已应用补丁
```

---

## 故障排除

### 问题1: 补丁执行失败

**症状**: 执行补丁时出现错误

**解决方案**:
1. 检查数据库连接信息是否正确
2. 确认数据库用户有足够的权限
3. 查看错误日志获取详细信息
4. 补丁可重复执行,修复问题后重试

### 问题2: 升级后应用功能异常

**症状**: 升级后应用无法正常工作

**解决方案**:
1. 立即停止应用服务
2. 从备份恢复数据库
3. 查看补丁文档了解具体变更
4. 联系技术支持

### 问题3: 忘记备份数据库

**症状**: 升级前忘记备份

**解决方案**:
1. 如果补丁只是修改表结构,可能不需要恢复
2. 使用数据库的二进制日志(binlog)尝试恢复
3. 联系技术支持寻求帮助

---

## 重要提示

⚠️ **升级前必须备份数据库!**

⚠️ **不要在生产环境直接测试,先在测试环境验证!**

⚠️ **升级期间建议暂停应用服务!**

---

## 获取帮助

- 详细文档: `README.md`
- 补丁说明: `patches/v2.1_to_v2.2/README.md`
- 技术支持: 联系云户科技技术团队

---

**更新日期**: 2026-02-13
**文档版本**: 1.0
