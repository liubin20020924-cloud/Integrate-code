#!/bin/bash
# =====================================================
# 数据库升级脚本 v2.1_to_v2.2
# 云户科技 - 2026-02-13
# =====================================================

# 设置数据库连接参数
# 请根据实际情况修改以下参数
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASS="${DB_PASS:-}"
BACKUP_DIR="database/backups"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "===================================================="
echo "云户科技数据库升级工具 v2.1_to_v2.2"
echo "===================================================="
echo ""

# 检查是否设置了密码
if [ -z "$DB_PASS" ]; then
    read -sp "请输入数据库密码: " DB_PASS
    echo ""
fi

echo ""
echo "配置信息:"
echo "  数据库主机: $DB_HOST"
echo "  数据库端口: $DB_PORT"
echo "  数据库用户: $DB_USER"
echo "  备份目录: $BACKUP_DIR"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_pre_v2.2_$TIMESTAMP.sql"

# =====================================================
# 第1步: 备份数据库
# =====================================================
echo "===================================================="
echo "第1步: 备份数据库"
echo "===================================================="
echo "开始备份..."
echo "备份文件: $BACKUP_FILE"

mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" \
  --databases clouddoors_db YHKB casedb \
  --single-transaction \
  --routines \
  --triggers \
  --result-file="$BACKUP_FILE"

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[错误]${NC} 数据库备份失败!"
    echo "请检查数据库连接信息和权限。"
    exit 1
fi

echo ""
echo -e "${GREEN}[成功]${NC} 数据库备份完成!"
echo ""

# 验证备份文件大小
if [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(wc -c < "$BACKUP_FILE")
    echo "备份文件大小: $BACKUP_SIZE 字节"
else
    echo -e "${YELLOW}[警告]${NC} 备份文件大小为0,备份可能失败!"
    echo ""
    read -p "是否继续升级? (y/n): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "升级已取消。"
        exit 1
    fi
fi

# =====================================================
# 第2步: 执行补丁1 - 添加工单系统缺失字段
# =====================================================
echo ""
echo "===================================================="
echo "第2步: 执行补丁1 - 添加工单系统缺失字段"
echo "===================================================="
echo "数据库: casedb"
echo "补丁文件: database/patches/v2.1_to_v2.2/001_add_missing_columns.sql"
echo ""

mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" casedb < database/patches/v2.1_to_v2.2/001_add_missing_columns.sql

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[错误]${NC} 补丁1执行失败!"
    echo "请检查错误信息。"
    exit 1
fi

echo ""
echo -e "${GREEN}[成功]${NC} 补丁1执行完成!"
echo ""

# =====================================================
# 第3步: 执行补丁2 - 扩展知识库名称字段长度
# =====================================================
echo ""
echo "===================================================="
echo "第3步: 执行补丁2 - 扩展知识库名称字段长度"
echo "===================================================="
echo "数据库: YHKB"
echo "补丁文件: database/patches/v2.1_to_v2.2/002_extend_kb_name_length.sql"
echo ""

mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" YHKB < database/patches/v2.1_to_v2.2/002_extend_kb_name_length.sql

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[错误]${NC} 补丁2执行失败!"
    echo "请检查错误信息。"
    exit 1
fi

echo ""
echo -e "${GREEN}[成功]${NC} 补丁2执行完成!"
echo ""

# =====================================================
# 第4步: 验证升级结果
# =====================================================
echo ""
echo "===================================================="
echo "第4步: 验证升级结果"
echo "===================================================="
echo ""

echo "验证工单系统 (casedb)..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" casedb -e "SHOW COLUMNS FROM tickets;"

echo ""
echo "验证知识库系统 (YHKB)..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" YHKB -e "SELECT COLUMN_NAME, COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='YHKB' AND TABLE_NAME='KB-info' AND COLUMN_NAME='KB_Name';"

echo ""
echo "===================================================="
echo "升级完成!"
echo "===================================================="
echo ""
echo "所有补丁已成功执行。"
echo ""
echo -e "${YELLOW}重要提示:${NC}"
echo "1. 备份文件保存在: $BACKUP_FILE"
echo "2. 如果发现问题,可以使用备份文件恢复数据库"
echo "3. 请重启应用服务以确保使用最新的数据库结构"
echo ""
echo "恢复命令:"
echo "  mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p < $BACKUP_FILE"
echo ""
