import mysql.connector

from crembo_app.config.settings import MYSQL_CONFIG


def mysql_connection():
    """Membuat koneksi ke database MySQL/MariaDB."""
    return mysql.connector.connect(**MYSQL_CONFIG)


def fetch_all(query: str, params: tuple | list | None = None) -> list[dict]:
    """Helper model umum untuk mengambil banyak data."""
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, tuple(params or ()))
        return cursor.fetchall() or []
    finally:
        cursor.close()
        conn.close()


def fetch_one(query: str, params: tuple | list | None = None) -> dict | None:
    """Helper model umum untuk mengambil satu data."""
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, tuple(params or ()))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
