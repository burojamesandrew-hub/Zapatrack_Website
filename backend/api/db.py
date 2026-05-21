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
from pathlib import Path

# Load .env from the backend directory (where manage.py is)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

_pool = None


def init_pool():
    global _pool
    db_url = os.getenv('DATABASE_URL')
    
    try:
        if db_url:
            print(f'[DB] Initializing pool using DATABASE_URL')
            _pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=db_url,
            )
        else:
            db_name = os.getenv('DB_NAME')
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            
            if not all([db_name, db_user]):
                print('[DB] Missing database configuration (DATABASE_URL or DB_NAME/DB_USER).')
                _pool = None
                return

            print(f'[DB] Initializing pool using individual variables (Host: {db_host})')
            
            # Neon DB usually requires sslmode=require.
            # We automatically add it if the host contains 'neon.tech' or DB_SSL=True
            connect_kwargs = {
                'dbname': db_name,
                'user': db_user,
                'password': db_password,
                'host': db_host,
                'port': db_port,
            }
            if os.getenv('DB_SSL', 'False') == 'True' or 'neon.tech' in db_host:
                connect_kwargs['sslmode'] = 'require'
                print('[DB] SSL mode: require')

            _pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                **connect_kwargs
            )
        print('[DB] Pool initialized successfully.')
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
