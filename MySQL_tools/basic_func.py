# mysql操作基础函数
import pymysql
from nonebot import logger
from ..config import config

def get_mysql_connection():
    try:
        connection = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"❌ 连接 MySQL 失败: {e}")
        return None

def execute_query(query: str, params: tuple = ()):
    connection = get_mysql_connection()
    if not connection:
        return None
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            connection.commit()
            return result
    except Exception as e:
        logger.error(f"❌ 执行 MySQL 查询失败: {e}")
        return None
    finally:
        connection.close()

def execute_update(query: str, params: tuple = ()):
    connection = get_mysql_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()
            return True
    except Exception as e:
        logger.error(f"❌ 执行 MySQL 更新失败: {e}")
        return False
    finally:
        connection.close()

def execute_delete(query: str, params: tuple = ()):
    return execute_update(query, params)

def execute_insert(query: str, params: tuple = ()):
    connection = get_mysql_connection()
    if not connection:
        return None
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"❌ 执行 MySQL 插入失败: {e}")
        return None
    finally:
        connection.close()