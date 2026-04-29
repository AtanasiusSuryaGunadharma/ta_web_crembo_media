from __future__ import annotations

import argparse
import sqlite3
import re
from pathlib import Path
from typing import Iterable

import mysql.connector
from mysql.connector import errorcode

BASE_DIR = Path(__file__).resolve().parent
LEGACY_DB = BASE_DIR.parent / "registrasi" / "crembo.db"

CORE_TABLE_DDL: dict[str, str] = {
    "anggota": """
        CREATE TABLE IF NOT EXISTS `anggota` (
            `id` INT NOT NULL,
            `nama` VARCHAR(255) NULL,
            `username` VARCHAR(150) NULL,
            `telp` VARCHAR(50) NULL,
            `password` VARCHAR(255) NULL,
            `role` VARCHAR(50) NULL,
            `tgl_lahir` VARCHAR(50) NULL,
            `email` VARCHAR(255) NULL,
            `alamat` TEXT NULL,
            `status_akun` VARCHAR(20) NOT NULL DEFAULT 'aktif',
            PRIMARY KEY (`id`),
            UNIQUE KEY `uniq_anggota_username` (`username`),
            UNIQUE KEY `uniq_anggota_email` (`email`),
            UNIQUE KEY `uniq_anggota_telp` (`telp`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    "kegiatan": """
        CREATE TABLE IF NOT EXISTS `kegiatan` (
            `id` INT NOT NULL,
            `judul` VARCHAR(255) NOT NULL,
            `tanggal` VARCHAR(50) NOT NULL,
            `status` VARCHAR(50) NOT NULL DEFAULT 'draft',
            `misa_json` LONGTEXT NOT NULL,
            `created_at` VARCHAR(50) NOT NULL,
            `updated_at` VARCHAR(50) NOT NULL,
            `misa_ke` INT NULL,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    "kegiatan_form": """
        CREATE TABLE IF NOT EXISTS `kegiatan_form` (
            `id` INT NOT NULL,
            `judul` VARCHAR(255) NULL,
            `slug` VARCHAR(255) NULL,
            `jumlah_hari` INT NULL,
            `jumlah_misa` INT NULL,
            `jml_kamera` INT NULL,
            `jml_supervisor` INT NULL,
            `jml_fotografer` INT NULL,
            `misa_terakhir` DATE NULL,
            `form_json` LONGTEXT NULL,
            `is_published` INT NULL DEFAULT 0,
            `created_at` VARCHAR(50) NULL,
            `updated_at` VARCHAR(50) NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `uniq_kegiatan_form_slug` (`slug`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    "tugas_form": """
        CREATE TABLE IF NOT EXISTS `tugas_form` (
            `id` INT NOT NULL,
            `judul` VARCHAR(255) NOT NULL,
            `slug` VARCHAR(255) NOT NULL,
            `keterangan` TEXT NULL,
            `start_date` VARCHAR(50) NOT NULL,
            `end_date` VARCHAR(50) NOT NULL,
            `sunday_times` VARCHAR(255) NULL DEFAULT '08:00,10:00,17:00,19:00',
            `weekday_time` VARCHAR(50) NULL DEFAULT '18:00',
            `status` VARCHAR(50) NULL DEFAULT 'draft',
            `created_at` VARCHAR(50) NULL,
            `published_at` VARCHAR(50) NULL,
            `expires_at` VARCHAR(50) NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `uniq_tugas_form_slug` (`slug`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    "tugas_form_slot": """
        CREATE TABLE IF NOT EXISTS `tugas_form_slot` (
            `id` INT NOT NULL,
            `form_id` INT NOT NULL,
            `date` VARCHAR(50) NOT NULL,
            `time` VARCHAR(50) NOT NULL,
            `operator_username` VARCHAR(150) NULL,
            `kameramen_username` VARCHAR(150) NULL,
            `supervisor_username` VARCHAR(150) NULL,
            `updated_at` VARCHAR(50) NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `uniq_tugas_form_slot` (`form_id`, `date`, `time`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
    "tugas_form_audit": """
        CREATE TABLE IF NOT EXISTS `tugas_form_audit` (
            `id` INT NOT NULL,
            `form_id` INT NOT NULL,
            `slot_id` INT NOT NULL,
            `actor_username` VARCHAR(150) NULL,
            `actor_role` VARCHAR(50) NULL,
            `actor_ip` VARCHAR(50) NULL,
            `actor_route` VARCHAR(255) NULL,
            `old_operator` VARCHAR(150) NULL,
            `old_kameramen` VARCHAR(150) NULL,
            `old_supervisor` VARCHAR(150) NULL,
            `new_operator` VARCHAR(150) NULL,
            `new_kameramen` VARCHAR(150) NULL,
            `new_supervisor` VARCHAR(150) NULL,
            `note` TEXT NULL,
            `created_at` VARCHAR(50) NULL,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
}

LEGACY_COLUMN_ALIASES = {
    "name": "username",
}


def mysql_connection(host: str, port: int, user: str, password: str, database: str | None = None):
    kwargs = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "autocommit": False,
    }
    if database:
        kwargs["database"] = database
    return mysql.connector.connect(**kwargs)


def ensure_database(cursor, database: str) -> None:
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
    )


def ensure_core_schema(cursor) -> None:
    for ddl in CORE_TABLE_DDL.values():
        cursor.execute(ddl)


def get_sqlite_tables(conn: sqlite3.Connection) -> list[str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cur.fetchall()]


def get_sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


def map_row(table: str, row: dict[str, object]) -> dict[str, object]:
    mapped = dict(row)
    for source_name, target_name in LEGACY_COLUMN_ALIASES.items():
        if source_name in mapped and target_name not in mapped:
            mapped[target_name] = mapped[source_name]
    return mapped


def quote_identifier(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def ensure_monthly_task_table(cursor, table_name: str) -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {quote_identifier(table_name)} (
            `id` INT NOT NULL,
            `username` VARCHAR(150) NULL,
            `date` VARCHAR(50) NULL,
            `time` VARCHAR(50) NULL,
            `position` VARCHAR(100) NULL,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )


def is_monthly_task_table(table_name: str) -> bool:
    return re.fullmatch(r"tugas_\d{4}_\d{2}", table_name) is not None


def migrate_table(sqlite_conn: sqlite3.Connection, mysql_cursor, table: str, reset: bool = True) -> int:
    sqlite_columns = get_sqlite_columns(sqlite_conn, table)
    if not sqlite_columns:
        return 0

    rows_cursor = sqlite_conn.cursor()
    rows_cursor.execute(f'SELECT * FROM "{table}"')
    rows = rows_cursor.fetchall()
    if not rows:
        return 0

    if is_monthly_task_table(table):
        ensure_monthly_task_table(mysql_cursor, table)
    elif table in CORE_TABLE_DDL:
        pass
    else:
        return 0

    if reset:
        mysql_cursor.execute(f"DELETE FROM {quote_identifier(table)}")

    columns = list(sqlite_columns)
    if is_monthly_task_table(table):
        if "name" in columns and "username" not in columns:
            columns = ["username" if col == "name" else col for col in columns]

    insert_columns = [col for col in columns]
    placeholders = ", ".join(["%s"] * len(insert_columns))
    column_sql = ", ".join(quote_identifier(col) for col in insert_columns)
    insert_sql = f"INSERT INTO {quote_identifier(table)} ({column_sql}) VALUES ({placeholders})"

    migrated = 0
    for raw_row in rows:
        row_dict = {sqlite_columns[i]: raw_row[i] for i in range(len(sqlite_columns))}
        row_dict = map_row(table, row_dict)

        if is_monthly_task_table(table) and "name" in row_dict and "username" not in row_dict:
            row_dict["username"] = row_dict["name"]

        ordered_values = [row_dict.get(col) for col in insert_columns]
        mysql_cursor.execute(insert_sql, ordered_values)
        migrated += 1

    return migrated


def migrate(sqlite_path: Path, mysql_cfg: dict[str, object], database: str, reset: bool = True) -> None:
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"SQLite source not found: {sqlite_path}")

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    mysql_conn = mysql_connection(
        host=str(mysql_cfg["host"]),
        port=int(mysql_cfg["port"]),
        user=str(mysql_cfg["user"]),
        password=str(mysql_cfg["password"]),
        database=None,
    )
    mysql_cursor = mysql_conn.cursor()
    ensure_database(mysql_cursor, database)
    mysql_conn.commit()
    mysql_conn.close()

    mysql_conn = mysql_connection(
        host=str(mysql_cfg["host"]),
        port=int(mysql_cfg["port"]),
        user=str(mysql_cfg["user"]),
        password=str(mysql_cfg["password"]),
        database=database,
    )
    mysql_cursor = mysql_conn.cursor()
    ensure_core_schema(mysql_cursor)
    mysql_conn.commit()

    tables = get_sqlite_tables(sqlite_conn)
    migrated_totals: dict[str, int] = {}
    for table in tables:
        migrated = migrate_table(sqlite_conn, mysql_cursor, table, reset=reset)
        if migrated:
            migrated_totals[table] = migrated
            mysql_conn.commit()

    mysql_cursor.close()
    mysql_conn.close()
    sqlite_conn.close()

    print(f"Migrated from {sqlite_path}")
    for table, count in migrated_totals.items():
        print(f"- {table}: {count} rows")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate legacy SQLite data into MySQL.")
    parser.add_argument("--sqlite", default=str(LEGACY_DB), help="Path to the legacy SQLite database")
    parser.add_argument("--mysql-host", default="127.0.0.1")
    parser.add_argument("--mysql-port", default=3306, type=int)
    parser.add_argument("--mysql-user", default="root")
    parser.add_argument("--mysql-password", default="")
    parser.add_argument("--mysql-database", default="crembo_db_new")
    parser.add_argument("--no-reset", action="store_true", help="Do not clear target tables before insert")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    mysql_cfg = {
        "host": args.mysql_host,
        "port": args.mysql_port,
        "user": args.mysql_user,
        "password": args.mysql_password,
    }

    try:
        migrate(Path(args.sqlite), mysql_cfg, args.mysql_database, reset=not args.no_reset)
    except mysql.connector.Error as exc:
        if exc.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("MySQL access denied. Check username/password.")
        elif exc.errno == errorcode.ER_BAD_DB_ERROR:
            print("MySQL database not found and could not be created.")
        else:
            print(f"MySQL error: {exc}")
        return 1
    except Exception as exc:
        print(f"Migration failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
