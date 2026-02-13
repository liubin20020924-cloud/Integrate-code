-- =====================================================
-- 补丁: 扩展知识库名称字段长度
-- 影响数据库: YHKB
-- 创建时间: 2026-02-13
-- 版本范围: v2.1 -> v2.2
-- 功能说明: 将 KB_Name 字段长度从 VARCHAR(200) 扩展到 VARCHAR(500)
-- =====================================================

USE `YHKB`;

-- =====================================================
-- 1. 显示当前表结构(备份信息)
-- =====================================================
SELECT '=================================================' AS info;
SELECT '知识库名称字段长度补丁' AS info;
SELECT '=================================================' AS info;

SHOW CREATE TABLE `KB-info`;

-- =====================================================
-- 2. 修改 KB_Name 字段长度
-- =====================================================

-- 检查当前长度
SELECT 
    COLUMN_NAME AS '字段名',
    COLUMN_TYPE AS '当前字段类型',
    CHARACTER_MAXIMUM_LENGTH AS '当前最大长度',
    IS_NULLABLE AS '可为空',
    COLUMN_COMMENT AS '注释'
FROM 
    INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_SCHEMA = 'YHKB' 
    AND TABLE_NAME = 'KB-info'
    AND COLUMN_NAME = 'KB_Name';

-- 修改字段长度
SELECT '正在修改 KB_Name 字段长度...' AS info;

ALTER TABLE `KB-info` 
MODIFY COLUMN `KB_Name` VARCHAR(500) NOT NULL COMMENT '知识库名称';

-- =====================================================
-- 3. 验证修改结果
-- =====================================================
SELECT '=================================================' AS info;
SELECT '修改后字段信息' AS info;
SELECT '=================================================' AS info;

SELECT 
    COLUMN_NAME AS '字段名',
    COLUMN_TYPE AS '修改后字段类型',
    CHARACTER_MAXIMUM_LENGTH AS '修改后最大长度',
    IS_NULLABLE AS '可为空',
    COLUMN_COMMENT AS '注释'
FROM 
    INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_SCHEMA = 'YHKB' 
    AND TABLE_NAME = 'KB-info'
    AND COLUMN_NAME = 'KB_Name';

-- 统计知识库名称长度分布
SELECT '=================================================' AS info;
SELECT '知识库名称长度统计' AS info;
SELECT '=================================================' AS info;

SELECT 
    COUNT(*) AS '总记录数',
    MAX(LENGTH(KB_Name)) AS '最大名称长度',
    MIN(LENGTH(KB_Name)) AS '最小名称长度',
    AVG(LENGTH(KB_Name)) AS '平均名称长度'
FROM 
    `KB-info`;

-- 查找名称长度接近限制的记录(接近500字符)
SELECT '=================================================' AS info;
SELECT '接近长度限制的记录(>400字符)' AS info;
SELECT '=================================================' AS info;

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
-- 4. 完成提示
-- =====================================================
SELECT '=================================================' AS info;
SELECT '补丁执行完成!' AS status;
SELECT '=================================================' AS info;
