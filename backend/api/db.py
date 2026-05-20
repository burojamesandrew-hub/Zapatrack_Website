"""
api/db.py
─────────
Raw psycopg2 connection pool for querying the NeonDB directly.
This bypasses Django ORM since the DB schema is already defined
by the desktop app (UUID PKs, custom ENUMs, etc.).
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

_pool = None


def init_pool():
    global _pool
    try:
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=os.getenv('DATABASE_URL'),
        )
    except Exception as e:
        print(f'[DB] Pool init failed: {e}')
        _pool = None


def get_conn():
    global _pool
    if _pool is None:
        init_pool()
    if _pool is None:
        raise ConnectionError('Database not available')
    return _pool.getconn()


def release_conn(conn):
    global _pool
    if _pool and conn:
        _pool.putconn(conn)


def query(sql, params=None, many=False):
    """Run a SELECT and return list of dicts (many=True) or one dict."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall() if many else cur.fetchone()
    except psycopg2.DatabaseError as e:
        print(f'[DB] Database error: {e}. SQL: {sql}')
        raise RuntimeError(f'Database error: Unable to retrieve data. {str(e)}')
    except Exception as e:
        print(f'[DB] Unexpected query error: {e}. SQL: {sql}')
        raise RuntimeError(f'Unexpected error: {str(e)}')
    finally:
        release_conn(conn)


init_pool()
