-- =====================================================
-- 知识库名称字段长度补丁脚本
-- 用于修改 KB_Name 字段长度以支持更长的知识库名称
-- 创建时间: 2026-02-12
-- =====================================================

-- =====================================================
-- 1. 备份当前表结构（可选）
-- =====================================================
USE `YHKB`;

-- 显示当前表结构
SHOW CREATE TABLE `KB-info`;

SELECT '=================================================' AS info;
SELECT '准备修改 KB_Name 字段长度' AS info;
SELECT '=================================================' AS info;

-- =====================================================
-- 2. 修改 KB_Name 字段长度
-- =====================================================

-- 方案1: 修改为 VARCHAR(500) - 适用于大多数场景
-- 说明: 500字符足够存储较长的标题和描述
ALTER TABLE `KB-info` 
MODIFY COLUMN `KB_Name` VARCHAR(500) NOT NULL COMMENT '知识库名称';

-- 方案2: 修改为 VARCHAR(1000) - 适用于需要更长标题的场景
-- 说明: 如果上面的500不够用，可以取消下面这行的注释
-- ALTER TABLE `KB-info` 
-- MODIFY COLUMN `KB_Name` VARCHAR(1000) NOT NULL COMMENT '知识库名称';

-- 方案3: 修改为 TEXT 类型 - 适用于非常长的标题（不推荐）
-- 说明: TEXT类型没有长度限制，但会降低索引性能
-- ALTER TABLE `KB-info` 
-- MODIFY COLUMN `KB_Name` TEXT NOT NULL COMMENT '知识库名称';

SELECT '=================================================' AS info;
SELECT 'KB_Name 字段长度修改完成' AS info;
SELECT '=================================================' AS info;

-- =====================================================
-- 3. 验证修改结果
-- =====================================================

-- 显示修改后的表结构
SHOW CREATE TABLE `KB-info`;

-- 查询 KB_Name 字段信息
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
    '知识库名称长度分布' AS info,
    COUNT(*) AS '总记录数',
    MAX(LENGTH(KB_Name)) AS '最大名称长度',
    MIN(LENGTH(KB_Name)) AS '最小名称长度',
    AVG(LENGTH(KB_Name)) AS '平均名称长度'
FROM 
    `KB-info`;

-- 查找名称长度接近限制的记录（接近500字符）
SELECT 
    KB_Number AS '编号',
    KB_Name AS '名称',
    LENGTH(KB_Name) AS '名称长度',
    CONCAT('警告: 接近500字符限制 (剩余: ', 500 - LENGTH(KB_Name), ' 字符)') AS '状态'
FROM 
    `KB-info`
WHERE 
    LENGTH(KB_Name) > 400
ORDER BY 
    LENGTH(KB_Name) DESC;

-- =====================================================
-- 4. 回滚脚本（如果需要恢复）
-- =====================================================

-- 如果修改后出现问题，可以使用以下SQL回滚到原始长度
/*
USE `YHKB`;

ALTER TABLE `KB-info` 
MODIFY COLUMN `KB_Name` VARCHAR(200) NOT NULL COMMENT '知识库名称';

SELECT 'KB_Name 字段已回滚到 VARCHAR(200)' AS info;
*/

-- =====================================================
-- 5. 完成提示
-- =====================================================

SELECT '=================================================' AS info;
SELECT '补丁脚本执行完成！' AS status;
SELECT '=================================================' AS info;
SELECT '如果遇到问题，请使用上面的回滚脚本' AS info;
SELECT '=================================================' AS info;
