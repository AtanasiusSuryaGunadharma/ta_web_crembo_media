"""Model akses data Activity Log Model."""

from crembo_app.models.database import fetch_all, fetch_one, execute_query, mysql_connection

TABLE_NAME = "activity_logs"
PRIMARY_KEY = "id"


def all_rows(limit: int = 100):
    return fetch_all(f"SELECT * FROM `{TABLE_NAME}` ORDER BY `{PRIMARY_KEY}` DESC LIMIT %s", (limit,))


def find_by_id(row_id):
    return fetch_one(f"SELECT * FROM `{TABLE_NAME}` WHERE `{PRIMARY_KEY}` = %s LIMIT 1", (row_id,))


def delete_by_id(row_id):
    return execute_query(f"DELETE FROM `{TABLE_NAME}` WHERE `{PRIMARY_KEY}` = %s", (row_id,))


__all__ = ["TABLE_NAME", "PRIMARY_KEY", "all_rows", "find_by_id", "delete_by_id", "fetch_all", "fetch_one", "execute_query", "mysql_connection"]
