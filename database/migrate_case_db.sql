-- =====================================================
-- 工单系统数据库补丁脚本
-- 修复 tickets 表缺少的字段
-- =====================================================

USE `casedb`;

-- 添加 assignee 字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'assignee');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `assignee` VARCHAR(100) NULL COMMENT "处理人" AFTER `status`',
    'SELECT "Column assignee already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 resolution 字段
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'resolution');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `resolution` TEXT NULL COMMENT "解决方案" AFTER `content`',
    'SELECT "Column resolution already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 idx_assignee 索引
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND INDEX_NAME = 'idx_assignee');
SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX `idx_assignee` ON `tickets`(`assignee`)',
    'SELECT "Index idx_assignee already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 submit_user 字段（提交工单的用户名，来自统一用户表）
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'submit_user');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `submit_user` VARCHAR(100) NOT NULL DEFAULT "" COMMENT "提交工单的用户名（来自统一用户表）" AFTER `customer_email`',
    'SELECT "Column submit_user already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 idx_submit_user 索引
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND INDEX_NAME = 'idx_submit_user');
SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX `idx_submit_user` ON `tickets`(`submit_user`)',
    'SELECT "Index idx_submit_user already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 customer_contact_name 字段（客户联系人姓名）
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'customer_contact_name');
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `tickets` ADD COLUMN `customer_contact_name` VARCHAR(100) NOT NULL DEFAULT "" COMMENT "客户联系人姓名（当前登录用户）" AFTER `customer_name`',
    'SELECT "Column customer_contact_name already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 idx_customer_contact_name 索引
SET @idx_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = 'casedb' AND TABLE_NAME = 'tickets' AND INDEX_NAME = 'idx_customer_contact_name');
SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX `idx_customer_contact_name` ON `tickets`(`customer_contact_name`)',
    'SELECT "Index idx_customer_contact_name already exists" AS message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 验证表结构
SHOW COLUMNS FROM `tickets`;

SELECT '工单系统数据库补丁完成！' AS status;
