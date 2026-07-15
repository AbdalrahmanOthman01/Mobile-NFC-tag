import sqlite3
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """Creates the vault schema if it doesn't already exist."""
    query_tags_table = """
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE NOT NULL,
        tag_type TEXT NOT NULL,
        name TEXT NOT NULL,
        payload_encrypted TEXT NOT NULL,
        is_emulatable INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    query_written_logs_table = """
    CREATE TABLE IF NOT EXISTS written_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payload_type TEXT NOT NULL,
        payload_encrypted TEXT NOT NULL,
        written_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    conn = get_connection()
    try:
        with conn:
            conn.execute(query_tags_table)
            conn.execute(query_written_logs_table)
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise e
    finally:
        conn.close()
