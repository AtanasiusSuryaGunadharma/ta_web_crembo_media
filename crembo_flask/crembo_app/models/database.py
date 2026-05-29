"""Lapisan model database untuk aplikasi Crembo Media."""

import json
from typing import Any

import mysql.connector

from crembo_app.config.settings import MYSQL_CONFIG


def mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)


def fetch_all(query: str, params: tuple[Any, ...] | list[Any] | None = None) -> list[dict[str, Any]]:
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, tuple(params or ()))
        return cursor.fetchall() or []
    finally:
        cursor.close()
        conn.close()


def fetch_one(query: str, params: tuple[Any, ...] | list[Any] | None = None) -> dict[str, Any] | None:
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, tuple(params or ()))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute_query(query: str, params: tuple[Any, ...] | list[Any] | None = None) -> int:
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, tuple(params or ()))
        conn.commit()
        return cursor.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)
