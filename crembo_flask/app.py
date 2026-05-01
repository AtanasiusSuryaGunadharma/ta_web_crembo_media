from pathlib import Path
import json
import os
import re
import time
import uuid

import mysql.connector
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR),
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = "dev-secret-change-me"

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "crembo_db_new",
    "autocommit": False,
}

UPLOAD_FOLDER = FRONTEND_DIR / "uploads"
ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".rar",
    ".7z",
    ".txt",
    ".csv",
}
PREVIEWABLE_ATTACHMENT_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".pdf",
}




def template_exists(template_name: str) -> bool:
    return (FRONTEND_DIR / template_name).is_file()


def mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)


def ensure_upload_folder() -> Path:
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    return UPLOAD_FOLDER


def attachment_record_from_url(url_value: str, *, name: str | None = None, mime_type: str | None = None, size: int | None = None) -> dict[str, object]:
    clean_url = (url_value or "").strip()
    filename = (name or Path(clean_url).name or "lampiran").strip()
    extension = Path(filename).suffix.lower() or Path(clean_url).suffix.lower()
    previewable = extension in PREVIEWABLE_ATTACHMENT_EXTENSIONS
    kind = "image" if extension in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"} else ("pdf" if extension == ".pdf" else "file")
    return {
        "url": clean_url,
        "name": filename,
        "mimeType": mime_type or "",
        "size": int(size) if isinstance(size, int) else 0,
        "previewable": previewable,
        "kind": kind,
    }


def normalize_attachment_payload(value) -> list[dict[str, object]]:
    if value in (None, "", []):
        return []

    raw_items = value
    if isinstance(value, str):
        raw_text = value.strip()
        if not raw_text:
            return []
        try:
            parsed = json.loads(raw_text)
            raw_items = parsed if isinstance(parsed, list) else [raw_text]
        except (TypeError, ValueError):
            raw_items = [raw_text]

    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    normalized_items: list[dict[str, object]] = []
    for item in raw_items or []:
        if isinstance(item, str):
            clean_item = item.strip()
            if clean_item:
                normalized_items.append(attachment_record_from_url(clean_item))
            continue

        if not isinstance(item, dict):
            continue

        url_value = str(item.get("url") or item.get("path") or item.get("fileUrl") or "").strip()
        if not url_value:
            continue

        normalized_items.append(
            attachment_record_from_url(
                url_value,
                name=str(item.get("name") or item.get("filename") or "").strip() or None,
                mime_type=str(item.get("mimeType") or item.get("mime_type") or "").strip() or None,
                size=item.get("size") if isinstance(item.get("size"), int) else None,
            )
        )

    return normalized_items


def save_uploaded_attachment(file_storage) -> dict[str, object]:
    filename = secure_filename(file_storage.filename or "")
    if not filename:
        raise ValueError("Nama file tidak valid.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise ValueError("Format file tidak didukung.")

    upload_folder = ensure_upload_folder()
    unique_name = f"{Path(filename).stem}_{uuid.uuid4().hex}{extension}"
    destination = upload_folder / unique_name
    file_storage.save(destination)

    return attachment_record_from_url(
        url_for("serve_uploaded_file", filename=unique_name),
        name=filename,
        mime_type=file_storage.mimetype,
        size=destination.stat().st_size,
    )


def current_user_context() -> dict[str, str]:
    return {
        "logged_in": bool(session.get("logged_in")),
        "user_id": session.get("user_id"),
        "username": session.get("username") or "",
        "nama": session.get("nama") or "",
        "role": session.get("role") or "",
        "telp": session.get("telp") or "",
        "email": session.get("email") or "",
        "alamat": session.get("alamat") or "",
        "tgl_lahir": session.get("tgl_lahir") or "",
        "status_akun": session.get("status_akun") or "",
    }


def normalize_phone(value: str) -> str:
    cleaned = re.sub(r"[\s\-()]+", "", (value or "").strip())
    if cleaned.startswith("+62"):
        return "62" + cleaned[3:]
    if cleaned.startswith("08"):
        return "62" + cleaned[1:]
    return cleaned


def normalize_status(value: str) -> str:
    raw = (value or "").strip().lower()
    return "aktif" if raw in {"", "aktif", "active"} else "nonaktif"


def normalize_role_value(value: str) -> str:
    raw = (value or "").strip().lower().replace(" ", "_")
    if raw in {"super_admin", "superadmin"}:
        return "super_admin"
    if raw == "admin":
        return "admin"
    return "user"


def member_row_to_dict(row: dict[str, object]) -> dict[str, object]:
    birth_date = row.get("tgl_lahir") or ""
    status_value = row.get("status_akun") or "aktif"
    return {
        "id": row.get("id"),
        "name": row.get("nama") or "Anggota",
        "fullName": row.get("nama") or "Anggota",
        "username": row.get("username") or "",
        "email": row.get("email") or "",
        "phone": row.get("telp") or "",
        "address": row.get("alamat") or "",
        "birthDate": birth_date,
        "tanggalLahir": birth_date,
        "role": normalize_role_value(row.get("role") or "user"),
        "status": "Aktif" if normalize_status(status_value) == "aktif" else "Nonaktif",
        "password": row.get("password") or "",
        "note": "",
        "registeredAt": row.get("created_at") or "",
        "createdAt": row.get("created_at") or "",
        "updatedAt": row.get("updated_at") or "",
        "inactiveUntil": "",
    }


def read_member_rows() -> list[dict[str, object]]:
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun
        , created_at, updated_at
        FROM anggota
        ORDER BY id ASC
        """
    )
    rows = [member_row_to_dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def hash_member_password(password_value: str, birth_date: str) -> str:
    candidate = (password_value or "").strip()
    if not candidate:
        candidate = default_password_from_birth_date(birth_date)
    if candidate.startswith(("scrypt:", "pbkdf2:", "argon2:", "bcrypt:")):
        return candidate
    return generate_password_hash(candidate)


def default_password_from_birth_date(birth_date: str) -> str:
    raw = (birth_date or "").strip()
    if not raw:
        return ""
    parts = raw.split("-")
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return raw


def ensure_column(cursor, table_name: str, column_name: str, definition: str) -> None:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (MYSQL_CONFIG["database"], table_name, column_name),
    )
    exists = cursor.fetchone()[0] > 0
    if not exists:
        cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {definition}")


def ensure_news_schema() -> None:
    """Ensure news/article tables exist in database."""
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        # News categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `news_categories` (
                `id` VARCHAR(100) PRIMARY KEY,
                `name` VARCHAR(255) NOT NULL UNIQUE,
                `slug` VARCHAR(255) NOT NULL UNIQUE,
                `description` TEXT,
                `order_index` INT DEFAULT 0,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)

        # News/articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `news` (
                `id` VARCHAR(100) PRIMARY KEY,
                `title` VARCHAR(500) NOT NULL,
                `slug` VARCHAR(500) NOT NULL UNIQUE,
                `content` LONGTEXT NOT NULL,
                `summary` TEXT,
                `thumbnails` JSON,
                `attachments` JSON,
                `status` VARCHAR(20) DEFAULT 'draft',
                `published_at` DATETIME,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)

        # Junction table for news-category mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `news_category_mapping` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `news_id` VARCHAR(100) NOT NULL,
                `category_id` VARCHAR(100) NOT NULL,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (`news_id`) REFERENCES `news`(`id`) ON DELETE CASCADE,
                FOREIGN KEY (`category_id`) REFERENCES `news_categories`(`id`) ON DELETE CASCADE,
                UNIQUE KEY `unique_news_category` (`news_id`, `category_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)

        conn.commit()
    except Exception as e:
        print(f"[INFO] News schema ensure: {e}")
    finally:
        cursor.close()
        conn.close()


def ensure_agenda_schema() -> None:
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `agendas` (
              `id` varchar(100) NOT NULL,
              `title` varchar(255) NOT NULL,
              `description` longtext DEFAULT NULL,
              `start_date` date NOT NULL,
              `start_time` time NOT NULL,
              `end_date` date DEFAULT NULL,
              `end_time` time DEFAULT NULL,
              `location` varchar(255) DEFAULT NULL,
              `registration_link` varchar(500) DEFAULT NULL,
              `image_url` text DEFAULT NULL,
              `image_name` varchar(255) DEFAULT NULL,
              `attachments` longtext DEFAULT NULL,
              `status` varchar(20) NOT NULL DEFAULT 'active',
              `order_index` int(11) NOT NULL DEFAULT 0,
              `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def ensure_auth_schema() -> None:
    conn = mysql_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `anggota` (
          `id` int(11) NOT NULL,
          `nama` varchar(255) DEFAULT NULL,
          `username` varchar(150) DEFAULT NULL,
          `telp` varchar(50) DEFAULT NULL,
          `password` varchar(255) DEFAULT NULL,
          `role` varchar(50) DEFAULT NULL,
          `tgl_lahir` varchar(50) DEFAULT NULL,
          `email` varchar(255) DEFAULT NULL,
          `alamat` text DEFAULT NULL,
          `status_akun` varchar(20) NOT NULL DEFAULT 'aktif',
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          UNIQUE KEY `uniq_anggota_username` (`username`),
          UNIQUE KEY `uniq_anggota_email` (`email`),
          UNIQUE KEY `uniq_anggota_telp` (`telp`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )

    ensure_column(cursor, "anggota", "alamat", "`alamat` text DEFAULT NULL")
    ensure_column(cursor, "anggota", "status_akun", "`status_akun` varchar(20) NOT NULL DEFAULT 'aktif'")
    ensure_column(cursor, "anggota", "created_at", "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
    ensure_column(cursor, "anggota", "updated_at", "`updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

    cursor.execute("UPDATE `anggota` SET `status_akun` = 'aktif' WHERE `status_akun` IS NULL OR `status_akun` = ''")
    cursor.execute(
        """
        UPDATE `anggota`
        SET `created_at` = COALESCE(`created_at`, CURRENT_TIMESTAMP),
            `updated_at` = COALESCE(`updated_at`, CURRENT_TIMESTAMP)
        WHERE `created_at` IS NULL OR `updated_at` IS NULL
        """
    )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'db_anggota'
        """,
        (MYSQL_CONFIG["database"],),
    )
    legacy_exists = cursor.fetchone()[0] > 0
    if legacy_exists:
        legacy_cursor = conn.cursor(dictionary=True)
        legacy_cursor.execute(
            "SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun FROM db_anggota"
        )
        for legacy_row in legacy_cursor.fetchall():
            cursor.execute(
                """
                INSERT IGNORE INTO anggota
                (id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    legacy_row.get("id"),
                    legacy_row.get("nama"),
                    legacy_row.get("username"),
                    legacy_row.get("telp"),
                    legacy_row.get("password"),
                    legacy_row.get("role"),
                    legacy_row.get("tgl_lahir"),
                    legacy_row.get("email"),
                    legacy_row.get("alamat"),
                    legacy_row.get("status_akun") or "aktif",
                ),
            )
        legacy_cursor.close()
        cursor.execute("DROP TABLE `db_anggota`")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `carousel_slides` (
          `id` varchar(100) NOT NULL,
          `title` varchar(255) DEFAULT NULL,
          `slug` varchar(255) DEFAULT NULL,
          `description` text DEFAULT NULL,
          `button_text` varchar(100) DEFAULT NULL,
          `button_link` varchar(255) DEFAULT NULL,
          `background_image` text DEFAULT NULL,
          `order_index` int(11) DEFAULT 0,
          `is_visible` tinyint(1) DEFAULT 1,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS `tentang_crembo_config` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `description` text DEFAULT NULL,
          `button_text` varchar(255) DEFAULT NULL,
          `button_link` varchar(255) DEFAULT NULL,
          `auto_seconds` int(11) DEFAULT 5,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        '''
    )
    cursor.execute("SELECT COUNT(*) FROM `tentang_crembo_config`")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO `tentang_crembo_config` (`id`, `description`, `button_text`, `button_link`, `auto_seconds`) VALUES (1, 'Ringkasan profil organisasi, visi pelayanan multimedia, serta peran Crembo dalam mendukung kegiatan liturgi dan agenda komunitas.', 'Pelajari Lebih Lanjut', 'profil.html', 5)")

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS `tentang_crembo_media` (
          `id` varchar(100) NOT NULL,
          `type` varchar(50) DEFAULT 'image',
          `url` text DEFAULT NULL,
          `order_index` int(11) DEFAULT 0,
          `is_visible` tinyint(1) DEFAULT 1,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS `instagram_posts` (
          `id_instagram` varchar(100) NOT NULL,
          `judul_instagram` varchar(200) NOT NULL,
          `url_instagram` varchar(255) NOT NULL,
          `urutan` int(11) NOT NULL DEFAULT 0,
          `tgl_instagram` datetime DEFAULT CURRENT_TIMESTAMP,
          `ip` varchar(25) DEFAULT NULL,
          `status` tinyint(1) NOT NULL DEFAULT 1,
          PRIMARY KEY (`id_instagram`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        '''
    )

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `youtube_embeds` (
          `id` varchar(100) NOT NULL,
          `url` varchar(255) NOT NULL,
          `order_index` int(11) DEFAULT 0,
          `is_visible` tinyint(1) DEFAULT 1,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `google_maps_embed` (
          `id` int(11) NOT NULL,
          `url` text DEFAULT NULL,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')
    cursor.execute("SELECT COUNT(*) FROM `google_maps_embed`")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO `google_maps_embed` (`id`, `url`) VALUES (1, '')")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `sertifikat_config` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `ketua_name` varchar(255) DEFAULT 'Ketua Crembo Media',
          `pembina_name` varchar(255) DEFAULT 'Pembina Crembo Media',
          `ketua_sign_url` text DEFAULT NULL,
          `pembina_sign_url` text DEFAULT NULL,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')
    cursor.execute("SELECT COUNT(*) FROM `sertifikat_config`")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO `sertifikat_config` (`id`, `ketua_name`, `pembina_name`, `ketua_sign_url`, `pembina_sign_url`) VALUES (1, 'Ketua Crembo Media', 'Pembina Crembo Media', '', '')")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `organization_profiles` (
          `id` varchar(100) NOT NULL,
          `title` varchar(255) NOT NULL,
          `description` text DEFAULT NULL,
          `attachment_url` text DEFAULT NULL,
          `order_index` int(11) DEFAULT 0,
          `is_visible` tinyint(1) DEFAULT 1,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')
        
    conn.commit()
    cursor.close()
    conn.close()

def fetch_member(identifier: str):
    ensure_auth_schema()
    needle = (identifier or "").strip()
    needle_lower = needle.lower()
    needle_phone = normalize_phone(needle)

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun
        , created_at, updated_at
        FROM anggota
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in rows:
        if needle_lower and (
            needle_lower == (row.get("username") or "").strip().lower()
            or needle_lower == (row.get("email") or "").strip().lower()
            or needle_phone and needle_phone == normalize_phone(row.get("telp") or "")
        ):
            return row
    return None


def can_manage_members() -> bool:
    return bool(session.get("logged_in")) and (session.get("role") or "") in {"admin", "super_admin"}


def read_members_for_admin() -> list[dict[str, object]]:
    return read_member_rows()


def sync_members_from_payload(payload: list[dict[str, object]]) -> None:
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute("DELETE FROM anggota")

        existing_ids = [int(i.get("id")) for i in payload if str(i.get("id")).isdigit()]
        next_id = max(existing_ids) + 1 if existing_ids else 1

        for index, item in enumerate(payload, start=1):
            birth_date = str(item.get("birthDate") or item.get("tanggalLahir") or "").strip()
            status_value = normalize_status(item.get("status") or item.get("status_akun") or "aktif")
            password_value = item.get("password") or ""
            hashed_password = hash_member_password(str(password_value), birth_date)
            
            try:
                member_id = int(item.get("id"))
            except (TypeError, ValueError):
                member_id = next_id
                next_id += 1

            cursor.execute(
                """
                INSERT INTO anggota
                (id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    member_id,
                    item.get("name") or item.get("fullName") or "Anggota",
                    item.get("username") or item.get("email") or item.get("phone") or f"anggota-{index}",
                    item.get("phone") or "",
                    hashed_password,
                    normalize_role_value(item.get("role") or "user"),
                    birth_date,
                    item.get("email") or "",
                    item.get("address") or "",
                    status_value,
                ),
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def login_target_for_role(role: str) -> str:
    if role == "user":
        return url_for("dashboard_anggota")
    return url_for("dashboard")


def load_about_content_from_db() -> dict[str, object]:
    default_about = {
        "description": "Ringkasan profil organisasi, visi pelayanan multimedia, serta peran Crembo dalam mendukung kegiatan liturgi dan agenda komunitas. Konten ini nantinya diatur dari panel admin setelah login.",
        "buttonText": "Pelajari Lebih Lanjut",
        "buttonLink": "profil.html",
        "autoSeconds": 5,
        "images": [],
    }

    try:
        ensure_auth_schema()
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT description, button_text, button_link, auto_seconds FROM `tentang_crembo_config` WHERE `id`=1 LIMIT 1")
        cfg = cursor.fetchone() or {}
        cursor.execute("SELECT `id`, `type`, `url`, `order_index`, `is_visible` FROM `tentang_crembo_media` ORDER BY `order_index` ASC")
        media_rows = cursor.fetchall() or []
        cursor.close()
        conn.close()

        return {
            "description": cfg.get("description") or default_about["description"],
            "buttonText": cfg.get("button_text") or default_about["buttonText"],
            "buttonLink": cfg.get("button_link") or default_about["buttonLink"],
            "autoSeconds": int(cfg.get("auto_seconds") or default_about["autoSeconds"]),
            "images": [
                {
                    "id": row.get("id"),
                    "type": row.get("type") or "image",
                    "url": row.get("url") or "",
                    "order": row.get("order_index") or 0,
                    "active": bool(row.get("is_visible")),
                }
                for row in media_rows
            ],
        }
    except Exception:
        return default_about


def is_valid_instagram_url(url: str) -> bool:
    return bool(re.match(r"^https?://(www\.)?(instagram\.com|instagr\.am)/(p|reel|tv)/[A-Za-z0-9_\-\.]+/?", (url or "").strip(), re.IGNORECASE))


def normalize_instagram_url(url: str) -> str:
    raw = (url or "").strip()
    if raw and not re.match(r"^https?://", raw, re.IGNORECASE):
        raw = "https://" + raw
    return raw


def load_instagram_posts_from_db(limit: int | None = None, active_only: bool = True) -> list[dict[str, object]]:
    try:
        ensure_auth_schema()
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT `id_instagram`, `judul_instagram`, `url_instagram`, `urutan`, `status`, `tgl_instagram` FROM `instagram_posts`"
        if active_only:
            sql += " WHERE `status` = 1"
        sql += " ORDER BY `urutan` ASC, `id_instagram` DESC"
        if limit is not None:
            sql += " LIMIT %s"
            cursor.execute(sql, (int(limit),))
        else:
            cursor.execute(sql)
        rows = cursor.fetchall() or []
        cursor.close()
        conn.close()
        return [
            {
                "id": row.get("id_instagram"),
                "title": row.get("judul_instagram") or "Instagram",
                "url": row.get("url_instagram") or "",
                "order": row.get("urutan") or 0,
                "active": bool(row.get("status")),
                "createdAt": row.get("tgl_instagram") or "",
            }
            for row in rows
        ]
    except Exception:
        return []


def save_instagram_posts_payload(payload: list[dict[str, object]]) -> int:
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute("DELETE FROM `instagram_posts`")
        saved_count = 0
        for index, item in enumerate(payload, start=1):
            title = str(item.get("title") or item.get("judul") or "").strip()
            url = normalize_instagram_url(str(item.get("url") or item.get("url_instagram") or "").strip())
            if not title or not url or not is_valid_instagram_url(url):
                continue

            post_id = str(item.get("id") or item.get("id_instagram") or f"ig-{index}-{int(time.time())}")
            order_value = int(item.get("order") or item.get("urutan") or index)
            active_value = 1 if item.get("active", True) else 0

            cursor.execute(
                """
                INSERT INTO `instagram_posts`
                (`id_instagram`, `judul_instagram`, `url_instagram`, `urutan`, `tgl_instagram`, `ip`, `status`)
                VALUES (%s, %s, %s, %s, NOW(), %s, %s)
                """,
                (post_id, title, url, order_value, request.remote_addr or "127.0.0.1", active_value),
            )
            saved_count += 1

        conn.commit()
        return saved_count
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def load_youtube_videos():
    try:
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM `youtube_embeds` WHERE `is_visible`=1 ORDER BY `order_index` ASC")
        rows = cursor.fetchall() or []
        conn.close()
        return [{"id": r["id"], "url": r["url"], "order": r["order_index"]} for r in rows]
    except Exception:
        return []

def load_gmaps_url():
    try:
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT `url` FROM `google_maps_embed` WHERE `id`=1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row["url"] if row and row["url"] else ""
    except Exception:
        return ""

def load_carousel_slides():
    try:
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        # Ambil hanya yang aktif untuk di home
        cursor.execute("SELECT * FROM `carousel_slides` WHERE `is_visible`=1 ORDER BY `order_index` ASC")
        rows = cursor.fetchall() or []
        conn.close()
        return [{
            "id": r["id"],
            "title": r["title"],
            "slug": r["slug"],
            "description": r["description"],
            "buttonText": r["button_text"],
            "link": r["button_link"],
            "backgroundImage": r["background_image"],
            "order": r["order_index"],
            "active": bool(r["is_visible"])
        } for r in rows]
    except Exception:
        return []


def load_public_profile_menu_from_db() -> list[dict[str, str]]:
    default_profile_menu = [
        {"id": "sejarah", "label": "Sejarah"},
        {"id": "tentang-crembo", "label": "Tentang Crembo"},
        {"id": "struktur", "label": "Struktur"},
        {"id": "visi-misi", "label": "Visi & Misi"},
    ]

    try:
        ensure_auth_schema()
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT `id`, `title`
            FROM `organization_profiles`
            WHERE COALESCE(`is_visible`, 1) = 1
            ORDER BY `order_index` ASC, `title` ASC
            """
        )
        rows = cursor.fetchall() or []
        cursor.close()
        conn.close()

        profile_menu = []
        for row in rows:
            profile_id = (row.get("id") or "").strip()
            title = (row.get("title") or "").strip()
            if profile_id and title:
                profile_menu.append({"id": profile_id, "label": title})

        return profile_menu or default_profile_menu
    except Exception:
        return default_profile_menu

def build_home_page_data() -> dict[str, object]:
    # Ambil slide dari database
    db_slides = load_carousel_slides()
    
    # Jika database masih kosong, tampilkan default bawaan (agar layout tidak hancur)
    if not db_slides:
        db_slides = [
            {
                "id": "default-1",
                "title": "Jadwal Misa Mingguan",
                "slug": "jadwal-misa",
                "description": "Lihat jadwal pelayanan streaming mingguan terbaru dari tim multimedia.",
                "link": "jadwal-streaming.html",
                "buttonText": "Lihat Jadwal",
                "backgroundImage": "",
                "order": 1,
                "active": True,
            },
            {
                "id": "default-2",
                "title": "Open Recruitment Petugas",
                "slug": "open-recruitment",
                "description": "Bergabung sebagai petugas multimedia untuk mendukung pelayanan misa.",
                "link": "form-pendaftaran.html",
                "buttonText": "Daftar Sekarang",
                "backgroundImage": "",
                "order": 2,
                "active": True,
            }
        ]

    return {
        "carouselSlides": db_slides,
        "aboutContent": load_about_content_from_db(),
        "instagramPosts": load_instagram_posts_from_db(limit=12, active_only=True),
        "youtubeVideos": load_youtube_videos(),
        "gmapsUrl": load_gmaps_url(),
        "bigMassSchedules": [],
        "instagramAutoSeconds": 4,
        "profileMenu": load_public_profile_menu_from_db(),
    }


@app.route("/")
def index():
    home_page_data = build_home_page_data()
    return render_template("home.html", home_page_data=home_page_data, current_user=current_user_context())


@app.route("/login", methods=["GET", "POST"])
def login():
    ensure_auth_schema()

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Username, email, atau nomor WhatsApp dan kata sandi wajib diisi.", "error")
            return render_template("login.html")

        member = fetch_member(identifier)
        if not member:
            flash("Akun tidak ditemukan.", "error")
            return render_template("login.html")

        if (member.get("status_akun") or "aktif").lower() != "aktif":
            flash("Akun Anda sedang nonaktif.", "error")
            return render_template("login.html")

        if not check_password_hash(member["password"], password):
            flash("Kata sandi salah.", "error")
            return render_template("login.html")

        session.clear()
        session["logged_in"] = True
        session["user_id"] = member["id"]
        session["username"] = member.get("username")
        session["nama"] = member.get("nama")
        session["role"] = member.get("role") or "user"
        session["telp"] = member.get("telp")
        session["email"] = member.get("email")
        session["alamat"] = member.get("alamat")
        session["tgl_lahir"] = member.get("tgl_lahir")
        session["status_akun"] = member.get("status_akun") or "aktif"

        return redirect(login_target_for_role(session["role"]))

    return render_template("login.html", current_user=current_user_context())


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") == "user":
        return redirect(url_for("dashboard_anggota"))
    return render_template("dashboard.html", current_user=current_user_context())


@app.route("/dashboard-anggota")
def dashboard_anggota():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") != "user":
        return redirect(url_for("dashboard"))
    return render_template("dashboard-anggota.html", current_user=current_user_context())


@app.route("/profil")
def profil():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") == "user":
        return render_template("profil-anggota.html", current_user=current_user_context())
    return render_template("profil-admin.html", current_user=current_user_context())


@app.route("/api/anggota", methods=["GET"])
def api_anggota_list():
    if not can_manage_members():
        return jsonify({"ok": False, "message": "Unauthorized"}), 403
    return jsonify({"ok": True, "members": read_members_for_admin()})


@app.route("/api/anggota/sync", methods=["POST"])
def api_anggota_sync():
    if not can_manage_members():
        return jsonify({"ok": False, "message": "Unauthorized"}), 403

    payload = request.get_json(silent=True) or {}
    members = payload.get("members")
    if not isinstance(members, list):
        return jsonify({"ok": False, "message": "Payload members harus array."}), 400

    sync_members_from_payload(members)
    return jsonify({"ok": True, "members": read_members_for_admin()})


@app.route("/api/profile/update", methods=["POST"])
def api_profile_update():
    if not session.get("logged_in"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    # Extract fields (do not allow updating role, nama, etc. if not authorized)
    # The requirement is that full name is readonly, so we skip it.
    username = payload.get("username", "").strip()
    email = payload.get("email", "").strip()
    telp = payload.get("phone", "").strip()
    alamat = payload.get("address", "").strip()
    tgl_lahir = payload.get("birthDate", "").strip()

    if not username or not email:
        return jsonify({"ok": False, "message": "Username dan email wajib diisi."}), 400

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        user_id = session.get("user_id")
        
        # Check uniqueness of username and email (excluding current user)
        cursor.execute("SELECT id FROM anggota WHERE (username = %s OR email = %s OR telp = %s) AND id != %s", (username, email, telp, user_id))
        if cursor.fetchone():
            return jsonify({"ok": False, "message": "Username, email, atau telepon sudah digunakan oleh akun lain."}), 400
            
        cursor.execute(
            """
            UPDATE anggota 
            SET username = %s, email = %s, telp = %s, alamat = %s, tgl_lahir = %s
            WHERE id = %s
            """,
            (username, email, telp, alamat, tgl_lahir, user_id)
        )
        conn.commit()
        
        # Update session
        session["username"] = username
        session["email"] = email
        session["telp"] = telp
        session["alamat"] = alamat
        session["tgl_lahir"] = tgl_lahir
        
        return jsonify({"ok": True, "message": "Profil berhasil diperbarui."})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/profile/password", methods=["POST"])
def api_profile_password():
    if not session.get("logged_in"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("currentPassword", "")
    new_password = payload.get("newPassword", "")

    if len(new_password) < 6:
        return jsonify({"ok": False, "message": "Password baru minimal 6 karakter."}), 400

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        user_id = session.get("user_id")
        cursor.execute("SELECT password, tgl_lahir FROM anggota WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        
        if not row or not check_password_hash(row["password"], current_password):
            return jsonify({"ok": False, "message": "Password saat ini salah."}), 400
            
        hashed_new_password = hash_member_password(new_password, row.get("tgl_lahir", ""))
        
        cursor.execute("UPDATE anggota SET password = %s WHERE id = %s", (hashed_new_password, user_id))
        conn.commit()
        
        return jsonify({"ok": True, "message": "Password berhasil diperbarui."})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/<path:page>")
def render_mockup_page(page: str):
    if page in {"favicon.ico"}:
        abort(404)

    asset_path = FRONTEND_DIR / page
    if asset_path.is_file() and not page.endswith(".html"):
        return send_from_directory(FRONTEND_DIR, page)

    candidate = page
    if not candidate.endswith(".html"):
        candidate = f"{candidate}.html"

    if candidate == "login.html":
        session.clear()

    if template_exists(candidate):
        extra_context = {"current_user": current_user_context()}
        if candidate == "home.html":
            extra_context["home_page_data"] = build_home_page_data()
        if candidate == "manajemen-anggota.html":
            extra_context["member_rows"] = read_members_for_admin() if session.get("logged_in") else []
        return render_template(candidate, **extra_context)

    abort(404)


# --- TENTANG CREMBO ENDPOINTS ---

@app.route("/api/tentang/config", methods=["GET"])
def get_tentang_config():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `tentang_crembo_config` LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return jsonify({
            "description": row["description"],
            "buttonText": row["button_text"],
            "buttonLink": row["button_link"],
            "autoSeconds": row["auto_seconds"]
        })
    return jsonify({})

@app.route("/api/tentang/config", methods=["POST"])
def set_tentang_config():
    ensure_auth_schema()
    data = request.json or {}
    description = data.get("description", "")
    button_text = data.get("buttonText", "")
    button_link = data.get("buttonLink", "")
    try:
        auto_seconds = int(data.get("autoSeconds", 5))
    except (ValueError, TypeError):
        auto_seconds = 5

    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO `tentang_crembo_config` (`id`, `description`, `button_text`, `button_link`, `auto_seconds`)
        VALUES (1, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          `description` = VALUES(`description`),
          `button_text` = VALUES(`button_text`),
          `button_link` = VALUES(`button_link`),
          `auto_seconds` = VALUES(`auto_seconds`)
        """,
        (description, button_text, button_link, auto_seconds),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/tentang/media", methods=["GET"])
def get_tentang_media():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT `id`, `type`, `url`, `order_index`, `is_visible` FROM `tentang_crembo_media` ORDER BY `order_index` ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "type": r["type"],
            "url": r["url"],
            "order": r["order_index"],
            "active": bool(r["is_visible"])
        })
    return jsonify(out)

@app.route("/api/tentang/media/sync", methods=["POST"])
def sync_tentang_media():
    ensure_auth_schema()
    payload = request.json
    if not isinstance(payload, list):
        return jsonify({"success": False, "error": "Invalid payload format"}), 400
        
    conn = mysql_connection()
    cursor = conn.cursor()
    
    # Simple sync: delete all and insert fresh order
    cursor.execute("DELETE FROM `tentang_crembo_media`")
    
    for item in payload:
        item_id = item.get("id", "")
        item_type = item.get("type", "image")
        url = item.get("url", "")
        order = int(item.get("order", 0))
        active = 1 if item.get("active", True) else 0
        
        if item_id:
            cursor.execute("""
                INSERT INTO `tentang_crembo_media` (`id`, `type`, `url`, `order_index`, `is_visible`)
                VALUES (%s, %s, %s, %s, %s)
            """, (item_id, item_type, url, order, active))
            
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "count": len(payload)})


@app.route("/api/instagram/posts", methods=["GET"])
def get_instagram_posts():
    ensure_auth_schema()
    return jsonify({"ok": True, "posts": load_instagram_posts_from_db(limit=None, active_only=False)})


@app.route("/api/instagram/posts/sync", methods=["POST"])
def sync_instagram_posts():
    ensure_auth_schema()
    payload = request.get_json(silent=True)
    if not isinstance(payload, list):
        return jsonify({"ok": False, "message": "Invalid payload format"}), 400

    saved_count = save_instagram_posts_payload(payload)
    return jsonify({"ok": True, "count": saved_count})

import werkzeug.utils

@app.route("/uploads/<path:filename>")
def serve_uploaded_file(filename: str):
    upload_folder = ensure_upload_folder()
    return send_from_directory(upload_folder, filename)


@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    ensure_auth_schema()
    incoming_files = request.files.getlist("files")
    if not incoming_files:
        single_file = request.files.get("file")
        incoming_files = [single_file] if single_file and single_file.filename else []

    if not incoming_files:
        return jsonify({"success": False, "error": "No selected file"}), 400

    saved_files: list[dict[str, object]] = []
    try:
        for file in incoming_files:
            if not file or not file.filename:
                continue
            saved_files.append(save_uploaded_attachment(file))
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    if not saved_files:
        return jsonify({"success": False, "error": "No selected file"}), 400

    return jsonify({
        "success": True,
        "files": saved_files,
        "url": saved_files[0]["url"],
    })

@app.route("/api/youtube", methods=["GET"])
def get_youtube():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `youtube_embeds` ORDER BY `order_index` ASC")
    rows = cursor.fetchall() or []
    conn.close()
    return jsonify([{"id": r["id"], "url": r["url"], "order": r["order_index"], "active": bool(r["is_visible"])} for r in rows])

@app.route("/api/youtube/sync", methods=["POST"])
def sync_youtube():
    ensure_auth_schema()
    payload = request.json
    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM `youtube_embeds`")
    for item in payload:
        cursor.execute("INSERT INTO `youtube_embeds` (`id`, `url`, `order_index`, `is_visible`) VALUES (%s, %s, %s, %s)",
                       (item.get("id"), item.get("url"), item.get("order"), 1 if item.get("active") else 0))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/gmaps", methods=["GET"])
def api_get_gmaps():
    return jsonify({"url": load_gmaps_url()})

@app.route("/api/gmaps", methods=["POST"])
def api_set_gmaps():
    ensure_auth_schema()
    url = request.json.get("url", "")
    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE `google_maps_embed` SET `url` = %s WHERE `id` = 1", (url,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/carousel", methods=["GET"])
def get_carousel():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `carousel_slides` ORDER BY `order_index` ASC")
    rows = cursor.fetchall() or []
    conn.close()
    return jsonify([{
        "id": r["id"],
        "title": r["title"],
        "slug": r["slug"],
        "description": r["description"],
        "buttonText": r["button_text"],
        "link": r["button_link"],
        "backgroundImage": r["background_image"],
        "order": r["order_index"],
        "active": bool(r["is_visible"])
    } for r in rows])

@app.route("/api/carousel/sync", methods=["POST"])
def sync_carousel():
    ensure_auth_schema()
    payload = request.json
    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM `carousel_slides`")
    for item in payload:
        cursor.execute("""
            INSERT INTO `carousel_slides` 
            (`id`, `title`, `slug`, `description`, `button_text`, `button_link`, `background_image`, `order_index`, `is_visible`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            item.get("id"), item.get("title"), item.get("slug"), item.get("description"),
            item.get("buttonText"), item.get("link"), item.get("backgroundImage"),
            item.get("order"), 1 if item.get("active") else 0
        ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
@app.route("/api/sertifikat/config", methods=["GET"])
def get_sertifikat_config():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `sertifikat_config` LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return jsonify({
            "ketuaName": row["ketua_name"],
            "pembinaName": row["pembina_name"],
            "ketuaSignUrl": row["ketua_sign_url"],
            "pembinaSignUrl": row["pembina_sign_url"],
            "updatedAt": row["updated_at"]
        })
    return jsonify({})

@app.route("/api/sertifikat/config", methods=["POST"])
def set_sertifikat_config():
    ensure_auth_schema()
    data = request.json or {}
    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE `sertifikat_config` 
        SET `ketua_name` = %s, `pembina_name` = %s, `ketua_sign_url` = %s, `pembina_sign_url` = %s
        WHERE `id` = 1
    """, (data.get("ketuaName", ""), data.get("pembinaName", ""), data.get("ketuaSignUrl", ""), data.get("pembinaSignUrl", "")))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

# --- ORGANIZATION PROFILES ENDPOINTS ---

@app.route("/api/profiles", methods=["GET"])
def get_profiles():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `organization_profiles` ORDER BY `order_index` ASC")
    rows = cursor.fetchall() or []
    cursor.close()
    conn.close()
    profile_rows = []
    for row in rows:
        attachments = normalize_attachment_payload(row["attachment_url"])
        profile_rows.append({
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "attachmentUrl": attachments[0]["url"] if attachments else "",
            "attachments": attachments,
            "order": row["order_index"],
            "active": bool(row["is_visible"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        })
    return jsonify(profile_rows)

@app.route("/api/profiles", methods=["POST"])
def create_profile():
    ensure_auth_schema()
    data = request.json or {}
    profile_id = f"profile-{int(time.time() * 1000)}"
    attachments = normalize_attachment_payload(data.get("attachments"))
    if not attachments:
        attachments = normalize_attachment_payload(data.get("attachmentUrl"))

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO `organization_profiles` 
            (`id`, `title`, `description`, `attachment_url`, `order_index`, `is_visible`)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            profile_id,
            data.get("title", ""),
            data.get("description", ""),
            json.dumps(attachments, ensure_ascii=False),
            int(data.get("order", 0)),
            1 if data.get("active") else 0,
        ))
        conn.commit()
        return jsonify({"success": True, "id": profile_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/profiles/<profile_id>", methods=["PUT"])
def update_profile(profile_id):
    ensure_auth_schema()
    data = request.json or {}
    attachments = normalize_attachment_payload(data.get("attachments"))
    if not attachments:
        attachments = normalize_attachment_payload(data.get("attachmentUrl"))

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE `organization_profiles`
            SET `title` = %s, `description` = %s, `attachment_url` = %s, `order_index` = %s, `is_visible` = %s
            WHERE `id` = %s
        """, (
            data.get("title", ""),
            data.get("description", ""),
            json.dumps(attachments, ensure_ascii=False),
            int(data.get("order", 0)),
            1 if data.get("active") else 0,
            profile_id
        ))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/profiles/<profile_id>", methods=["DELETE"])
def delete_profile(profile_id):
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM `organization_profiles` WHERE `id` = %s", (profile_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# --- AGENDA ENDPOINTS ---

def agenda_row_to_dict(row):
    attachments_raw = row.get("attachments") or "[]"
    try:
        attachments = json.loads(attachments_raw) if isinstance(attachments_raw, str) else (attachments_raw or [])
    except (TypeError, ValueError):
        attachments = []

    return {
        "id": row.get("id"),
        "title": row.get("title") or "Agenda",
        "description": row.get("description") or "",
        "startDate": str(row.get("start_date") or ""),
        "startTime": str(row.get("start_time") or "")[:5],
        "endDate": str(row.get("end_date") or ""),
        "endTime": str(row.get("end_time") or "")[:5],
        "location": row.get("location") or "",
        "registrationLink": row.get("registration_link") or "",
        "imageUrl": row.get("image_url") or "",
        "imageName": row.get("image_name") or "",
        "attachments": attachments if isinstance(attachments, list) else [],
        "status": "active" if (row.get("status") or "active") == "active" else "inactive",
        "order": int(row.get("order_index") or 0),
        "createdAt": row.get("created_at") or "",
        "updatedAt": row.get("updated_at") or "",
    }


def agenda_payload_to_db_values(data, existing=None):
    source = existing or {}
    attachments = normalize_attachment_payload(data.get("attachments", source.get("attachments", [])))

    def value_for(*keys, default=""):
        for key in keys:
            current = data.get(key)
            if current not in (None, ""):
                return current
            current = source.get(key)
            if current not in (None, ""):
                return current
        return default

    order_value = data.get("order")
    if order_value in (None, ""):
        order_value = data.get("orderIndex")
    if order_value in (None, ""):
        order_value = source.get("order_index") or 0

    status_value = str(value_for("status", default="active")).lower()

    return {
        "title": str(value_for("title")).strip(),
        "description": str(value_for("description")).strip(),
        "start_date": str(value_for("startDate", "start_date")).strip(),
        "start_time": str(value_for("startTime", "start_time")).strip(),
        "end_date": str(value_for("endDate", "end_date")).strip() or None,
        "end_time": str(value_for("endTime", "end_time")).strip() or None,
        "location": str(value_for("location")).strip(),
        "registration_link": str(value_for("registrationLink", "registration_link")).strip(),
        "image_url": str(value_for("imageUrl", "image_url")).strip(),
        "image_name": str(value_for("imageName", "image_name")).strip(),
        "attachments": json.dumps(attachments, ensure_ascii=False),
        "status": "inactive" if status_value == "inactive" else "active",
        "order_index": int(order_value or 0),
    }


@app.route("/api/agendas", methods=["GET"])
def get_agendas():
    ensure_agenda_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `agendas` ORDER BY `order_index` ASC, `updated_at` DESC")
        rows = cursor.fetchall() or []
        return jsonify([agenda_row_to_dict(row) for row in rows])
    finally:
        cursor.close()
        conn.close()


@app.route("/api/agendas/<agenda_id>", methods=["GET"])
def get_agenda_detail(agenda_id):
    ensure_agenda_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `agendas` WHERE `id` = %s LIMIT 1", (agenda_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Agenda not found"}), 404
        return jsonify(agenda_row_to_dict(row))
    finally:
        cursor.close()
        conn.close()


@app.route("/api/agendas", methods=["POST"])
def create_agenda():
    ensure_agenda_schema()
    data = request.json or {}
    values = agenda_payload_to_db_values(data)
    if not values["title"] or not values["start_date"] or not values["start_time"]:
        return jsonify({"success": False, "error": "Judul, tanggal mulai, dan waktu mulai wajib diisi."}), 400

    agenda_id = f"agenda-{int(time.time() * 1000)}"
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `agendas`
            (`id`, `title`, `description`, `start_date`, `start_time`, `end_date`, `end_time`, `location`, `registration_link`, `image_url`, `image_name`, `attachments`, `status`, `order_index`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                agenda_id,
                values["title"],
                values["description"],
                values["start_date"],
                values["start_time"],
                values["end_date"],
                values["end_time"],
                values["location"],
                values["registration_link"],
                values["image_url"],
                values["image_name"],
                values["attachments"],
                values["status"],
                values["order_index"],
            ),
        )
        conn.commit()
        return jsonify({"success": True, "id": agenda_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/agendas/<agenda_id>", methods=["PUT"])
def update_agenda(agenda_id):
    ensure_agenda_schema()
    data = request.json or {}
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `agendas` WHERE `id` = %s LIMIT 1", (agenda_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "Agenda not found"}), 404

        values = agenda_payload_to_db_values(data, existing)
        if not values["title"] or not values["start_date"] or not values["start_time"]:
            return jsonify({"success": False, "error": "Judul, tanggal mulai, dan waktu mulai wajib diisi."}), 400

        cursor.execute(
            """
            UPDATE `agendas`
            SET `title` = %s,
                `description` = %s,
                `start_date` = %s,
                `start_time` = %s,
                `end_date` = %s,
                `end_time` = %s,
                `location` = %s,
                `registration_link` = %s,
                `image_url` = %s,
                `image_name` = %s,
                `attachments` = %s,
                `status` = %s,
                `order_index` = %s
            WHERE `id` = %s
            """,
            (
                values["title"],
                values["description"],
                values["start_date"],
                values["start_time"],
                values["end_date"],
                values["end_time"],
                values["location"],
                values["registration_link"],
                values["image_url"],
                values["image_name"],
                values["attachments"],
                values["status"],
                values["order_index"],
                agenda_id,
            ),
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/agendas/<agenda_id>", methods=["DELETE"])
def delete_agenda(agenda_id):
    ensure_agenda_schema()
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM `agendas` WHERE `id` = %s", (agenda_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- NEWS & CATEGORIES ENDPOINTS ---

@app.route("/api/news-categories", methods=["GET"])
def get_news_categories():
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `news_categories` ORDER BY `order_index`, `name`")
        categories = cursor.fetchall()
        return jsonify([{
            "id": cat["id"],
            "name": cat["name"],
            "slug": cat["slug"],
            "description": cat["description"],
            "order": cat["order_index"]
        } for cat in categories])
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news-categories", methods=["POST"])
def create_news_category():
    ensure_news_schema()
    data = request.json or {}
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    category_id = f"cat-{int(time.time() * 1000)}"

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO `news_categories` (`id`, `name`, `slug`, `description`, `order_index`)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            category_id,
            name,
            slug,
            data.get("description", ""),
            int(data.get("order", 0))
        ))
        conn.commit()
        return jsonify({"success": True, "id": category_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news-categories/<category_id>", methods=["PUT"])
def update_news_category(category_id):
    ensure_news_schema()
    data = request.json or {}
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE `news_categories`
            SET `name` = %s, `slug` = %s, `description` = %s, `order_index` = %s
            WHERE `id` = %s
        """, (
            name,
            slug,
            data.get("description", ""),
            int(data.get("order", 0)),
            category_id
        ))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news-categories/<category_id>", methods=["DELETE"])
def delete_news_category(category_id):
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM `news_category_mapping` WHERE `category_id` = %s", (category_id,))
        cursor.execute("DELETE FROM `news_categories` WHERE `id` = %s", (category_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news", methods=["GET"])
def get_news():
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM `news` ORDER BY `published_at` DESC, `created_at` DESC
        """)
        news_items = cursor.fetchall()
        
        result = []
        for item in news_items:
            # Get categories for this news
            cursor.execute("""
                SELECT c.id, c.name, c.slug FROM `news_category_mapping` m
                JOIN `news_categories` c ON m.category_id = c.id
                WHERE m.news_id = %s
            """, (item["id"],))
            categories = cursor.fetchall()
            
            result.append({
                "id": item["id"],
                "title": item["title"],
                "slug": item["slug"],
                "content": item["content"],
                "summary": item["summary"],
                "thumbnails": json.loads(item["thumbnails"] or "[]"),
                "attachments": json.loads(item["attachments"] or "[]"),
                "status": item["status"],
                "publishedAt": item["published_at"].isoformat() if item["published_at"] else None,
                "createdAt": item["created_at"].isoformat() if item["created_at"] else None,
                "categories": [{"id": c["id"], "name": c["name"], "slug": c["slug"]} for c in categories]
            })
        return jsonify(result)
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news/<news_id>", methods=["GET"])
def get_news_detail(news_id):
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `news` WHERE `id` = %s", (news_id,))
        item = cursor.fetchone()
        if not item:
            return jsonify({"error": "News not found"}), 404

        # Get categories for this news
        cursor.execute("""
            SELECT c.id, c.name, c.slug FROM `news_category_mapping` m
            JOIN `news_categories` c ON m.category_id = c.id
            WHERE m.news_id = %s
        """, (news_id,))
        categories = cursor.fetchall()

        return jsonify({
            "id": item["id"],
            "title": item["title"],
            "slug": item["slug"],
            "content": item["content"],
            "summary": item["summary"],
            "thumbnails": json.loads(item["thumbnails"] or "[]"),
            "attachments": json.loads(item["attachments"] or "[]"),
            "status": item["status"],
            "publishedAt": item["published_at"].isoformat() if item["published_at"] else None,
            "createdAt": item["created_at"].isoformat() if item["created_at"] else None,
            "categories": [{"id": c["id"], "name": c["name"], "slug": c["slug"]} for c in categories]
        })
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news", methods=["POST"])
def create_news():
    ensure_news_schema()
    data = request.json or {}
    news_id = f"news-{int(time.time() * 1000)}"
    
    title = (data.get("title") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    content = data.get("content", "")
    summary = data.get("summary", "")
    thumbnails = normalize_attachment_payload(data.get("thumbnails", []))
    attachments = normalize_attachment_payload(data.get("attachments", []))
    status = data.get("status", "draft")
    category_ids = data.get("categoryIds", [])

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO `news` (`id`, `title`, `slug`, `content`, `summary`, `thumbnails`, `attachments`, `status`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            news_id,
            title,
            slug,
            content,
            summary,
            json.dumps(thumbnails, ensure_ascii=False),
            json.dumps(attachments, ensure_ascii=False),
            status
        ))

        # Add categories
        for cat_id in category_ids:
            cursor.execute("""
                INSERT IGNORE INTO `news_category_mapping` (`news_id`, `category_id`)
                VALUES (%s, %s)
            """, (news_id, cat_id))

        conn.commit()
        return jsonify({"success": True, "id": news_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news/<news_id>", methods=["PUT"])
def update_news(news_id):
    ensure_news_schema()
    data = request.json or {}
    
    title = (data.get("title") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    content = data.get("content", "")
    summary = data.get("summary", "")
    thumbnails = normalize_attachment_payload(data.get("thumbnails", []))
    attachments = normalize_attachment_payload(data.get("attachments", []))
    status = data.get("status", "draft")
    category_ids = data.get("categoryIds", [])

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE `news`
            SET `title` = %s, `slug` = %s, `content` = %s, `summary` = %s, 
                `thumbnails` = %s, `attachments` = %s, `status` = %s
            WHERE `id` = %s
        """, (
            title,
            slug,
            content,
            summary,
            json.dumps(thumbnails, ensure_ascii=False),
            json.dumps(attachments, ensure_ascii=False),
            status,
            news_id
        ))

        # Update categories
        cursor.execute("DELETE FROM `news_category_mapping` WHERE `news_id` = %s", (news_id,))
        for cat_id in category_ids:
            cursor.execute("""
                INSERT IGNORE INTO `news_category_mapping` (`news_id`, `category_id`)
                VALUES (%s, %s)
            """, (news_id, cat_id))

        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/news/<news_id>", methods=["DELETE"])
def delete_news(news_id):
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM `news_category_mapping` WHERE `news_id` = %s", (news_id,))
        cursor.execute("DELETE FROM `news` WHERE `id` = %s", (news_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        ensure_auth_schema()
        ensure_news_schema()
        ensure_agenda_schema()
    except Exception as exc:
        print(f"[WARN] MySQL bootstrap skipped: {exc}")
    app.run(debug=True)
        
