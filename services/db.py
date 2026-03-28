import pymysql
import pymysql.cursors
from contextlib import contextmanager
import logging
from config import Config

logger = logging.getLogger(__name__)

class DatabasePool:
    def __init__(self):
        self.config = {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
            'connect_timeout': 10
        }
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

db_pool = DatabasePool()

def execute_query(query, params=None):
    """Execute a query and return results"""
    with db_pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

def execute_query_one(query, params=None):
    """Execute a query and return single result"""
    with db_pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
