"""
知识库工具函数
从 modules/kb 迁移而来
优化版本 - 使用连接池提高性能
"""
import pymysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME_KB
from common.db_manager import get_pool

def get_kb_db_connection():
    """获取知识库数据库连接 - 使用连接池"""
    try:
        pool = get_pool('kb')
        if pool:
            return pool.connection()
        # 降级到直接连接
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME_KB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"知识库数据库连接失败: {e}")
        return None


def fetch_all_records():
    """获取所有记录 - 使用连接池优化"""
    connection = get_kb_db_connection()
    if connection is None:
        return []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `KB-info` ORDER BY KB_Number ASC")
            records = cursor.fetchall()
        return records
    except Exception as e:
        print(f"获取记录失败: {e}")
        return []
    finally:
        connection.close()


def fetch_record_by_id(kb_number):
    """根据ID获取记录 - 使用连接池优化"""
    connection = get_kb_db_connection()
    if connection is None:
        return None

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `KB-info` WHERE KB_Number = %s", (kb_number,))
            record = cursor.fetchone()
        return record
    except Exception as e:
        print(f"获取记录失败: {e}")
        return None
    finally:
        connection.close()


def get_total_count():
    """获取记录总数 - 使用连接池优化"""
    connection = get_kb_db_connection()
    if connection is None:
        return 0

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM `KB-info`")
            result = cursor.fetchone()
        return result['count'] if result else 0
    except Exception as e:
        print(f"获取记录总数失败: {e}")
        return 0
    finally:
        connection.close()


def fetch_records_with_pagination(page, per_page):
    """分页获取记录 - 使用连接池优化"""
    connection = get_kb_db_connection()
    if connection is None:
        return [], 0

    try:
        offset = (page - 1) * per_page

        with connection.cursor() as cursor:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as count FROM `KB-info`")
            total_count_result = cursor.fetchone()
            total_count = total_count_result['count'] if total_count_result else 0

            # 获取分页数据
            cursor.execute("SELECT * FROM `KB-info` ORDER BY KB_Number ASC LIMIT %s OFFSET %s", (per_page, offset))
            records = cursor.fetchall()

        return records, total_count
    except Exception as e:
        print(f"分页获取记录失败: {e}")
        return [], 0
    finally:
        connection.close()


def fetch_records_by_name_with_pagination(name, page, per_page):
    """按名称分页搜索记录 - 使用连接池优化"""
    connection = get_kb_db_connection()
    if connection is None:
        return [], 0

    try:
        offset = (page - 1) * per_page
        search_pattern = f"%{name}%"

        with connection.cursor() as cursor:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as count FROM `KB-info` WHERE KB_Name LIKE %s", (search_pattern,))
            total_count_result = cursor.fetchone()
            total_count = total_count_result['count'] if total_count_result else 0

            # 获取分页数据
            cursor.execute("SELECT * FROM `KB-info` WHERE KB_Name LIKE %s ORDER BY KB_Number ASC LIMIT %s OFFSET %s", (search_pattern, per_page, offset))
            records = cursor.fetchall()

        return records, total_count
    except Exception as e:
        print(f"按名称分页搜索记录失败: {e}")
        return [], 0
    finally:
        connection.close()
