-- =====================================================
-- 补丁: 添加工单系统缺失字段
-- 影响数据库: casedb
-- 创建时间: 2026-02-13
-- 版本范围: v2.1 -> v2.2
-- 功能说明: 为工单系统添加处理人、解决方案、提交用户等字段
-- =====================================================

USE `casedb`;

-- =====================================================
-- 1. 添加 assignee 字段(处理人)
-- =====================================================
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'assignee');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `assignee` VARCHAR(100) NULL COMMENT "处理人" AFTER `status`',
    'SELECT "Column assignee already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 2. 添加 resolution 字段(解决方案)
-- =====================================================
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'resolution');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `resolution` TEXT NULL COMMENT "解决方案" AFTER `content`',
    'SELECT "Column resolution already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 3. 添加 idx_assignee 索引
-- =====================================================
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND INDEX_NAME = 'idx_assignee');
SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX `idx_assignee` ON `tickets`(`assignee`)',
    'SELECT "Index idx_assignee already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 4. 添加 submit_user 字段(提交工单的用户名,来自统一用户表)
-- =====================================================
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'submit_user');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `submit_user` VARCHAR(100) NOT NULL DEFAULT "" COMMENT "提交工单的用户名(来自统一用户表)" AFTER `customer_email`',
    'SELECT "Column submit_user already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 5. 添加 idx_submit_user 索引
-- =====================================================
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND INDEX_NAME = 'idx_submit_user');
SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX `idx_submit_user` ON `tickets`(`submit_user`)',
    'SELECT "Index idx_submit_user already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 6. 添加 customer_contact_name 字段(客户联系人姓名)
-- =====================================================
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'customer_contact_name');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `customer_contact_name` VARCHAR(100) NOT NULL DEFAULT "" COMMENT "客户联系人姓名(当前登录用户)" AFTER `customer_name`',
    'SELECT "Column customer_contact_name already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 7. 添加 idx_customer_contact_name 索引
-- =====================================================
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND INDEX_NAME = 'idx_customer_contact_name');
SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX `idx_customer_contact_name` ON `tickets`(`customer_contact_name`)',
    'SELECT "Index idx_customer_contact_name already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 8. 验证表结构
-- =====================================================
SELECT '=================================================' AS info;
SELECT '工单系统数据库补丁验证' AS info;
SELECT '=================================================' AS info;

SHOW COLUMNS FROM `tickets`;

SELECT '=================================================' AS info;
SELECT '补丁执行完成!' AS status;
SELECT '=================================================' AS info;
