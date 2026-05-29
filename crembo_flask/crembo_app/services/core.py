from pathlib import Path
import json
from datetime import datetime, timedelta
from io import BytesIO
import os
import re
import time
import uuid
import html
import calendar
import secrets
import smtplib
import threading
import queue
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr
import mimetypes

from crembo_app.config import settings as app_settings

import mysql.connector
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = app_settings.BASE_DIR
FRONTEND_DIR = app_settings.FRONTEND_DIR
PUBLIC_FAVICON_PATH = app_settings.PUBLIC_FAVICON_PATH

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR),
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = app_settings.SECRET_KEY
app.permanent_session_lifetime = timedelta(days=app_settings.SESSION_LIFETIME_DAYS)


@app.errorhandler(404)
def handle_api_not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "message": "Endpoint API tidak ditemukan."}), 404
    return error

@app.errorhandler(403)
def handle_api_forbidden(error):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "message": "Akses ditolak."}), 403
    return error

@app.errorhandler(500)
def handle_api_internal_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "message": "Terjadi kesalahan server pada API. Cek terminal Flask untuk detailnya."}), 500
    return error


@app.after_request
def add_monitoring_api_cors_headers(response):
    if request.path.startswith("/api/monitoring-kewajiban-tugas/"):
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
    return response

@app.after_request
def add_html_no_cache_headers(response):
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "text/html" in content_type:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.after_request
def clean_public_html_urls(response):
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "text/html" not in content_type:
        return response

    body = response.get_data(as_text=True)
    if not body:
        return response

    if "rel=\"icon\"" not in body and "rel='icon'" not in body:
        favicon_links = (
            '    <link rel="icon" type="image/png" href="/favicon.ico">\n'
            '    <link rel="shortcut icon" type="image/png" href="/favicon.ico">\n'
        )
        body = body.replace("</head>", f"{favicon_links}</head>", 1)

    body = body.replace(".html", "")
    response.set_data(body)
    return response



MYSQL_CONFIG = app_settings.MYSQL_CONFIG

# Konfigurasi aplikasi diambil dari crembo_app/config/settings.py dan file .env.
SMTP_HOST = app_settings.SMTP_HOST
SMTP_PORT = app_settings.SMTP_PORT
SMTP_USERNAME = app_settings.SMTP_USERNAME
SMTP_PASSWORD = app_settings.SMTP_PASSWORD
SMTP_FROM_EMAIL = app_settings.SMTP_FROM_EMAIL
SMTP_FROM_NAME = app_settings.SMTP_FROM_NAME
EMAIL_LOGO_PATH = app_settings.EMAIL_LOGO_PATH
PUBLIC_BASE_URL = app_settings.PUBLIC_BASE_URL
NOTIFICATION_EMAIL_ENABLED = app_settings.NOTIFICATION_EMAIL_ENABLED
NOTIFICATION_EMAIL_RETRY_COUNT = app_settings.NOTIFICATION_EMAIL_RETRY_COUNT
NOTIFICATION_EMAIL_RETRY_DELAY_SECONDS = app_settings.NOTIFICATION_EMAIL_RETRY_DELAY_SECONDS
NOTIFICATION_EMAIL_SEND_DELAY_SECONDS = app_settings.NOTIFICATION_EMAIL_SEND_DELAY_SECONDS
NOTIFICATION_EMAIL_ROW_WAIT_ATTEMPTS = app_settings.NOTIFICATION_EMAIL_ROW_WAIT_ATTEMPTS
NOTIFICATION_EMAIL_ROW_WAIT_SECONDS = app_settings.NOTIFICATION_EMAIL_ROW_WAIT_SECONDS
_notification_email_queue: "queue.Queue[dict[str, object]]" = queue.Queue()
_notification_email_worker_started = False
_notification_email_worker_lock = threading.Lock()
_smtp_send_lock = threading.Lock()
PASSWORD_RESET_OTP_MINUTES = app_settings.PASSWORD_RESET_OTP_MINUTES
PASSWORD_RESET_RESEND_SECONDS = app_settings.PASSWORD_RESET_RESEND_SECONDS
PASSWORD_RESET_MAX_ATTEMPTS = app_settings.PASSWORD_RESET_MAX_ATTEMPTS

UPLOAD_FOLDER = FRONTEND_DIR / "uploads"
ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".pdf",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".txt", ".csv",
}
PREVIEWABLE_ATTACHMENT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".pdf",
}
INVENTORY_DEFAULT_CATEGORIES = ["Kamera", "Audio", "Aksesori", "Switcher", "Kabel", "Lighting", "Lainnya"]
INVENTORY_DEFAULT_ITEMS = []


ADMIN_MODULE_KEYS = ["streaming", "inventaris", "publikasi", "konten", "keanggotaan"]
ADMIN_MODULE_LABELS = {
    "streaming": "Tugas Streaming",
    "inventaris": "Inventaris & Peminjaman",
    "publikasi": "Informasi & Publikasi",
    "konten": "Konten Utama Website",
    "keanggotaan": "Keanggotaan",
}
ADMIN_PAGE_MODULE_MAP = {
    "jadwal-tugas-streaming-admin.html": "streaming",
    "registrasi-tugas-misa-besar.html": "streaming",
    "penugasan-petugas-misa.html": "streaming",
    "monitoring-tugas-anggota.html": "streaming",
    "hasil-evaluasi-streaming.html": "streaming",
    "setting-pertanyaan-evaluasi-streaming.html": "streaming",
    "data-inventaris-barang.html": "inventaris",
    "persetujuan-peminjaman.html": "inventaris",
    "riwayat-peminjaman-pengembalian.html": "inventaris",
    "hasil-form-kerusakan-barang.html": "inventaris",
    "manajemen-profil.html": "publikasi",
    "kelola-berita.html": "publikasi",
    "manajemen-agenda.html": "publikasi",
    "manajemen-form-pendaftaran.html": "publikasi",
    "kelola-carousel-home.html": "konten",
    "kelola-tentang-crembo.html": "konten",
    "kelola-embed-youtube.html": "konten",
    "kelola-embed-google-maps.html": "konten",
    "kelola-embed-instagram.html": "konten",
    "manajemen-anggota.html": "keanggotaan",
    "setting-sertifikat-anggota.html": "keanggotaan",
}

def default_admin_permissions() -> dict[str, bool]:
    return {key: True for key in ADMIN_MODULE_KEYS}

def normalize_admin_permissions(value=None, *, default_all: bool = True) -> dict[str, bool]:
    base = {key: bool(default_all) for key in ADMIN_MODULE_KEYS}
    if isinstance(value, str):
        value = safe_json_loads(value, {})
    if not isinstance(value, dict):
        return base
    normalized = {}
    for key in ADMIN_MODULE_KEYS:
        raw = value.get(key, base[key])
        normalized[key] = bool(raw) and str(raw).lower() not in {"0", "false", "no", "tidak", "off"}
    return normalized

def permission_row_to_dict(row) -> dict[str, bool]:
    if not row:
        return default_admin_permissions()
    return {key: bool(row.get(key, 1)) for key in ADMIN_MODULE_KEYS}

def ensure_admin_permissions_schema(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `admin_module_permissions` (
          `member_id` int(11) NOT NULL,
          `streaming` tinyint(1) NOT NULL DEFAULT 1,
          `inventaris` tinyint(1) NOT NULL DEFAULT 1,
          `publikasi` tinyint(1) NOT NULL DEFAULT 1,
          `konten` tinyint(1) NOT NULL DEFAULT 1,
          `keanggotaan` tinyint(1) NOT NULL DEFAULT 1,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`member_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    for key in ADMIN_MODULE_KEYS:
        ensure_column(cursor, "admin_module_permissions", key, f"`{key}` tinyint(1) NOT NULL DEFAULT 1")
    ensure_column(cursor, "admin_module_permissions", "created_at", "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
    ensure_column(cursor, "admin_module_permissions", "updated_at", "`updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    cursor.execute(
        """
        INSERT IGNORE INTO `admin_module_permissions`
          (`member_id`, `streaming`, `inventaris`, `publikasi`, `konten`, `keanggotaan`)
        SELECT `id`, 1, 1, 1, 1, 1
        FROM `anggota`
        WHERE `role` = 'admin'
        """
    )
    cursor.execute(
        """
        DELETE p FROM `admin_module_permissions` p
        LEFT JOIN `anggota` a ON a.id = p.member_id
        WHERE a.id IS NULL OR COALESCE(a.role, '') <> 'admin'
        """
    )

def get_admin_permissions(member_id=None, role: str | None = None) -> dict[str, bool]:
    normalized_role = normalize_role_value(role or session.get("role") or "")
    if normalized_role == "super_admin":
        return default_admin_permissions()
    if normalized_role != "admin":
        return default_admin_permissions()
    try:
        target_id = int(member_id if member_id is not None else session.get("user_id"))
    except (TypeError, ValueError):
        return default_admin_permissions()

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_admin_permissions_schema(cursor)
        cursor.execute("SELECT streaming, inventaris, publikasi, konten, keanggotaan FROM admin_module_permissions WHERE member_id = %s LIMIT 1", (target_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                """
                INSERT IGNORE INTO admin_module_permissions
                  (member_id, streaming, inventaris, publikasi, konten, keanggotaan)
                VALUES (%s, 1, 1, 1, 1, 1)
                """,
                (target_id,),
            )
            conn.commit()
            return default_admin_permissions()
        return permission_row_to_dict(row)
    finally:
        cursor.close()
        conn.close()

def admin_has_module_access(module_key: str) -> bool:
    if not session.get("logged_in"):
        return False
    role = normalize_role_value(session.get("role") or "")
    if role == "super_admin":
        return True
    if role != "admin":
        return False
    permissions = get_admin_permissions(session.get("user_id"), role)
    return bool(permissions.get(module_key))

def require_super_admin_api():
    if not session.get("logged_in") or normalize_role_value(session.get("role") or "") != "super_admin":
        return jsonify({"ok": False, "message": "Hanya Super Admin yang dapat mengakses Kelola Data Admin."}), 403
    return None

def template_exists(template_name: str) -> bool:
    return (FRONTEND_DIR / template_name).is_file()

def mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

def ensure_upload_folder() -> Path:
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    return UPLOAD_FOLDER

def normalize_text(value, fallback: str = "") -> str:
    return str(value if value is not None else fallback).strip()

def parse_optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return None

def parse_required_int(value, fallback: int = 0) -> int:
    parsed = parse_optional_int(value)
    return fallback if parsed is None else parsed

def fetch_scalar_value(row, default=0):
    if row is None:
        return default
    if isinstance(row, dict):
        return next(iter(row.values()), default)
    if isinstance(row, (list, tuple)):
        return row[0] if row else default
    return row

def parse_optional_date(value) -> str | None:
    raw = normalize_text(value)
    if not raw:
        return None
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None
    return raw

def safe_json_loads(value, fallback):
    if isinstance(value, (list, dict)):
        return value
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback

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

def remove_physical_file(file_url: str):
    if not file_url:
        return
    try:
        filename = file_url.split('/')[-1]
        file_path = UPLOAD_FOLDER / filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception as e:
        print(f"[WARN] Failed to delete file {file_url}: {e}")

def normalize_inventory_photos(value) -> list[dict[str, object]]:
    photos = normalize_attachment_payload(value)
    normalized: list[dict[str, object]] = []
    for photo in photos:
        if not isinstance(photo, dict):
            continue
        url_value = normalize_text(photo.get("url"))
        if not url_value:
            continue
        normalized.append(
            {
                "url": url_value,
                "name": normalize_text(photo.get("name")) or Path(url_value).name,
                "mimeType": normalize_text(photo.get("mimeType")),
                "size": parse_required_int(photo.get("size"), 0),
                "previewable": True,
                "kind": "image",
            }
        )
    return normalized

INVENTORY_UNIT_STATUSES = {"Tersedia", "Dipinjam", "Perbaikan", "Rusak", "Hilang"}

def inventory_unit_reason_for_status(status: str) -> str:
    return {
        "Dipinjam": "Sedang digunakan",
        "Perbaikan": "Sedang diperbaiki",
        "Rusak": "Kondisi rusak",
        "Hilang": "Belum ditemukan",
    }.get(normalize_text(status), "")

def normalize_inventory_unit_detail(value, index: int, fallback_status: str = "Tersedia") -> dict[str, object]:
    raw = value if isinstance(value, dict) else {}
    if isinstance(value, str):
        raw_status = normalize_text(value)
        if raw_status in INVENTORY_UNIT_STATUSES:
            raw = {"status": raw_status}
    status = normalize_text(raw.get("status")) or normalize_text(fallback_status) or "Tersedia"
    if status not in INVENTORY_UNIT_STATUSES:
        status = "Tersedia"
    reason = normalize_text(raw.get("reason") or raw.get("note") or raw.get("keterangan"))
    if not reason and status != "Tersedia":
        reason = inventory_unit_reason_for_status(status)
    return {
        "index": index + 1,
        "label": f"Unit {index + 1}",
        "status": status,
        "reason": reason,
        "available": status == "Tersedia",
    }

def normalize_inventory_unit_details(value, total_unit: int, available_unit: int | None = None, fallback_status: str = "Tersedia") -> list[dict[str, object]]:
    total = max(1, parse_required_int(total_unit, 1))
    raw_items = safe_json_loads(value, [])
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        raw_items = []

    normalized: list[dict[str, object]] = []
    available_target = total if available_unit is None else max(0, min(total, parse_required_int(available_unit, total)))
    fallback = normalize_text(fallback_status) or "Tersedia"
    if fallback not in INVENTORY_UNIT_STATUSES:
        fallback = "Dipinjam"
    if fallback == "Tersedia" and available_target < total:
        fallback = "Dipinjam"

    for index in range(total):
        raw_item = raw_items[index] if index < len(raw_items) else {}
        if not isinstance(raw_item, dict):
            raw_item = {}
        detail = normalize_inventory_unit_detail(raw_item, index, fallback_status=fallback)
        if index >= len(raw_items):
            if index < available_target:
                detail["status"] = "Tersedia"
                detail["reason"] = ""
                detail["available"] = True
            else:
                detail["status"] = fallback
                detail["reason"] = inventory_unit_reason_for_status(fallback) or detail["reason"]
                detail["available"] = False
        normalized.append(detail)

    return normalized

def inventory_status_from_unit_details(unit_details: list[dict[str, object]], fallback: str = "Tersedia") -> str:
    statuses = [normalize_text(unit.get("status")) for unit in unit_details if isinstance(unit, dict)]
    if not statuses or all(status == "Tersedia" for status in statuses):
        return "Tersedia"
    if any(status == "Dipinjam" for status in statuses):
        return "Dipinjam"
    if any(status == "Rusak" for status in statuses):
        return "Rusak"
    if any(status == "Perbaikan" for status in statuses):
        return "Perbaikan"
    if any(status == "Hilang" for status in statuses):
        return "Hilang"
    return normalize_text(fallback) or "Tersedia"

def inventory_unit_details_text(unit_details: list[dict[str, object]]) -> str:
    parts: list[str] = []
    for unit in unit_details:
        if not isinstance(unit, dict):
            continue
        label = normalize_text(unit.get("label")) or f"Unit {unit.get('index') or len(parts) + 1}"
        status = normalize_text(unit.get("status")) or "Tersedia"
        reason = normalize_text(unit.get("reason"))
        if reason:
            parts.append(f"{label}: {status} - {reason}")
        else:
            parts.append(f"{label}: {status}")
    return "; \n".join(parts)

def inventory_item_row_to_dict(row: dict[str, object]) -> dict[str, object]:
    photos = normalize_inventory_photos(safe_json_loads(row.get("photos"), []))
    total_unit = parse_required_int(row.get("total_unit"), 1)
    fallback_status = normalize_text(row.get("status")) or "Tersedia"
    unit_details = normalize_inventory_unit_details(
        safe_json_loads(row.get("unit_details"), []),
        total_unit,
        parse_required_int(row.get("available_unit"), total_unit),
        fallback_status=fallback_status,
    )
    available_unit = sum(1 for unit in unit_details if unit.get("status") == "Tersedia")
    purchase_date = row.get("purchase_date")
    purchase_price = row.get("purchase_price")
    updated_at = row.get("updated_at")
    created_at = row.get("created_at")
    photo_url = photos[0]["url"] if photos else ""
    return {
        "id": row.get("id") or "",
        "code": normalize_text(row.get("code")).upper(),
        "name": normalize_text(row.get("name")),
        "category": normalize_text(row.get("category")) or "Lainnya",
        "location": normalize_text(row.get("location")),
        "purchaseDate": purchase_date.isoformat() if hasattr(purchase_date, "isoformat") else normalize_text(purchase_date),
        "purchasePrice": int(purchase_price) if purchase_price not in (None, "") else None,
        "totalUnit": total_unit,
        "availableUnit": available_unit,
        "borrowedUnit": max(total_unit - available_unit, 0),
        "hasMultiple": bool(row.get("has_multiple")),
        "canBorrow": bool(row.get("can_borrow", True)),
        "status": inventory_status_from_unit_details(unit_details, fallback=fallback_status),
        "notes": normalize_text(row.get("notes")),
        "photos": photos,
        "unitDetails": unit_details,
        "photo": photo_url,
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else normalize_text(created_at),
        "updatedAt": updated_at.isoformat() if hasattr(updated_at, "isoformat") else normalize_text(updated_at),
    }

def inventory_summary_from_items(items: list[dict[str, object]]) -> dict[str, int]:
    total_unit = 0
    total_available = 0
    total_borrowed = 0
    for item in items:
        current_total = parse_required_int(item.get("totalUnit"), 0)
        current_available = parse_required_int(item.get("availableUnit"), 0)
        total_unit += current_total
        total_available += current_available
        total_borrowed += max(current_total - current_available, 0)
    return {
        "totalJenisBarang": len(items),
        "totalUnit": total_unit,
        "totalAvailable": total_available,
        "totalBorrowed": total_borrowed,
    }

def inventory_sort_items(items: list[dict[str, object]], sort_mode: str) -> list[dict[str, object]]:
    mode = normalize_text(sort_mode) or "updated-desc"
    def item_time(item: dict[str, object]) -> datetime:
        raw = normalize_text(item.get("updatedAt")) or "1970-01-01T00:00:00"
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return datetime(1970, 1, 1)

    if mode == "name-asc":
        return sorted(items, key=lambda item: normalize_text(item.get("name")).lower())
    if mode == "name-desc":
        return sorted(items, key=lambda item: normalize_text(item.get("name")).lower(), reverse=True)
    if mode == "updated-asc":
        return sorted(items, key=item_time)
    return sorted(items, key=item_time, reverse=True)

def inventory_filter_items(items: list[dict[str, object]], search: str = "", category: str = "all", status: str = "all", sort_mode: str = "updated-desc") -> list[dict[str, object]]:
    keyword = normalize_text(search).lower()
    category_value = normalize_text(category) or "all"
    status_value = normalize_text(status) or "all"

    filtered: list[dict[str, object]] = []
    for item in items:
        haystack = " ".join([
            normalize_text(item.get("code")),
            normalize_text(item.get("name")),
            normalize_text(item.get("category")),
            normalize_text(item.get("location")),
            normalize_text(item.get("notes")),
        ]).lower()
        matches_keyword = not keyword or keyword in haystack
        matches_category = category_value == "all" or normalize_text(item.get("category")) == category_value
        matches_status = status_value == "all" or normalize_text(item.get("status")) == status_value
        if matches_keyword and matches_category and matches_status:
            filtered.append(item)

    return inventory_sort_items(filtered, sort_mode)

def inventory_request_filters(args) -> dict[str, str]:
    return {
        "search": normalize_text(args.get("search")),
        "category": normalize_text(args.get("category")) or "all",
        "status": normalize_text(args.get("status")) or "all",
        "sort": normalize_text(args.get("sort")) or "updated-desc",
    }

def ensure_column(cursor, table_name: str, column_name: str, definition: str) -> None:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (MYSQL_CONFIG["database"], table_name, column_name),
    )
    row = cursor.fetchone()
    if isinstance(row, dict):
        exists = list(row.values())[0] > 0
    else:
        exists = row[0] > 0 if row else False
        
    if not exists:
        try:
            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {definition}")
        except mysql.connector.Error as exc:
            # Intermittent race antar request: dua request bisa ALTER kolom yang sama.
            # 1060 = Duplicate column name.
            if getattr(exc, "errno", None) != 1060:
                raise

def ensure_inventory_schema(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `inventory_categories` (
          `id` varchar(100) NOT NULL,
          `name` varchar(255) NOT NULL,
          `order_index` int(11) NOT NULL DEFAULT 0,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          UNIQUE KEY `uniq_inventory_category_name` (`name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `inventory_items` (
          `id` varchar(100) NOT NULL,
          `code` varchar(100) NOT NULL,
          `name` varchar(255) NOT NULL,
          `category` varchar(255) NOT NULL,
          `location` varchar(255) NOT NULL,
          `purchase_date` date DEFAULT NULL,
          `purchase_price` bigint(20) DEFAULT NULL,
          `total_unit` int(11) NOT NULL DEFAULT 1,
          `available_unit` int(11) NOT NULL DEFAULT 1,
          `has_multiple` tinyint(1) NOT NULL DEFAULT 0,
          `can_borrow` tinyint(1) NOT NULL DEFAULT 1,
          `status` varchar(50) NOT NULL DEFAULT 'Tersedia',
          `notes` text DEFAULT NULL,
          `photos` longtext DEFAULT NULL,
          `unit_details` longtext DEFAULT NULL,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          UNIQUE KEY `uniq_inventory_item_code` (`code`),
          KEY `idx_inventory_item_category` (`category`),
          KEY `idx_inventory_item_updated_at` (`updated_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    try:
        cursor.execute("ALTER TABLE `inventory_items` DROP COLUMN `condition`")
    except Exception:
        pass

    ensure_column(cursor, "inventory_items", "unit_details", "`unit_details` longtext DEFAULT NULL")

    cursor.execute("SELECT COUNT(*) FROM `inventory_categories`")
    if cursor.fetchone()[0] == 0:
        for order_index, category_name in enumerate(INVENTORY_DEFAULT_CATEGORIES, start=1):
            cursor.execute(
                """
                INSERT INTO `inventory_categories` (`id`, `name`, `order_index`)
                VALUES (%s, %s, %s)
                """,
                (f"inv-cat-{order_index:02d}", category_name, order_index),
            )

def inventory_category_exists(cursor, category_name: str) -> bool:
    cursor.execute("SELECT COUNT(*) FROM `inventory_categories` WHERE `name` = %s", (category_name,))
    row = cursor.fetchone()
    if isinstance(row, dict):
        return next(iter(row.values())) > 0
    return row[0] > 0 if row else False

def ensure_inventory_category(cursor, category_name: str) -> None:
    clean_name = normalize_text(category_name)
    if not clean_name:
        raise ValueError("Kategori wajib diisi.")
    if inventory_category_exists(cursor, clean_name):
        return
    cursor.execute("SELECT COALESCE(MAX(`order_index`), 0) + 1 FROM `inventory_categories`")
    row = cursor.fetchone()
    if isinstance(row, dict):
        next_order = next(iter(row.values())) or 1
    else:
        next_order = row[0] or 1 if row else 1
    cursor.execute(
        """
        INSERT INTO `inventory_categories` (`id`, `name`, `order_index`)
        VALUES (%s, %s, %s)
        """,
        (f"inv-cat-{uuid.uuid4().hex[:12]}", clean_name, next_order),
    )

def inventory_item_payload_from_request(data: dict[str, object], existing: dict[str, object] | None = None) -> dict[str, object]:
    code = normalize_text(data.get("code")).upper()
    name = normalize_text(data.get("name"))
    category = normalize_text(data.get("category"))
    location = normalize_text(data.get("location"))
    if not code:
        raise ValueError("Kode barang wajib diisi.")
    if not name:
        raise ValueError("Nama barang wajib diisi.")
    if not category:
        raise ValueError("Kategori wajib dipilih.")
    if not location:
        raise ValueError("Lokasi simpan wajib diisi.")

    has_multiple = bool(data.get("hasMultiple"))
    total_unit = parse_required_int(data.get("totalUnit"), 1) if has_multiple else 1
    total_unit = max(1, total_unit)
    available_unit = parse_required_int(data.get("availableUnit"), total_unit) if has_multiple else 1
    available_unit = min(total_unit, max(0, available_unit))
    fallback_status = normalize_text(data.get("status")) or (normalize_text(existing.get("status")) if existing else "Tersedia")
    purchase_date = parse_optional_date(data.get("purchaseDate"))
    purchase_price = parse_optional_int(data.get("purchasePrice"))
    can_borrow = bool(data.get("canBorrow", True))
    notes = normalize_text(data.get("notes"))

    if data.get("photos") is not None:
        photos = normalize_inventory_photos(data.get("photos"))
    elif data.get("photo"):
        photos = normalize_inventory_photos([data.get("photo")])
    elif existing is not None:
        photos = normalize_inventory_photos(safe_json_loads(existing.get("photos"), []))
    else:
        photos = []

    unit_details_source = data.get("unitDetails")
    if unit_details_source is None and existing is not None:
        unit_details_source = safe_json_loads(existing.get("unit_details"), [])
    unit_details = normalize_inventory_unit_details(unit_details_source, total_unit, available_unit, fallback_status=fallback_status)
    available_unit = sum(1 for unit in unit_details if unit.get("status") == "Tersedia")
    status = inventory_status_from_unit_details(unit_details, fallback=fallback_status)
    if status not in INVENTORY_UNIT_STATUSES:
        status = "Tersedia"
    if not can_borrow and status == "Dipinjam":
        status = "Tersedia"

    return {
        "code": code,
        "name": name,
        "category": category,
        "location": location,
        "purchase_date": purchase_date,
        "purchase_price": purchase_price,
        "total_unit": total_unit,
        "available_unit": available_unit,
        "has_multiple": 1 if has_multiple or total_unit > 1 else 0,
        "can_borrow": 1 if can_borrow else 0,
        "status": status,
        "notes": notes,
        "photos": photos,
        "unit_details": unit_details,
    }

def inventory_export_rows(items: list[dict[str, object]]):
    headers = [
        "Kode Barang",
        "Nama Barang",
        "Kategori",
        "Lokasi Simpan",
        "Tgl Pembelian",
        "Harga",
        "Total",
        "Tersedia",
        "Dipinjam",
        "Bisa Pinjam",
        "Rincian Unit",
        "Foto",
        "Keterangan",
        "Update",
    ]
    rows = []
    base_url = PUBLIC_BASE_URL 

    for item in items:
        photos = item.get("photos") or []
        photo_links = []
        for p in photos:
            if isinstance(p, dict) and p.get("url"):
                url = str(p.get("url"))
                if url.startswith("/"):
                    url = f"{base_url}{url}"
                photo_links.append(url)
                
        photo_label = "\n".join(photo_links) if photo_links else "-"
        rincian = inventory_unit_details_text(item.get("unitDetails") or [])
        keterangan = normalize_text(item.get("notes")) or "-"

        rows.append([
            normalize_text(item.get("code")),
            normalize_text(item.get("name")),
            normalize_text(item.get("category")),
            normalize_text(item.get("location")),
            normalize_text(item.get("purchaseDate")) or "-",
            format_currency(item.get("purchasePrice")),
            str(parse_required_int(item.get("totalUnit"), 0)),
            str(parse_required_int(item.get("availableUnit"), 0)),
            str(parse_required_int(item.get("borrowedUnit"), max(parse_required_int(item.get("totalUnit"), 0) - parse_required_int(item.get("availableUnit"), 0), 0))),
            "Ya" if item.get("canBorrow") else "Tidak",
            rincian,
            photo_label,
            keterangan,
            normalize_text(item.get("updatedAt"))[:10] if item.get("updatedAt") else "-",
        ])
    return headers, rows

def inventory_export_filename(extension: str) -> str:
    return f"laporan-data-inventaris-barang.{extension}"

def fetch_inventory_items_for_report(cursor, filters: dict[str, str]) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT `id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`,
                   `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `status`,
                   `notes`, `photos`, `unit_details`, `created_at`, `updated_at`
        FROM `inventory_items`
        ORDER BY `updated_at` DESC, `code` ASC
        """
    )
    items = [inventory_item_row_to_dict(row) for row in cursor.fetchall() or []]
    return inventory_filter_items(
        items,
        search=filters.get("search", ""),
        category=filters.get("category", "all"),
        status=filters.get("status", "all"),
        sort_mode=filters.get("sort", "updated-desc"),
    )

def format_currency(value):
    if value is None or value == "" or str(value).lower() == "none":
        return "-"
    try:
        val = int(value)
        return f"Rp {val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "-"










def get_inventory_item_response(cursor, item_id: str) -> dict[str, object]:
    cursor.execute(
        """
        SELECT `id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`,
         `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `status`,
         `notes`, `photos`, `unit_details`, `created_at`, `updated_at`
        FROM `inventory_items`
        WHERE `id` = %s
        LIMIT 1
        """,
        (item_id,),
    )
    row = cursor.fetchone() or {}
    return inventory_item_row_to_dict(row)





def _date_to_iso(value) -> str:
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)

def sync_session_from_member_row(row: dict[str, object] | None) -> None:
    """Sinkronkan session dari 1 row anggota tanpa menjalankan proses tulis DB."""
    if not row:
        return
    session["user_id"] = row.get("id")
    session["username"] = row.get("username") or ""
    session["nama"] = row.get("nama") or ""
    session["role"] = normalize_role_value(row.get("role") or "user")
    session["telp"] = row.get("telp") or ""
    session["email"] = row.get("email") or ""
    session["alamat"] = row.get("alamat") or ""
    session["tgl_lahir"] = _date_to_iso(row.get("tgl_lahir"))
    session["status_akun"] = row.get("status_akun") or "aktif"


def current_user_context_from_row(row: dict[str, object] | None, *, include_admin_permissions: bool = False) -> dict[str, object]:
    """Bangun context user dari row yang sudah dibaca.

    Fungsi ini sengaja tidak memanggil apply_membership_status_transitions(),
    ensure_auth_schema(), atau query tambahan lain agar endpoint read-only seperti
    profil anggota tidak memicu deadlock ketika beberapa request berjalan bersamaan.
    """
    if not row:
        return {
            "logged_in": bool(session.get("logged_in")),
            "user_id": session.get("user_id"),
            "username": session.get("username") or "",
            "nama": session.get("nama") or "",
            "role": session.get("role") or "",
            "telp": session.get("telp") or "",
            "email": session.get("email") or "",
            "alamat": session.get("alamat") or "",
            "tgl_lahir": _date_to_iso(session.get("tgl_lahir")),
            "status_akun": session.get("status_akun") or "",
            "inactive_until": "",
            "inactive_from": "",
            "inactive_type": "",
            "inactive_reason": "",
            "admin_permissions": {},
            "created_at": "",
            "updated_at": "",
        }

    role_value = normalize_role_value(row.get("role") or "user")
    admin_permissions = {}
    if include_admin_permissions and session.get("logged_in") and role_value in {"admin", "super_admin"}:
        admin_permissions = get_admin_permissions(row.get("id"), role_value)

    return {
        "logged_in": bool(session.get("logged_in")),
        "user_id": row.get("id"),
        "username": row.get("username") or "",
        "nama": row.get("nama") or "",
        "role": role_value,
        "telp": row.get("telp") or "",
        "email": row.get("email") or "",
        "alamat": row.get("alamat") or "",
        "tgl_lahir": _date_to_iso(row.get("tgl_lahir")),
        "status_akun": row.get("status_akun") or "aktif",
        "inactive_until": _date_to_iso(row.get("inactive_until")),
        "inactive_from": _date_to_iso(row.get("inactive_from")),
        "inactive_type": row.get("inactive_type") or "",
        "inactive_reason": row.get("inactive_reason") or "",
        "admin_permissions": admin_permissions,
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else "",
        "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else "",
    }


def refresh_session_user_from_db() -> dict[str, object] | None:
    """Ambil ulang user login dari database dengan proses read-only.

    Sebelumnya fungsi ini menjalankan apply_membership_status_transitions() setiap
    kali halaman profil/dashboard dirender. Karena proses tersebut melakukan
    UPDATE ke tabel anggota dan membership_status_requests, request paralel dari
    halaman profil anggota bisa saling mengunci dan memunculkan error MySQL 1213
    deadlock. Refresh session cukup membaca data user login saja.
    """
    if not session.get("logged_in") or not session.get("user_id"):
        return None

    conn = None
    cursor = None
    try:
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat,
                   status_akun, inactive_until, inactive_from, inactive_type,
                   inactive_reason, inactive_note, created_at, updated_at
            FROM anggota
            WHERE id = %s
            LIMIT 1
            """,
            (session.get("user_id"),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        sync_session_from_member_row(row)
        return row
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def current_user_context() -> dict[str, object]:
    row = refresh_session_user_from_db()
    return current_user_context_from_row(row, include_admin_permissions=True)

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
    inactive_until_value = row.get("inactive_until") or ""
    if hasattr(inactive_until_value, "isoformat"):
        inactive_until_value = inactive_until_value.isoformat()
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
        "inactiveUntil": inactive_until_value or "",
        "inactiveFrom": _date_to_iso(row.get("inactive_from")),
        "inactiveType": row.get("inactive_type") or "",
        "inactiveReason": row.get("inactive_reason") or "",
        "inactiveNote": row.get("inactive_note") or "",
    }

def read_member_rows() -> list[dict[str, object]]:
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun, inactive_until, inactive_from, inactive_type, inactive_reason, inactive_note
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
    return {
        "logged_in": bool(session.get("logged_in")),
        "user_id": session.get("user_id"),
        "username": session.get("username") or "",
        "nama": session.get("nama") or "",
        "role": session.get("role") or "",
        "telp": session.get("telp") or "",
        "email": session.get("email") or "",
        "alamat": session.get("alamat") or "",
    }

def ensure_loan_schema(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `loan_requests` (
          `id` varchar(100) NOT NULL,
          `member_id` varchar(100) DEFAULT NULL,
          `barang_id` varchar(100) NOT NULL,
          `barang_name` varchar(255) NOT NULL,
          `barang_code` varchar(100) DEFAULT NULL,
          `barang_photo` text DEFAULT NULL,
          `jumlah` int(11) NOT NULL DEFAULT 1,
          `tanggal_pengajuan` date DEFAULT NULL,
          `tanggal_mulai` date DEFAULT NULL,
          `waktu_mulai` time DEFAULT NULL,
          `tanggal_selesai` date DEFAULT NULL,
          `waktu_selesai` time DEFAULT NULL,
          `tujuan` text DEFAULT NULL,
          `status` varchar(50) NOT NULL DEFAULT 'pending',
          `pickup_info` longtext DEFAULT NULL,
          `pickup_at` datetime DEFAULT NULL,
          `return_info` longtext DEFAULT NULL,
          `return_at` datetime DEFAULT NULL,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `idx_loan_status` (`status`),
          KEY `idx_loan_member` (`member_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    ensure_column(cursor, "loan_requests", "waktu_mulai", "`waktu_mulai` time DEFAULT NULL")
    ensure_column(cursor, "loan_requests", "waktu_selesai", "`waktu_selesai` time DEFAULT NULL")

def ensure_misa_besar_schema():
    conn = mysql_connection()
    cursor = conn.cursor(buffered=True)
    try:
        # Pastikan tabel utama ada
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `misa_besar` (
              `id` int AUTO_INCREMENT PRIMARY KEY,
              `misa_name` varchar(255) NOT NULL,
              `misa_date` date NOT NULL,
              `misa_time` time NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """)
        conn.commit()

        # Tambahkan kolom baru (Safe Alter)
        for col, col_def in [
            ("misa_note", "text"),
            ("allow_member_request", "tinyint(1) DEFAULT 0"),
            ("status", "enum('draft','published') DEFAULT 'draft'"),
            ("created_at", "timestamp DEFAULT CURRENT_TIMESTAMP")
        ]:
            try:
                cursor.execute(f"ALTER TABLE misa_besar ADD COLUMN {col} {col_def}")
            except:
                pass 
        conn.commit()
                
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `misa_besar_names` (
              `id` int AUTO_INCREMENT PRIMARY KEY,
              `misa_id` int NOT NULL,
              `role_name` varchar(100) NOT NULL,
              FOREIGN KEY (misa_id) REFERENCES misa_besar(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """)
        conn.commit()

        try:
            cursor.execute("ALTER TABLE misa_besar_names ADD COLUMN required_count int NOT NULL DEFAULT 1")
        except:
            pass
        conn.commit()
            
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `misa_besar_assignments` (
              `id` int AUTO_INCREMENT PRIMARY KEY,
              `role_id` int NOT NULL,
              `member_id` int NOT NULL,
              FOREIGN KEY (role_id) REFERENCES misa_besar_names(id) ON DELETE CASCADE,
              FOREIGN KEY (member_id) REFERENCES anggota(id) ON DELETE CASCADE,
              UNIQUE KEY `uniq_role_member` (`role_id`, `member_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """)
        try:
            ensure_column(cursor, "misa_besar_assignments", "created_at", "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
            ensure_column(cursor, "misa_besar_assignments", "request_source", "`request_source` varchar(30) NOT NULL DEFAULT 'admin'")
            conn.commit()
        except Exception as exc:
            print(f"[WARN] Failed to ensure misa besar assignment metadata: {exc}")
    finally:
        cursor.close()
        conn.close()

def ensure_damage_schema(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `form_kerusakan_barang` (
          `id` varchar(100) NOT NULL,
          `member_id` varchar(100) DEFAULT NULL,
          `barang_id` varchar(100) DEFAULT NULL,
          `barang_name` varchar(255) NOT NULL,
          `barang_code` varchar(100) DEFAULT NULL,
          `tingkat_kerusakan` varchar(50) NOT NULL DEFAULT 'Sedang',
          `status` varchar(50) NOT NULL DEFAULT 'Pending Review',
          `deskripsi_kerusakan` longtext DEFAULT NULL,
          `waktu_kejadian` datetime DEFAULT NULL,
          `foto_kerusakan` longtext DEFAULT NULL,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `idx_damage_status` (`status`),
          KEY `idx_damage_member` (`member_id`),
          KEY `idx_damage_created` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )






# --- DAMAGE REPORT ENDPOINTS ---







def ensure_news_schema() -> None:
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `news_categories` (
                `id` VARCHAR(100) PRIMARY KEY,
                `name` VARCHAR(255) NOT NULL UNIQUE,
                `description` TEXT,
                `order_index` INT DEFAULT 0,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)

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

def ensure_registration_form_schema() -> None:
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `registration_forms` (
              `id` varchar(100) NOT NULL,
              `title` varchar(255) NOT NULL,
              `description` longtext DEFAULT NULL,
              `target` varchar(20) NOT NULL DEFAULT 'public',
              `visibility` varchar(20) NOT NULL DEFAULT 'visible',
              `open_date` date DEFAULT NULL,
              `close_date` date DEFAULT NULL,
              `quota` int(11) NOT NULL DEFAULT 0,
              `image_url` text DEFAULT NULL,
              `image_name` varchar(255) DEFAULT NULL,
              `attachments` longtext DEFAULT NULL,
              `fields_json` longtext DEFAULT NULL,
              `created_by` varchar(100) DEFAULT NULL,
              `created_by_name` varchar(255) DEFAULT NULL,
              `created_by_role` varchar(50) DEFAULT NULL,
              `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              KEY `idx_registration_forms_target` (`target`),
              KEY `idx_registration_forms_visibility` (`visibility`),
              KEY `idx_registration_forms_dates` (`open_date`, `close_date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        ensure_column(cursor, "registration_forms", "image_url", "`image_url` text DEFAULT NULL")
        ensure_column(cursor, "registration_forms", "image_name", "`image_name` varchar(255) DEFAULT NULL")
        ensure_column(cursor, "registration_forms", "attachments", "`attachments` longtext DEFAULT NULL")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `registration_form_submissions` (
              `id` varchar(100) NOT NULL,
              `form_id` varchar(100) NOT NULL,
              `submitter_key` varchar(255) NOT NULL,
              `submitter_identifier` varchar(255) NOT NULL DEFAULT '',
              `submitter_role` varchar(50) NOT NULL DEFAULT 'public',
              `submitter_user_id` varchar(100) DEFAULT NULL,
              `submitter_source` varchar(20) NOT NULL DEFAULT 'public',
              `answers_json` longtext NOT NULL,
              `submitted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `uniq_registration_submission` (`form_id`, `submitter_key`),
              KEY `idx_registration_submissions_form` (`form_id`),
              KEY `idx_registration_submissions_submitter` (`submitter_key`),
              CONSTRAINT `fk_registration_submissions_form`
                FOREIGN KEY (`form_id`) REFERENCES `registration_forms` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def ensure_notifications_schema() -> None:
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `notifications` (
              `id` varchar(100) NOT NULL,
              `type` varchar(50) DEFAULT NULL,
              `title` varchar(255) DEFAULT NULL,
              `body` text DEFAULT NULL,
              `url` varchar(255) DEFAULT NULL,
              `data` longtext DEFAULT NULL,
              `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `notification_reads` (
              `notification_id` varchar(100) NOT NULL,
              `user_key` varchar(255) NOT NULL,
              `read_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`notification_id`,`user_key`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        ''')
        ensure_column(cursor, "notifications", "target_role", "`target_role` varchar(50) DEFAULT NULL")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `notification_email_deliveries` (
              `notification_id` varchar(100) NOT NULL,
              `recipient_user_id` varchar(100) NOT NULL DEFAULT '',
              `recipient_email` varchar(255) NOT NULL,
              `status` varchar(30) NOT NULL DEFAULT 'sent',
              `error_message` text DEFAULT NULL,
              `sent_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`notification_id`, `recipient_email`),
              KEY `idx_notification_email_recipient` (`recipient_email`),
              KEY `idx_notification_email_status` (`status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def public_url_for_notification(url: str | None) -> str | None:
    """Ubah URL relatif atau URL lokal menjadi URL domain produksi."""
    raw = normalize_text(url)
    if not raw:
        return None
    local_prefixes = (
        "http://127.0.0.1:5000",
        "https://127.0.0.1:5000",
        "http://localhost:5000",
        "https://localhost:5000",
    )
    for prefix in local_prefixes:
        if raw.startswith(prefix):
            raw = raw[len(prefix):] or "/"
            break
    if raw.startswith("//"):
        return "https:" + raw
    if re.match(r"^https?://", raw, re.IGNORECASE):
        return raw
    if raw.startswith("/"):
        return f"{PUBLIC_BASE_URL}{raw}"
    return f"{PUBLIC_BASE_URL}/{raw.lstrip('/')}"


def html_to_plain_text(value: str) -> str:
    raw = str(value or "")
    raw = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", raw)
    raw = re.sub(r"(?i)</\s*p\s*>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def notification_button_label(type_value: str, title: str, url: str | None) -> str:
    haystack = normalize_text(" ".join([type_value or "", title or "", url or ""]))
    if "agenda" in haystack:
        return "Lihat Agenda"
    if "pengumuman" in haystack or "news" in haystack:
        return "Lihat Pengumuman"
    if "form" in haystack or "pendaftaran" in haystack:
        return "Lihat Form Pendaftaran"
    if "peminjaman" in haystack or "barang" in haystack:
        return "Lihat Peminjaman"
    if "kerusakan" in haystack:
        return "Lihat Laporan Kerusakan"
    if "evaluasi" in haystack:
        return "Lihat Evaluasi"
    if "tugas" in haystack or "jadwal" in haystack:
        return "Lihat Jadwal Tugas"
    if "akun" in haystack or "login" in haystack or "password" in haystack:
        return "Login ke Crembo Media"
    if "keanggotaan" in haystack or "anggota" in haystack:
        return "Lihat Keanggotaan"
    return "Buka Halaman"


def build_notification_email(recipient_name: str, type_value: str, title: str, body: str, absolute_url: str | None) -> tuple[str, str, str]:
    site_name = "Crembo Media"
    safe_title = normalize_text(title) or "Notifikasi Crembo Media"
    body_text = html_to_plain_text(body) or "Ada notifikasi baru di dashboard Crembo Media Anda."
    recipient_label = normalize_text(recipient_name) or "Anggota"
    button_label = notification_button_label(type_value, safe_title, absolute_url)
    url_text = absolute_url or PUBLIC_BASE_URL
    subject = f"{safe_title} - {site_name}"
    text_body = (
        f"Halo {recipient_label},\n\n"
        f"{safe_title}\n\n"
        f"{body_text}\n\n"
        f"URL halaman:\n{url_text}\n\n"
        f"Salam,\nTim {site_name}"
    )
    body_html = html.escape(body_text).replace("\n", "<br>")
    button_html = ""
    if url_text:
        button_html = (
            f'<div style="margin:18px 0 6px;">'
            f'<a href="{html.escape(url_text)}" target="_blank" style="display:inline-block;background:linear-gradient(135deg,#800000,#b11f1f);color:#ffffff;text-decoration:none;border-radius:12px;padding:12px 18px;font-weight:800;font-size:14px;">{html.escape(button_label)}</a>'
            f'</div>'
        )
    html_body = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{html.escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f5f0ef;font-family:Inter,Segoe UI,Arial,sans-serif;color:#1a1a1a;">
  <div style="max-width:620px;margin:0 auto;padding:28px 14px;">
    <div style="background:linear-gradient(135deg,#3a0000,#800000 55%,#a52a2a);border-radius:18px 18px 0 0;padding:24px;color:#fff;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
        <tr>
          <td width="64" style="vertical-align:middle;padding-right:14px;">
            <img src="cid:crembo_logo" alt="Logo Crembo Media" width="58" height="58" style="display:block;width:58px;height:58px;object-fit:contain;border-radius:12px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);padding:4px;">
          </td>
          <td style="vertical-align:middle;">
            <div style="font-size:22px;font-weight:900;letter-spacing:.4px;line-height:1.2;">CREMBO MEDIA</div>
            <div style="margin-top:4px;color:rgba(255,255,255,.82);font-size:13px;">Sistem Informasi Internal Komunitas</div>
          </td>
        </tr>
      </table>
    </div>
    <div style="background:#fff;border:1px solid rgba(128,0,0,.13);border-top:0;border-radius:0 0 18px 18px;padding:28px;box-shadow:0 12px 32px rgba(128,0,0,.13);">
      <div style="display:inline-block;margin:0 0 12px;padding:6px 10px;border-radius:999px;background:#fff3f3;border:1px solid #f1caca;color:#800000;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;">{html.escape(type_value or "Notifikasi")}</div>
      <h1 style="margin:0 0 8px;font-size:22px;color:#800000;line-height:1.35;">{html.escape(safe_title)}</h1>
      <p style="margin:0 0 18px;line-height:1.7;color:#4a4a4a;">Halo <strong>{html.escape(recipient_label)}</strong>, ada notifikasi baru untuk Anda.</p>
      <div style="margin:18px 0;padding:16px;border-radius:14px;background:#fff8f8;border:1px solid #f1d1d1;color:#333;line-height:1.7;font-size:14px;">{body_html}</div>
      <div style="margin:18px 0;padding:14px;border-left:4px solid #d4a017;background:#fff8e1;border-radius:10px;color:#5c3b00;font-size:13px;line-height:1.7;">
        <strong>URL halaman:</strong><br>
        <a href="{html.escape(url_text)}" target="_blank" style="color:#800000;word-break:break-all;">{html.escape(url_text)}</a>
      </div>
      {button_html}
      <p style="margin:22px 0 0;color:#7a7a7a;font-size:12px;line-height:1.6;">Email ini dikirim otomatis oleh sistem {html.escape(site_name)} karena notifikasi yang sama muncul pada dashboard Anda.</p>
    </div>
  </div>
</body>
</html>"""
    return subject, text_body, html_body


def _row_value(row, key: str, index: int = 0, default=""):
    if isinstance(row, dict):
        return row.get(key, default)
    if isinstance(row, (list, tuple)) and len(row) > index:
        return row[index]
    return default


def notification_email_recipients(cursor, type_value: str, data: dict | None = None, target_role: str | None = None) -> list[dict[str, str]]:
    payload = data or {}
    target_user_id = normalize_text(payload.get("target_user_id"))
    target_role_value = normalize_role_value(target_role or "") if target_role else ""
    user_scoped_types = {"tugas", "evaluasi", "tukar", "keanggotaan", "peminjaman", "kerusakan", "akun"}
    notif_type = normalize_text(type_value)
    include_inactive = bool(payload.get("include_inactive") or payload.get("allow_inactive_email"))

    params = []
    if target_user_id:
        where_clause = "WHERE `id` = %s"
        params.append(target_user_id)
    elif target_role_value == "admin":
        where_clause = "WHERE `role` IN ('admin', 'super_admin')"
    elif target_role_value == "super_admin":
        where_clause = "WHERE `role` = 'super_admin'"
    elif target_role_value == "user":
        where_clause = "WHERE `role` = 'user'"
    elif notif_type in user_scoped_types:
        # Notifikasi personal tanpa target_user_id tidak dikirim massal agar tidak bocor ke user lain.
        return []
    else:
        # Broadcast umum seperti agenda, pengumuman, atau form pendaftaran.
        where_clause = "WHERE `role` IN ('user', 'admin', 'super_admin')"

    cursor.execute(
        f"""
        SELECT `id`, `nama`, `email`, `role`, `status_akun`
        FROM `anggota`
        {where_clause}
          AND COALESCE(`email`, '') <> ''
          {"" if include_inactive else "AND LOWER(COALESCE(`status_akun`, 'aktif')) = 'aktif'"}
        """,
        tuple(params),
    )
    rows = cursor.fetchall() or []
    recipients = []
    seen_emails = set()
    for row in rows:
        email_value = normalize_text(_row_value(row, "email", 2))
        if not email_value or "@" not in email_value:
            continue
        email_key = email_value.lower()
        if email_key in seen_emails:
            continue
        seen_emails.add(email_key)
        recipients.append({
            "id": str(_row_value(row, "id", 0, "")),
            "name": normalize_text(_row_value(row, "nama", 1)) or email_value,
            "email": email_value,
            "role": normalize_role_value(_row_value(row, "role", 3, "user")),
        })
    return recipients


def record_notification_email_delivery(cursor, notification_id: str, recipient: dict[str, str], status: str, error_message: str | None = None) -> None:
    cursor.execute(
        """
        INSERT INTO `notification_email_deliveries`
          (`notification_id`, `recipient_user_id`, `recipient_email`, `status`, `error_message`, `sent_at`)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
          `status` = VALUES(`status`),
          `error_message` = VALUES(`error_message`),
          `sent_at` = VALUES(`sent_at`)
        """,
        (
            notification_id,
            normalize_text(recipient.get("id")),
            normalize_text(recipient.get("email")),
            normalize_text(status) or "sent",
            (error_message or None),
        ),
    )


def notification_email_already_sent(cursor, notification_id: str, email_value: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM `notification_email_deliveries`
        WHERE `notification_id` = %s AND `recipient_email` = %s AND `status` = 'sent'
        LIMIT 1
        """,
        (notification_id, email_value),
    )
    return cursor.fetchone() is not None


def send_notification_email_for_notification(cursor, notification_id: str, type_value: str, title: str, body: str, url: str | None, data: dict | None, target_role: str | None) -> None:
    if not NOTIFICATION_EMAIL_ENABLED:
        return
    absolute_url = public_url_for_notification(url) if url else None
    recipients = notification_email_recipients(cursor, type_value, data, target_role)
    if not recipients:
        return
    for recipient in recipients:
        email_value = normalize_text(recipient.get("email"))
        if not email_value:
            continue
        try:
            if notification_email_already_sent(cursor, notification_id, email_value):
                continue
            subject, text_body, html_body = build_notification_email(
                recipient.get("name") or email_value,
                type_value,
                title,
                body,
                absolute_url,
            )
            send_email_message(email_value, recipient.get("name") or email_value, subject, text_body, html_body)
            record_notification_email_delivery(cursor, notification_id, recipient, "sent", None)
        except Exception as exc:
            error_text = str(exc)[:500]
            print(f"[WARN] Gagal mengirim email notifikasi {notification_id} ke {email_value}: {error_text}")
            try:
                record_notification_email_delivery(cursor, notification_id, recipient, "failed", error_text)
            except Exception as log_exc:
                print(f"[WARN] Gagal mencatat status email notifikasi: {log_exc}")


def ensure_notification_email_worker_started() -> None:
    """Jalankan worker email notifikasi satu kali saja.

    Email dashboard dikirim lewat antrean background agar proses simpan
    notifikasi ke database tidak tertahan oleh koneksi SMTP.
    """
    global _notification_email_worker_started
    if not NOTIFICATION_EMAIL_ENABLED:
        return
    with _notification_email_worker_lock:
        if _notification_email_worker_started:
            return
        worker = threading.Thread(
            target=notification_email_worker_loop,
            name="crembo-notification-email-worker",
            daemon=True,
        )
        worker.start()
        _notification_email_worker_started = True


def enqueue_notification_email_job(notification_id: str) -> None:
    if not NOTIFICATION_EMAIL_ENABLED:
        return
    clean_id = normalize_text(notification_id)
    if not clean_id:
        return
    ensure_notification_email_worker_started()
    _notification_email_queue.put({"notification_id": clean_id})


def notification_email_worker_loop() -> None:
    while True:
        job = _notification_email_queue.get()
        try:
            notification_id = normalize_text(job.get("notification_id") if isinstance(job, dict) else "")
            if notification_id:
                deliver_notification_email_job(notification_id)
        except Exception as exc:
            print(f"[WARN] Worker email notifikasi gagal: {exc}")
        finally:
            try:
                _notification_email_queue.task_done()
            except Exception:
                pass


def fetch_committed_notification_for_email(notification_id: str) -> dict[str, object] | None:
    """Ambil notifikasi dari koneksi baru.

    Worker bisa berjalan sebelum transaksi pembuat notifikasi selesai commit.
    Karena itu pembacaan dibuat retry agar email tidak hilang dan dashboard tetap
    bisa menerima notifikasi lebih cepat.
    """
    for attempt in range(NOTIFICATION_EMAIL_ROW_WAIT_ATTEMPTS):
        conn = None
        cursor = None
        try:
            conn = mysql_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT `id`, `type`, `title`, `body`, `url`, `data`, `target_role`, `created_at` FROM `notifications` WHERE `id` = %s LIMIT 1",
                (notification_id,),
            )
            row = cursor.fetchone()
            if row:
                return row
        except Exception as exc:
            if attempt >= NOTIFICATION_EMAIL_ROW_WAIT_ATTEMPTS - 1:
                print(f"[WARN] Gagal membaca notifikasi {notification_id} untuk email: {exc}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        time.sleep(NOTIFICATION_EMAIL_ROW_WAIT_SECONDS)
    return None


def deliver_notification_email_job(notification_id: str) -> None:
    if not NOTIFICATION_EMAIL_ENABLED:
        return

    row = fetch_committed_notification_for_email(notification_id)
    if not row:
        print(f"[WARN] Notifikasi {notification_id} belum ditemukan setelah retry; email dilewati.")
        return

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        try:
            payload = json.loads(row.get("data") or "{}")
        except Exception:
            payload = {}

        type_value = normalize_text(row.get("type"))
        title = normalize_text(row.get("title"))
        body = str(row.get("body") or "")
        public_url = public_url_for_notification(row.get("url")) if row.get("url") else None
        target_role = normalize_text(row.get("target_role")) or None

        recipients = notification_email_recipients(cursor, type_value, payload, target_role)
        if not recipients:
            return

        for recipient in recipients:
            email_value = normalize_text(recipient.get("email"))
            if not email_value:
                continue

            try:
                if notification_email_already_sent(cursor, notification_id, email_value):
                    continue
            except Exception:
                pass

            last_error = None
            delivered = False
            for attempt in range(1, NOTIFICATION_EMAIL_RETRY_COUNT + 1):
                try:
                    subject, text_body, html_body = build_notification_email(
                        recipient.get("name") or email_value,
                        type_value,
                        title,
                        body,
                        public_url,
                    )
                    # Gmail sering menutup koneksi bila terlalu banyak koneksi SMTP
                    # dibuat paralel. Lock ini memastikan pengiriman berjalan satu per satu.
                    with _smtp_send_lock:
                        send_email_message(email_value, recipient.get("name") or email_value, subject, text_body, html_body)
                    record_notification_email_delivery(cursor, notification_id, recipient, "sent", None)
                    conn.commit()
                    delivered = True
                    break
                except Exception as exc:
                    last_error = str(exc)[:500]
                    if attempt < NOTIFICATION_EMAIL_RETRY_COUNT:
                        time.sleep(NOTIFICATION_EMAIL_RETRY_DELAY_SECONDS)

            if not delivered:
                print(f"[WARN] Gagal mengirim email notifikasi {notification_id} ke {email_value}: {last_error}")
                try:
                    record_notification_email_delivery(cursor, notification_id, recipient, "failed", last_error)
                    conn.commit()
                except Exception as log_exc:
                    conn.rollback()
                    print(f"[WARN] Gagal mencatat status email notifikasi: {log_exc}")

            if NOTIFICATION_EMAIL_SEND_DELAY_SECONDS:
                time.sleep(NOTIFICATION_EMAIL_SEND_DELAY_SECONDS)
    finally:
        cursor.close()
        conn.close()


def create_notification(cursor, type_value: str, title: str, body: str, url: str | None = None, data: dict | None = None, target_role: str | None = None):
    nid = f"notif-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
    clean_type = str(type_value or "")
    clean_title = str(title or "")
    clean_body = str(body or "")
    payload = data or {}
    public_url = public_url_for_notification(url) if url else None
    cursor.execute(
        """
        INSERT INTO `notifications` (`id`, `type`, `title`, `body`, `url`, `data`, `target_role`)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            nid,
            clean_type,
            clean_title,
            clean_body,
            public_url,
            json.dumps(payload, ensure_ascii=False),
            target_role 
        ),
    )
    # Email dikirim lewat antrean background.
    # Dengan cara ini notifikasi dashboard tidak menunggu koneksi SMTP selesai.
    try:
        enqueue_notification_email_job(nid)
    except Exception as exc:
        print(f"[WARN] Gagal memasukkan email notifikasi {nid} ke antrean: {exc}")
    return nid

def create_notification_once(
    cursor,
    type_value: str,
    title: str,
    body: str,
    url: str | None = None,
    data: dict | None = None,
    target_role: str | None = None,
    *,
    dedupe_key: str | None = None,
):
    """Buat notifikasi sekali saja berdasarkan dedupe_key di payload data.

    Dedupe dibuat tahan terhadap variasi JSON yang memakai spasi ataupun tidak,
    karena data notifikasi lama di database bisa berasal dari beberapa versi kode.
    """
    payload = dict(data or {})
    clean_key = normalize_text(dedupe_key or payload.get("dedupe_key"))
    if clean_key:
        payload["dedupe_key"] = clean_key
        cursor.execute(
            """
            SELECT `id` FROM `notifications`
            WHERE `type` = %s
              AND (`data` LIKE %s OR `data` LIKE %s)
            LIMIT 1
            """,
            (
                str(type_value or ""),
                f'%"dedupe_key": "{clean_key}"%',
                f'%"dedupe_key":"{clean_key}"%',
            ),
        )
        existing = cursor.fetchone()
        if existing:
            return existing.get("id") if isinstance(existing, dict) else existing[0]
    return create_notification(cursor, type_value, title, body, url, payload, target_role)


def notification_target_url_for_member_role(role_value: str | None, *, default_user_url: str = "/jadwal-tugas-misa-anggota.html") -> str:
    normalized = normalize_role_value(role_value or "user")
    if normalized in {"admin", "super_admin"}:
        return "/jadwal-tugas-streaming-admin.html"
    return default_user_url


def create_task_success_notification(
    cursor,
    *,
    member_id: object,
    member_role: str | None = "user",
    misa_type: str,
    misa_name: str,
    role_name: str,
    date_text: str,
    time_text: str,
    source: str = "member_request",
    misa_besar_id: object | None = None,
):
    """Notif langsung setelah anggota berhasil mengambil/request jadwal mandiri."""
    safe_role = normalize_text(role_name) or "Role"
    safe_misa = normalize_text(misa_name) or ("Misa Besar" if misa_type == "misa_besar" else "Misa Biasa")
    time_label = format_time_hhmm(time_text)
    day_label = request_task_day_name(date_text) if 'request_task_day_name' in globals() else "-"
    date_label = request_task_format_date(date_text) if 'request_task_format_date' in globals() else normalize_text(date_text)
    title = f"Request Tugas Berhasil: {safe_role}"
    body = (
        f"Anda berhasil terdaftar sebagai <b>{html.escape(safe_role)}</b> untuk "
        f"<b>{html.escape(safe_misa)}</b> pada hari {html.escape(day_label)}, "
        f"{html.escape(date_label)} jam {html.escape(time_label)} WIB."
    )
    return create_notification(
        cursor,
        "tugas",
        title,
        body,
        "/request-tugas-anggota.html",
        {
            "target_user_id": str(member_id),
            "notification_kind": "member_request_success",
            "misa_type": misa_type,
            "misa_besar_id": misa_besar_id,
            "misa_name": safe_misa,
            "role": safe_role,
            "misa_date": date_text,
            "misa_time": time_label,
            "source": source,
        },
        target_role=None,
    )


def create_due_task_reminder_notifications() -> int:
    """Generate pengingat H-1 dan hari-H untuk semua petugas yang sudah terdaftar.

    Fungsi ini dipanggil saat dashboard memuat notifikasi. Dedupe key mencegah
    notifikasi H-1 / hari-H dibuat berulang untuk jadwal dan petugas yang sama.
    """
    ensure_task_request_schema()
    ensure_notifications_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    sent = 0
    try:
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        today_text = today.strftime("%Y-%m-%d")
        tomorrow_text = tomorrow.strftime("%Y-%m-%d")

        reminder_labels = {
            today_text: ("hari_h", "Hari Ini", "Pengingat Tugas Hari Ini"),
            tomorrow_text: ("h_1", "H-1", "Pengingat Tugas H-1"),
        }

        # Misa Biasa
        cursor.execute(
            """
            SELECT DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS schedule_date,
                   DATE_FORMAT(sa.schedule_time, '%H:%i') AS schedule_time,
                   sa.role_name, sa.member_id,
                   COALESCE(a.nama, CONCAT('ID ', sa.member_id)) AS member_name,
                   COALESCE(a.role, 'user') AS member_role,
                   COALESCE(cfg.mass_name, 'Misa Biasa') AS mass_name
            FROM streaming_assignments sa
            JOIN anggota a ON a.id = sa.member_id
            LEFT JOIN streaming_weekly_config cfg
              ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                ELSE 'Minggu' END
              AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            WHERE sa.schedule_date IN (%s, %s)
              AND LOWER(COALESCE(a.status_akun, 'aktif')) IN ('', 'aktif', 'active')
            """,
            (today_text, tomorrow_text),
        )
        for row in cursor.fetchall() or []:
            date_text = normalize_text(row.get("schedule_date"))
            reminder_code, reminder_label, title_prefix = reminder_labels.get(date_text, ("", "", ""))
            if not reminder_code:
                continue
            time_text = format_time_hhmm(row.get("schedule_time"))
            role_name = normalize_text(row.get("role_name")) or "Role"
            misa_name = normalize_text(row.get("mass_name")) or "Misa Biasa"
            member_id = normalize_text(row.get("member_id"))
            member_role = normalize_text(row.get("member_role")) or "user"
            day_label = request_task_day_name(date_text)
            date_label = request_task_format_date(date_text)
            title = f"{title_prefix}: {role_name}"
            body = (
                f"{html.escape(reminder_label)}: Anda bertugas sebagai <b>{html.escape(role_name)}</b> "
                f"untuk <b>{html.escape(misa_name)}</b> pada hari {html.escape(day_label)}, "
                f"{html.escape(date_label)} jam {html.escape(time_text)} WIB."
            )
            dedupe_key = f"task-reminder:biasa:{date_text}:{time_text}:{role_name}:{member_id}:{reminder_code}"
            create_notification_once(
                cursor, "tugas", title, body,
                notification_target_url_for_member_role(member_role),
                {
                    "target_user_id": member_id,
                    "notification_kind": "task_reminder",
                    "reminder": reminder_code,
                    "reminder_label": reminder_label,
                    "misa_type": "misa_biasa",
                    "misa_name": misa_name,
                    "role": role_name,
                    "misa_date": date_text,
                    "misa_time": time_text,
                },
                target_role=None,
                dedupe_key=dedupe_key,
            )
            sent += 1

        # Misa Besar
        cursor.execute(
            """
            SELECT mb.id AS misa_id, mb.misa_name, DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS misa_date,
                   DATE_FORMAT(mb.misa_time, '%H:%i') AS misa_time,
                   n.id AS role_id, n.role_name, a.member_id,
                   COALESCE(ag.nama, CONCAT('ID ', a.member_id)) AS member_name,
                   COALESCE(ag.role, 'user') AS member_role
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            JOIN anggota ag ON ag.id = a.member_id
            WHERE mb.status = 'published'
              AND mb.misa_date IN (%s, %s)
              AND LOWER(COALESCE(ag.status_akun, 'aktif')) IN ('', 'aktif', 'active')
            """,
            (today_text, tomorrow_text),
        )
        for row in cursor.fetchall() or []:
            date_text = normalize_text(row.get("misa_date"))
            reminder_code, reminder_label, title_prefix = reminder_labels.get(date_text, ("", "", ""))
            if not reminder_code:
                continue
            time_text = format_time_hhmm(row.get("misa_time"))
            role_name = normalize_text(row.get("role_name")) or "Role"
            misa_name = normalize_text(row.get("misa_name")) or "Misa Besar"
            misa_id = row.get("misa_id")
            member_id = normalize_text(row.get("member_id"))
            member_role = normalize_text(row.get("member_role")) or "user"
            day_label = request_task_day_name(date_text)
            date_label = request_task_format_date(date_text)
            title = f"{title_prefix}: {role_name}"
            body = (
                f"{html.escape(reminder_label)}: Anda bertugas sebagai <b>{html.escape(role_name)}</b> "
                f"untuk <b>{html.escape(misa_name)}</b> pada hari {html.escape(day_label)}, "
                f"{html.escape(date_label)} jam {html.escape(time_text)} WIB."
            )
            dedupe_key = f"task-reminder:besar:{misa_id}:{row.get('role_id')}:{member_id}:{reminder_code}"
            create_notification_once(
                cursor, "tugas", title, body,
                notification_target_url_for_member_role(member_role),
                {
                    "target_user_id": member_id,
                    "notification_kind": "task_reminder",
                    "reminder": reminder_code,
                    "reminder_label": reminder_label,
                    "misa_type": "misa_besar",
                    "misa_besar_id": misa_id,
                    "misa_name": misa_name,
                    "role": role_name,
                    "misa_date": date_text,
                    "misa_time": time_text,
                },
                target_role=None,
                dedupe_key=dedupe_key,
            )
            sent += 1

        conn.commit()
        return sent
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()




def dashboard_period_bounds(range_value: str) -> tuple[object, object]:
    """Return inclusive start/end dates for dashboard range."""
    now = datetime.now()
    mode = normalize_text(range_value).lower() or "month"
    if mode == "year":
        return datetime(now.year, 1, 1).date(), datetime(now.year, 12, 31).date()
    if mode == "week":
        start_dt = now - timedelta(days=now.weekday())
        start = datetime(start_dt.year, start_dt.month, start_dt.day).date()
        return start, start + timedelta(days=6)
    start = datetime(now.year, now.month, 1).date()
    end = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1]).date()
    return start, end


def dashboard_series_template(range_value: str) -> tuple[list[str], list[object]]:
    now = datetime.now()
    mode = normalize_text(range_value).lower() or "month"
    month_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    if mode == "year":
        labels = month_names[:]
        keys = [(now.year, month) for month in range(1, 13)]
        return labels, keys
    if mode == "week":
        start, _ = dashboard_period_bounds("week")
        labels = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
        keys = [(start + timedelta(days=idx)).isoformat() for idx in range(7)]
        return labels, keys
    start, end = dashboard_period_bounds("month")
    labels = []
    keys = []
    total_days = end.day
    for day in range(1, total_days + 1):
        labels.append(str(day) if day == 1 or day == total_days or day % 3 == 0 else "")
        keys.append(datetime(now.year, now.month, day).date().isoformat())
    return labels, keys


def dashboard_count_schedules_by_range(cursor, range_value: str) -> int:
    start, end = dashboard_period_bounds(range_value)
    schedules = eval_all_schedules(cursor, start, end, "all")
    return len(schedules)


def dashboard_schedule_series(cursor, range_value: str) -> dict[str, object]:
    mode = normalize_text(range_value).lower() or "month"
    start, end = dashboard_period_bounds(mode)
    labels, keys = dashboard_series_template(mode)
    counts = {key: 0 for key in keys}
    schedules = eval_all_schedules(cursor, start, end, "all")
    for item in schedules:
        date_text = normalize_text(item.get("date"))
        if not date_text:
            continue
        if mode == "year":
            try:
                parsed = datetime.strptime(date_text, "%Y-%m-%d")
                key = (parsed.year, parsed.month)
            except Exception:
                continue
        else:
            key = date_text
        if key in counts:
            counts[key] += 1
    return {"range": mode, "labels": labels, "values": [counts.get(key, 0) for key in keys]}


def dashboard_loan_series(cursor, range_value: str) -> dict[str, object]:
    mode = normalize_text(range_value).lower() or "year"
    start, end = dashboard_period_bounds(mode)
    labels, keys = dashboard_series_template(mode)
    counts = {key: 0 for key in keys}
    cursor.execute(
        """
        SELECT DATE(COALESCE(`tanggal_pengajuan`, `created_at`)) AS item_date, COUNT(*) AS total
        FROM `loan_requests`
        WHERE DATE(COALESCE(`tanggal_pengajuan`, `created_at`)) BETWEEN %s AND %s
        GROUP BY DATE(COALESCE(`tanggal_pengajuan`, `created_at`))
        """,
        (start.isoformat(), end.isoformat()),
    )
    for row in cursor.fetchall() or []:
        raw_date = row.get("item_date") if isinstance(row, dict) else None
        date_text = raw_date.isoformat() if hasattr(raw_date, "isoformat") else normalize_text(raw_date)
        if not date_text:
            continue
        if mode == "year":
            try:
                parsed = datetime.strptime(date_text, "%Y-%m-%d")
                key = (parsed.year, parsed.month)
            except Exception:
                continue
        else:
            key = date_text
        if key in counts:
            counts[key] = int(row.get("total") or 0)
    return {"range": mode, "labels": labels, "values": [counts.get(key, 0) for key in keys]}


def dashboard_pending_evaluation_count(cursor) -> int:
    now = datetime.now()
    start, end = dashboard_period_bounds("month")
    schedules = eval_all_schedules(cursor, start, end, "all")
    evaluation_map = eval_evaluation_map(cursor, start.isoformat(), end.isoformat())
    pending = 0
    for schedule in schedules:
        schedule_dt = eval_datetime_from_parts(schedule.get("date"), schedule.get("time"))
        if not schedule_dt or schedule_dt > now:
            continue
        if not eval_schedule_has_staff(schedule):
            continue
        key = (normalize_text(schedule.get("kind")), normalize_text(schedule.get("scheduleKey")))
        if key not in evaluation_map:
            pending += 1
    return pending




# -----------------------------------------------------------------------------
# Dashboard Anggota: ringkasan backend real-time untuk panel anggota
# -----------------------------------------------------------------------------

def member_dashboard_schedule_dt(date_text: str, time_text: str = "00:00") -> datetime:
    try:
        return datetime.strptime(f"{normalize_text(date_text)} {format_time_hhmm(time_text)}", "%Y-%m-%d %H:%M")
    except Exception:
        try:
            return datetime.strptime(normalize_text(date_text), "%Y-%m-%d")
        except Exception:
            return datetime(1970, 1, 1)


def member_dashboard_type_filter(value: str) -> str:
    raw = normalize_text(value).lower()
    if raw in {"biasa", "misa_biasa"}:
        return "biasa"
    if raw in {"besar", "misa_besar"}:
        return "besar"
    return "all"


def member_dashboard_kind_label(kind: str) -> str:
    return "Misa Besar" if kind == "besar" else "Misa Biasa"


def member_dashboard_registered_tasks(cursor, member_id: object, *, month: int, year: int, kind_filter: str = "all") -> list[dict[str, object]]:
    """Ambil tugas terdaftar user untuk tabel dashboard anggota.

    Data dibangun dari assignment aktif. Tugas yang sudah dibatalkan tidak muncul
    lagi di tabel ini karena histori pembatalan sudah tersedia di Riwayat Tugas.
    """
    kind_filter = member_dashboard_type_filter(kind_filter)
    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
    evaluation_map = {}
    try:
        evaluation_map = eval_evaluation_map(cursor, start_date, end_date)
    except Exception as exc:
        print(f"[WARN] Dashboard anggota gagal membaca evaluasi: {exc}")

    now = datetime.now()
    rows: list[dict[str, object]] = []

    if kind_filter in {"all", "biasa"}:
        cursor.execute(
            """
            SELECT sa.id AS assignment_id,
                   DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                   sa.role_name AS role,
                   COALESCE(sa.request_source, 'admin') AS request_source,
                   COALESCE(cfg.mass_name, 'Misa Biasa') AS mass_name
            FROM streaming_assignments sa
            LEFT JOIN streaming_weekly_config cfg
              ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                ELSE 'Minggu' END
              AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            LEFT JOIN streaming_cancelled sc
              ON sc.mass_date = sa.schedule_date
             AND DATE_FORMAT(sc.mass_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            LEFT JOIN misa_besar mb
              ON mb.status = 'published'
             AND mb.misa_date = sa.schedule_date
             AND DATE_FORMAT(mb.misa_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            WHERE sa.member_id = %s
              AND MONTH(sa.schedule_date) = %s
              AND YEAR(sa.schedule_date) = %s
              AND sc.id IS NULL
              AND mb.id IS NULL
            ORDER BY sa.schedule_date DESC, sa.schedule_time DESC, sa.id DESC
            """,
            (member_id, month, year),
        )
        for row in cursor.fetchall() or []:
            date_text = normalize_text(row.get("date"))
            time_text = format_time_hhmm(row.get("time"))
            schedule_dt = member_dashboard_schedule_dt(date_text, time_text)
            schedule_key = f"biasa:{date_text}:{time_text}"
            evaluated = ("misa_biasa", schedule_key) in evaluation_map
            can_cancel = schedule_dt > now and cancel_task_can_cancel(date_text)
            rows.append({
                "id": f"biasa:{row.get('assignment_id')}",
                "type": "biasa",
                "typeLabel": "Misa Biasa",
                "assignmentId": row.get("assignment_id"),
                "misaId": None,
                "roleId": None,
                "misaName": normalize_text(row.get("mass_name")) or "Misa Biasa",
                "date": date_text,
                "dateLabel": request_task_format_date(date_text),
                "dayName": request_task_day_name(date_text),
                "time": time_text,
                "role": normalize_text(row.get("role")) or "Role",
                "status": "Selesai" if schedule_dt < now else "Terdaftar",
                "evaluation": "Sudah Diisi" if evaluated else "Belum Diisi",
                "evaluated": evaluated,
                "source": normalize_text(row.get("request_source")) or "admin",
                "sourceLabel": "Request Mandiri" if normalize_text(row.get("request_source")) == "member_request" else "Ditugaskan Admin",
                "canCancel": bool(can_cancel),
                "cancelDeadlineLabel": cancel_task_rule_label(date_text),
            })

    if kind_filter in {"all", "besar"}:
        cursor.execute(
            """
            SELECT a.id AS assignment_id, mb.id AS misa_id, n.id AS role_id,
                   mb.misa_name,
                   DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                   n.role_name AS role,
                   COALESCE(a.request_source, 'admin') AS request_source
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            WHERE a.member_id = %s
              AND mb.status = 'published'
              AND MONTH(mb.misa_date) = %s
              AND YEAR(mb.misa_date) = %s
            ORDER BY mb.misa_date DESC, mb.misa_time DESC, a.id DESC
            """,
            (member_id, month, year),
        )
        for row in cursor.fetchall() or []:
            date_text = normalize_text(row.get("date"))
            time_text = format_time_hhmm(row.get("time"))
            schedule_dt = member_dashboard_schedule_dt(date_text, time_text)
            schedule_key = f"besar:{row.get('misa_id')}"
            evaluated = ("misa_besar", schedule_key) in evaluation_map
            can_cancel = schedule_dt > now and cancel_task_can_cancel(date_text)
            rows.append({
                "id": f"besar:{row.get('assignment_id')}",
                "type": "besar",
                "typeLabel": "Misa Besar",
                "assignmentId": row.get("assignment_id"),
                "misaId": row.get("misa_id"),
                "roleId": row.get("role_id"),
                "misaName": normalize_text(row.get("misa_name")) or "Misa Besar",
                "date": date_text,
                "dateLabel": request_task_format_date(date_text),
                "dayName": request_task_day_name(date_text),
                "time": time_text,
                "role": normalize_text(row.get("role")) or "Role",
                "status": "Selesai" if schedule_dt < now else "Terdaftar",
                "evaluation": "Sudah Diisi" if evaluated else "Belum Diisi",
                "evaluated": evaluated,
                "source": normalize_text(row.get("request_source")) or "admin",
                "sourceLabel": "Request Mandiri" if normalize_text(row.get("request_source")) == "member_request" else "Ditugaskan Admin",
                "canCancel": bool(can_cancel),
                "cancelDeadlineLabel": cancel_task_rule_label(date_text),
            })

    rows.sort(key=lambda item: member_dashboard_schedule_dt(item.get("date"), item.get("time")), reverse=True)
    return rows


def member_dashboard_request_chart(cursor, member_id: object, range_value: str) -> dict[str, object]:
    mode = normalize_text(range_value).lower() or "month"
    if mode not in {"week", "month", "year"}:
        mode = "month"
    start, end = dashboard_period_bounds(mode)
    labels, keys = dashboard_series_template(mode)
    counts = {key: 0 for key in keys}

    def add_rows(table_sql: str, params: tuple[object, ...]):
        cursor.execute(table_sql, params)
        for row in cursor.fetchall() or []:
            raw_date = row.get("item_date") if isinstance(row, dict) else None
            date_text = raw_date.isoformat() if hasattr(raw_date, "isoformat") else normalize_text(raw_date)
            if not date_text:
                continue
            if mode == "year":
                try:
                    parsed = datetime.strptime(date_text, "%Y-%m-%d")
                    key = (parsed.year, parsed.month)
                except Exception:
                    continue
            else:
                key = date_text
            if key in counts:
                counts[key] += parse_required_int(row.get("total") if isinstance(row, dict) else 0, 0)

    add_rows(
        """
        SELECT DATE(schedule_date) AS item_date, COUNT(*) AS total
        FROM streaming_assignments
        WHERE member_id = %s
          AND DATE(schedule_date) BETWEEN %s AND %s
        GROUP BY DATE(schedule_date)
        """,
        (member_id, start.isoformat(), end.isoformat()),
    )
    add_rows(
        """
        SELECT DATE(mb.misa_date) AS item_date, COUNT(*) AS total
        FROM misa_besar_assignments a
        JOIN misa_besar_names n ON n.id = a.role_id
        JOIN misa_besar mb ON mb.id = n.misa_id
        WHERE a.member_id = %s
          AND mb.status = 'published'
          AND DATE(mb.misa_date) BETWEEN %s AND %s
        GROUP BY DATE(mb.misa_date)
        """,
        (member_id, start.isoformat(), end.isoformat()),
    )
    return {"range": mode, "labels": labels, "values": [counts.get(key, 0) for key in keys]}


def member_dashboard_recommended_tasks(cursor, member_id: object, *, target_minimum: int, regular_count: int) -> list[dict[str, object]]:
    if regular_count >= target_minimum:
        return []
    now = datetime.now()
    items = request_task_regular_items(cursor, now.month, now.year, str(member_id))
    result: list[dict[str, object]] = []
    for item in items:
        if not item.get("canRequest"):
            continue
        schedule_dt = member_dashboard_schedule_dt(item.get("date"), item.get("time"))
        if schedule_dt < now:
            continue
        roles = item.get("roles") or []
        filled_count = sum(1 for role in roles if isinstance(role, dict) and role.get("filled"))
        total_roles = len(roles)
        open_roles = [normalize_text(role.get("role")) for role in (item.get("openRoles") or []) if isinstance(role, dict) and normalize_text(role.get("role"))]
        first_role = open_roles[0] if open_roles else "Role kosong"
        result.append({
            "id": item.get("id"),
            "type": "biasa",
            "typeLabel": "Misa Biasa",
            "misaName": item.get("misaName"),
            "date": item.get("date"),
            "dateLabel": item.get("dateLabel"),
            "dayName": item.get("dayName"),
            "time": item.get("time"),
            "role": first_role,
            "openRoles": open_roles,
            "filledCount": filled_count,
            "totalRoles": total_roles,
            "href": f"request-tugas-anggota.html?jenis=biasa&month={now.month}&year={now.year}",
        })
        if len(result) >= 3:
            break
    return result










def ensure_streaming_schema() -> None:
    conn = mysql_connection()
    # PERBAIKAN: Gunakan buffered=True agar tidak ada error unread result
    cursor = conn.cursor(buffered=True)
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS `streaming_weekly_config` (`id` int AUTO_INCREMENT PRIMARY KEY, `day_name` varchar(20), `start_time` time, `mass_name` varchar(255))")
        cursor.execute("CREATE TABLE IF NOT EXISTS `streaming_cancelled` (`id` int AUTO_INCREMENT PRIMARY KEY, `mass_date` date, `mass_time` time)")
        cursor.execute("CREATE TABLE IF NOT EXISTS `streaming_roles` (`id` int AUTO_INCREMENT PRIMARY KEY, `role_name` varchar(100) UNIQUE, `order_index` int DEFAULT 0)")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `streaming_assignments` (
              `id` int AUTO_INCREMENT PRIMARY KEY,
              `schedule_date` date NOT NULL,
              `schedule_time` time NOT NULL,
              `role_name` varchar(100) NOT NULL,
              `member_id` int NOT NULL,
              UNIQUE KEY `uniq_assignment` (`schedule_date`, `schedule_time`, `role_name`)
            )
        """)
        try:
            ensure_column(cursor, "streaming_assignments", "created_at", "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
            ensure_column(cursor, "streaming_assignments", "request_source", "`request_source` varchar(30) NOT NULL DEFAULT 'admin'")
            conn.commit()
        except Exception as exc:
            print(f"[WARN] Failed to ensure streaming assignment metadata: {exc}")
        
        cursor.execute("SELECT COUNT(*) FROM `streaming_roles`")
        res = cursor.fetchone()
        if res and res[0] == 0:
            cursor.execute("INSERT IGNORE INTO `streaming_roles` (role_name, order_index) VALUES ('Produser', 1), ('Operator Streaming', 2), ('Kameramen 1', 3), ('Kameramen 2', 4), ('Kameramen 3', 5)")
            conn.commit()
    except Exception as e:
        print(f"[WARN] Error in schema: {e}")
    finally:
        cursor.close()
        conn.close()

def format_time_hhmm(t_obj):
    """Mencegah bug timedelta slicing '7:30:' menjadi '07:30'"""
    if t_obj is None:
        return "00:00"
    if isinstance(t_obj, str):
        return t_obj[:5].zfill(5)
    if hasattr(t_obj, 'total_seconds'):
        hours, remainder = divmod(int(t_obj.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"
    return str(t_obj)[:5].zfill(5)

DAYS_INDO = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def clear_streaming_assignments_for_published_misa_besar(cursor, misa_date, misa_time, status) -> int:
    """Hapus penugasan Misa Biasa bila Misa Besar published memakai tanggal+jam yang sama.

    Ini menjaga aturan operasional: dalam tanggal dan jam mulai yang sama hanya ada satu misa.
    Misa Besar yang masih draft tidak mengubah penugasan Misa Biasa.
    """
    if normalize_misa_besar_status(status) != "published":
        return 0

    if hasattr(misa_date, "isoformat"):
        date_value = misa_date.isoformat()
    else:
        date_value = normalize_text(misa_date)
    time_value = format_time_hhmm(misa_time)
    if not date_value or not time_value:
        return 0

    cursor.execute(
        """
        DELETE FROM `streaming_assignments`
        WHERE `schedule_date` = %s AND `schedule_time` = %s
        """,
        (date_value, time_value),
    )
    return cursor.rowcount or 0

def normalize_misa_besar_status(value: str | None) -> str:
    raw = normalize_text(value).lower()
    return "published" if raw in {"published", "publish", "publikasi"} else "draft"

def fetch_misa_besar_notification_snapshot(cursor, misa_id: int) -> dict[str, object] | None:
    """Ambil snapshot Misa Besar + petugas untuk kebutuhan notifikasi.

    Snapshot ini dipakai untuk dua jenis notifikasi:
    1. notifikasi petugas yang memang ditugaskan;
    2. notifikasi ke anggota aktif jika Misa Besar published masih memiliki role/slot kosong.
    """
    cursor.execute(
        """
        SELECT id, misa_name, DATE_FORMAT(misa_date, '%Y-%m-%d') AS misa_date,
               DATE_FORMAT(misa_time, '%H:%i') AS misa_time, misa_note,
               allow_member_request, status
        FROM misa_besar
        WHERE id = %s
        LIMIT 1
        """,
        (misa_id,),
    )
    event = cursor.fetchone()
    if not event:
        return None

    cursor.execute(
        """
        SELECT n.id AS role_id, n.role_name, n.required_count, a.member_id
        FROM misa_besar_names n
        LEFT JOIN misa_besar_assignments a ON a.role_id = n.id
        WHERE n.misa_id = %s
        ORDER BY n.id ASC, a.id ASC
        """,
        (misa_id,),
    )

    assignments: list[dict[str, str]] = []
    seen_assignments: set[tuple[str, str]] = set()
    roles_by_id: dict[str, dict[str, object]] = {}

    for row in cursor.fetchall() or []:
        if not isinstance(row, dict):
            continue

        role_id = normalize_text(row.get("role_id"))
        role_name = normalize_text(row.get("role_name")) or "Role"
        required_count = parse_required_int(row.get("required_count"), 1) or 1
        required_count = max(1, required_count)

        if role_id and role_id not in roles_by_id:
            roles_by_id[role_id] = {
                "roleId": role_id,
                "role": role_name,
                "requiredCount": required_count,
                "memberIds": [],
            }

        member_id = row.get("member_id")
        if member_id in (None, ""):
            continue

        member_id_text = str(member_id)
        if role_id and role_id in roles_by_id and member_id_text not in roles_by_id[role_id]["memberIds"]:
            roles_by_id[role_id]["memberIds"].append(member_id_text)

        key = (role_name, member_id_text)
        if key in seen_assignments:
            continue
        seen_assignments.add(key)
        assignments.append({"role": role_name, "memberId": member_id_text})

    roles: list[dict[str, object]] = []
    for role in roles_by_id.values():
        filled_count = len(role.get("memberIds") or [])
        required_count = parse_required_int(role.get("requiredCount"), 1) or 1
        role["filledCount"] = filled_count
        role["emptyCount"] = max(required_count - filled_count, 0)
        roles.append(role)

    return {
        "id": int(event.get("id") or misa_id),
        "misaName": normalize_text(event.get("misa_name")) or "Misa Besar",
        "misaDate": normalize_text(event.get("misa_date")),
        "misaTime": format_time_hhmm(event.get("misa_time")),
        "misaNote": normalize_text(event.get("misa_note")),
        "allowMemberRequest": bool(event.get("allow_member_request")),
        "status": normalize_misa_besar_status(event.get("status")),
        "assignments": assignments,
        "roles": roles,
    }

def misa_besar_assignment_keys(snapshot: dict[str, object] | None) -> set[tuple[str, str]]:
    if not snapshot:
        return set()
    keys: set[tuple[str, str]] = set()
    for item in snapshot.get("assignments") or []:
        if not isinstance(item, dict):
            continue
        role_name = normalize_text(item.get("role")) or "Role"
        member_id = normalize_text(item.get("memberId"))
        if member_id:
            keys.add((role_name, member_id))
    return keys

def create_misa_besar_assignment_notifications(
    cursor,
    snapshot: dict[str, object] | None,
    *,
    only_keys: set[tuple[str, str]] | None = None,
) -> int:
    """Kirim notif tugas untuk petugas Misa Besar yang statusnya sudah published."""
    if not snapshot or normalize_misa_besar_status(snapshot.get("status")) != "published":
        return 0

    try:
        date_obj = datetime.strptime(normalize_text(snapshot.get("misaDate")), "%Y-%m-%d")
        day_name = DAYS_INDO[date_obj.weekday()]
        date_formatted = date_obj.strftime("%d/%m/%Y")
    except Exception:
        day_name = "-"
        date_formatted = normalize_text(snapshot.get("misaDate")) or "-"

    misa_id = snapshot.get("id")
    misa_name = normalize_text(snapshot.get("misaName")) or "Misa Besar"
    misa_time = format_time_hhmm(snapshot.get("misaTime"))
    sent = 0
    sent_keys: set[tuple[str, str]] = set()

    for item in snapshot.get("assignments") or []:
        if not isinstance(item, dict):
            continue
        role_name = normalize_text(item.get("role")) or "Role"
        member_id = normalize_text(item.get("memberId"))
        key = (role_name, member_id)
        if not member_id or key in sent_keys:
            continue
        if only_keys is not None and key not in only_keys:
            continue

        title = f"Tugas Baru: {role_name}"
        body = (
            f"Anda ditugaskan sebagai <b>{html.escape(role_name)}</b> untuk "
            f"<b>{html.escape(misa_name)}</b> pada hari {html.escape(day_name)}, "
            f"{html.escape(date_formatted)} jam {html.escape(misa_time)} WIB."
        )
        create_notification(
            cursor,
            "tugas",
            title,
            body,
            "/jadwal-tugas-misa-anggota.html",
            {
                "target_user_id": member_id,
                "misa_besar_id": misa_id,
                "misa_type": "misa_besar",
                "role": role_name,
                "misa_name": misa_name,
                "misa_date": snapshot.get("misaDate"),
                "misa_time": misa_time,
            },
            target_role=None,
        )
        sent_keys.add(key)
        sent += 1
    return sent

def notify_misa_besar_assignment_changes(cursor, old_snapshot: dict[str, object] | None, new_snapshot: dict[str, object] | None) -> int:
    """
    Aturan notifikasi Misa Besar:
    - draft tidak mengirim notifikasi;
    - saat berubah ke published, semua petugas terisi dapat notifikasi;
    - saat sudah published, hanya petugas baru/peran baru yang dapat notifikasi.
    """
    if not new_snapshot or normalize_misa_besar_status(new_snapshot.get("status")) != "published":
        return 0

    ensure_notifications_schema()

    old_status = normalize_misa_besar_status(old_snapshot.get("status")) if old_snapshot else "draft"
    if old_status != "published":
        return create_misa_besar_assignment_notifications(cursor, new_snapshot)

    new_keys = misa_besar_assignment_keys(new_snapshot)
    old_keys = misa_besar_assignment_keys(old_snapshot)
    changed_keys = new_keys - old_keys
    if not changed_keys:
        return 0
    return create_misa_besar_assignment_notifications(cursor, new_snapshot, only_keys=changed_keys)


def misa_besar_open_role_labels(snapshot: dict[str, object] | None) -> list[str]:
    """Kembalikan daftar role/slot Misa Besar yang masih kosong."""
    if not snapshot:
        return []

    labels: list[str] = []
    for role in snapshot.get("roles") or []:
        if not isinstance(role, dict):
            continue
        role_name = normalize_text(role.get("role")) or "Role"
        empty_count = parse_required_int(role.get("emptyCount"), 0)
        if empty_count <= 0:
            continue
        if empty_count > 1:
            labels.append(f"{role_name} ({empty_count} slot)")
        else:
            labels.append(role_name)
    return labels

def create_misa_besar_open_role_notifications(cursor, snapshot: dict[str, object] | None) -> int:
    """Kirim notifikasi kategori tugas ke anggota aktif biasa bila published Misa Besar masih punya slot kosong.

    Notifikasi dibuat per anggota agar dashboard anggota bisa tetap memfilter menggunakan target_user_id,
    sama seperti notifikasi tugas lain.
    """
    if not snapshot or normalize_misa_besar_status(snapshot.get("status")) != "published":
        return 0

    empty_roles = misa_besar_open_role_labels(snapshot)
    if not empty_roles:
        return 0

    ensure_notifications_schema()

    try:
        date_obj = datetime.strptime(normalize_text(snapshot.get("misaDate")), "%Y-%m-%d")
        day_name = DAYS_INDO[date_obj.weekday()]
        date_formatted = date_obj.strftime("%d/%m/%Y")
    except Exception:
        day_name = "-"
        date_formatted = normalize_text(snapshot.get("misaDate")) or "-"

    misa_id = snapshot.get("id")
    misa_name = normalize_text(snapshot.get("misaName")) or "Misa Besar"
    misa_time = format_time_hhmm(snapshot.get("misaTime"))
    request_label = "dibuka" if snapshot.get("allowMemberRequest") else "ditutup"
    empty_role_text = ", ".join(empty_roles)

    cursor.execute(
        """
        SELECT id, nama
        FROM anggota
        WHERE LOWER(COALESCE(role, '')) = 'user'
          AND LOWER(COALESCE(status_akun, '')) = 'aktif'
        ORDER BY nama ASC, id ASC
        """
    )
    members = cursor.fetchall() or []

    sent = 0
    for member in members:
        if not isinstance(member, dict):
            continue
        member_id = normalize_text(member.get("id"))
        if not member_id:
            continue

        title = "Misa Besar Butuh Petugas"
        body = (
            f"Ada Misa Besar baru <b>{html.escape(misa_name)}</b> pada hari {html.escape(day_name)}, "
            f"{html.escape(date_formatted)} jam {html.escape(misa_time)} WIB yang masih memiliki slot kosong: "
            f"<b>{html.escape(empty_role_text)}</b>. "
            f"Status request anggota: <b>{html.escape(request_label)}</b>. "
            "Silakan buka halaman request tugas untuk melihat detail dan mengajukan tugas."
        )

        create_notification(
            cursor,
            "tugas",
            title,
            body,
            f"/request-tugas-anggota.html?misaBesarId={misa_id}",
            {
                "target_user_id": member_id,
                "notification_kind": "misa_besar_open_roles",
                "misa_besar_id": misa_id,
                "misa_type": "misa_besar",
                "misa_name": misa_name,
                "misa_date": snapshot.get("misaDate"),
                "misa_time": misa_time,
                "empty_roles": empty_roles,
                "allow_member_request": bool(snapshot.get("allowMemberRequest")),
            },
            target_role="user",
        )
        sent += 1

    return sent

def notify_misa_besar_open_roles_if_newly_published(cursor, old_snapshot: dict[str, object] | None, new_snapshot: dict[str, object] | None) -> int:
    """Kirim notifikasi slot kosong hanya saat Misa Besar baru masuk status published."""
    if not new_snapshot or normalize_misa_besar_status(new_snapshot.get("status")) != "published":
        return 0

    old_status = normalize_misa_besar_status(old_snapshot.get("status")) if old_snapshot else "draft"
    if old_status == "published":
        return 0

    return create_misa_besar_open_role_notifications(cursor, new_snapshot)

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
    ensure_column(cursor, "anggota", "inactive_until", "`inactive_until` date DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_from", "`inactive_from` date DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_type", "`inactive_type` varchar(30) DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_reason", "`inactive_reason` varchar(255) DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_note", "`inactive_note` text DEFAULT NULL")
    ensure_membership_request_schema(cursor)
    ensure_admin_permissions_schema(cursor)
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
          `url` text NOT NULL,
          `embed_type` varchar(30) NOT NULL DEFAULT 'video',
          `title` varchar(255) DEFAULT NULL,
          `order_index` int(11) DEFAULT 0,
          `is_visible` tinyint(1) DEFAULT 1,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')
    ensure_column(cursor, "youtube_embeds", "embed_type", "`embed_type` varchar(30) NOT NULL DEFAULT 'video'")
    ensure_column(cursor, "youtube_embeds", "title", "`title` varchar(255) DEFAULT NULL")
    try:
        cursor.execute("ALTER TABLE `youtube_embeds` MODIFY COLUMN `url` text NOT NULL")
    except Exception:
        pass

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
          `romo_name` varchar(255) DEFAULT 'Romo Paroki GKR Baciro',
          `pembina_name` varchar(255) DEFAULT 'Pembina Crembo Media',
          `ketua_name` varchar(255) DEFAULT 'Ketua Crembo Media',
          `romo_sign_url` text DEFAULT NULL,
          `pembina_sign_url` text DEFAULT NULL,
          `ketua_sign_url` text DEFAULT NULL,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')
    ensure_column(cursor, "sertifikat_config", "romo_name", "`romo_name` varchar(255) DEFAULT 'Romo Paroki GKR Baciro'")
    ensure_column(cursor, "sertifikat_config", "romo_sign_url", "`romo_sign_url` text DEFAULT NULL")
    cursor.execute("SELECT COUNT(*) FROM `sertifikat_config`")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO `sertifikat_config` (`id`, `romo_name`, `pembina_name`, `ketua_name`, `romo_sign_url`, `pembina_sign_url`, `ketua_sign_url`) VALUES (1, 'Romo Paroki GKR Baciro', 'Pembina Crembo Media', 'Ketua Crembo Media', '', '', '')")

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

    ensure_inventory_schema(cursor)

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
        SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun, inactive_until, inactive_from, inactive_type, inactive_reason, inactive_note
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



# ===== Membership inactive request helpers =====
MEMBERSHIP_PENDING = "pending"
MEMBERSHIP_APPROVED = "approved"
MEMBERSHIP_REJECTED = "rejected"
MEMBERSHIP_CANCELLED = "cancelled"

MEMBERSHIP_STATUS_LABELS = {
    MEMBERSHIP_PENDING: "Menunggu Review Admin",
    MEMBERSHIP_APPROVED: "Disetujui",
    MEMBERSHIP_REJECTED: "Ditolak",
    MEMBERSHIP_CANCELLED: "Dibatalkan",
}

def membership_status_label(value: str | None) -> str:
    return MEMBERSHIP_STATUS_LABELS.get(normalize_text(value).lower(), normalize_text(value) or "Menunggu Review Admin")

def membership_status_key(value: str | None) -> str:
    raw = normalize_text(value).lower()
    if raw in {"pending", "menunggu", "menunggu review admin"}:
        return MEMBERSHIP_PENDING
    if raw in {"approved", "approve", "disetujui", "acc"}:
        return MEMBERSHIP_APPROVED
    if raw in {"rejected", "reject", "ditolak"}:
        return MEMBERSHIP_REJECTED
    if raw in {"cancelled", "canceled", "dibatalkan", "cancel"}:
        return MEMBERSHIP_CANCELLED
    return raw or MEMBERSHIP_PENDING

def ensure_membership_request_schema(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `membership_status_requests` (
          `id` varchar(100) NOT NULL,
          `member_id` int(11) NOT NULL,
          `member_name` varchar(255) DEFAULT NULL,
          `inactive_type` varchar(30) NOT NULL DEFAULT 'permanent',
          `reason` varchar(255) NOT NULL,
          `start_date` date NOT NULL,
          `return_date` date DEFAULT NULL,
          `note` text NOT NULL,
          `evidence_json` longtext DEFAULT NULL,
          `status` varchar(30) NOT NULL DEFAULT 'pending',
          `admin_id` int(11) DEFAULT NULL,
          `admin_name` varchar(255) DEFAULT NULL,
          `admin_note` text DEFAULT NULL,
          `decided_at` datetime DEFAULT NULL,
          `applied_at` datetime DEFAULT NULL,
          `manual_reactivated_at` datetime DEFAULT NULL,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `idx_membership_member` (`member_id`),
          KEY `idx_membership_status` (`status`),
          KEY `idx_membership_start` (`start_date`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    ensure_column(cursor, "membership_status_requests", "applied_at", "`applied_at` datetime DEFAULT NULL")
    ensure_column(cursor, "membership_status_requests", "manual_reactivated_at", "`manual_reactivated_at` datetime DEFAULT NULL")

def membership_evidence_payload(value) -> dict[str, object]:
    attachments = normalize_attachment_payload(value)
    return attachments[0] if attachments else {}

def membership_request_row_to_dict(row: dict[str, object]) -> dict[str, object]:
    if not row:
        return {}
    evidence = membership_evidence_payload(row.get("evidence_json"))
    status_key = membership_status_key(row.get("status"))
    start_date = row.get("start_date")
    return_date = row.get("return_date")
    created_at = row.get("created_at")
    updated_at = row.get("updated_at")
    decided_at = row.get("decided_at")
    applied_at = row.get("applied_at")
    manual_reactivated_at = row.get("manual_reactivated_at")
    return {
        "id": row.get("id"),
        "memberId": row.get("member_id"),
        "memberName": row.get("member_name") or "Anggota",
        "requestType": "Nonaktif",
        "inactiveType": "temporary" if normalize_text(row.get("inactive_type")).lower() == "temporary" else "permanent",
        "reason": row.get("reason") or "",
        "effectiveDate": start_date.isoformat() if hasattr(start_date, "isoformat") else normalize_text(start_date),
        "reactivateDate": return_date.isoformat() if hasattr(return_date, "isoformat") else normalize_text(return_date),
        "note": row.get("note") or "",
        "evidence": evidence,
        "evidenceName": evidence.get("name") or "",
        "evidenceType": evidence.get("mimeType") or "",
        "evidenceUrl": evidence.get("url") or "",
        "evidencePreviewable": bool(evidence.get("previewable")),
        "statusKey": status_key,
        "status": membership_status_label(status_key),
        "adminName": row.get("admin_name") or "",
        "adminNote": row.get("admin_note") or "",
        "submittedDate": created_at.date().isoformat() if hasattr(created_at, "date") else normalize_text(created_at)[:10],
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else normalize_text(created_at),
        "updatedAt": updated_at.isoformat() if hasattr(updated_at, "isoformat") else normalize_text(updated_at),
        "decidedAt": decided_at.isoformat() if hasattr(decided_at, "isoformat") else normalize_text(decided_at),
        "appliedAt": applied_at.isoformat() if hasattr(applied_at, "isoformat") else normalize_text(applied_at),
        "manualReactivatedAt": manual_reactivated_at.isoformat() if hasattr(manual_reactivated_at, "isoformat") else normalize_text(manual_reactivated_at),
    }

def ensure_membership_columns(cursor) -> None:
    ensure_column(cursor, "anggota", "inactive_until", "`inactive_until` date DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_from", "`inactive_from` date DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_type", "`inactive_type` varchar(30) DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_reason", "`inactive_reason` varchar(255) DEFAULT NULL")
    ensure_column(cursor, "anggota", "inactive_note", "`inactive_note` text DEFAULT NULL")
    ensure_membership_request_schema(cursor)

def apply_membership_status_transitions(cursor) -> None:
    """Aktifkan/nonaktifkan otomatis berdasarkan request yang sudah disetujui."""
    today = datetime.now().date()
    ensure_membership_columns(cursor)

    # Mulai masa nonaktif yang sudah sampai tanggal efektif.
    cursor.execute(
        """
        SELECT r.*, a.status_akun
        FROM `membership_status_requests` r
        JOIN `anggota` a ON a.id = r.member_id
        WHERE r.status = 'approved'
          AND r.start_date <= %s
          AND r.applied_at IS NULL
          AND r.manual_reactivated_at IS NULL
          AND COALESCE(a.status_akun, 'aktif') <> 'nonaktif'
          AND (r.return_date IS NULL OR r.return_date > %s)
        """,
        (today, today),
    )
    for row in cursor.fetchall() or []:
        cursor.execute(
            """
            UPDATE `anggota`
            SET status_akun = 'nonaktif', inactive_from = %s, inactive_until = %s,
                inactive_type = %s, inactive_reason = %s, inactive_note = %s
            WHERE id = %s
            """,
            (
                row.get("start_date"),
                row.get("return_date"),
                row.get("inactive_type"),
                row.get("reason"),
                row.get("note"),
                row.get("member_id"),
            ),
        )
        cursor.execute(
            """
            UPDATE `membership_status_requests`
            SET applied_at = COALESCE(applied_at, CURRENT_TIMESTAMP), updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (row.get("id"),),
        )
        create_notification_once(
            cursor,
            "keanggotaan",
            "Status Keanggotaan Nonaktif",
            "Pengajuan nonaktif Anda sudah disetujui dan status akun menjadi nonaktif.",
            "/profil-anggota.html",
            {"target_user_id": row.get("member_id"), "request_id": row.get("id")},
            target_role="user",
            dedupe_key=f"membership-approved-active-{row.get('id')}",
        )

    # Aktif kembali otomatis untuk nonaktif berjangka.
    cursor.execute(
        """
        SELECT r.*
        FROM `membership_status_requests` r
        JOIN `anggota` a ON a.id = r.member_id
        WHERE r.status = 'approved'
          AND r.inactive_type = 'temporary'
          AND r.return_date IS NOT NULL
          AND r.return_date <= %s
          AND r.manual_reactivated_at IS NULL
          AND COALESCE(a.status_akun, 'aktif') = 'nonaktif'
        """,
        (today,),
    )
    for row in cursor.fetchall() or []:
        cursor.execute(
            """
            UPDATE `anggota`
            SET status_akun = 'aktif', inactive_until = NULL, inactive_from = NULL,
                inactive_type = NULL, inactive_reason = NULL, inactive_note = NULL
            WHERE id = %s
            """,
            (row.get("member_id"),),
        )
        create_notification_once(
            cursor,
            "keanggotaan",
            "Status Keanggotaan Aktif Kembali",
            "Masa nonaktif berjangka Anda sudah selesai. Status akun Anda aktif kembali.",
            "/profil-anggota.html",
            {"target_user_id": row.get("member_id"), "request_id": row.get("id")},
            target_role="user",
            dedupe_key=f"membership-auto-reactivate-{row.get('id')}",
        )


def _effective_membership_request_for_member(cursor, member_id):
    """Ambil pengajuan nonaktif approved yang masih aktif untuk 1 anggota.

    Helper ini dipakai untuk menjaga agar status anggota di Manajemen Anggota
    tidak tertimpa kembali menjadi aktif setelah request nonaktif disetujui.
    """
    try:
        member_id_int = int(member_id)
    except (TypeError, ValueError):
        return None

    today = datetime.now().date()
    ensure_membership_columns(cursor)
    cursor.execute(
        """
        SELECT *
        FROM membership_status_requests
        WHERE member_id = %s
          AND status = 'approved'
          AND start_date <= %s
          AND (return_date IS NULL OR return_date > %s)
          AND manual_reactivated_at IS NULL
        ORDER BY start_date DESC, decided_at DESC, updated_at DESC, created_at DESC
        LIMIT 1
        """,
        (member_id_int, today, today),
    )
    return cursor.fetchone()


def force_apply_effective_membership_status(cursor, member_id):
    """Paksa sinkron status_akun anggota dari request nonaktif yang approved.

    Kasus bug sebelumnya:
    - Approve dari Dashboard Admin aman.
    - Approve dari Manajemen Anggota bisa terlihat tetap Aktif karena data anggota
      yang dirender/sinkron masih stale.
    Fungsi ini memastikan sumber kebenaran tetap tabel membership_status_requests.
    """
    req = _effective_membership_request_for_member(cursor, member_id)
    if not req:
        return None

    cursor.execute(
        """
        UPDATE anggota
        SET status_akun = 'nonaktif',
            inactive_from = %s,
            inactive_until = %s,
            inactive_type = %s,
            inactive_reason = %s,
            inactive_note = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (
            req.get("start_date"),
            req.get("return_date"),
            req.get("inactive_type") or "permanent",
            req.get("reason") or "",
            req.get("note") or "",
            req.get("member_id"),
        ),
    )
    cursor.execute(
        """
        UPDATE membership_status_requests
        SET applied_at = COALESCE(applied_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (req.get("id"),),
    )
    return req


def repair_effective_membership_statuses_for_admin(cursor) -> None:
    """Sinkron ulang status anggota untuk halaman admin/manajemen anggota."""
    today = datetime.now().date()
    ensure_membership_columns(cursor)

    # Jalankan transisi otomatis lebih dulu untuk request yang belum applied
    # dan request temporary yang sudah melewati tanggal aktif kembali.
    apply_membership_status_transitions(cursor)

    # Perbaiki juga data lama yang sudah approved/applied tetapi status anggota
    # sempat tertimpa aktif oleh proses sync halaman Manajemen Anggota.
    cursor.execute(
        """
        SELECT DISTINCT member_id
        FROM membership_status_requests
        WHERE status = 'approved'
          AND start_date <= %s
          AND (return_date IS NULL OR return_date > %s)
          AND manual_reactivated_at IS NULL
        """,
        (today, today),
    )
    member_ids = [row.get("member_id") if isinstance(row, dict) else row[0] for row in (cursor.fetchall() or [])]
    for member_id in member_ids:
        force_apply_effective_membership_status(cursor, member_id)



def member_default_password_label(birth_date: str) -> str:
    """Format password default anggota baru menjadi dd/mm/yyyy."""
    password = default_password_from_birth_date(birth_date)
    if isinstance(password, str) and password.strip():
        return password.strip()
    return "tanggal lahir Anda dengan format dd/mm/yyyy"


def create_new_member_account_notification(cursor, member_id: int, *, full_name: str, username: str, email_value: str, birth_date: str, role_value: str) -> None:
    """Buat notifikasi dashboard dan email akun untuk anggota/admin baru."""
    safe_name = normalize_text(full_name) or "Anggota Crembo Media"
    safe_username = normalize_text(username) or normalize_text(email_value) or f"anggota-{member_id}"
    default_password = member_default_password_label(birth_date)
    role_label = {
        "user": "Anggota",
        "admin": "Admin",
        "super_admin": "Super Admin",
    }.get(normalize_role_value(role_value), "Anggota")
    body = (
        f"Halo <b>{html.escape(safe_name)}</b>, akun Anda sudah terdaftar pada website "
        f"<b>Crembo Media</b>.<br>"
        f"Anda dapat login melalui website <b>crembomedia.com</b> dengan data berikut:<br>"
        f"<b>Role:</b> {html.escape(role_label)}<br>"
        f"<b>Username:</b> {html.escape(safe_username)}<br>"
        f"<b>Password default:</b> {html.escape(default_password)}<br>"
        f"Password default memakai tanggal lahir dengan format <b>dd/mm/yyyy</b>. "
        f"Contoh: 1 Februari 2001 menjadi <b>01/02/2001</b>. "
        f"Silakan login dan ubah password setelah masuk jika diperlukan."
    )
    create_notification(
        cursor,
        "keanggotaan",
        "Akun Crembo Media Anda Telah Terdaftar",
        body,
        "/login.html",
        {
            "target_user_id": member_id,
            "member_id": member_id,
            "include_inactive": True,
            "event": "new_member_account",
        },
        target_role=None,
    )


def current_member_is_inactive() -> bool:
    return session.get("logged_in") and normalize_role_value(session.get("role") or "user") == "user" and normalize_status(session.get("status_akun") or "aktif") == "nonaktif"

def is_inactive_member_page_allowed(candidate: str) -> bool:
    allowed = {
        "dashboard-anggota.html",
        "profil-anggota.html",
        "profil.html",
        "sertifikat-anggota.html",
        "/sertifikat-anggota",
        "unduh-sertifikat-anggota.html",
        "log-aktivitas-saya.html",
        "log-aktivitas.html",
        "home.html",
        "login.html",
    }
    return candidate in allowed

def can_manage_members() -> bool:
    if not session.get("logged_in"):
        return False
    role = normalize_role_value(session.get("role") or "")
    if role == "super_admin":
        return True
    if role == "admin":
        return admin_has_module_access("keanggotaan")
    return False


def can_manage_registration_forms() -> bool:
    return bool(session.get("logged_in")) and (session.get("role") or "") in {"admin", "super_admin"}


def registration_form_field_to_dict(item, index):
    return {
        "id": str(item and item.get("id") or f"field-{index + 1}"),
        "label": str(item and item.get("label") or f"Pertanyaan {index + 1}"),
        "type": str(item and item.get("type") or "text"),
        "required": bool(item and item.get("required")),
        "placeholder": str(item and item.get("placeholder") or ""),
        "options": [str(value) for value in (item and item.get("options") or []) if str(value).strip()],
    }


def normalize_registration_fields(value) -> list[dict[str, object]]:
    if value in (None, "", []):
        return []

    raw_items = value
    if isinstance(value, str):
        raw_text = value.strip()
        if not raw_text:
            return []
        try:
            parsed = json.loads(raw_text)
            raw_items = parsed if isinstance(parsed, list) else [parsed]
        except (TypeError, ValueError):
            raw_items = [raw_text]

    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    normalized_items: list[dict[str, object]] = []
    for index, item in enumerate(raw_items or []):
        if not isinstance(item, dict):
            continue
        normalized_items.append(registration_form_field_to_dict(item, index))
    return normalized_items


def registration_form_row_to_dict(row: dict[str, object], submission_count: int = 0) -> dict[str, object]:
    fields_raw = row.get("fields_json") or row.get("fields") or "[]"
    try:
        fields = json.loads(fields_raw) if isinstance(fields_raw, str) else (fields_raw or [])
    except (TypeError, ValueError):
        fields = []

    # BACA DATA BARU imageUrl dan attachments
    attachments_raw = row.get("attachments") or "[]"
    try:
        attachments = json.loads(attachments_raw) if isinstance(attachments_raw, str) else (attachments_raw or [])
    except (TypeError, ValueError):
        attachments = []

    return {
        "id": row.get("id"),
        "title": row.get("title") or "Form Pendaftaran",
        "description": row.get("description") or "",
        "target": "internal" if (row.get("target") or "public") == "internal" else "public",
        "visibility": "draft" if (row.get("visibility") or "visible") == "draft" else "visible",
        "openDate": str(row.get("open_date") or ""),
        "closeDate": str(row.get("close_date") or ""),
        "quota": int(row.get("quota") or 0),
        "imageUrl": row.get("image_url") or "",
        "imageName": row.get("image_name") or "",
        "attachments": attachments if isinstance(attachments, list) else [],
        "fields": normalize_registration_fields(fields),
        "submissionCount": int(submission_count or 0),
        "createdAt": row.get("created_at") or "",
        "updatedAt": row.get("updated_at") or "",
    }


def registration_form_payload_to_db_values(data, existing=None):
    source = existing or {}
    fields = normalize_registration_fields(data.get("fields", source.get("fields_json", source.get("fields", []))))
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

    quota_value = data.get("quota")
    if quota_value in (None, ""):
        quota_value = source.get("quota") or 0

    return {
        "title": str(value_for("title")).strip(),
        "description": str(value_for("description")).strip(),
        "target": "internal" if str(value_for("target", default="public")).strip().lower() == "internal" else "public",
        "visibility": "draft" if str(value_for("visibility", default="visible")).strip().lower() == "draft" else "visible",
        "open_date": str(value_for("openDate", "open_date")).strip() or None,
        "close_date": str(value_for("closeDate", "close_date")).strip() or None,
        "quota": int(quota_value or 0),
        "image_url": str(value_for("imageUrl", "image_url")).strip(),
        "image_name": str(value_for("imageName", "image_name")).strip(),
        "attachments": json.dumps(attachments, ensure_ascii=False),
        "fields_json": json.dumps(fields, ensure_ascii=False),
    }


def registration_form_status(form: dict[str, object], submission_count: int) -> dict[str, object]:
    now = datetime.now().date()
    if form.get("visibility") == "draft":
        return {"open": False, "reason": "draft", "text": "Draft"}

    open_date_value = str(form.get("openDate") or "").strip()
    close_date_value = str(form.get("closeDate") or "").strip()
    open_date = datetime.strptime(open_date_value, "%Y-%m-%d").date() if open_date_value else None
    close_date = datetime.strptime(close_date_value, "%Y-%m-%d").date() if close_date_value else None

    if open_date and now < open_date:
        return {"open": False, "reason": "not_open", "text": "Belum dibuka"}
    if close_date and now > close_date:
        return {"open": False, "reason": "closed", "text": "Sudah ditutup"}
    if int(form.get("quota") or 0) > 0 and int(submission_count or 0) >= int(form.get("quota") or 0):
        return {"open": False, "reason": "quota", "text": "Kuota penuh"}
    return {"open": True, "reason": "open", "text": "Aktif"}


def registration_form_submission_counts(cursor) -> dict[str, int]:
    cursor.execute("SELECT `form_id`, COUNT(*) AS `count` FROM `registration_form_submissions` GROUP BY `form_id`")
    counts: dict[str, int] = {}
    for row in cursor.fetchall() or []:
        counts[str(row.get("form_id") or "")] = int(row.get("count") or 0)
    return counts


def registration_submission_row_to_dict(row: dict[str, object]) -> dict[str, object]:
    answers_raw = row.get("answers_json") or "[]"
    try:
        answers = json.loads(answers_raw) if isinstance(answers_raw, str) else (answers_raw or [])
    except (TypeError, ValueError):
        answers = []
    return {
        "id": row.get("id"),
        "formId": row.get("form_id"),
        "submittedAt": row.get("submitted_at") or "",
        "submitter": {
            "key": row.get("submitter_key") or "",
            "identifier": row.get("submitter_identifier") or "",
            "role": row.get("submitter_role") or "public",
            "userId": row.get("submitter_user_id") or "",
            "source": row.get("submitter_source") or "public",
        },
        "answers": answers if isinstance(answers, list) else [],
    }


def registration_submitter_context(form: dict[str, object], payload_submitter) -> tuple[dict[str, object] | None, tuple[dict[str, object], int] | None]:
    viewer = current_user_context()
    submitter_data = payload_submitter if isinstance(payload_submitter, dict) else {}

    if form.get("target") == "internal":
        if not viewer.get("logged_in"):
            return None, ({"success": False, "error": "Form internal hanya bisa diisi setelah login."}, 401)
        submitter_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'internal'}"
        return {
            "key": submitter_key,
            "identifier": viewer.get("nama") or viewer.get("username") or viewer.get("email") or "Anggota",
            "role": viewer.get("role") or "user",
            "user_id": viewer.get("user_id") or "",
            "source": "internal",
        }, None

    if viewer.get("logged_in"):
        submitter_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'public'}"
        return {
            "key": submitter_key,
            "identifier": viewer.get("nama") or viewer.get("username") or viewer.get("email") or "Pengguna",
            "role": viewer.get("role") or "user",
            "user_id": viewer.get("user_id") or "",
            "source": "logged_in",
        }, None

    client_key = str(submitter_data.get("key") or submitter_data.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    if not client_key:
        client_key = f"guest:{uuid.uuid4().hex}"
    return {
        "key": client_key,
        "identifier": str(submitter_data.get("identifier") or "Pengunjung").strip() or "Pengunjung",
        "role": str(submitter_data.get("role") or "public").strip() or "public",
        "user_id": "",
        "source": "public",
    }, None


def registration_submission_payload_to_rows(form: dict[str, object], answers_payload):
    fields = form.get("fields") if isinstance(form.get("fields"), list) else []
    answers_list = answers_payload if isinstance(answers_payload, list) else []
    answer_map = {}
    for item in answers_list:
        if not isinstance(item, dict):
            continue
        field_id = str(item.get("fieldId") or item.get("field_id") or "").strip()
        if not field_id:
            continue
        answer_map[field_id] = item.get("value")

    normalized_answers: list[dict[str, object]] = []
    for field in fields:
        if not isinstance(field, dict):
            continue
        field_id = str(field.get("id") or "").strip()
        field_label = str(field.get("label") or field_id or "Pertanyaan").strip()
        field_type = str(field.get("type") or "text").strip().lower()
        value = answer_map.get(field_id)

        # Upload Lampiran (Tambahan handling lampiran pada saat visitor isi form)
        if field_type == "file":
             # Value dari client adalah list url jika input type file (seperti attachment)
             if isinstance(value, list):
                 normalized_value = [str(item).strip() for item in value if str(item).strip()]
             elif value in (None, ""):
                 normalized_value = []
             else:
                 normalized_value = [str(value).strip()]
             if field.get("required") and not normalized_value:
                 return None, f'Mohon isi/upload: {field_label}'

        elif field_type == "checkbox":
            if isinstance(value, list):
                normalized_value = [str(item).strip() for item in value if str(item).strip()]
            elif value in (None, ""):
                normalized_value = []
            else:
                normalized_value = [str(value).strip()]
            if field.get("required") and not normalized_value:
                return None, f'Mohon isi: {field_label}'
        else:
            normalized_value = str(value or "").strip()
            if field.get("required") and not normalized_value:
                return None, f'Mohon isi: {field_label}'

        normalized_answers.append({
            "fieldId": field_id,
            "label": field_label,
            "type": field_type,
            "value": normalized_value,
        })

    return normalized_answers, None


def read_members_for_admin() -> list[dict[str, object]]:
    # Khusus halaman admin/manajemen anggota, sinkronkan dulu request nonaktif
    # yang sudah approved agar tabel anggota tidak menampilkan status stale.
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        repair_effective_membership_statuses_for_admin(cursor)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"[WARN] Failed to repair membership status before admin read: {exc}")
    finally:
        cursor.close()
        conn.close()
    return read_member_rows()



def _session_actor_id() -> int | None:
    try:
        return int(session.get("user_id"))
    except (TypeError, ValueError):
        return None


def _member_action_allowed(actor_role: str, actor_id: int | None, target_role: str, target_id: int | None, action: str, requested_role: str | None = None) -> tuple[bool, str]:
    actor_role = normalize_role_value(actor_role)
    target_role = normalize_role_value(target_role)
    requested_role = normalize_role_value(requested_role or target_role)
    is_self = actor_id is not None and target_id is not None and int(actor_id) == int(target_id)

    if actor_role == "super_admin":
        if action == "delete" and is_self:
            return False, "Super Admin tidak dapat menghapus akunnya sendiri. Gunakan Super Admin lain jika akun ini perlu dihapus."
        return True, ""

    if actor_role == "admin":
        if action == "create":
            if requested_role == "super_admin":
                return False, "Admin biasa tidak dapat membuat akun Super Admin."
            return True, ""

        if action == "delete":
            if is_self:
                return False, "Admin tidak dapat menghapus akunnya sendiri."
            if target_role != "user":
                return False, "Admin biasa hanya dapat menghapus akun anggota biasa."
            return True, ""

        if action == "reset":
            if is_self:
                return True, ""
            if target_role != "user":
                return False, "Admin biasa tidak dapat reset password akun Admin atau Super Admin lain."
            return True, ""

        if action == "edit":
            if requested_role == "super_admin":
                return False, "Admin biasa tidak dapat menetapkan role Super Admin."
            if is_self:
                if requested_role != target_role:
                    return False, "Admin biasa tidak dapat mengubah role akunnya sendiri dari halaman ini."
                return True, ""
            if target_role != "user":
                return False, "Admin biasa tidak dapat mengedit akun Admin atau Super Admin lain."
            return True, ""

    return False, "Akses ditolak."


def _password_hash_from_payload(incoming_password: str, existing_hash: str | None, birth_date: str) -> str:
    incoming = normalize_text(incoming_password)
    current_hash = normalize_text(existing_hash)
    if current_hash and (not incoming or incoming == current_hash or incoming.startswith(("scrypt:", "pbkdf2:", "sha256$"))):
        return current_hash
    return hash_member_password(incoming, birth_date)


def sync_members_from_payload(payload: list[dict[str, object]]) -> None:
    ensure_notifications_schema()
    actor_role = normalize_role_value(session.get("role") or "")
    actor_id = _session_actor_id()
    if actor_role not in {"admin", "super_admin"}:
        raise PermissionError("Akses ditolak.")

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")

        ensure_membership_columns(cursor)
        cursor.execute(
            """
            SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun, inactive_until, inactive_from, inactive_type, inactive_reason, inactive_note, created_at, updated_at
            FROM anggota
            """
        )
        existing_rows = cursor.fetchall() or []
        existing_by_id: dict[int, dict[str, object]] = {}
        existing_ids: set[int] = set()
        for row in existing_rows:
            try:
                row_id = int(row.get("id"))
            except (TypeError, ValueError):
                continue
            existing_ids.add(row_id)
            existing_by_id[row_id] = row

        next_id = max(existing_ids) + 1 if existing_ids else 1
        kept_ids: set[int] = set()

        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                continue
            birth_date = normalize_text(item.get("birthDate") or item.get("tanggalLahir"))
            status_value = normalize_status(item.get("status") or item.get("status_akun") or "aktif")
            inactive_until = parse_optional_date(item.get("inactiveUntil") or item.get("inactive_until"))
            inactive_from_value = parse_optional_date(item.get("inactiveFrom") or item.get("inactive_from"))
            inactive_type_value = normalize_text(item.get("inactiveType") or item.get("inactive_type"))
            inactive_reason_value = normalize_text(item.get("inactiveReason") or item.get("inactive_reason"))
            inactive_note_value = normalize_text(item.get("inactiveNote") or item.get("inactive_note"))
            if status_value == "aktif":
                inactive_until = None
                inactive_from_value = None
                inactive_type_value = ""
                inactive_reason_value = ""
                inactive_note_value = ""
            elif status_value == "nonaktif" and not inactive_from_value:
                inactive_from_value = datetime.now().date().isoformat()
            requested_role = normalize_role_value(item.get("role") or "user")
            explicit_status_change = bool(item.get("manualStatusChange") or item.get("_manualStatusChange"))

            raw_id = item.get("id")
            try:
                parsed_id = int(raw_id)
            except (TypeError, ValueError):
                parsed_id = None

            is_existing = parsed_id is not None and parsed_id in existing_by_id
            if is_existing:
                member_id = int(parsed_id)
                existing = existing_by_id[member_id]
                target_role = normalize_role_value(existing.get("role") or "user")
                allowed, message = _member_action_allowed(actor_role, actor_id, target_role, member_id, "edit", requested_role)
                if not allowed:
                    raise PermissionError(message)
                hashed_password = _password_hash_from_payload(
                    normalize_text(item.get("password")),
                    normalize_text(existing.get("password")),
                    birth_date,
                )
            else:
                member_id = parsed_id if parsed_id is not None and parsed_id > 0 else next_id
                while member_id in existing_ids or member_id in kept_ids:
                    member_id = next_id
                    next_id += 1
                allowed, message = _member_action_allowed(actor_role, actor_id, "user", member_id, "create", requested_role)
                if not allowed:
                    raise PermissionError(message)
                hashed_password = hash_member_password(normalize_text(item.get("password")), birth_date)

            # Jika ada pengajuan nonaktif approved yang sedang berlaku, jangan biarkan
            # payload stale dari halaman Manajemen Anggota menimpa status menjadi Aktif.
            # Status Aktif hanya boleh dipakai sebagai aktivasi manual bila perubahan
            # status memang berasal dari submit form edit anggota.
            if is_existing:
                effective_req = _effective_membership_request_for_member(cursor, member_id)
                if effective_req and status_value == "aktif" and not explicit_status_change:
                    status_value = "nonaktif"
                    inactive_from_value = _date_to_iso(effective_req.get("start_date")) or datetime.now().date().isoformat()
                    inactive_until = _date_to_iso(effective_req.get("return_date")) or None
                    inactive_type_value = normalize_text(effective_req.get("inactive_type")) or "permanent"
                    inactive_reason_value = normalize_text(effective_req.get("reason"))
                    inactive_note_value = normalize_text(effective_req.get("note"))

            kept_ids.add(member_id)

            cursor.execute(
                """
                INSERT INTO anggota
                (id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun, inactive_until, inactive_from, inactive_type, inactive_reason, inactive_note, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                  updated_at = IF(
                    NOT (
                      COALESCE(nama, '') = COALESCE(VALUES(nama), '') AND
                      COALESCE(username, '') = COALESCE(VALUES(username), '') AND
                      COALESCE(telp, '') = COALESCE(VALUES(telp), '') AND
                      COALESCE(password, '') = COALESCE(VALUES(password), '') AND
                      COALESCE(role, '') = COALESCE(VALUES(role), '') AND
                      COALESCE(tgl_lahir, '') = COALESCE(VALUES(tgl_lahir), '') AND
                      COALESCE(email, '') = COALESCE(VALUES(email), '') AND
                      COALESCE(alamat, '') = COALESCE(VALUES(alamat), '') AND
                      COALESCE(status_akun, '') = COALESCE(VALUES(status_akun), '') AND
                      COALESCE(inactive_until, '') = COALESCE(VALUES(inactive_until), '') AND
                      COALESCE(inactive_from, '') = COALESCE(VALUES(inactive_from), '') AND
                      COALESCE(inactive_type, '') = COALESCE(VALUES(inactive_type), '') AND
                      COALESCE(inactive_reason, '') = COALESCE(VALUES(inactive_reason), '') AND
                      COALESCE(inactive_note, '') = COALESCE(VALUES(inactive_note), '')
                    ),
                    CURRENT_TIMESTAMP,
                    updated_at
                  ),
                  nama = VALUES(nama),
                  username = VALUES(username),
                  telp = VALUES(telp),
                  password = VALUES(password),
                  role = VALUES(role),
                  tgl_lahir = VALUES(tgl_lahir),
                  email = VALUES(email),
                  alamat = VALUES(alamat),
                  status_akun = VALUES(status_akun),
                  inactive_until = VALUES(inactive_until),
                  inactive_from = VALUES(inactive_from),
                  inactive_type = VALUES(inactive_type),
                  inactive_reason = VALUES(inactive_reason),
                  inactive_note = VALUES(inactive_note)
                """,
                (
                    member_id,
                    normalize_text(item.get("name") or item.get("fullName") or "Anggota"),
                    normalize_text(item.get("username") or item.get("email") or item.get("phone") or f"anggota-{index}"),
                    normalize_text(item.get("phone")),
                    hashed_password,
                    requested_role,
                    birth_date,
                    normalize_text(item.get("email")),
                    normalize_text(item.get("address")),
                    status_value,
                    inactive_until,
                    inactive_from_value,
                    inactive_type_value,
                    inactive_reason_value,
                    inactive_note_value,
                ),
            )

            if requested_role == "admin":
                cursor.execute(
                    """
                    INSERT IGNORE INTO admin_module_permissions
                      (member_id, streaming, inventaris, publikasi, konten, keanggotaan)
                    VALUES (%s, 1, 1, 1, 1, 1)
                    """,
                    (member_id,),
                )
            else:
                cursor.execute("DELETE FROM admin_module_permissions WHERE member_id = %s", (member_id,))

            if not is_existing:
                create_new_member_account_notification(
                    cursor,
                    member_id,
                    full_name=normalize_text(item.get("name") or item.get("fullName") or "Anggota"),
                    username=normalize_text(item.get("username") or item.get("email") or item.get("phone") or f"anggota-{index}"),
                    email_value=normalize_text(item.get("email")),
                    birth_date=birth_date,
                    role_value=requested_role,
                )

            if is_existing:
                previous_status = normalize_status(existing.get("status_akun") or "aktif")
                if previous_status == "nonaktif" and status_value == "aktif" and explicit_status_change:
                    cursor.execute(
                        """
                        UPDATE membership_status_requests
                        SET manual_reactivated_at = COALESCE(manual_reactivated_at, CURRENT_TIMESTAMP),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE member_id = %s
                          AND status = 'approved'
                          AND start_date <= CURDATE()
                          AND (return_date IS NULL OR return_date > CURDATE())
                          AND manual_reactivated_at IS NULL
                        """,
                        (member_id,),
                    )
                    create_notification_once(
                        cursor,
                        "keanggotaan",
                        "Status Keanggotaan Diaktifkan",
                        "Admin telah mengaktifkan kembali status keanggotaan Anda.",
                        "/profil-anggota.html",
                        {"target_user_id": member_id},
                        target_role="user",
                        dedupe_key=f"membership-manual-activate-{member_id}-{int(time.time())}",
                    )
                elif previous_status == "aktif" and status_value == "nonaktif":
                    create_notification_once(
                        cursor,
                        "keanggotaan",
                        "Status Keanggotaan Nonaktif",
                        "Admin telah mengubah status keanggotaan Anda menjadi nonaktif.",
                        "/profil-anggota.html",
                        {"target_user_id": member_id},
                        target_role="user",
                        dedupe_key=f"membership-manual-inactivate-{member_id}-{int(time.time())}",
                    )

        ids_to_delete = sorted(existing_ids - kept_ids)
        for delete_id in ids_to_delete:
            existing = existing_by_id.get(delete_id) or {}
            target_role = normalize_role_value(existing.get("role") or "user")
            allowed, message = _member_action_allowed(actor_role, actor_id, target_role, delete_id, "delete")
            if not allowed:
                raise PermissionError(message)

        if ids_to_delete:
            placeholders = ",".join(["%s"] * len(ids_to_delete))
            cursor.execute(f"DELETE FROM admin_module_permissions WHERE member_id IN ({placeholders})", tuple(ids_to_delete))
            cursor.execute(f"DELETE FROM anggota WHERE id IN ({placeholders})", tuple(ids_to_delete))

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

def normalize_youtube_embed_type(value: str | None) -> str:
    kind = normalize_text(value).lower()
    return "playlist" if kind == "playlist" else "video"


def load_youtube_videos():
    try:
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM `youtube_embeds` WHERE `is_visible`=1 ORDER BY `order_index` ASC")
        rows = cursor.fetchall() or []
        conn.close()
        return [
            {
                "id": r["id"],
                "url": r["url"],
                "type": normalize_youtube_embed_type(r.get("embed_type")),
                "title": r.get("title") or "",
                "order": r["order_index"],
            }
            for r in rows
        ]
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


@app.errorhandler(403)
def forbidden_page(error):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "message": "Akses modul ini tidak diizinkan."}), 403
    return "<h1>403 Forbidden</h1><p>Akses modul ini tidak diizinkan untuk akun Anda.</p>", 403






# ===== Password reset OTP via email =====
def ensure_password_reset_schema(cursor=None) -> None:
    """Buat/upgrade tabel OTP reset password."""
    own_conn = None
    own_cursor = cursor
    if own_cursor is None:
        own_conn = mysql_connection()
        own_cursor = own_conn.cursor()

    own_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `password_reset_otps` (
          `id` varchar(80) NOT NULL,
          `member_id` int(11) NOT NULL,
          `member_email` varchar(255) NOT NULL,
          `identifier` varchar(255) DEFAULT NULL,
          `otp_hash` varchar(255) NOT NULL,
          `reset_token_hash` varchar(255) DEFAULT NULL,
          `expires_at` datetime NOT NULL,
          `resend_available_at` datetime NOT NULL,
          `verified_at` datetime DEFAULT NULL,
          `used_at` datetime DEFAULT NULL,
          `attempts` int(11) NOT NULL DEFAULT 0,
          `request_ip` varchar(80) DEFAULT NULL,
          `user_agent` text DEFAULT NULL,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `idx_password_reset_member` (`member_id`),
          KEY `idx_password_reset_email` (`member_email`),
          KEY `idx_password_reset_expires` (`expires_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    ensure_column(own_cursor, "password_reset_otps", "identifier", "`identifier` varchar(255) DEFAULT NULL")
    ensure_column(own_cursor, "password_reset_otps", "otp_hash", "`otp_hash` varchar(255) NOT NULL")
    ensure_column(own_cursor, "password_reset_otps", "reset_token_hash", "`reset_token_hash` varchar(255) DEFAULT NULL")
    ensure_column(own_cursor, "password_reset_otps", "expires_at", "`expires_at` datetime NOT NULL")
    ensure_column(own_cursor, "password_reset_otps", "resend_available_at", "`resend_available_at` datetime NOT NULL")
    ensure_column(own_cursor, "password_reset_otps", "verified_at", "`verified_at` datetime DEFAULT NULL")
    ensure_column(own_cursor, "password_reset_otps", "used_at", "`used_at` datetime DEFAULT NULL")
    ensure_column(own_cursor, "password_reset_otps", "attempts", "`attempts` int(11) NOT NULL DEFAULT 0")
    ensure_column(own_cursor, "password_reset_otps", "request_ip", "`request_ip` varchar(80) DEFAULT NULL")
    ensure_column(own_cursor, "password_reset_otps", "user_agent", "`user_agent` text DEFAULT NULL")
    ensure_column(own_cursor, "password_reset_otps", "created_at", "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
    ensure_column(own_cursor, "password_reset_otps", "updated_at", "`updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

    if own_conn is not None:
        own_conn.commit()
        own_cursor.close()
        own_conn.close()


def mask_email_address(email_value: str) -> str:
    email_value = normalize_text(email_value)
    if "@" not in email_value:
        return email_value
    local, domain = email_value.split("@", 1)
    if len(local) <= 2:
        masked_local = local[:1] + "*"
    else:
        masked_local = local[:2] + ("*" * max(2, len(local) - 2))
    return f"{masked_local}@{domain}"


def now_utc() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def seconds_until(dt_value) -> int:
    if not dt_value:
        return 0
    if isinstance(dt_value, str):
        try:
            dt_value = datetime.fromisoformat(dt_value)
        except ValueError:
            return 0
    return max(0, int((dt_value - now_utc()).total_seconds()))


def build_reset_otp_email(member: dict[str, object], otp_code: str, expires_at: datetime) -> tuple[str, str, str]:
    site_name = "Crembo Media"
    member_name = normalize_text(member.get("nama")) or normalize_text(member.get("username")) or "Anggota"
    expires_text = expires_at.strftime("%d/%m/%Y %H:%M:%S")
    subject = f"Kode OTP Reset Password - {site_name}"
    text_body = (
        f"Halo {member_name},\n\n"
        "Anda telah meminta reset password akun Crembo Media.\n"
        f"Kode OTP Anda: {otp_code}\n\n"
        f"Kode ini berlaku selama {PASSWORD_RESET_OTP_MINUTES} menit sampai {expires_text} WIB.\n"
        "Jangan berikan kode ini kepada siapa pun. Jika Anda tidak meminta reset password, abaikan email ini.\n\n"
        f"Salam,\nTim {site_name}"
    )
    spaced_otp = " ".join(otp_code)
    html_body = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{html.escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f5f0ef;font-family:Inter,Segoe UI,Arial,sans-serif;color:#1a1a1a;">
  <div style="max-width:620px;margin:0 auto;padding:28px 14px;">
    <div style="background:linear-gradient(135deg,#3a0000,#800000 55%,#a52a2a);border-radius:18px 18px 0 0;padding:24px;color:#fff;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
        <tr>
          <td width="64" style="vertical-align:middle;padding-right:14px;">
            <img src="cid:crembo_logo" alt="Logo Crembo Media" width="58" height="58" style="display:block;width:58px;height:58px;object-fit:contain;border-radius:12px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);padding:4px;">
          </td>
          <td style="vertical-align:middle;">
            <div style="font-size:22px;font-weight:900;letter-spacing:.4px;line-height:1.2;">CREMBO MEDIA</div>
            <div style="margin-top:4px;color:rgba(255,255,255,.82);font-size:13px;">Sistem Informasi Internal Komunitas</div>
          </td>
        </tr>
      </table>
    </div>
    <div style="background:#fff;border:1px solid rgba(128,0,0,.13);border-top:0;border-radius:0 0 18px 18px;padding:28px;box-shadow:0 12px 32px rgba(128,0,0,.13);">
      <h1 style="margin:0 0 8px;font-size:22px;color:#800000;">Kode OTP Reset Password</h1>
      <p style="margin:0 0 18px;line-height:1.7;color:#4a4a4a;">Halo <strong>{html.escape(member_name)}</strong>, gunakan kode OTP berikut untuk melanjutkan proses reset password akun Crembo Media Anda.</p>
      <div style="margin:22px 0;padding:18px;border-radius:14px;background:linear-gradient(135deg,#5c0000,#a00000);text-align:center;color:#fff;">
        <div style="font-size:30px;font-weight:900;letter-spacing:10px;font-family:Consolas,Monaco,monospace;">{html.escape(spaced_otp)}</div>
        <div style="margin-top:8px;font-size:12px;color:rgba(255,255,255,.82);">Berlaku {PASSWORD_RESET_OTP_MINUTES} menit sampai {html.escape(expires_text)} WIB</div>
      </div>
      <div style="border-left:4px solid #d4a017;background:#fff8e1;padding:12px 14px;border-radius:10px;color:#5c3b00;font-size:13px;line-height:1.7;">
        Jangan berikan kode ini kepada siapa pun. Jika Anda tidak meminta reset password, abaikan email ini atau hubungi admin.
      </div>
      <p style="margin:22px 0 0;color:#7a7a7a;font-size:12px;">Email ini dikirim otomatis oleh sistem {html.escape(site_name)}.</p>
    </div>
  </div>
</body>
</html>"""
    return subject, text_body, html_body


def send_email_message(recipient_email: str, recipient_name: str, subject: str, text_body: str, html_body: str) -> None:
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError("SMTP belum dikonfigurasi. Isi SMTP_USERNAME dan SMTP_PASSWORD.")

    # Struktur related -> alternative agar logo bisa tampil inline via CID di Gmail.
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
    msg["To"] = formataddr((recipient_name or recipient_email, recipient_email))

    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(text_body, "plain", "utf-8"))
    alternative.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alternative)

    logo_path = EMAIL_LOGO_PATH
    if logo_path and logo_path.exists() and logo_path.is_file():
        mime_type, _ = mimetypes.guess_type(str(logo_path))
        image_subtype = (mime_type or "image/png").split("/", 1)[-1]
        try:
            with logo_path.open("rb") as logo_file:
                logo_part = MIMEImage(logo_file.read(), _subtype=image_subtype)
            logo_part.add_header("Content-ID", "<crembo_logo>")
            logo_part.add_header("Content-Disposition", "inline", filename=logo_path.name)
            msg.attach(logo_part)
        except Exception as exc:
            # Email tetap dikirim meskipun file logo bermasalah.
            print(f"[WARN] Gagal melampirkan logo email: {exc}")
    else:
        print(f"[WARN] Logo email tidak ditemukan: {logo_path}")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, [recipient_email], msg.as_string())

def create_password_reset_otp(cursor, member: dict[str, object], identifier: str) -> dict[str, object]:
    otp_code = f"{secrets.randbelow(1000000):06d}"
    reset_id = uuid.uuid4().hex
    issued_at = now_utc()
    expires_at = issued_at + timedelta(minutes=PASSWORD_RESET_OTP_MINUTES)
    resend_available_at = issued_at + timedelta(seconds=PASSWORD_RESET_RESEND_SECONDS)

    cursor.execute(
        """
        INSERT INTO `password_reset_otps`
          (`id`, `member_id`, `member_email`, `identifier`, `otp_hash`, `expires_at`, `resend_available_at`, `request_ip`, `user_agent`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            reset_id,
            member.get("id"),
            normalize_text(member.get("email")),
            normalize_text(identifier),
            generate_password_hash(otp_code),
            expires_at,
            resend_available_at,
            request.headers.get("X-Forwarded-For", request.remote_addr or "")[:80],
            (request.headers.get("User-Agent") or "")[:1000],
        ),
    )
    return {
        "reset_id": reset_id,
        "otp": otp_code,
        "expires_at": expires_at,
        "resend_available_at": resend_available_at,
    }


def password_reset_response_payload(reset_id: str, email_value: str, expires_at, resend_available_at, extra: dict[str, object] | None = None) -> dict[str, object]:
    payload = {
        "ok": True,
        "resetId": reset_id,
        "maskedEmail": mask_email_address(email_value),
        "expiresIn": seconds_until(expires_at),
        "resendAfter": seconds_until(resend_available_at),
        "expiresAt": expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at),
        "resendAvailableAt": resend_available_at.isoformat() if hasattr(resend_available_at, "isoformat") else str(resend_available_at),
    }
    if extra:
        payload.update(extra)
    return payload


























def admin_user_row_to_dict(row: dict[str, object]) -> dict[str, object]:
    permissions = permission_row_to_dict(row)
    birth_date = _date_to_iso(row.get("tgl_lahir"))
    status_value = normalize_status(row.get("status_akun") or "aktif")
    return {
        "id": row.get("id"),
        "fullName": row.get("nama") or "Admin",
        "name": row.get("nama") or "Admin",
        "username": row.get("username") or "",
        "loginIdentifier": row.get("username") or "",
        "email": row.get("email") or "",
        "phone": row.get("telp") or "",
        "address": row.get("alamat") or "",
        "birthDate": birth_date,
        "role": "admin",
        "status": "Aktif" if status_value == "aktif" else "Nonaktif",
        "permissions": permissions,
        "createdAt": row.get("created_at").isoformat() if row.get("created_at") else "",
        "updatedAt": row.get("updated_at").isoformat() if row.get("updated_at") else "",
    }

def fetch_admin_users_for_super(cursor) -> list[dict[str, object]]:
    ensure_admin_permissions_schema(cursor)
    cursor.execute(
        """
        SELECT a.id, a.nama, a.username, a.telp, a.role, a.tgl_lahir, a.email, a.alamat,
               a.status_akun, a.created_at, a.updated_at,
               p.streaming, p.inventaris, p.publikasi, p.konten, p.keanggotaan
        FROM anggota a
        LEFT JOIN admin_module_permissions p ON p.member_id = a.id
        WHERE a.role = 'admin'
        ORDER BY a.nama ASC, a.id ASC
        """
    )
    return [admin_user_row_to_dict(row) for row in cursor.fetchall() or []]

def validate_admin_user_payload(payload: dict[str, object], *, existing_id: int | None = None) -> tuple[dict[str, object] | None, str | None]:
    full_name = normalize_text(payload.get("fullName") or payload.get("name"))
    username = normalize_text(payload.get("loginIdentifier") or payload.get("username"))
    email = normalize_text(payload.get("email"))
    phone = normalize_text(payload.get("phone") or payload.get("telp"))
    address = normalize_text(payload.get("address") or payload.get("alamat"))
    birth_date = parse_optional_date(payload.get("birthDate") or payload.get("tanggalLahir"))
    status_value = normalize_status(payload.get("status") or payload.get("status_akun") or "aktif")
    permissions = normalize_admin_permissions(payload.get("permissions"), default_all=False)

    if not full_name:
        return None, "Nama lengkap admin wajib diisi."
    if not username:
        return None, "Login identifier/username wajib diisi."
    if not email:
        return None, "Email admin wajib diisi."
    if not phone:
        return None, "Nomor WhatsApp admin wajib diisi."
    if not address:
        return None, "Alamat admin wajib diisi."
    if not birth_date:
        return None, "Tanggal lahir admin wajib diisi dengan format valid."

    return {
        "full_name": full_name,
        "username": username,
        "email": email,
        "phone": phone,
        "address": address,
        "birth_date": birth_date,
        "status": status_value,
        "permissions": permissions,
    }, None

def ensure_admin_user_unique(cursor, username: str, email: str, phone: str, *, except_id: int | None = None) -> str | None:
    params = [username, email, phone]
    sql = "SELECT id, username, email, telp FROM anggota WHERE (username = %s OR email = %s OR telp = %s)"
    if except_id is not None:
        sql += " AND id <> %s"
        params.append(except_id)
    sql += " LIMIT 1"
    cursor.execute(sql, tuple(params))
    existing = cursor.fetchone()
    if existing:
        return "Username, email, atau nomor WhatsApp sudah digunakan akun lain."
    return None

def upsert_admin_permissions(cursor, member_id: int, permissions: dict[str, bool]) -> None:
    normalized = normalize_admin_permissions(permissions, default_all=False)
    cursor.execute(
        """
        INSERT INTO admin_module_permissions
          (member_id, streaming, inventaris, publikasi, konten, keanggotaan)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          streaming = VALUES(streaming),
          inventaris = VALUES(inventaris),
          publikasi = VALUES(publikasi),
          konten = VALUES(konten),
          keanggotaan = VALUES(keanggotaan),
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            member_id,
            1 if normalized.get("streaming") else 0,
            1 if normalized.get("inventaris") else 0,
            1 if normalized.get("publikasi") else 0,
            1 if normalized.get("konten") else 0,
            1 if normalized.get("keanggotaan") else 0,
        ),
    )




















def render_public_page(template_name: str, **context):
    if not template_exists(template_name):
        abort(404)
    return render_template(template_name, current_user=current_user_context(), **context)









# --- TENTANG CREMBO ENDPOINTS ---









import werkzeug.utils











# --- ORGANIZATION PROFILES ENDPOINTS ---






# --- REGISTRATION FORM ENDPOINTS ---


def registration_form_lookup(cursor, form_id: str, include_counts: bool = False):
    cursor.execute("SELECT * FROM `registration_forms` WHERE `id` = %s LIMIT 1", (form_id,))
    row = cursor.fetchone()
    if not row:
        return None
    submission_count = 0
    if include_counts:
        cursor.execute("SELECT COUNT(*) AS `count` FROM `registration_form_submissions` WHERE `form_id` = %s", (form_id,))
        count_row = cursor.fetchone() or {}
        submission_count = int(count_row.get("count") or 0)
    return registration_form_row_to_dict(row, submission_count)






# Di dalam app.py, cari fungsi create_registration_form()








def registration_export_rows(form: dict[str, object], submissions: list[dict[str, object]]):
    fields = form.get("fields") if isinstance(form.get("fields"), list) else []
    headers = ["No", "Waktu Submit", "Identitas", "Role"] + [str(field.get("label") or "Pertanyaan") for field in fields if isinstance(field, dict)]
    rows = []

    # Format domain utama (Contoh untuk local) Jika dionline sesuaikan URL-nya jika ingin url full
    base_url = PUBLIC_BASE_URL 

    for index, submission in enumerate(submissions, start=1):
        answer_map = {}
        for answer in submission.get("answers") if isinstance(submission.get("answers"), list) else []:
            if not isinstance(answer, dict):
                continue
            answer_map[str(answer.get("fieldId") or "")] = answer.get("value")

        row_values = [
            index,
            submission.get("submittedAt") or "",
            submission.get("submitter", {}).get("identifier") or "",
            submission.get("submitter", {}).get("role") or "public",
        ]
        for field in fields:
            if not isinstance(field, dict):
                continue
            
            value = answer_map.get(str(field.get("id") or ""))
            field_type = str(field.get("type") or "").strip().lower()

            if field_type == "file":
                # Convert path to full URL to make it clickable on PDF/Excel
                if isinstance(value, list):
                    urls = [f"{base_url}{item}" if str(item).startswith("/") else str(item) for item in value]
                    row_values.append(", ".join(urls))
                elif isinstance(value, str) and value.startswith("/"):
                    row_values.append(f"{base_url}{value}")
                else:
                    row_values.append(str(value or ""))
            else:
                if isinstance(value, list):
                    row_values.append(", ".join(str(item) for item in value))
                else:
                    row_values.append(str(value or ""))

        rows.append(row_values)

    return headers, rows


def registration_export_filename(form: dict[str, object], extension: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(form.get("title") or "form-pendaftaran").lower()).strip("-") or "form-pendaftaran"
    return f"pendaftar-{slug}.{extension}"












# --- SEARCH ENDPOINT ---



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











# --- NEWS & CATEGORIES ENDPOINTS ---










# --- EXPORT EXCEL & PDF RIWAYAT PEMINJAMAN ---





















# -----------------------------------------------------------------------------
# Request Tugas Anggota: self-service assignment for Misa Biasa & Misa Besar
# -----------------------------------------------------------------------------

def ensure_task_request_schema(cursor=None) -> None:
    """Pastikan tabel penugasan memiliki metadata untuk request anggota."""
    ensure_streaming_schema()
    ensure_misa_besar_schema()

    owns_connection = cursor is None
    conn = None
    if owns_connection:
        conn = mysql_connection()
        cursor = conn.cursor(buffered=True)

    try:
        ensure_column(cursor, "streaming_assignments", "created_at", "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
        ensure_column(cursor, "streaming_assignments", "request_source", "`request_source` varchar(30) NOT NULL DEFAULT 'admin'")
        ensure_column(cursor, "misa_besar_assignments", "created_at", "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
        ensure_column(cursor, "misa_besar_assignments", "request_source", "`request_source` varchar(30) NOT NULL DEFAULT 'admin'")
        if conn:
            conn.commit()
    finally:
        if owns_connection:
            cursor.close()
            conn.close()


def require_active_request_member(cursor):
    if not session.get("logged_in"):
        return None, (jsonify({"success": False, "error": "Anda harus login terlebih dahulu."}), 401)

    user_id = session.get("user_id")
    if not user_id:
        return None, (jsonify({"success": False, "error": "Sesi tidak valid."}), 401)

    cursor.execute(
        """
        SELECT id, nama, role, status_akun
        FROM anggota
        WHERE id = %s
        LIMIT 1
        """,
        (user_id,),
    )
    member = cursor.fetchone()
    if not member:
        return None, (jsonify({"success": False, "error": "Akun anggota tidak ditemukan."}), 404)

    if normalize_role_value(member.get("role") or "user") != "user":
        return None, (jsonify({"success": False, "error": "Halaman request tugas hanya untuk anggota biasa."}), 403)

    if normalize_status(member.get("status_akun") or "aktif") != "aktif":
        return None, (jsonify({"success": False, "error": "Akun Anda sedang nonaktif."}), 403)

    member["id"] = str(member.get("id"))
    member["name"] = normalize_text(member.get("nama")) or "Anggota"
    return member, None


def request_task_is_past(date_text: str, time_text: str = "00:00") -> bool:
    try:
        schedule_dt = datetime.strptime(f"{date_text} {format_time_hhmm(time_text)}", "%Y-%m-%d %H:%M")
        return schedule_dt < datetime.now()
    except Exception:
        try:
            return datetime.strptime(date_text, "%Y-%m-%d").date() < datetime.now().date()
        except Exception:
            return False


def request_task_day_name(date_text: str) -> str:
    try:
        return DAYS_INDO[datetime.strptime(date_text, "%Y-%m-%d").weekday()]
    except Exception:
        return "-"


def request_task_format_date(date_text: str) -> str:
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return normalize_text(date_text) or "-"


def request_task_schedule_key(kind: str, date_text: str, time_text: str, misa_id: object | None = None) -> str:
    if kind == "besar":
        return f"besar:{misa_id}"
    return f"biasa:{date_text}:{format_time_hhmm(time_text)}"


def request_task_get_regular_cfg(cursor, date_text: str, time_text: str):
    day_name = request_task_day_name(date_text)
    cursor.execute(
        """
        SELECT mass_name, day_name, DATE_FORMAT(start_time, '%H:%i') AS start_time
        FROM streaming_weekly_config
        WHERE day_name = %s AND DATE_FORMAT(start_time, '%H:%i') = %s
        LIMIT 1
        """,
        (day_name, format_time_hhmm(time_text)),
    )
    return cursor.fetchone()


def request_task_regular_slot_blocked(cursor, date_text: str, time_text: str) -> str:
    time_text = format_time_hhmm(time_text)
    cursor.execute(
        """
        SELECT 1 FROM streaming_cancelled
        WHERE mass_date = %s AND DATE_FORMAT(mass_time, '%H:%i') = %s
        LIMIT 1
        """,
        (date_text, time_text),
    )
    if cursor.fetchone():
        return "Jadwal ditiadakan."

    cursor.execute(
        """
        SELECT misa_name FROM misa_besar
        WHERE status = 'published'
          AND misa_date = %s
          AND DATE_FORMAT(misa_time, '%H:%i') = %s
        LIMIT 1
        """,
        (date_text, time_text),
    )
    row = cursor.fetchone()
    if row:
        return f"Bentrok dengan Misa Besar: {normalize_text(row.get('misa_name')) or 'Misa Besar'}."
    return ""


def request_task_fetch_roles(cursor) -> list[str]:
    cursor.execute("SELECT role_name AS name FROM streaming_roles ORDER BY order_index ASC, id ASC")
    return [normalize_text(row.get("name")) for row in (cursor.fetchall() or []) if normalize_text(row.get("name"))]


def request_task_regular_items(cursor, month: int, year: int, member_id: str) -> list[dict[str, object]]:
    roles = request_task_fetch_roles(cursor)
    cursor.execute("SELECT day_name, mass_name, DATE_FORMAT(start_time, '%H:%i') AS start_time FROM streaming_weekly_config ORDER BY start_time ASC, id ASC")
    weekly_configs = cursor.fetchall() or []

    cursor.execute(
        """
        SELECT DATE_FORMAT(schedule_date, '%Y-%m-%d') AS schedule_date,
               DATE_FORMAT(schedule_time, '%H:%i') AS schedule_time,
               role_name, member_id, COALESCE(a.nama, CONCAT('ID ', sa.member_id)) AS member_name
        FROM streaming_assignments sa
        LEFT JOIN anggota a ON a.id = sa.member_id
        WHERE MONTH(schedule_date) = %s AND YEAR(schedule_date) = %s
        """,
        (month, year),
    )
    assignments: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
    for row in cursor.fetchall() or []:
        key = (row.get("schedule_date"), format_time_hhmm(row.get("schedule_time")))
        assignments.setdefault(key, {})[normalize_text(row.get("role_name"))] = {
            "memberId": str(row.get("member_id") or ""),
            "memberName": normalize_text(row.get("member_name")),
        }

    items: list[dict[str, object]] = []
    num_days = calendar.monthrange(year, month)[1]
    for day in range(1, num_days + 1):
        date_obj = datetime(year, month, day)
        date_text = date_obj.strftime("%Y-%m-%d")
        day_name = DAYS_INDO[date_obj.weekday()]
        for cfg in weekly_configs:
            if normalize_text(cfg.get("day_name")) != day_name:
                continue
            time_text = format_time_hhmm(cfg.get("start_time"))
            blocked_reason = request_task_regular_slot_blocked(cursor, date_text, time_text)
            if blocked_reason:
                continue

            key = (date_text, time_text)
            slot_assignments = assignments.get(key, {})
            role_details = []
            open_roles = []
            current_user_roles = []
            for role_name in roles:
                assigned = slot_assignments.get(role_name) or {}
                member_id_text = normalize_text(assigned.get("memberId"))
                member_name = normalize_text(assigned.get("memberName"))
                filled = bool(member_id_text)
                if not filled:
                    open_roles.append({"role": role_name})
                elif member_id and str(member_id) == member_id_text:
                    current_user_roles.append(role_name)
                role_details.append({
                    "role": role_name,
                    "filled": filled,
                    "memberId": member_id_text,
                    "memberName": member_name,
                })

            is_past = request_task_is_past(date_text, time_text)
            is_current_user_assigned = bool(current_user_roles)
            can_request = bool(open_roles) and not is_current_user_assigned and not is_past
            status_label = "Terbuka" if can_request else "Tertutup"
            if is_current_user_assigned:
                reason = "Anda sudah bertugas di jadwal ini."
            elif is_past:
                reason = "Jadwal sudah lewat."
            elif not open_roles:
                reason = "Semua role sudah terisi."
            else:
                reason = "Masih ada role kosong."

            items.append({
                "id": request_task_schedule_key("biasa", date_text, time_text),
                "type": "biasa",
                "typeLabel": "Misa Biasa",
                "misaName": normalize_text(cfg.get("mass_name")) or "Misa Biasa",
                "date": date_text,
                "dateLabel": request_task_format_date(date_text),
                "dayName": day_name,
                "time": time_text,
                "roles": role_details,
                "openRoles": open_roles,
                "currentUserRoles": current_user_roles,
                "isCurrentUserAssigned": is_current_user_assigned,
                "canRequest": can_request,
                "status": status_label,
                "statusReason": reason,
            })

    items.sort(key=lambda item: (item.get("date"), item.get("time")))
    return items


def request_task_big_items(cursor, month: int, year: int, member_id: str) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT id, misa_name, DATE_FORMAT(misa_date, '%Y-%m-%d') AS misa_date,
               DATE_FORMAT(misa_time, '%H:%i') AS misa_time, misa_note,
               allow_member_request, status
        FROM misa_besar
        WHERE status = 'published' AND MONTH(misa_date) = %s AND YEAR(misa_date) = %s
        ORDER BY misa_date ASC, misa_time ASC, id ASC
        """,
        (month, year),
    )
    events = cursor.fetchall() or []
    items: list[dict[str, object]] = []
    for event in events:
        misa_id = event.get("id")
        cursor.execute(
            """
            SELECT n.id AS role_id, n.role_name, n.required_count,
                   a.member_id, COALESCE(ag.nama, CONCAT('ID ', a.member_id)) AS member_name
            FROM misa_besar_names n
            LEFT JOIN misa_besar_assignments a ON a.role_id = n.id
            LEFT JOIN anggota ag ON ag.id = a.member_id
            WHERE n.misa_id = %s
            ORDER BY n.id ASC, a.id ASC
            """,
            (misa_id,),
        )
        grouped: dict[str, dict[str, object]] = {}
        for row in cursor.fetchall() or []:
            role_id = str(row.get("role_id") or "")
            if not role_id:
                continue
            if role_id not in grouped:
                grouped[role_id] = {
                    "roleId": role_id,
                    "role": normalize_text(row.get("role_name")) or "Role",
                    "requiredCount": max(1, parse_required_int(row.get("required_count"), 1)),
                    "members": [],
                }
            if row.get("member_id") not in (None, ""):
                grouped[role_id]["members"].append({
                    "memberId": str(row.get("member_id")),
                    "memberName": normalize_text(row.get("member_name")),
                })

        role_details = []
        open_roles = []
        current_user_roles = []
        for role in grouped.values():
            members = role.get("members") or []
            filled_count = len(members)
            required_count = max(1, parse_required_int(role.get("requiredCount"), 1))
            empty_count = max(required_count - filled_count, 0)
            for member_row in members:
                if member_id and str(member_row.get("memberId")) == str(member_id):
                    current_user_roles.append(normalize_text(role.get("role")) or "Role")
            if empty_count > 0:
                open_roles.append({
                    "role": normalize_text(role.get("role")) or "Role",
                    "roleId": role.get("roleId"),
                    "emptyCount": empty_count,
                })
            role_details.append({
                "roleId": role.get("roleId"),
                "role": normalize_text(role.get("role")) or "Role",
                "requiredCount": required_count,
                "filledCount": filled_count,
                "emptyCount": empty_count,
                "members": members,
            })

        date_text = normalize_text(event.get("misa_date"))
        time_text = format_time_hhmm(event.get("misa_time"))
        allow_request = bool(event.get("allow_member_request"))
        is_past = request_task_is_past(date_text, time_text)
        is_current_user_assigned = bool(current_user_roles)
        can_request = allow_request and bool(open_roles) and not is_current_user_assigned and not is_past
        if is_current_user_assigned:
            reason = "Anda sudah bertugas di misa ini."
        elif is_past:
            reason = "Jadwal sudah lewat."
        elif not allow_request:
            reason = "Request ditutup admin."
        elif not open_roles:
            reason = "Semua role sudah terisi."
        else:
            reason = "Masih ada role kosong."

        items.append({
            "id": request_task_schedule_key("besar", date_text, time_text, misa_id),
            "type": "besar",
            "typeLabel": "Misa Besar",
            "misaId": misa_id,
            "misaName": normalize_text(event.get("misa_name")) or "Misa Besar",
            "date": date_text,
            "dateLabel": request_task_format_date(date_text),
            "dayName": request_task_day_name(date_text),
            "time": time_text,
            "note": normalize_text(event.get("misa_note")),
            "allowMemberRequest": allow_request,
            "roles": role_details,
            "openRoles": open_roles,
            "currentUserRoles": current_user_roles,
            "isCurrentUserAssigned": is_current_user_assigned,
            "canRequest": can_request,
            "status": "Terbuka" if can_request else "Tertutup",
            "statusReason": reason,
        })
    return items










# -----------------------------------------------------------------------------
# Riwayat Tugas Saya: histori tugas anggota dari jadwal Misa Biasa & Misa Besar
# -----------------------------------------------------------------------------




# -----------------------------------------------------------------------------
# Pembatalan Tugas Anggota: self-service cancel assignment H-3
# -----------------------------------------------------------------------------

def ensure_task_cancellation_schema(cursor=None) -> None:
    """Pastikan tabel riwayat pembatalan tugas tersedia."""
    ensure_task_request_schema(cursor)
    ensure_notifications_schema()

    owns_connection = cursor is None
    conn = None
    if owns_connection:
        conn = mysql_connection()
        cursor = conn.cursor(buffered=True)

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `task_cancellations` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `member_id` int(11) NOT NULL,
              `member_name` varchar(255) DEFAULT NULL,
              `kind` varchar(20) NOT NULL,
              `type_label` varchar(50) DEFAULT NULL,
              `misa_id` int(11) DEFAULT NULL,
              `role_id` int(11) DEFAULT NULL,
              `assignment_id` int(11) DEFAULT NULL,
              `schedule_date` date NOT NULL,
              `schedule_time` time NOT NULL,
              `misa_name` varchar(255) DEFAULT NULL,
              `role_name` varchar(100) DEFAULT NULL,
              `request_source` varchar(30) DEFAULT NULL,
              `cancelled_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              `status` varchar(30) NOT NULL DEFAULT 'batal',
              `note` text DEFAULT NULL,
              PRIMARY KEY (`id`),
              KEY `idx_task_cancel_member` (`member_id`),
              KEY `idx_task_cancel_date` (`schedule_date`),
              KEY `idx_task_cancel_kind` (`kind`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        # Aman untuk database lama yang sudah pernah dibuat sebelum struktur lengkap.
        ensure_column(cursor, "task_cancellations", "member_name", "`member_name` varchar(255) DEFAULT NULL")
        ensure_column(cursor, "task_cancellations", "type_label", "`type_label` varchar(50) DEFAULT NULL")
        ensure_column(cursor, "task_cancellations", "misa_id", "`misa_id` int(11) DEFAULT NULL")
        ensure_column(cursor, "task_cancellations", "role_id", "`role_id` int(11) DEFAULT NULL")
        ensure_column(cursor, "task_cancellations", "assignment_id", "`assignment_id` int(11) DEFAULT NULL")
        ensure_column(cursor, "task_cancellations", "request_source", "`request_source` varchar(30) DEFAULT NULL")
        ensure_column(cursor, "task_cancellations", "note", "`note` text DEFAULT NULL")
        if conn:
            conn.commit()
    finally:
        if owns_connection:
            cursor.close()
            conn.close()


def cancel_task_can_cancel(date_text: str) -> bool:
    """Boleh dibatalkan maksimal H-3: hari ini <= tanggal tugas - 3 hari."""
    try:
        schedule_date = datetime.strptime(normalize_text(date_text), "%Y-%m-%d").date()
        return schedule_date >= (datetime.now().date() + timedelta(days=3))
    except Exception:
        return False


def cancel_task_rule_label(date_text: str) -> str:
    try:
        schedule_date = datetime.strptime(normalize_text(date_text), "%Y-%m-%d").date()
        deadline = schedule_date - timedelta(days=3)
        return request_task_format_date(deadline.strftime("%Y-%m-%d"))
    except Exception:
        return "-"


def cancel_task_build_item(row: dict[str, object], *, kind: str) -> dict[str, object]:
    date_text = normalize_text(row.get("date") or row.get("schedule_date") or row.get("misa_date"))
    time_text = format_time_hhmm(row.get("time") or row.get("schedule_time") or row.get("misa_time"))
    type_label = "Misa Besar" if kind == "besar" else "Misa Biasa"
    misa_name = normalize_text(row.get("misa_name") or row.get("mass_name")) or type_label
    role_name = normalize_text(row.get("role") or row.get("role_name")) or "Role"
    can_cancel = cancel_task_can_cancel(date_text)
    return {
        "id": f"{kind}:{row.get('assignment_id') or row.get('id') or row.get('role_id') or ''}:{date_text}:{time_text}:{role_name}",
        "type": kind,
        "typeLabel": type_label,
        "assignmentId": row.get("assignment_id") or row.get("id"),
        "misaId": row.get("misa_id"),
        "roleId": row.get("role_id"),
        "misaName": misa_name,
        "date": date_text,
        "dateLabel": request_task_format_date(date_text),
        "dayName": request_task_day_name(date_text),
        "time": time_text,
        "role": role_name,
        "status": "Terdaftar",
        "source": normalize_text(row.get("request_source")) or "admin",
        "sourceLabel": "Request Mandiri" if normalize_text(row.get("request_source")) == "member_request" else "Ditugaskan Admin",
        "canCancel": can_cancel,
        "deadlineLabel": cancel_task_rule_label(date_text),
    }


def cancel_task_filter_items(items: list[dict[str, object]], *, search_text: str = "", kind_filter: str = "all") -> list[dict[str, object]]:
    keyword = normalize_text(search_text).lower()
    kind = (normalize_text(kind_filter) or "all").lower()
    filtered = []
    for item in items:
        if kind in {"biasa", "besar"} and item.get("type") != kind:
            continue
        haystack = " ".join([
            normalize_text(item.get("typeLabel")), normalize_text(item.get("misaName")),
            normalize_text(item.get("dayName")), normalize_text(item.get("dateLabel")),
            normalize_text(item.get("date")), normalize_text(item.get("time")),
            normalize_text(item.get("role")), normalize_text(item.get("status")),
            normalize_text(item.get("sourceLabel")),
        ]).lower()
        if keyword and keyword not in haystack:
            continue
        filtered.append(item)
    return filtered


def cancel_task_sort_items(items: list[dict[str, object]], sort_mode: str, *, history: bool = False) -> list[dict[str, object]]:
    mode = normalize_text(sort_mode) or ("cancelled_desc" if history else "date_asc")

    def schedule_key(item):
        return (normalize_text(item.get("date")), normalize_text(item.get("time")), normalize_text(item.get("misaName")), normalize_text(item.get("role")))

    def cancelled_key(item):
        return normalize_text(item.get("cancelledAt"))

    if mode == "date_desc":
        return sorted(items, key=schedule_key, reverse=True)
    if mode == "cancelled_asc":
        return sorted(items, key=cancelled_key)
    if mode == "cancelled_desc":
        return sorted(items, key=cancelled_key, reverse=True)
    return sorted(items, key=schedule_key)


def cancel_task_paginate(items: list[dict[str, object]], page: int, page_size: int) -> tuple[list[dict[str, object]], dict[str, int]]:
    page = max(1, page)
    page_size = max(1, min(25, page_size))
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    for no, item in enumerate(page_items, start=start + 1):
        item["no"] = no
    return page_items, {"page": page, "pageSize": page_size, "total": total, "totalPages": total_pages}


def cancel_task_notify(cursor, *, member: dict[str, object], item: dict[str, object]) -> None:
    member_id = normalize_text(member.get("id"))
    member_name = normalize_text(member.get("name") or member.get("nama")) or "Anggota"
    type_label = normalize_text(item.get("typeLabel")) or "Jadwal"
    misa_name = normalize_text(item.get("misaName")) or type_label
    role_name = normalize_text(item.get("role")) or "Role"
    day_label = normalize_text(item.get("dayName")) or request_task_day_name(item.get("date"))
    date_label = normalize_text(item.get("dateLabel")) or request_task_format_date(item.get("date"))
    time_text = format_time_hhmm(item.get("time"))
    safe_member = html.escape(member_name)
    safe_type = html.escape(type_label)
    safe_misa = html.escape(misa_name)
    safe_role = html.escape(role_name)
    safe_day = html.escape(day_label)
    safe_date = html.escape(date_label)
    safe_time = html.escape(time_text)

    admin_body = (
        f"<b>{safe_member}</b> membatalkan tugas sebagai <b>{safe_role}</b> pada "
        f"<b>{safe_type} - {safe_misa}</b>, hari {safe_day}, {safe_date} jam {safe_time} WIB."
    )
    create_notification(
        cursor,
        "tugas",
        f"Pembatalan Tugas: {member_name}",
        admin_body,
        "/dashboard.html",
        {
            "notification_kind": "task_cancelled_by_member",
            "member_id": member_id,
            "member_name": member_name,
            "misa_type": item.get("type"),
            "misa_name": misa_name,
            "role": role_name,
            "misa_date": item.get("date"),
            "misa_time": time_text,
        },
        target_role="admin",
    )

    user_body = (
        f"Tugas Anda sebagai <b>{safe_role}</b> untuk <b>{safe_type} - {safe_misa}</b> "
        f"pada hari {safe_day}, {safe_date} jam {safe_time} WIB telah berhasil dibatalkan."
    )
    create_notification(
        cursor,
        "tugas",
        f"Tugas Dibatalkan: {role_name}",
        user_body,
        "/pembatalan-tugas-anggota.html",
        {
            "target_user_id": member_id,
            "notification_kind": "task_cancelled_success",
            "misa_type": item.get("type"),
            "misa_name": misa_name,
            "role": role_name,
            "misa_date": item.get("date"),
            "misa_time": time_text,
        },
        target_role="user",
    )


def cancel_task_insert_history(cursor, *, member: dict[str, object], item: dict[str, object]) -> None:
    cursor.execute(
        """
        INSERT INTO task_cancellations
          (member_id, member_name, kind, type_label, misa_id, role_id, assignment_id,
           schedule_date, schedule_time, misa_name, role_name, request_source, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'batal')
        """,
        (
            member.get("id"), member.get("name") or member.get("nama"), item.get("type"), item.get("typeLabel"),
            item.get("misaId"), item.get("roleId"), item.get("assignmentId"), item.get("date"),
            format_time_hhmm(item.get("time")), item.get("misaName"), item.get("role"), item.get("source"),
        ),
    )









# -----------------------------------------------------------------------------
# Penukaran Jadwal Tugas Anggota: tukeran / pengganti tugas
# -----------------------------------------------------------------------------

def ensure_task_exchange_schema(cursor=None) -> None:
    ensure_task_request_schema(cursor)
    ensure_notifications_schema()
    owns_connection = cursor is None
    conn = None
    if owns_connection:
        conn = mysql_connection()
        cursor = conn.cursor(buffered=True)
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `task_exchange_requests` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `requester_id` varchar(50) NOT NULL,
              `target_user_id` varchar(50) NOT NULL,
              `kind` varchar(20) NOT NULL DEFAULT 'biasa',
              `request_mode` varchar(30) NOT NULL DEFAULT 'swap',
              `my_assignment_id` int(11) DEFAULT NULL,
              `my_misa_id` int(11) DEFAULT NULL,
              `my_role_id` int(11) DEFAULT NULL,
              `my_type_label` varchar(80) DEFAULT NULL,
              `my_misa_name` varchar(255) DEFAULT NULL,
              `my_role_name` varchar(255) DEFAULT NULL,
              `my_schedule_date` date DEFAULT NULL,
              `my_schedule_time` time DEFAULT NULL,
              `target_assignment_id` int(11) DEFAULT NULL,
              `target_misa_id` int(11) DEFAULT NULL,
              `target_role_id` int(11) DEFAULT NULL,
              `target_type_label` varchar(80) DEFAULT NULL,
              `target_misa_name` varchar(255) DEFAULT NULL,
              `target_role_name` varchar(255) DEFAULT NULL,
              `target_schedule_date` date DEFAULT NULL,
              `target_schedule_time` time DEFAULT NULL,
              `reason` text DEFAULT NULL,
              `status` varchar(30) NOT NULL DEFAULT 'pending',
              `response_note` text DEFAULT NULL,
              `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              `responded_at` datetime DEFAULT NULL,
              `cancelled_at` datetime DEFAULT NULL,
              `auto_cancelled_at` datetime DEFAULT NULL,
              PRIMARY KEY (`id`),
              KEY `idx_exchange_requester` (`requester_id`),
              KEY `idx_exchange_target` (`target_user_id`),
              KEY `idx_exchange_status` (`status`),
              KEY `idx_exchange_my_date` (`my_schedule_date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        for col, definition in {
            "request_mode": "`request_mode` varchar(30) NOT NULL DEFAULT 'swap'",
            "my_assignment_id": "`my_assignment_id` int(11) DEFAULT NULL",
            "my_misa_id": "`my_misa_id` int(11) DEFAULT NULL",
            "my_role_id": "`my_role_id` int(11) DEFAULT NULL",
            "my_type_label": "`my_type_label` varchar(80) DEFAULT NULL",
            "my_misa_name": "`my_misa_name` varchar(255) DEFAULT NULL",
            "my_role_name": "`my_role_name` varchar(255) DEFAULT NULL",
            "my_schedule_date": "`my_schedule_date` date DEFAULT NULL",
            "my_schedule_time": "`my_schedule_time` time DEFAULT NULL",
            "target_assignment_id": "`target_assignment_id` int(11) DEFAULT NULL",
            "target_misa_id": "`target_misa_id` int(11) DEFAULT NULL",
            "target_role_id": "`target_role_id` int(11) DEFAULT NULL",
            "target_type_label": "`target_type_label` varchar(80) DEFAULT NULL",
            "target_misa_name": "`target_misa_name` varchar(255) DEFAULT NULL",
            "target_role_name": "`target_role_name` varchar(255) DEFAULT NULL",
            "target_schedule_date": "`target_schedule_date` date DEFAULT NULL",
            "target_schedule_time": "`target_schedule_time` time DEFAULT NULL",
            "response_note": "`response_note` text DEFAULT NULL",
            "responded_at": "`responded_at` datetime DEFAULT NULL",
            "cancelled_at": "`cancelled_at` datetime DEFAULT NULL",
            "auto_cancelled_at": "`auto_cancelled_at` datetime DEFAULT NULL",
        }.items():
            ensure_column(cursor, "task_exchange_requests", col, definition)
        if conn:
            conn.commit()
    finally:
        if owns_connection:
            cursor.close()
            conn.close()


def exchange_current_member(cursor, *, require_active: bool = True):
    if not session.get("logged_in"):
        return None, (jsonify({"success": False, "error": "Anda harus login terlebih dahulu."}), 401)
    user_id = session.get("user_id")
    if not user_id:
        return None, (jsonify({"success": False, "error": "Sesi tidak valid."}), 401)
    cursor.execute(
        """
        SELECT id, nama, role, status_akun
        FROM anggota
        WHERE id = %s
        LIMIT 1
        """,
        (user_id,),
    )
    member = cursor.fetchone()
    if not member:
        return None, (jsonify({"success": False, "error": "Akun tidak ditemukan."}), 404)
    if require_active and normalize_status(member.get("status_akun") or "aktif") != "aktif":
        return None, (jsonify({"success": False, "error": "Akun Anda sedang nonaktif."}), 403)
    member["id"] = str(member.get("id"))
    member["name"] = normalize_text(member.get("nama")) or "Anggota"
    member["roleNormalized"] = normalize_role_value(member.get("role") or "user")
    return member, None


def exchange_date_is_eligible(date_text: str) -> bool:
    """Penukaran hanya bisa untuk jadwal besok atau setelahnya; hari-H tidak bisa."""
    try:
        return datetime.strptime(normalize_text(date_text), "%Y-%m-%d").date() > datetime.now().date()
    except Exception:
        return False


def exchange_status_label(status: str) -> str:
    return {
        "pending": "Menunggu",
        "accepted": "Diterima",
        "rejected": "Ditolak",
        "cancelled": "Dibatalkan",
        "auto_cancelled": "Batal Otomatis",
    }.get(normalize_text(status).lower(), normalize_text(status) or "Menunggu")


def exchange_mode_label(mode: str) -> str:
    return "Menggantikan" if normalize_text(mode).lower() in {"substitute", "menggantikan"} else "Tukeran"


def exchange_kind_label(kind: str) -> str:
    return "Misa Besar" if normalize_text(kind).lower() == "besar" else "Misa Biasa"


def exchange_member_role_for_target(cursor, member_id: object) -> str:
    cursor.execute("SELECT role FROM anggota WHERE id = %s LIMIT 1", (member_id,))
    row = cursor.fetchone()
    return normalize_role_value((row or {}).get("role") or "user") if isinstance(row, dict) else "user"


def exchange_task_label_from_parts(name: str, date_text: str, time_text: str, role: str) -> str:
    return f"{normalize_text(name) or 'Misa'} - {request_task_day_name(date_text)}, {request_task_format_date(date_text)} {format_time_hhmm(time_text)} WIB ({normalize_text(role) or 'Role'})"


def exchange_format_row(row: dict[str, object]) -> dict[str, object]:
    date_text = normalize_text(row.get("date") or row.get("schedule_date") or row.get("my_schedule_date"))
    time_text = format_time_hhmm(row.get("time") or row.get("schedule_time") or row.get("my_schedule_time"))
    kind = normalize_text(row.get("kind") or row.get("type") or "biasa").lower()
    type_label = normalize_text(row.get("type_label") or row.get("typeLabel")) or exchange_kind_label(kind)
    misa_name = normalize_text(row.get("misa_name") or row.get("mass_name") or row.get("misaName")) or type_label
    role = normalize_text(row.get("role") or row.get("role_name") or row.get("roleName")) or "Role"
    member_id = normalize_text(row.get("member_id") or row.get("memberId"))
    member_name = normalize_text(row.get("member_name") or row.get("memberName")) or "Anggota"
    assignment_id = row.get("assignment_id") or row.get("assignmentId")
    return {
        "assignmentId": assignment_id,
        "id": f"{kind}:{assignment_id}",
        "type": kind,
        "typeLabel": type_label,
        "misaId": row.get("misa_id") or row.get("misaId"),
        "roleId": row.get("role_id") or row.get("roleId"),
        "misaName": misa_name,
        "date": date_text,
        "dateLabel": request_task_format_date(date_text),
        "dayName": request_task_day_name(date_text),
        "time": time_text,
        "role": role,
        "memberId": member_id,
        "memberName": member_name,
        "label": exchange_task_label_from_parts(misa_name, date_text, time_text, role),
    }


def exchange_fetch_assignment(cursor, *, kind: str, assignment_id: object | None = None, member_id: object | None = None, for_update: bool = False) -> dict[str, object] | None:
    clean_kind = normalize_text(kind).lower()
    lock_clause = " FOR UPDATE" if for_update else ""
    params: list[object] = []
    if clean_kind == "besar":
        where_parts = []
        if assignment_id is not None:
            where_parts.append("a.id = %s")
            params.append(assignment_id)
        if member_id is not None:
            where_parts.append("a.member_id = %s")
            params.append(member_id)
        if not where_parts:
            return None
        cursor.execute(
            f"""
            SELECT a.id AS assignment_id, a.member_id, COALESCE(mem.nama, CONCAT('ID ', a.member_id)) AS member_name,
                   mb.id AS misa_id, n.id AS role_id, mb.misa_name,
                   DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                   n.role_name AS role, 'besar' AS kind, 'Misa Besar' AS type_label
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            LEFT JOIN anggota mem ON mem.id = a.member_id
            WHERE {' AND '.join(where_parts)} AND mb.status = 'published'
            LIMIT 1{lock_clause}
            """,
            tuple(params),
        )
    else:
        where_parts = []
        if assignment_id is not None:
            where_parts.append("sa.id = %s")
            params.append(assignment_id)
        if member_id is not None:
            where_parts.append("sa.member_id = %s")
            params.append(member_id)
        if not where_parts:
            return None
        cursor.execute(
            f"""
            SELECT sa.id AS assignment_id, sa.member_id, COALESCE(mem.nama, CONCAT('ID ', sa.member_id)) AS member_name,
                   NULL AS misa_id, NULL AS role_id,
                   COALESCE(cfg.mass_name, 'Misa Biasa') AS misa_name,
                   DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                   sa.role_name AS role, 'biasa' AS kind, 'Misa Biasa' AS type_label
            FROM streaming_assignments sa
            LEFT JOIN anggota mem ON mem.id = sa.member_id
            LEFT JOIN streaming_weekly_config cfg
              ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                ELSE 'Minggu' END
              AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            WHERE {' AND '.join(where_parts)}
            LIMIT 1{lock_clause}
            """,
            tuple(params),
        )
    row = cursor.fetchone()
    return exchange_format_row(row) if row else None


def exchange_fetch_user_tasks(cursor, *, member_id: object, kind: str, month: int, year: int) -> list[dict[str, object]]:
    today = datetime.now().date()
    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
    items: list[dict[str, object]] = []
    clean_kind = normalize_text(kind).lower()
    if clean_kind in {"all", "biasa"}:
        cursor.execute(
            """
            SELECT sa.id AS assignment_id, sa.member_id, COALESCE(mem.nama, CONCAT('ID ', sa.member_id)) AS member_name,
                   COALESCE(cfg.mass_name, 'Misa Biasa') AS misa_name,
                   DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                   sa.role_name AS role, 'biasa' AS kind, 'Misa Biasa' AS type_label
            FROM streaming_assignments sa
            LEFT JOIN anggota mem ON mem.id = sa.member_id
            LEFT JOIN streaming_weekly_config cfg
              ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                ELSE 'Minggu' END
              AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            WHERE sa.member_id = %s AND sa.schedule_date BETWEEN %s AND %s AND sa.schedule_date > %s
            ORDER BY sa.schedule_date ASC, sa.schedule_time ASC
            """,
            (member_id, start_date, end_date, today),
        )
        items.extend(exchange_format_row(row) for row in (cursor.fetchall() or []))
    if clean_kind in {"all", "besar"}:
        cursor.execute(
            """
            SELECT a.id AS assignment_id, a.member_id, COALESCE(mem.nama, CONCAT('ID ', a.member_id)) AS member_name,
                   mb.id AS misa_id, n.id AS role_id, mb.misa_name,
                   DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                   n.role_name AS role, 'besar' AS kind, 'Misa Besar' AS type_label
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            LEFT JOIN anggota mem ON mem.id = a.member_id
            WHERE a.member_id = %s AND mb.status = 'published' AND mb.misa_date BETWEEN %s AND %s AND mb.misa_date > %s
            ORDER BY mb.misa_date ASC, mb.misa_time ASC
            """,
            (member_id, start_date, end_date, today),
        )
        items.extend(exchange_format_row(row) for row in (cursor.fetchall() or []))
    items.sort(key=lambda item: (item.get("date") or "", item.get("time") or ""))
    return items


def exchange_fetch_target_tasks(cursor, *, current_member_id: object, kind: str, month: int, year: int) -> list[dict[str, object]]:
    today = datetime.now().date()
    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
    items: list[dict[str, object]] = []
    clean_kind = normalize_text(kind).lower()
    if clean_kind == "biasa":
        cursor.execute(
            """
            SELECT sa.id AS assignment_id, sa.member_id, COALESCE(mem.nama, CONCAT('ID ', sa.member_id)) AS member_name,
                   COALESCE(cfg.mass_name, 'Misa Biasa') AS misa_name,
                   DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                   sa.role_name AS role, 'biasa' AS kind, 'Misa Biasa' AS type_label
            FROM streaming_assignments sa
            JOIN anggota mem ON mem.id = sa.member_id
            LEFT JOIN streaming_weekly_config cfg
              ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                ELSE 'Minggu' END
              AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            WHERE sa.member_id <> %s AND mem.status_akun = 'aktif'
              AND sa.schedule_date BETWEEN %s AND %s AND sa.schedule_date > %s
              AND NOT EXISTS (
                SELECT 1
                FROM streaming_assignments mine
                WHERE mine.member_id = %s
                  AND mine.schedule_date = sa.schedule_date
                  AND DATE_FORMAT(mine.schedule_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
              )
            ORDER BY sa.schedule_date ASC, sa.schedule_time ASC
            """,
            (current_member_id, start_date, end_date, today, current_member_id),
        )
        items.extend(exchange_format_row(row) for row in (cursor.fetchall() or []))
    elif clean_kind == "besar":
        cursor.execute(
            """
            SELECT a.id AS assignment_id, a.member_id, COALESCE(mem.nama, CONCAT('ID ', a.member_id)) AS member_name,
                   mb.id AS misa_id, n.id AS role_id, mb.misa_name,
                   DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                   n.role_name AS role, 'besar' AS kind, 'Misa Besar' AS type_label
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            JOIN anggota mem ON mem.id = a.member_id
            WHERE a.member_id <> %s AND mem.status_akun = 'aktif' AND mb.status = 'published'
              AND mb.misa_date BETWEEN %s AND %s AND mb.misa_date > %s
              AND NOT EXISTS (
                SELECT 1
                FROM misa_besar_assignments mine
                JOIN misa_besar_names mine_role ON mine_role.id = mine.role_id
                WHERE mine.member_id = %s AND mine_role.misa_id = mb.id
              )
            ORDER BY mb.misa_date ASC, mb.misa_time ASC
            """,
            (current_member_id, start_date, end_date, today, current_member_id),
        )
        items.extend(exchange_format_row(row) for row in (cursor.fetchall() or []))
    return items


def exchange_fetch_active_members(cursor, *, exclude_member_id: object | None = None) -> list[dict[str, object]]:
    params: list[object] = []
    where = "WHERE status_akun = 'aktif'"
    if exclude_member_id is not None:
        where += " AND id <> %s"
        params.append(exclude_member_id)
    cursor.execute(
        f"""
        SELECT id, nama, role
        FROM anggota
        {where}
        ORDER BY FIELD(role, 'user', 'admin', 'super_admin'), nama ASC
        """,
        tuple(params),
    )
    results = []
    for row in cursor.fetchall() or []:
        role_value = normalize_role_value(row.get("role") or "user")
        results.append({
            "id": str(row.get("id")),
            "name": normalize_text(row.get("nama")) or f"Anggota {row.get('id')}",
            "role": role_value,
            "roleLabel": "Super Admin" if role_value == "super_admin" else ("Admin" if role_value == "admin" else "Anggota"),
        })
    return results


def exchange_has_pending_for_assignment(cursor, requester_id: object, kind: str, assignment_id: object, exclude_id: object | None = None) -> bool:
    params: list[object] = [str(requester_id), normalize_text(kind).lower(), assignment_id]
    extra = ""
    if exclude_id is not None:
        extra = " AND id <> %s"
        params.append(exclude_id)
    cursor.execute(
        f"""
        SELECT id FROM task_exchange_requests
        WHERE requester_id = %s AND kind = %s AND my_assignment_id = %s AND status = 'pending'{extra}
        LIMIT 1
        """,
        tuple(params),
    )
    return cursor.fetchone() is not None


def exchange_member_already_in_schedule(cursor, *, kind: str, member_id: object, date_text: str, time_text: str, misa_id: object | None = None, exclude_assignment_id: object | None = None) -> bool:
    clean_kind = normalize_text(kind).lower()
    params: list[object] = []
    if clean_kind == "besar":
        where = "a.member_id = %s AND mb.id = %s"
        params = [member_id, misa_id]
        if exclude_assignment_id is not None:
            where += " AND a.id <> %s"
            params.append(exclude_assignment_id)
        cursor.execute(
            f"""
            SELECT a.id FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            WHERE {where}
            LIMIT 1
            """,
            tuple(params),
        )
    else:
        where = "member_id = %s AND schedule_date = %s AND DATE_FORMAT(schedule_time, '%H:%i') = %s"
        params = [member_id, date_text, format_time_hhmm(time_text)]
        if exclude_assignment_id is not None:
            where += " AND id <> %s"
            params.append(exclude_assignment_id)
        cursor.execute(f"SELECT id FROM streaming_assignments WHERE {where} LIMIT 1", tuple(params))
    return cursor.fetchone() is not None




def exchange_schedule_member_ids(cursor, *, kind: str, date_text: str, time_text: str, misa_id: object | None = None) -> list[str]:
    # Return all member IDs assigned in a single misa session, so candidates never create double roles.
    clean_kind = normalize_text(kind).lower()
    if clean_kind == "besar":
        if not misa_id:
            return []
        cursor.execute(
            """
            SELECT DISTINCT a.member_id
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            WHERE n.misa_id = %s AND a.member_id IS NOT NULL
            """,
            (misa_id,),
        )
    else:
        cursor.execute(
            """
            SELECT DISTINCT member_id
            FROM streaming_assignments
            WHERE schedule_date = %s
              AND DATE_FORMAT(schedule_time, '%H:%i') = %s
              AND member_id IS NOT NULL
            """,
            (date_text, format_time_hhmm(time_text)),
        )
    return [str(row.get("member_id")) for row in (cursor.fetchall() or []) if row.get("member_id") is not None]

def exchange_insert_notification(cursor, *, target_user_id: object, target_role: str | None, title: str, body: str, request_id: object, status: str = "pending", url: str | None = None):
    role_norm = normalize_role_value(target_role or exchange_member_role_for_target(cursor, target_user_id))
    return create_notification(
        cursor,
        "tukar",
        title,
        body,
        url,
        {
            "target_user_id": str(target_user_id),
            "exchange_request_id": int(request_id) if str(request_id).isdigit() else request_id,
            "exchange_status": status,
        },
        target_role=role_norm,
    )


def exchange_notify_new_request(cursor, request_row: dict[str, object]):
    target_role = exchange_member_role_for_target(cursor, request_row.get("target_user_id"))
    requester_name = normalize_text(request_row.get("requester_name")) or "Teman"
    mode_label = exchange_mode_label(request_row.get("request_mode"))
    my_label = exchange_task_label_from_parts(request_row.get("my_misa_name"), normalize_text(request_row.get("my_schedule_date")), request_row.get("my_schedule_time"), request_row.get("my_role_name"))
    if normalize_text(request_row.get("request_mode")).lower() in {"substitute", "menggantikan"}:
        title = f"Permintaan Pengganti dari {requester_name}"
        body = f"<b>{html.escape(requester_name)}</b> meminta Anda menggantikan tugas <b>{html.escape(str(request_row.get('my_role_name') or 'Role'))}</b> pada <b>{html.escape(str(request_row.get('my_misa_name') or 'Misa'))}</b>, {html.escape(request_task_day_name(normalize_text(request_row.get('my_schedule_date'))))}, {html.escape(request_task_format_date(normalize_text(request_row.get('my_schedule_date'))))} jam {html.escape(format_time_hhmm(request_row.get('my_schedule_time')))} WIB."
    else:
        target_label = exchange_task_label_from_parts(request_row.get("target_misa_name"), normalize_text(request_row.get("target_schedule_date")), request_row.get("target_schedule_time"), request_row.get("target_role_name"))
        title = f"Permintaan Tukar Jadwal dari {requester_name}"
        body = f"<b>{html.escape(requester_name)}</b> mengajak tukeran jadwal. Jadwal dia: {html.escape(my_label)}. Jadwal Anda: {html.escape(target_label)}."
    url = None if target_role in {"admin", "super_admin"} else "/penukaran-jadwal-tugas-anggota.html"
    exchange_insert_notification(cursor, target_user_id=request_row.get("target_user_id"), target_role=target_role, title=title, body=body, request_id=request_row.get("id"), status="pending", url=url)


def exchange_notify_requester_result(cursor, request_row: dict[str, object], status: str):
    status_label = exchange_status_label(status)
    target_name = normalize_text(request_row.get("target_name")) or "Teman"
    title_map = {
        "accepted": "Penukaran Jadwal Diterima",
        "rejected": "Penukaran Jadwal Ditolak",
        "cancelled": "Penukaran Jadwal Dibatalkan",
        "auto_cancelled": "Penukaran Jadwal Batal Otomatis",
    }
    title = title_map.get(status, f"Status Penukaran: {status_label}")
    my_label = exchange_task_label_from_parts(request_row.get("my_misa_name"), normalize_text(request_row.get("my_schedule_date")), request_row.get("my_schedule_time"), request_row.get("my_role_name"))
    if status == "accepted":
        body = f"Permintaan Anda sudah <b>diterima</b> oleh <b>{html.escape(target_name)}</b>. Jadwal terkait: {html.escape(my_label)}."
    elif status == "rejected":
        body = f"Permintaan Anda <b>ditolak</b> oleh <b>{html.escape(target_name)}</b>. Jadwal terkait: {html.escape(my_label)}."
    elif status == "cancelled":
        body = f"Permintaan penukaran/pengganti untuk jadwal {html.escape(my_label)} sudah dibatalkan."
    else:
        body = f"Permintaan penukaran/pengganti untuk jadwal {html.escape(my_label)} otomatis dibatalkan karena belum direspons sampai hari-H jadwal."
    exchange_insert_notification(cursor, target_user_id=request_row.get("requester_id"), target_role="user", title=title, body=body, request_id=request_row.get("id"), status=status, url="/penukaran-jadwal-tugas-anggota.html")


def exchange_fetch_request_row(cursor, request_id: object, for_update: bool = False) -> dict[str, object] | None:
    lock_clause = " FOR UPDATE" if for_update else ""
    cursor.execute(
        f"""
        SELECT er.*, req.nama AS requester_name, tgt.nama AS target_name,
               req.role AS requester_role, tgt.role AS target_role
        FROM task_exchange_requests er
        LEFT JOIN anggota req ON req.id = er.requester_id
        LEFT JOIN anggota tgt ON tgt.id = er.target_user_id
        WHERE er.id = %s
        LIMIT 1{lock_clause}
        """,
        (request_id,),
    )
    return cursor.fetchone()


def exchange_expire_pending_requests(cursor) -> int:
    today = datetime.now().date()
    cursor.execute(
        """
        SELECT er.*, req.nama AS requester_name, tgt.nama AS target_name,
               req.role AS requester_role, tgt.role AS target_role
        FROM task_exchange_requests er
        LEFT JOIN anggota req ON req.id = er.requester_id
        LEFT JOIN anggota tgt ON tgt.id = er.target_user_id
        WHERE er.status = 'pending' AND er.my_schedule_date <= %s
        """,
        (today,),
    )
    rows = cursor.fetchall() or []
    for row in rows:
        cursor.execute(
            """
            UPDATE task_exchange_requests
            SET status = 'auto_cancelled', auto_cancelled_at = NOW(), updated_at = NOW()
            WHERE id = %s AND status = 'pending'
            """,
            (row.get("id"),),
        )
        row["status"] = "auto_cancelled"
        exchange_notify_requester_result(cursor, row, "auto_cancelled")
        exchange_insert_notification(
            cursor,
            target_user_id=row.get("target_user_id"),
            target_role=row.get("target_role"),
            title="Permintaan Tukar Jadwal Batal Otomatis",
            body="Permintaan tukar/ganti tugas otomatis dibatalkan karena belum direspons sampai hari-H jadwal.",
            request_id=row.get("id"),
            status="auto_cancelled",
            url=None if normalize_role_value(row.get("target_role") or "user") in {"admin", "super_admin"} else "/penukaran-jadwal-tugas-anggota.html",
        )
    return len(rows)


def exchange_request_to_dict(row: dict[str, object], *, direction: str) -> dict[str, object]:
    status = normalize_text(row.get("status") or "pending").lower()
    my_date = normalize_text(row.get("my_schedule_date"))
    target_date = normalize_text(row.get("target_schedule_date"))
    created_at = row.get("created_at")
    responded_at = row.get("responded_at")
    return {
        "id": row.get("id"),
        "direction": direction,
        "type": normalize_text(row.get("kind")) or "biasa",
        "typeLabel": exchange_kind_label(row.get("kind")),
        "mode": normalize_text(row.get("request_mode")) or "swap",
        "modeLabel": exchange_mode_label(row.get("request_mode")),
        "requesterId": str(row.get("requester_id") or ""),
        "requesterName": normalize_text(row.get("requester_name")) or "Anggota",
        "targetUserId": str(row.get("target_user_id") or ""),
        "targetName": normalize_text(row.get("target_name")) or "Teman",
        "myAssignmentId": row.get("my_assignment_id"),
        "targetAssignmentId": row.get("target_assignment_id"),
        "myMisaName": normalize_text(row.get("my_misa_name")),
        "myRole": normalize_text(row.get("my_role_name")),
        "myDate": my_date,
        "myDateLabel": request_task_format_date(my_date),
        "myDayName": request_task_day_name(my_date),
        "myTime": format_time_hhmm(row.get("my_schedule_time")),
        "myLabel": exchange_task_label_from_parts(row.get("my_misa_name"), my_date, row.get("my_schedule_time"), row.get("my_role_name")),
        "targetMisaName": normalize_text(row.get("target_misa_name")),
        "targetRole": normalize_text(row.get("target_role_name")),
        "targetDate": target_date,
        "targetDateLabel": request_task_format_date(target_date),
        "targetDayName": request_task_day_name(target_date),
        "targetTime": format_time_hhmm(row.get("target_schedule_time")),
        "targetLabel": exchange_task_label_from_parts(row.get("target_misa_name"), target_date, row.get("target_schedule_time"), row.get("target_role_name")) if target_date else "-",
        "reason": normalize_text(row.get("reason")),
        "status": status,
        "statusLabel": exchange_status_label(status),
        "canAct": status == "pending" and direction == "incoming" and exchange_date_is_eligible(my_date),
        "canCancel": status == "pending" and direction == "outgoing" and exchange_date_is_eligible(my_date),
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else normalize_text(created_at),
        "createdAtLabel": created_at.strftime("%d/%m/%Y %H:%M") if hasattr(created_at, "strftime") else normalize_text(created_at),
        "respondedAt": responded_at.isoformat() if hasattr(responded_at, "isoformat") else normalize_text(responded_at),
    }


def exchange_filter_requests(items: list[dict[str, object]], search_text: str = "") -> list[dict[str, object]]:
    keyword = normalize_text(search_text).lower()
    if not keyword:
        return items
    filtered = []
    for item in items:
        haystack = " ".join([
            normalize_text(item.get("requesterName")), normalize_text(item.get("targetName")),
            normalize_text(item.get("myLabel")), normalize_text(item.get("targetLabel")),
            normalize_text(item.get("myRole")), normalize_text(item.get("targetRole")),
            normalize_text(item.get("reason")), normalize_text(item.get("statusLabel")),
            normalize_text(item.get("typeLabel")), normalize_text(item.get("modeLabel")),
        ]).lower()
        if keyword in haystack:
            filtered.append(item)
    return filtered


def exchange_paginate(items: list[dict[str, object]], page: int, page_size: int = 5):
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    return items[start:start + page_size], {"page": page, "pageSize": page_size, "total": total, "totalPages": total_pages, "hasPrev": page > 1, "hasNext": page < total_pages}








def exchange_list_requests(*, direction: str):
    ensure_task_exchange_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = exchange_current_member(cursor)
        if error:
            return error
        exchange_expire_pending_requests(cursor)
        conn.commit()
        member_id = member["id"]
        search_text = normalize_text(request.args.get("search"))
        sort_mode = normalize_text(request.args.get("sort")) or "created_desc"
        page = max(1, parse_required_int(request.args.get("page"), 1))
        page_size = max(1, min(25, parse_required_int(request.args.get("pageSize"), 5)))
        status_filter = normalize_text(request.args.get("status")) or "all"
        kind_filter = normalize_text(request.args.get("type")) or "all"
        conditions = ["er.target_user_id = %s" if direction == "incoming" else "er.requester_id = %s"]
        params: list[object] = [member_id]
        if status_filter != "all":
            conditions.append("er.status = %s")
            params.append(status_filter)
        if kind_filter in {"biasa", "besar"}:
            conditions.append("er.kind = %s")
            params.append(kind_filter)
        where_clause = " AND ".join(conditions)
        cursor.execute(
            f"""
            SELECT er.*, req.nama AS requester_name, tgt.nama AS target_name,
                   req.role AS requester_role, tgt.role AS target_role
            FROM task_exchange_requests er
            LEFT JOIN anggota req ON req.id = er.requester_id
            LEFT JOIN anggota tgt ON tgt.id = er.target_user_id
            WHERE {where_clause}
            """,
            tuple(params),
        )
        items = [exchange_request_to_dict(row, direction=direction) for row in (cursor.fetchall() or [])]
        items = exchange_filter_requests(items, search_text)
        if sort_mode == "created_asc":
            items.sort(key=lambda item: item.get("createdAt") or "")
        elif sort_mode == "date_asc":
            items.sort(key=lambda item: (item.get("myDate") or "", item.get("myTime") or ""))
        elif sort_mode == "date_desc":
            items.sort(key=lambda item: (item.get("myDate") or "", item.get("myTime") or ""), reverse=True)
        else:
            items.sort(key=lambda item: item.get("createdAt") or "", reverse=True)
        page_items, pagination = exchange_paginate(items, page, page_size)
        return jsonify({"success": True, "items": page_items, "pagination": pagination})
    finally:
        cursor.close()
        conn.close()











# ---------------------------------------------------------------------------
# Monitoring Tugas Anggota - kewajiban bulanan Misa Biasa saja
# ---------------------------------------------------------------------------

def ensure_monthly_monitoring_schema(cursor) -> None:
    """Schema kecil untuk menyimpan target minimum tugas bulanan.

    Default target minimum disamakan dengan kebutuhan sistem saat ini: 3 tugas
    Misa Biasa per bulan. Jika row default sudah ada, nilainya tidak ditimpa;
    admin tetap bisa mengubahnya dari halaman monitoring admin.
    """
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `monthly_task_settings` (
          `id` varchar(50) NOT NULL,
          `target_minimum` int NOT NULL DEFAULT 3,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    try:
        ensure_column(cursor, "monthly_task_settings", "target_minimum", "`target_minimum` int NOT NULL DEFAULT 3")
    except Exception:
        pass
    cursor.execute(
        """
        INSERT IGNORE INTO `monthly_task_settings` (`id`, `target_minimum`)
        VALUES ('default', 3)
        """
    )
    try:
        ensure_column(cursor, "anggota", "inactive_until", "`inactive_until` date DEFAULT NULL")
    except Exception:
        pass
def monitoring_require_admin():
    if not session.get("logged_in"):
        return jsonify({"success": False, "error": "Anda harus login terlebih dahulu."}), 401
    if normalize_role_value(session.get("role") or "user") not in {"admin", "super_admin"}:
        return jsonify({"success": False, "error": "Akses hanya untuk admin/super admin."}), 403
    return None


def monitoring_get_target_minimum(cursor) -> int:
    """Ambil target minimum bulanan dengan fallback aman.

    Target default sekarang 3. Jika tabel/row belum ada, backend membuat row
    default bernilai 3 agar halaman anggota tidak menampilkan 0/2 lagi.
    """
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `monthly_task_settings` (
              `id` varchar(50) NOT NULL,
              `target_minimum` int NOT NULL DEFAULT 3,
              `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        try:
            ensure_column(cursor, "monthly_task_settings", "target_minimum", "`target_minimum` int NOT NULL DEFAULT 3")
        except Exception:
            pass
        cursor.execute("SELECT target_minimum FROM monthly_task_settings WHERE id = 'default' LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO monthly_task_settings (id, target_minimum) VALUES ('default', 3)")
            return 3
        value = fetch_scalar_value(row, 3)
        return max(1, min(99, parse_required_int(value, 3)))
    except Exception as exc:
        print(f"[WARN] Gagal membaca target minimum monitoring: {exc}")
        return 3
def monitoring_account_role_label(role_value: str) -> str:
    role = normalize_role_value(role_value or "user")
    if role == "super_admin":
        return "Super Admin"
    if role == "admin":
        return "Admin"
    return "Anggota"


def monitoring_is_member_active_for_period(row: dict[str, object], year: int, month: int) -> bool:
    # Saat ini status aktif/nonaktif di database menjadi sumber utama.
    # Jika kolom inactive_until tersedia dan tanggalnya sudah lewat sebelum periode, anggota dianggap aktif lagi.
    status = normalize_status(row.get("status_akun") or "aktif")
    if status == "aktif":
        return True
    inactive_until = row.get("inactive_until")
    if not inactive_until:
        return False
    try:
        if hasattr(inactive_until, "year"):
            until_date = inactive_until
        else:
            until_date = datetime.strptime(str(inactive_until)[:10], "%Y-%m-%d").date()
        period_start = datetime(year, month, 1).date()
        return until_date <= period_start
    except Exception:
        return False


def monitoring_status(total_tasks: int, target_minimum: int) -> tuple[str, str, int]:
    shortage = max(0, int(target_minimum) - int(total_tasks or 0))
    if shortage <= 0:
        return "Aman", "ok", shortage
    if shortage == 1:
        return "Perlu Tambahan", "warn", shortage
    return "Kritis", "danger", shortage


def monitoring_count_regular_assignments(cursor, year: int, month: int) -> dict[int, int]:
    cursor.execute(
        """
        SELECT member_id, COUNT(*) AS total
        FROM streaming_assignments
        WHERE YEAR(schedule_date) = %s AND MONTH(schedule_date) = %s
        GROUP BY member_id
        """,
        (year, month),
    )
    result: dict[int, int] = {}
    for row in cursor.fetchall() or []:
        try:
            result[int(row.get("member_id") if isinstance(row, dict) else row[0])] = int(row.get("total") if isinstance(row, dict) else row[1])
        except Exception:
            continue
    return result


def monitoring_fetch_members(cursor, year: int, month: int) -> list[dict[str, object]]:
    try:
        ensure_column(cursor, "anggota", "inactive_until", "`inactive_until` date DEFAULT NULL")
    except Exception:
        pass
    cursor.execute(
        """
        SELECT id, nama, username, role, status_akun, inactive_until
        FROM anggota
        ORDER BY nama ASC, id ASC
        """
    )
    rows = cursor.fetchall() or []
    active_members: list[dict[str, object]] = []
    for row in rows:
        if not monitoring_is_member_active_for_period(row, year, month):
            continue
        role = normalize_role_value(row.get("role") or "user")
        active_members.append({
            "id": row.get("id"),
            "name": normalize_text(row.get("nama") or row.get("username")) or f"Anggota {row.get('id')}",
            "accountRole": role,
            "accountRoleLabel": monitoring_account_role_label(role),
        })
    return active_members


def monitoring_month_range(year: int, month: int) -> tuple[str, str]:
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}"


def monitoring_regular_slot_conflict(cursor, date_text: str, time_text: str) -> bool:
    time_clean = format_time_hhmm(time_text)
    cursor.execute(
        """
        SELECT 1 FROM streaming_cancelled
        WHERE mass_date = %s AND DATE_FORMAT(mass_time, '%H:%i') = %s
        LIMIT 1
        """,
        (date_text, time_clean),
    )
    if cursor.fetchone():
        return True
    cursor.execute(
        """
        SELECT 1 FROM misa_besar
        WHERE status = 'published' AND misa_date = %s AND DATE_FORMAT(misa_time, '%H:%i') = %s
        LIMIT 1
        """,
        (date_text, time_clean),
    )
    return cursor.fetchone() is not None


def monitoring_open_regular_slots(cursor, year: int, month: int, member_id: object | None = None) -> list[dict[str, object]]:
    """Ambil slot misa biasa yang masih punya role kosong, hanya tanggal setelah hari ini."""
    roles = request_task_fetch_roles(cursor)
    if not roles:
        return []
    cursor.execute(
        """
        SELECT day_name, mass_name, DATE_FORMAT(start_time, '%H:%i') AS start_time
        FROM streaming_weekly_config
        ORDER BY FIELD(day_name, 'Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu'), start_time ASC, id ASC
        """
    )
    configs = cursor.fetchall() or []
    cursor.execute(
        """
        SELECT DATE_FORMAT(schedule_date, '%Y-%m-%d') AS schedule_date,
               DATE_FORMAT(schedule_time, '%H:%i') AS schedule_time,
               role_name, member_id
        FROM streaming_assignments
        WHERE YEAR(schedule_date) = %s AND MONTH(schedule_date) = %s
        """,
        (year, month),
    )
    assignment_map: dict[tuple[str, str], dict[str, str]] = {}
    assigned_members_by_slot: dict[tuple[str, str], set[str]] = {}
    for row in cursor.fetchall() or []:
        key = (normalize_text(row.get("schedule_date")), format_time_hhmm(row.get("schedule_time")))
        assignment_map.setdefault(key, {})[normalize_text(row.get("role_name"))] = str(row.get("member_id") or "")
        assigned_members_by_slot.setdefault(key, set()).add(str(row.get("member_id") or ""))

    today = datetime.now().date()
    items: list[dict[str, object]] = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        date_obj = datetime(year, month, day).date()
        if date_obj <= today:
            continue
        date_text = date_obj.strftime("%Y-%m-%d")
        day_name = DAYS_INDO[date_obj.weekday()]
        for cfg in configs:
            if normalize_text(cfg.get("day_name")) != day_name:
                continue
            time_text = format_time_hhmm(cfg.get("start_time"))
            if monitoring_regular_slot_conflict(cursor, date_text, time_text):
                continue
            key = (date_text, time_text)
            if member_id and str(member_id) in assigned_members_by_slot.get(key, set()):
                # 1 orang hanya boleh 1 role dalam 1 misa/sesi.
                continue
            filled_by_role = assignment_map.get(key, {})
            open_roles = [role for role in roles if not filled_by_role.get(role)]
            if not open_roles:
                continue
            items.append({
                "id": request_task_schedule_key("biasa", date_text, time_text),
                "date": date_text,
                "dateLabel": request_task_format_date(date_text),
                "dayName": day_name,
                "time": time_text,
                "misaName": normalize_text(cfg.get("mass_name")) or "Misa Biasa",
                "openRoles": open_roles,
            })
    items.sort(key=lambda item: (item.get("date"), item.get("time")))
    return items


def monitoring_has_open_future_slots(cursor, year: int, month: int) -> bool:
    return bool(monitoring_open_regular_slots(cursor, year, month, member_id=None))


def monitoring_notification_url_for_role(role_value: str) -> str:
    role = normalize_role_value(role_value or "user")
    if role == "admin":
        return "/jadwal-tugas-streaming-admin.html"
    return "/request-tugas-anggota.html"


def create_monthly_requirement_notifications() -> int:
    """Buat notifikasi target bulanan untuk user/admin biasa, bukan super_admin.

    - H-7 dan H-1 sebelum bulan berikutnya.
    - Harian pada bulan berjalan jika masih kurang dan masih ada slot masa depan yang kosong.
    """
    ensure_auth_schema()
    ensure_streaming_schema()
    ensure_notifications_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    sent = 0
    try:
        ensure_monthly_monitoring_schema(cursor)
        target = monitoring_get_target_minimum(cursor)
        today = datetime.now().date()

        periods: list[tuple[int, int, str, str]] = []
        # Notifikasi harian bulan berjalan.
        periods.append((today.year, today.month, "daily_current", "Pengingat target tugas bulan ini"))
        # H-7 / H-1 untuk bulan berikutnya.
        first_next_month = (datetime(today.year, today.month, 28).date() + timedelta(days=4)).replace(day=1)
        h7_date = first_next_month - timedelta(days=7)
        h1_date = first_next_month - timedelta(days=1)
        if today == h7_date:
            periods.append((first_next_month.year, first_next_month.month, "h7_next_month", "Pengingat H-7 target tugas bulan depan"))
        if today == h1_date:
            periods.append((first_next_month.year, first_next_month.month, "h1_next_month", "Pengingat H-1 target tugas bulan depan"))

        for year, month, code, title in periods:
            if not monitoring_has_open_future_slots(cursor, year, month):
                continue
            counts = monitoring_count_regular_assignments(cursor, year, month)
            members = monitoring_fetch_members(cursor, year, month)
            for member in members:
                role_value = normalize_role_value(member.get("accountRole") or "user")
                if role_value == "super_admin":
                    continue
                total = counts.get(int(member.get("id") or 0), 0)
                shortage = max(0, target - total)
                if shortage <= 0:
                    continue
                month_name = calendar.month_name[month]
                month_label = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"][month]
                body = (
                    f"Target tugas Misa Biasa bulan <b>{html.escape(month_label)} {year}</b> belum terpenuhi. "
                    f"Saat ini Anda memiliki <b>{total}</b> tugas dari target minimum <b>{target}</b>; "
                    f"masih kurang <b>{shortage}</b> tugas. Silakan mengambil/request jadwal yang masih kosong."
                )
                dedupe_day = today.strftime("%Y-%m-%d") if code == "daily_current" else code
                dedupe_key = f"monthly-monitoring:{year}-{month:02d}:{member.get('id')}:{code}:{dedupe_day}:target{target}"
                create_notification_once(
                    cursor,
                    "tugas",
                    title,
                    body,
                    monitoring_notification_url_for_role(role_value),
                    {
                        "target_user_id": str(member.get("id")),
                        "notification_kind": "monthly_task_requirement",
                        "period_year": year,
                        "period_month": month,
                        "target_minimum": target,
                        "current_total": total,
                        "shortage": shortage,
                    },
                    target_role="admin" if role_value == "admin" else "user",
                    dedupe_key=dedupe_key,
                )
                sent += 1
        conn.commit()
        return sent
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()











# ---------------------------------------------------------------------------
# Monitoring Kewajiban Tugas Anggota - statistik personal anggota
# ---------------------------------------------------------------------------

def member_monitoring_current_user(cursor):
    """Ambil user login terbaru dari database untuk halaman monitoring anggota."""
    if not session.get("logged_in"):
        return None, (jsonify({"success": False, "error": "Anda harus login terlebih dahulu."}), 401)
    user_id = session.get("user_id")
    if not user_id:
        return None, (jsonify({"success": False, "error": "Sesi login tidak valid."}), 401)
    cursor.execute(
        """
        SELECT id, nama, username, role, status_akun
        FROM anggota
        WHERE id = %s
        LIMIT 1
        """,
        (user_id,),
    )
    user = cursor.fetchone()
    if not user:
        return None, (jsonify({"success": False, "error": "Akun tidak ditemukan."}), 404)
    if normalize_status(user.get("status_akun") or "aktif") != "aktif":
        return None, (jsonify({"success": False, "error": "Akun Anda sedang nonaktif."}), 403)
    user["id"] = str(user.get("id"))
    user["name"] = normalize_text(user.get("nama") or user.get("username") or "Anggota")
    user["roleNormalized"] = normalize_role_value(user.get("role") or "user")
    user["roleLabel"] = monitoring_account_role_label(user.get("role") or "user")
    return user, None


def member_monitoring_month_name(month: int) -> str:
    month_names = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    try:
        return month_names[int(month) - 1]
    except Exception:
        return "-"


def member_monitoring_period_label(month: str | int, year: str | int) -> str:
    month_text = normalize_text(month)
    year_text = normalize_text(year)
    if month_text.lower() == "all" and year_text.lower() == "all":
        return "Semua Bulan & Semua Tahun"
    if month_text.lower() == "all":
        return f"Semua Bulan {year_text}"
    if year_text.lower() == "all":
        return f"{member_monitoring_month_name(parse_required_int(month_text, 1))} Semua Tahun"
    return f"{member_monitoring_month_name(parse_required_int(month_text, 1))} {year_text}"


def member_monitoring_parse_month(value, default_month: int | None = None) -> str:
    raw = normalize_text(value)
    if raw.lower() == "all":
        return "all"
    if raw == "":
        return str(default_month or datetime.now().month)
    return str(min(12, max(1, parse_required_int(raw, default_month or datetime.now().month))))


def member_monitoring_parse_year(value, default_year: int | None = None) -> str:
    raw = normalize_text(value)
    if raw.lower() == "all":
        return "all"
    if raw == "":
        return str(default_year or datetime.now().year)
    return str(parse_required_int(raw, default_year or datetime.now().year))


def member_monitoring_schedule_dt(date_text: str, time_text: str) -> datetime:
    try:
        return datetime.strptime(f"{normalize_text(date_text)} {format_time_hhmm(time_text)}", "%Y-%m-%d %H:%M")
    except Exception:
        try:
            return datetime.strptime(normalize_text(date_text), "%Y-%m-%d")
        except Exception:
            return datetime(1970, 1, 1)


def member_monitoring_task_item(kind: str, type_label: str, misa_name: str, date_text: str, time_text: str, role_name: str, created_at=None) -> dict[str, object]:
    schedule_dt = member_monitoring_schedule_dt(date_text, time_text)
    is_completed = schedule_dt < datetime.now()
    created_text = created_at.isoformat() if hasattr(created_at, "isoformat") else normalize_text(created_at)
    return {
        "type": kind,
        "typeLabel": type_label,
        "misaName": normalize_text(misa_name) or type_label,
        "date": normalize_text(date_text),
        "dateLabel": request_task_format_date(normalize_text(date_text)),
        "dayName": request_task_day_name(normalize_text(date_text)),
        "time": format_time_hhmm(time_text),
        "role": normalize_text(role_name) or "-",
        "status": "Selesai" if is_completed else "Terjadwal",
        "completed": is_completed,
        "createdAt": created_text,
        "display": f"{normalize_text(misa_name) or type_label} - {request_task_day_name(normalize_text(date_text))}, {request_task_format_date(normalize_text(date_text))} jam {format_time_hhmm(time_text)} WIB",
    }


def member_monitoring_fetch_regular_tasks(cursor, member_id: object, *, month: str = "all", year: str = "all") -> list[dict[str, object]]:
    """Ambil semua tugas Misa Biasa milik anggota secara defensif."""
    try:
        ensure_streaming_schema()
    except Exception as exc:
        print(f"[WARN] ensure_streaming_schema monitoring anggota gagal: {exc}")

    def build_filters(alias: str = "sa"):
        where_parts = [f"{alias}.member_id = %s"]
        params_local: list[object] = [member_id]
        if normalize_text(month).lower() != "all":
            where_parts.append(f"MONTH({alias}.schedule_date) = %s")
            params_local.append(parse_required_int(month, datetime.now().month))
        if normalize_text(year).lower() != "all":
            where_parts.append(f"YEAR({alias}.schedule_date) = %s")
            params_local.append(parse_required_int(year, datetime.now().year))
        return " AND ".join(where_parts), params_local

    rows = []
    where_sql, params = build_filters("sa")
    try:
        cursor.execute(
            f"""
            SELECT DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                   TIME_FORMAT(sa.schedule_time, '%H:%i') AS time,
                   sa.role_name,
                   sa.created_at,
                   COALESCE(cfg.mass_name, 'Misa Biasa') AS mass_name
            FROM streaming_assignments sa
            LEFT JOIN streaming_weekly_config cfg
              ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                ELSE 'Minggu' END
              AND TIME_FORMAT(cfg.start_time, '%H:%i') = TIME_FORMAT(sa.schedule_time, '%H:%i')
            LEFT JOIN streaming_cancelled sc
              ON sc.mass_date = sa.schedule_date
             AND TIME_FORMAT(sc.mass_time, '%H:%i') = TIME_FORMAT(sa.schedule_time, '%H:%i')
            LEFT JOIN misa_besar mb
              ON mb.status = 'published'
             AND mb.misa_date = sa.schedule_date
             AND TIME_FORMAT(mb.misa_time, '%H:%i') = TIME_FORMAT(sa.schedule_time, '%H:%i')
            WHERE {where_sql}
              AND sc.id IS NULL
              AND mb.id IS NULL
            ORDER BY sa.schedule_date ASC, sa.schedule_time ASC, sa.role_name ASC
            """,
            tuple(params),
        )
        rows = cursor.fetchall() or []
    except Exception as exc:
        print(f"[WARN] Query lengkap tugas Misa Biasa gagal, pakai fallback: {exc}")
        try:
            where_sql, params = build_filters("sa")
            cursor.execute(
                f"""
                SELECT DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                       TIME_FORMAT(sa.schedule_time, '%H:%i') AS time,
                       sa.role_name,
                       sa.created_at,
                       'Misa Biasa' AS mass_name
                FROM streaming_assignments sa
                WHERE {where_sql}
                ORDER BY sa.schedule_date ASC, sa.schedule_time ASC, sa.role_name ASC
                """,
                tuple(params),
            )
            rows = cursor.fetchall() or []
        except Exception as fallback_exc:
            print(f"[ERROR] Fallback tugas Misa Biasa anggota gagal: {fallback_exc}")
            rows = []

    tasks: list[dict[str, object]] = []
    for row in rows:
        try:
            tasks.append(member_monitoring_task_item(
                "biasa",
                "Misa Biasa",
                row.get("mass_name") or "Misa Biasa",
                row.get("date"),
                row.get("time"),
                row.get("role_name"),
                row.get("created_at"),
            ))
        except Exception as exc:
            print(f"[WARN] Skip row tugas Misa Biasa yang tidak valid: {exc}")
    return tasks
def member_monitoring_fetch_big_tasks(cursor, member_id: object, *, month: str = "all", year: str = "all") -> list[dict[str, object]]:
    """Ambil tugas Misa Besar milik anggota dengan fallback aman."""
    try:
        ensure_misa_besar_schema()
    except Exception as exc:
        print(f"[WARN] ensure_misa_besar_schema monitoring anggota gagal: {exc}")

    where = ["a.member_id = %s", "COALESCE(mb.status, 'published') = 'published'"]
    params: list[object] = [member_id]
    if normalize_text(month).lower() != "all":
        where.append("MONTH(mb.misa_date) = %s")
        params.append(parse_required_int(month, datetime.now().month))
    if normalize_text(year).lower() != "all":
        where.append("YEAR(mb.misa_date) = %s")
        params.append(parse_required_int(year, datetime.now().year))
    where_sql = " AND ".join(where)

    try:
        cursor.execute(
            f"""
            SELECT mb.misa_name,
                   DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                   TIME_FORMAT(mb.misa_time, '%H:%i') AS time,
                   n.role_name,
                   a.created_at
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            WHERE {where_sql}
            ORDER BY mb.misa_date ASC, mb.misa_time ASC, n.role_name ASC
            """,
            tuple(params),
        )
        rows = cursor.fetchall() or []
    except Exception as exc:
        print(f"[ERROR] Gagal mengambil tugas Misa Besar anggota: {exc}")
        rows = []

    tasks: list[dict[str, object]] = []
    for row in rows:
        try:
            tasks.append(member_monitoring_task_item(
                "besar",
                "Misa Besar",
                row.get("misa_name") or "Misa Besar",
                row.get("date"),
                row.get("time"),
                row.get("role_name"),
                row.get("created_at"),
            ))
        except Exception as exc:
            print(f"[WARN] Skip row tugas Misa Besar yang tidak valid: {exc}")
    return tasks
def member_monitoring_fetch_all_tasks(cursor, member_id: object, *, month: str = "all", year: str = "all", include_big: bool = True) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    try:
        tasks.extend(member_monitoring_fetch_regular_tasks(cursor, member_id, month=month, year=year))
    except Exception as exc:
        print(f"[ERROR] Ambil tugas Misa Biasa gagal: {exc}")
    if include_big:
        try:
            tasks.extend(member_monitoring_fetch_big_tasks(cursor, member_id, month=month, year=year))
        except Exception as exc:
            print(f"[ERROR] Ambil tugas Misa Besar gagal: {exc}")
    try:
        tasks.sort(key=lambda item: member_monitoring_schedule_dt(item.get("date"), item.get("time")))
    except Exception:
        pass
    return tasks
def member_monitoring_available_years(cursor, member_id: object) -> list[int]:
    years = {datetime.now().year}
    try:
        cursor.execute(
            """
            SELECT DISTINCT YEAR(schedule_date) AS year_value
            FROM streaming_assignments
            WHERE member_id = %s
            UNION
            SELECT DISTINCT YEAR(mb.misa_date) AS year_value
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            WHERE a.member_id = %s
            """,
            (member_id, member_id),
        )
        for row in cursor.fetchall() or []:
            year_val = fetch_scalar_value(row, None)
            if year_val:
                years.add(int(year_val))
    except Exception:
        pass
    current = datetime.now().year
    years.update({current - 1, current, current + 1})
    return sorted(years)


def member_monitoring_period_list(cursor, member_id: object, *, month: str, year: str, default_all_months: bool = False) -> list[tuple[int, int]]:
    month_value = normalize_text(month).lower() or "all"
    year_value = normalize_text(year).lower() or str(datetime.now().year)
    years = member_monitoring_available_years(cursor, member_id) if year_value == "all" else [parse_required_int(year_value, datetime.now().year)]
    periods: list[tuple[int, int]] = []
    if month_value == "all" or default_all_months:
        for y in years:
            for m in range(1, 13):
                periods.append((y, m))
    else:
        m = min(12, max(1, parse_required_int(month_value, datetime.now().month)))
        for y in years:
            periods.append((y, m))
    return periods


def member_monitoring_progress_group(tasks: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[str, dict[str, object]] = {}
    for task in tasks:
        type_key = normalize_text(task.get("type")) or "biasa"
        if type_key not in groups:
            groups[type_key] = {
                "type": type_key,
                "title": normalize_text(task.get("typeLabel")) or "Misa",
                "count": 0,
                "completed": 0,
                "schedules": [],
                "roles": [],
            }
        group = groups[type_key]
        group["count"] += 1
        if task.get("completed"):
            group["completed"] += 1
        group["schedules"].append(task.get("display"))
        group["roles"].append(task.get("role"))
    result: list[dict[str, object]] = []
    for group in groups.values():
        total = max(0, int(group.get("count") or 0))
        completed = max(0, int(group.get("completed") or 0))
        percentage = min(100, round((completed / total) * 100)) if total else 0
        if total == 0:
            status_label = "Belum Ada"
        elif completed >= total:
            status_label = "Selesai"
        elif completed > 0:
            status_label = "Sebagian Selesai"
        else:
            status_label = "Terjadwal"
        result.append({
            "type": group.get("type"),
            "title": group.get("title"),
            "count": total,
            "completed": completed,
            "schedules": group.get("schedules") or [],
            "roles": sorted(set([normalize_text(role) for role in group.get("roles") or [] if normalize_text(role)])),
            "status": status_label,
            "percentage": percentage,
            "progressClass": "good" if percentage >= 80 else ("warn" if percentage >= 60 else "low"),
        })
    result.sort(key=lambda item: 0 if item.get("type") == "biasa" else 1)
    return result


def member_monitoring_regular_count_for_period(cursor, member_id: object, year: int, month: int) -> int:
    return len(member_monitoring_fetch_regular_tasks(cursor, member_id, month=str(month), year=str(year)))


def member_monitoring_api_error(exc: Exception, message: str = "Gagal mengambil data monitoring."):
    """Return JSON error agar frontend tidak menerima HTML 500/teks kosong."""
    detail = str(exc)
    print(f"[ERROR] {message} {detail}")
    shown = message if not detail else f"{message} Detail: {detail}"
    return jsonify({"success": False, "error": shown, "detail": detail}), 500




# -----------------------------------------------------------------------------
# Evaluasi Streaming: Misa Biasa & Misa Besar
# -----------------------------------------------------------------------------

EVAL_DEFAULT_QUESTIONS = [
    {
        "id": "kesan-umum",
        "label": "Apa kesan umum pelayanan streaming pada misa ini?",
        "type": "single_choice",
        "required": True,
        "helpText": "Pilih satu penilaian umum.",
        "options": ["Sangat Baik", "Baik", "Cukup", "Perlu Pendampingan"],
    },
    {
        "id": "bagian-terbaik",
        "label": "Bagian mana yang sudah paling baik?",
        "type": "long_text",
        "required": False,
        "helpText": "Contoh: alur kamera, audio, koordinasi.",
        "options": [],
    },
]

EVAL_GENERAL_OPTIONS = {"aman", "kendala ringan", "kendala serius", "urgent", "kendala serius (urgent)"}
EVAL_REQUIRED_CHECKS = ["streaming_lancar", "koordinasi_baik"]


def eval_safe_json(value, fallback=None):
    if fallback is None:
        fallback = []
    return safe_json_loads(value, fallback)


def eval_date_to_iso(value) -> str:
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    raw = normalize_text(value)
    return raw[:10]


def eval_time_to_hhmm(value) -> str:
    return format_time_hhmm(value)


def eval_datetime_from_parts(date_text: str, time_text: str) -> datetime | None:
    try:
        return datetime.strptime(f"{date_text} {eval_time_to_hhmm(time_text)}", "%Y-%m-%d %H:%M")
    except Exception:
        return None


def eval_day_name(date_text: str) -> str:
    try:
        return DAYS_INDO[datetime.strptime(date_text, "%Y-%m-%d").weekday()]
    except Exception:
        return "-"


def eval_format_date_id(date_text: str) -> str:
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return normalize_text(date_text) or "-"


def eval_format_period_id(date_text: str, time_text: str = "") -> str:
    time_label = eval_time_to_hhmm(time_text) if time_text else ""
    base = f"{eval_day_name(date_text)}, {eval_format_date_id(date_text)}"
    return f"{base} jam {time_label} WIB" if time_label else base


def ensure_streaming_evaluation_schema(cursor=None) -> None:
    ensure_streaming_schema()
    ensure_misa_besar_schema()
    ensure_notifications_schema()
    owns_connection = cursor is None
    conn = None
    if owns_connection:
        conn = mysql_connection()
        cursor = conn.cursor(buffered=True)
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `streaming_evaluation_settings` (
              `id` int NOT NULL DEFAULT 1,
              `start_month` int NOT NULL DEFAULT 5,
              `start_year` int NOT NULL DEFAULT 2026,
              `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        cursor.execute(
            """
            INSERT IGNORE INTO `streaming_evaluation_settings` (`id`, `start_month`, `start_year`)
            VALUES (1, 5, 2026)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `streaming_evaluation_questions` (
              `id` varchar(100) NOT NULL,
              `label` varchar(500) NOT NULL,
              `question_type` varchar(40) NOT NULL DEFAULT 'short_text',
              `required` tinyint(1) NOT NULL DEFAULT 0,
              `help_text` text DEFAULT NULL,
              `options_json` longtext DEFAULT NULL,
              `order_index` int NOT NULL DEFAULT 0,
              `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        # Pertanyaan tambahan evaluasi bersifat opsional.
        # Jangan auto-seed ulang ketika tabel kosong, supaya admin bisa menyimpan konfigurasi tanpa pertanyaan tambahan.
        # Tombol "Reset ke Default" tetap tersedia untuk mengisi kembali pertanyaan default.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `streaming_evaluations` (
              `id` int NOT NULL AUTO_INCREMENT,
              `schedule_kind` varchar(30) NOT NULL,
              `schedule_key` varchar(120) NOT NULL,
              `schedule_date` date NOT NULL,
              `schedule_time` time NOT NULL,
              `misa_name` varchar(255) NOT NULL,
              `misa_type_label` varchar(50) NOT NULL,
              `evaluator_id` int DEFAULT NULL,
              `evaluator_name` varchar(255) NOT NULL,
              `evaluator_role` varchar(100) DEFAULT NULL,
              `staff_json` longtext DEFAULT NULL,
              `extra_staff_json` longtext DEFAULT NULL,
              `staff_evaluations_json` longtext DEFAULT NULL,
              `technical_issue` longtext DEFAULT NULL,
              `nontechnical_issue` longtext DEFAULT NULL,
              `checklist_json` longtext DEFAULT NULL,
              `final_note` longtext DEFAULT NULL,
              `dynamic_answers_json` longtext DEFAULT NULL,
              `general_assessment` varchar(100) NOT NULL,
              `submitted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `uniq_streaming_evaluation_schedule` (`schedule_kind`, `schedule_key`),
              KEY `idx_streaming_eval_date` (`schedule_date`, `schedule_time`),
              KEY `idx_streaming_eval_kind` (`schedule_kind`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """
        )
        if owns_connection:
            conn.commit()
    finally:
        if owns_connection:
            cursor.close()
            conn.close()


def eval_get_settings(cursor) -> dict[str, int]:
    ensure_streaming_evaluation_schema(cursor)
    cursor.execute("SELECT `start_month`, `start_year` FROM `streaming_evaluation_settings` WHERE `id` = 1 LIMIT 1")
    row = cursor.fetchone() or {}
    if not isinstance(row, dict):
        return {"startMonth": 5, "startYear": 2026}
    return {"startMonth": parse_required_int(row.get("start_month"), 5), "startYear": parse_required_int(row.get("start_year"), 2026)}


def eval_start_date_from_settings(settings: dict[str, int]) -> datetime.date:
    month = max(1, min(12, parse_required_int(settings.get("startMonth"), 5)))
    year = parse_required_int(settings.get("startYear"), 2026)
    return datetime(year, month, 1).date()


def eval_question_row_to_dict(row) -> dict[str, object]:
    if not isinstance(row, dict):
        return {}
    return {
        "id": normalize_text(row.get("id")),
        "label": normalize_text(row.get("label")),
        "type": normalize_text(row.get("question_type")) or "short_text",
        "required": bool(row.get("required")),
        "helpText": normalize_text(row.get("help_text")),
        "options": eval_safe_json(row.get("options_json"), []),
        "orderIndex": parse_required_int(row.get("order_index"), 0),
    }


def eval_fetch_questions(cursor) -> list[dict[str, object]]:
    ensure_streaming_evaluation_schema(cursor)
    cursor.execute(
        """
        SELECT `id`, `label`, `question_type`, `required`, `help_text`, `options_json`, `order_index`
        FROM `streaming_evaluation_questions`
        ORDER BY `order_index` ASC, `created_at` ASC
        """
    )
    rows = [eval_question_row_to_dict(row) for row in cursor.fetchall() or []]
    return [row for row in rows if row.get("id") and row.get("label")]


def eval_normalize_question_payload(items) -> list[dict[str, object]]:
    normalized = []
    if not isinstance(items, list):
        items = []
    allowed_types = {"short_text", "long_text", "single_choice", "multi_choice"}
    seen = set()
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        label = normalize_text(item.get("label"))
        if not label:
            continue
        raw_id = normalize_text(item.get("id")) or re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or f"q-{idx}"
        qid = raw_id[:90]
        if qid in seen:
            qid = f"{qid[:75]}-{idx}"
        seen.add(qid)
        qtype = normalize_text(item.get("type") or item.get("question_type")) or "short_text"
        if qtype not in allowed_types:
            qtype = "short_text"
        options = item.get("options") if isinstance(item.get("options"), list) else []
        clean_options = []
        for opt in options:
            opt_text = normalize_text(opt)
            if opt_text and opt_text not in clean_options:
                clean_options.append(opt_text)
        if qtype in {"single_choice", "multi_choice"} and not clean_options:
            clean_options = ["Ya", "Tidak"]
        normalized.append({
            "id": qid,
            "label": label,
            "type": qtype,
            "required": bool(item.get("required")),
            "helpText": normalize_text(item.get("helpText") or item.get("help_text")),
            "options": clean_options,
            "orderIndex": idx,
        })
    return normalized


def eval_evaluation_map(cursor, start_date: str | None = None, end_date: str | None = None) -> dict[tuple[str, str], dict[str, object]]:
    params = []
    where = []
    if start_date:
        where.append("schedule_date >= %s")
        params.append(start_date)
    if end_date:
        where.append("schedule_date <= %s")
        params.append(end_date)
    sql = "SELECT * FROM streaming_evaluations"
    if where:
        sql += " WHERE " + " AND ".join(where)
    cursor.execute(sql, tuple(params))
    result = {}
    for row in cursor.fetchall() or []:
        if isinstance(row, dict):
            result[(normalize_text(row.get("schedule_kind")), normalize_text(row.get("schedule_key")))] = row
    return result


def eval_fetch_active_members(cursor) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT id, nama, username, role, status_akun
        FROM anggota
        WHERE LOWER(COALESCE(status_akun, 'aktif')) IN ('', 'aktif', 'active')
        ORDER BY nama ASC, username ASC
        """
    )
    members = []
    for row in cursor.fetchall() or []:
        if not isinstance(row, dict):
            continue
        members.append({
            "id": str(row.get("id")),
            "name": normalize_text(row.get("nama") or row.get("username")),
            "username": normalize_text(row.get("username")),
            "accountRole": normalize_role_value(row.get("role") or "user"),
        })
    return members


def eval_fetch_regular_roles(cursor) -> list[str]:
    cursor.execute("SELECT role_name FROM streaming_roles ORDER BY order_index ASC, id ASC")
    roles = [normalize_text(row.get("role_name") if isinstance(row, dict) else row[0]) for row in cursor.fetchall() or []]
    return [r for r in roles if r]


def eval_fetch_regular_config(cursor) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT day_name, mass_name, DATE_FORMAT(start_time, '%H:%i') AS start_time
        FROM streaming_weekly_config
        ORDER BY FIELD(day_name, 'Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu'), start_time ASC
        """
    )
    return cursor.fetchall() or []


def eval_fetch_regular_assignments(cursor, start_date: str, end_date: str) -> dict[tuple[str, str], dict[str, dict[str, object]]]:
    cursor.execute(
        """
        SELECT sa.id AS assignment_id, DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS schedule_date,
               DATE_FORMAT(sa.schedule_time, '%H:%i') AS schedule_time, sa.role_name, sa.member_id,
               COALESCE(a.nama, CONCAT('ID ', sa.member_id)) AS member_name,
               COALESCE(a.role, 'user') AS account_role
        FROM streaming_assignments sa
        LEFT JOIN anggota a ON a.id = sa.member_id
        WHERE sa.schedule_date BETWEEN %s AND %s
        """,
        (start_date, end_date),
    )
    result: dict[tuple[str, str], dict[str, dict[str, object]]] = {}
    for row in cursor.fetchall() or []:
        date_text = normalize_text(row.get("schedule_date"))
        time_text = eval_time_to_hhmm(row.get("schedule_time"))
        key = (date_text, time_text)
        result.setdefault(key, {})[normalize_text(row.get("role_name"))] = {
            "assignmentId": row.get("assignment_id"),
            "role": normalize_text(row.get("role_name")),
            "memberId": str(row.get("member_id")),
            "memberName": normalize_text(row.get("member_name")),
            "accountRole": normalize_role_value(row.get("account_role") or "user"),
        }
    return result


def eval_fetch_regular_blocked(cursor, start_date: str, end_date: str) -> set[tuple[str, str]]:
    blocked = set()
    cursor.execute(
        """
        SELECT DATE_FORMAT(mass_date, '%Y-%m-%d') AS mass_date, DATE_FORMAT(mass_time, '%H:%i') AS mass_time
        FROM streaming_cancelled
        WHERE mass_date BETWEEN %s AND %s
        """,
        (start_date, end_date),
    )
    for row in cursor.fetchall() or []:
        blocked.add((normalize_text(row.get("mass_date")), eval_time_to_hhmm(row.get("mass_time"))))
    cursor.execute(
        """
        SELECT DATE_FORMAT(misa_date, '%Y-%m-%d') AS misa_date, DATE_FORMAT(misa_time, '%H:%i') AS misa_time
        FROM misa_besar
        WHERE status = 'published' AND misa_date BETWEEN %s AND %s
        """,
        (start_date, end_date),
    )
    for row in cursor.fetchall() or []:
        blocked.add((normalize_text(row.get("misa_date")), eval_time_to_hhmm(row.get("misa_time"))))
    return blocked


def eval_schedule_member_ids(schedule: dict[str, object]) -> set[str]:
    result = set()
    for staff in schedule.get("staff") or []:
        mid = normalize_text(staff.get("memberId") if isinstance(staff, dict) else "")
        if mid:
            result.add(mid)
    return result


def eval_schedule_has_staff(schedule: dict[str, object]) -> bool:
    return any(normalize_text(s.get("memberId")) for s in (schedule.get("staff") or []) if isinstance(s, dict))


def eval_build_regular_schedules(cursor, start_date: datetime.date, end_date: datetime.date) -> list[dict[str, object]]:
    roles = eval_fetch_regular_roles(cursor)
    cfg_rows = eval_fetch_regular_config(cursor)
    assignments = eval_fetch_regular_assignments(cursor, start_date.isoformat(), end_date.isoformat())
    blocked = eval_fetch_regular_blocked(cursor, start_date.isoformat(), end_date.isoformat())
    schedules = []
    current = start_date
    while current <= end_date:
        day_name = DAYS_INDO[current.weekday()]
        for cfg in cfg_rows:
            if normalize_text(cfg.get("day_name")) != day_name:
                continue
            date_text = current.isoformat()
            time_text = eval_time_to_hhmm(cfg.get("start_time"))
            if (date_text, time_text) in blocked:
                continue
            staff = []
            assigned_by_role = assignments.get((date_text, time_text), {})
            for role in roles:
                assigned = assigned_by_role.get(role) or {}
                staff.append({
                    "slotId": f"biasa:{date_text}:{time_text}:{role}",
                    "assignmentId": assigned.get("assignmentId"),
                    "role": role,
                    "roleId": role,
                    "memberId": assigned.get("memberId") or "",
                    "memberName": assigned.get("memberName") or "Belum terisi",
                    "accountRole": assigned.get("accountRole") or "",
                    "attendance": "present" if assigned.get("memberId") else "empty",
                })
            schedules.append({
                "kind": "misa_biasa",
                "kindLabel": "Misa Biasa",
                "scheduleKey": f"biasa:{date_text}:{time_text}",
                "id": f"misa_biasa|biasa:{date_text}:{time_text}",
                "misaId": None,
                "misaName": normalize_text(cfg.get("mass_name")) or "Misa Biasa",
                "date": date_text,
                "time": time_text,
                "dayName": day_name,
                "dateText": eval_format_date_id(date_text),
                "displayDateTime": eval_format_period_id(date_text, time_text),
                "staff": staff,
            })
        current += timedelta(days=1)
    return schedules


def eval_build_misa_besar_schedules(cursor, start_date: datetime.date, end_date: datetime.date) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT id, misa_name, DATE_FORMAT(misa_date, '%Y-%m-%d') AS misa_date,
               DATE_FORMAT(misa_time, '%H:%i') AS misa_time, misa_note, allow_member_request, status
        FROM misa_besar
        WHERE status = 'published' AND misa_date BETWEEN %s AND %s
        ORDER BY misa_date ASC, misa_time ASC, id ASC
        """,
        (start_date.isoformat(), end_date.isoformat()),
    )
    events = cursor.fetchall() or []
    schedules = []
    for ev in events:
        misa_id = ev.get("id")
        cursor.execute(
            """
            SELECT n.id AS role_id, n.role_name, n.required_count,
                   a.id AS assignment_id, a.member_id,
                   COALESCE(ag.nama, CONCAT('ID ', a.member_id)) AS member_name,
                   COALESCE(ag.role, 'user') AS account_role
            FROM misa_besar_names n
            LEFT JOIN misa_besar_assignments a ON a.role_id = n.id
            LEFT JOIN anggota ag ON ag.id = a.member_id
            WHERE n.misa_id = %s
            ORDER BY n.id ASC, a.id ASC
            """,
            (misa_id,),
        )
        grouped: dict[str, dict[str, object]] = {}
        for row in cursor.fetchall() or []:
            role_id = str(row.get("role_id"))
            if role_id not in grouped:
                grouped[role_id] = {
                    "roleId": role_id,
                    "role": normalize_text(row.get("role_name")) or "Role",
                    "requiredCount": max(1, parse_required_int(row.get("required_count"), 1)),
                    "assignments": [],
                }
            if row.get("assignment_id"):
                grouped[role_id]["assignments"].append({
                    "assignmentId": row.get("assignment_id"),
                    "memberId": str(row.get("member_id")),
                    "memberName": normalize_text(row.get("member_name")),
                    "accountRole": normalize_role_value(row.get("account_role") or "user"),
                })
        staff = []
        for role_data in grouped.values():
            assignments = role_data.get("assignments") or []
            required = max(len(assignments), parse_required_int(role_data.get("requiredCount"), 1))
            for idx in range(required):
                assigned = assignments[idx] if idx < len(assignments) else {}
                staff.append({
                    "slotId": f"besar:{misa_id}:{role_data.get('roleId')}:{idx}",
                    "assignmentId": assigned.get("assignmentId"),
                    "role": role_data.get("role"),
                    "roleId": role_data.get("roleId"),
                    "memberId": assigned.get("memberId") or "",
                    "memberName": assigned.get("memberName") or "Belum terisi",
                    "accountRole": assigned.get("accountRole") or "",
                    "attendance": "present" if assigned.get("memberId") else "empty",
                })
        date_text = normalize_text(ev.get("misa_date"))
        time_text = eval_time_to_hhmm(ev.get("misa_time"))
        schedules.append({
            "kind": "misa_besar",
            "kindLabel": "Misa Besar",
            "scheduleKey": f"besar:{misa_id}",
            "id": f"misa_besar|besar:{misa_id}",
            "misaId": misa_id,
            "misaName": normalize_text(ev.get("misa_name")) or "Misa Besar",
            "note": normalize_text(ev.get("misa_note")),
            "allowMemberRequest": bool(ev.get("allow_member_request")),
            "date": date_text,
            "time": time_text,
            "dayName": eval_day_name(date_text),
            "dateText": eval_format_date_id(date_text),
            "displayDateTime": eval_format_period_id(date_text, time_text),
            "staff": staff,
        })
    return schedules


def eval_period_bounds(scale: str, year: int | None = None, month: int | None = None, week: int | None = None) -> tuple[datetime.date, datetime.date]:
    now = datetime.now()
    scale = normalize_text(scale) or "month"
    if scale == "all":
        return datetime(1900, 1, 1).date(), datetime(2999, 12, 31).date()
    if scale == "year":
        y = year or now.year
        return datetime(y, 1, 1).date(), datetime(y, 12, 31).date()
    if scale == "week":
        y = year or now.year
        w = max(1, min(53, parse_required_int(week, int(now.strftime('%V')))))
        start = datetime.strptime(f"{y}-W{w:02d}-1", "%G-W%V-%u").date()
        return start, start + timedelta(days=6)
    y = year or now.year
    m = month or now.month
    m = max(1, min(12, m))
    start = datetime(y, m, 1).date()
    end = datetime(y, m, calendar.monthrange(y, m)[1]).date()
    return start, end


def eval_all_schedules(cursor, start_date: datetime.date, end_date: datetime.date, kind: str = "all") -> list[dict[str, object]]:
    settings = eval_get_settings(cursor)
    min_start = eval_start_date_from_settings(settings)
    if start_date < min_start:
        start_date = min_start
    if end_date < start_date:
        return []
    schedules = []
    if kind in {"all", "misa_biasa", "biasa"}:
        schedules.extend(eval_build_regular_schedules(cursor, start_date, end_date))
    if kind in {"all", "misa_besar", "besar"}:
        schedules.extend(eval_build_misa_besar_schedules(cursor, start_date, end_date))
    schedules.sort(key=lambda item: (item.get("date") or "", item.get("time") or "", item.get("kindLabel") or ""))
    return schedules


def eval_find_schedule(cursor, schedule_id: str) -> dict[str, object] | None:
    raw = normalize_text(schedule_id)
    if "|" not in raw:
        return None
    kind, key = raw.split("|", 1)
    # Build a narrow period where possible.
    if kind == "misa_besar" and key.startswith("besar:"):
        misa_id = key.split(":", 1)[1]
        cursor.execute("SELECT DATE_FORMAT(misa_date, '%Y-%m-%d') AS d FROM misa_besar WHERE id = %s LIMIT 1", (misa_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = datetime.strptime(row.get("d"), "%Y-%m-%d").date()
        schedules = eval_all_schedules(cursor, d, d, "misa_besar")
    elif kind == "misa_biasa" and key.startswith("biasa:"):
        parts = key.split(":")
        if len(parts) < 3:
            return None
        d = datetime.strptime(parts[1], "%Y-%m-%d").date()
        schedules = eval_all_schedules(cursor, d, d, "misa_biasa")
    else:
        return None
    for schedule in schedules:
        if schedule.get("id") == raw:
            return schedule
    return None


def eval_row_to_dict(row: dict[str, object]) -> dict[str, object]:
    date_text = eval_date_to_iso(row.get("schedule_date"))
    time_text = eval_time_to_hhmm(row.get("schedule_time"))
    return {
        "id": row.get("id"),
        "kind": normalize_text(row.get("schedule_kind")),
        "kindLabel": normalize_text(row.get("misa_type_label")) or ("Misa Besar" if normalize_text(row.get("schedule_kind")) == "misa_besar" else "Misa Biasa"),
        "scheduleKey": normalize_text(row.get("schedule_key")),
        "scheduleId": f"{normalize_text(row.get('schedule_kind'))}|{normalize_text(row.get('schedule_key'))}",
        "date": date_text,
        "time": time_text,
        "dayName": eval_day_name(date_text),
        "displayDateTime": eval_format_period_id(date_text, time_text),
        "misaName": normalize_text(row.get("misa_name")),
        "evaluatorId": row.get("evaluator_id"),
        "evaluatorName": normalize_text(row.get("evaluator_name")),
        "evaluatorRole": normalize_text(row.get("evaluator_role")),
        "staff": eval_safe_json(row.get("staff_json"), []),
        "extraStaff": eval_safe_json(row.get("extra_staff_json"), []),
        "staffEvaluations": eval_safe_json(row.get("staff_evaluations_json"), []),
        "technicalIssue": normalize_text(row.get("technical_issue")),
        "nontechnicalIssue": normalize_text(row.get("nontechnical_issue")),
        "checklist": eval_safe_json(row.get("checklist_json"), {}),
        "finalNote": normalize_text(row.get("final_note")),
        "dynamicAnswers": eval_safe_json(row.get("dynamic_answers_json"), []),
        "generalAssessment": normalize_text(row.get("general_assessment")),
        "submittedAt": row.get("submitted_at").isoformat() if row.get("submitted_at") else None,
    }


def eval_fetch_evaluations(cursor, start_date: str | None = None, end_date: str | None = None, kind: str = "all", search: str = "", sort: str = "date_asc") -> list[dict[str, object]]:
    params = []
    where = []
    if start_date:
        where.append("schedule_date >= %s")
        params.append(start_date)
    if end_date:
        where.append("schedule_date <= %s")
        params.append(end_date)
    if kind in {"misa_biasa", "misa_besar"}:
        where.append("schedule_kind = %s")
        params.append(kind)
    sql = "SELECT * FROM streaming_evaluations"
    if where:
        sql += " WHERE " + " AND ".join(where)
    cursor.execute(sql, tuple(params))
    rows = [eval_row_to_dict(row) for row in cursor.fetchall() or []]
    kw = normalize_text(search).lower()
    if kw:
        rows = [r for r in rows if kw in " ".join([normalize_text(r.get("misaName")), normalize_text(r.get("kindLabel")), normalize_text(r.get("evaluatorName")), normalize_text(r.get("generalAssessment")), normalize_text(r.get("finalNote"))]).lower()]
    if sort == "date_desc":
        rows.sort(key=lambda r: (r.get("date") or "", r.get("time") or ""), reverse=True)
    elif sort == "submitted_desc":
        rows.sort(key=lambda r: r.get("submittedAt") or "", reverse=True)
    elif sort == "submitted_asc":
        rows.sort(key=lambda r: r.get("submittedAt") or "")
    else:
        rows.sort(key=lambda r: (r.get("date") or "", r.get("time") or ""))
    return rows


def eval_upsert_regular_assignment(cursor, schedule, staff_slot):
    date_text = schedule.get("date")
    time_text = schedule.get("time")
    role = normalize_text(staff_slot.get("role"))
    attendance = normalize_text(staff_slot.get("attendance"))
    actual_member_id = normalize_text(staff_slot.get("actualMemberId") or staff_slot.get("memberId"))
    if not role:
        return
    if attendance == "not_attend" or not actual_member_id:
        cursor.execute(
            "DELETE FROM streaming_assignments WHERE schedule_date = %s AND DATE_FORMAT(schedule_time, '%H:%i') = %s AND role_name = %s",
            (date_text, time_text, role),
        )
        return
    cursor.execute(
        """
        INSERT INTO streaming_assignments (schedule_date, schedule_time, role_name, member_id, request_source, created_at)
        VALUES (%s, %s, %s, %s, 'evaluasi', NOW())
        ON DUPLICATE KEY UPDATE member_id = VALUES(member_id), request_source = 'evaluasi', created_at = NOW()
        """,
        (date_text, time_text, role, actual_member_id),
    )


def eval_upsert_misa_besar_assignment(cursor, schedule, staff_slot):
    role_id = normalize_text(staff_slot.get("roleId"))
    assignment_id = normalize_text(staff_slot.get("assignmentId"))
    attendance = normalize_text(staff_slot.get("attendance"))
    actual_member_id = normalize_text(staff_slot.get("actualMemberId") or staff_slot.get("memberId"))
    if not role_id:
        return
    if attendance == "not_attend" or not actual_member_id:
        if assignment_id:
            cursor.execute("DELETE FROM misa_besar_assignments WHERE id = %s", (assignment_id,))
        return
    if assignment_id:
        cursor.execute("UPDATE misa_besar_assignments SET member_id = %s, request_source = 'evaluasi', created_at = NOW() WHERE id = %s", (actual_member_id, assignment_id))
    else:
        cursor.execute("INSERT IGNORE INTO misa_besar_assignments (role_id, member_id, request_source, created_at) VALUES (%s, %s, 'evaluasi', NOW())", (role_id, actual_member_id))


def eval_create_urgent_notifications(cursor, evaluation: dict[str, object]) -> int:
    general = normalize_text(evaluation.get("generalAssessment")).lower()
    if "urgent" not in general and "serius" not in general:
        return 0
    title = f"Evaluasi Urgent: {evaluation.get('misaName') or 'Jadwal Streaming'}"
    body = (
        f"Ada evaluasi streaming berstatus <b>{html.escape(evaluation.get('generalAssessment') or 'Urgent')}</b> "
        f"untuk <b>{html.escape(evaluation.get('misaName') or '-')}</b> pada {html.escape(evaluation.get('displayDateTime') or '-')}. "
        f"Pengisi: <b>{html.escape(evaluation.get('evaluatorName') or '-')}</b>."
    )
    create_notification_once(
        cursor,
        "evaluasi",
        title,
        body,
        "/hasil-evaluasi-streaming.html",
        {"notification_kind": "streaming_evaluation_urgent", "evaluation_id": evaluation.get("id")},
        target_role="admin",
        dedupe_key=f"eval-urgent:admin:{evaluation.get('id')}",
    )
    create_notification_once(
        cursor,
        "evaluasi",
        title,
        body,
        "/hasil-evaluasi-streaming.html",
        {"notification_kind": "streaming_evaluation_urgent", "evaluation_id": evaluation.get("id")},
        target_role="super_admin",
        dedupe_key=f"eval-urgent:super:{evaluation.get('id')}",
    )
    return 2


def eval_validate_submit_payload(payload: dict[str, object]) -> tuple[bool, str]:
    if not normalize_text(payload.get("scheduleId")):
        return False, "Jadwal evaluasi wajib dipilih."
    if not normalize_text(payload.get("evaluatorName")) and not current_user_context().get("logged_in"):
        return False, "Nama pengisi evaluasi wajib dipilih."
    if not normalize_text(payload.get("technicalIssue")):
        return False, "Kendala teknis wajib diisi."
    if not normalize_text(payload.get("nontechnicalIssue")):
        return False, "Kendala non-teknis wajib diisi."
    # Checklist kondisi pelayanan bersifat informatif/opsional.
    # Tidak semua kondisi harus dicentang karena form juga dipakai untuk mencatat sesi yang mengalami kendala.
    if not normalize_text(payload.get("generalAssessment")):
        return False, "Penilaian umum wajib dipilih."
    return True, ""




















def eval_build_admin_summary(evaluations: list[dict[str, object]], pending: list[dict[str, object]]) -> dict[str, object]:
    count = len(evaluations)
    rating_scores = {"Sangat Baik": 4, "Baik": 3, "Cukup": 2, "Perlu Pendampingan": 1}
    rating_counts: dict[str, int] = {"Sangat Baik": 0, "Baik": 0, "Cukup": 0, "Perlu Pendampingan": 0}
    general_counts: dict[str, int] = {"Aman": 0, "Kendala Ringan": 0, "Kendala Serius (Urgent)": 0}
    checklist_stream = 0
    checklist_coord = 0
    technical_min = 0
    nontechnical_min = 0
    total_staff_score = 0
    total_staff = 0
    dynamic_answer_count = 0
    for e in evaluations:
        general = normalize_text(e.get("generalAssessment")) or "Aman"
        general_counts[general] = general_counts.get(general, 0) + 1
        tech = normalize_text(e.get("technicalIssue")).lower()
        nontech = normalize_text(e.get("nontechnicalIssue")).lower()
        if tech in {"-", "tidak ada", "aman", "none"} or len(tech) < 5:
            technical_min += 1
        if nontech in {"-", "tidak ada", "aman", "none"} or len(nontech) < 5:
            nontechnical_min += 1
        checklist = e.get("checklist") or {}
        if checklist.get("streaming_lancar"):
            checklist_stream += 1
        if checklist.get("koordinasi_baik"):
            checklist_coord += 1
        for staff_eval in e.get("staffEvaluations") or []:
            rating = normalize_text(staff_eval.get("rating") if isinstance(staff_eval, dict) else "")
            if rating in rating_counts:
                rating_counts[rating] += 1
            if rating in rating_scores:
                total_staff_score += rating_scores[rating]
                total_staff += 1
        for ans in e.get("dynamicAnswers") or []:
            if isinstance(ans, dict):
                val = ans.get("answer")
                if (isinstance(val, list) and val) or normalize_text(val):
                    dynamic_answer_count += 1
    avg_staff = round(total_staff_score / total_staff, 2) if total_staff else 0
    checklist_rate = round(((checklist_stream + checklist_coord) / (count * 2)) * 100) if count else 0
    safe_count = general_counts.get("Aman", 0)
    urgent_count = sum(v for k, v in general_counts.items() if "Urgent" in k or "Serius" in k)
    insight = "Belum ada evaluasi pada periode ini."
    if count:
        insight = f"Dalam periode ini terdapat {count} evaluasi masuk. Rata-rata penilaian petugas {avg_staff}/4, kepatuhan checklist {checklist_rate}%, dan {urgent_count} sesi masuk kategori urgent."
    recommendation = "Prioritaskan pengisian evaluasi untuk misa yang sudah lewat dan belum diisi."
    if urgent_count:
        recommendation = "Segera cek evaluasi urgent dan tindak lanjuti kendala teknis/non-teknis yang tercatat."
    elif count and checklist_rate >= 80:
        recommendation = "Pertahankan pola koordinasi dan dokumentasikan praktik yang sudah berjalan baik."
    return {
        "averageStaffScore": avg_staff,
        "checklistRate": checklist_rate,
        "generalSafeRate": round((safe_count / count) * 100) if count else 0,
        "generalUrgentCount": urgent_count,
        "dynamicAnswerCount": dynamic_answer_count,
        "ratingCounts": rating_counts,
        "generalCounts": general_counts,
        "technicalMinRate": round((technical_min / count) * 100) if count else 0,
        "nontechnicalMinRate": round((nontechnical_min / count) * 100) if count else 0,
        "pendingCount": len(pending),
        "insight": insight,
        "recommendation": recommendation,
    }





def eval_export_value(value) -> str:
    if value is None:
        return "-"
    text = normalize_text(value)
    return text if text else "-"


def eval_checklist_export_text(checklist: dict[str, object]) -> str:
    checklist = checklist if isinstance(checklist, dict) else {}
    labels = {
        "streaming_lancar": "Streaming berjalan lancar sampai akhir",
        "koordinasi_baik": "Koordinasi tim berjalan baik",
        "rekaman_tersimpan": "Rekaman tersimpan dengan benar",
    }
    parts = []
    for key, label in labels.items():
        if key in checklist:
            parts.append(f"{label}: {'Ya' if checklist.get(key) else 'Tidak'}")
    for key, value in checklist.items():
        if key not in labels:
            parts.append(f"{key}: {'Ya' if value else 'Tidak'}")
    return "; ".join(parts) or "-"


def eval_staff_export_text(staff: list[dict[str, object]]) -> str:
    parts = []
    for slot in staff or []:
        if not isinstance(slot, dict):
            continue
        role = eval_export_value(slot.get("role"))
        scheduled = eval_export_value(slot.get("memberName"))
        actual = eval_export_value(slot.get("actualMemberName") or slot.get("memberName"))
        attendance = normalize_text(slot.get("attendance"))
        attendance_label = "Tidak datang" if attendance == "not_attend" else "Hadir/Digantikan"
        if actual == "Tidak datang":
            attendance_label = "Tidak datang"
        parts.append(f"{role}: jadwal {scheduled}; aktual {actual}; status {attendance_label}")
    return "; ".join(parts) or "-"


def eval_extra_staff_export_text(extra_staff: list[dict[str, object]]) -> str:
    parts = []
    for staff in extra_staff or []:
        if not isinstance(staff, dict):
            continue
        name = eval_export_value(staff.get("name") or staff.get("memberName"))
        role = eval_export_value(staff.get("role") or staff.get("helpRole"))
        parts.append(f"{name} ({role})")
    return "; ".join(parts) or "-"


def eval_staff_evaluation_export_text(staff_evals: list[dict[str, object]]) -> str:
    parts = []
    for item in staff_evals or []:
        if not isinstance(item, dict):
            continue
        name = eval_export_value(item.get("memberName") or item.get("name"))
        role = eval_export_value(item.get("role"))
        rating = eval_export_value(item.get("rating") or item.get("assessment"))
        note = eval_export_value(item.get("note") or item.get("catatan") or item.get("comment"))
        parts.append(f"{name} ({role}) - {rating}; catatan: {note}")
    return "; ".join(parts) or "-"


def eval_dynamic_answers_export_text(dynamic_answers: list[dict[str, object]]) -> str:
    parts = []
    for item in dynamic_answers or []:
        if not isinstance(item, dict):
            continue
        question = eval_export_value(item.get("question") or item.get("label") or item.get("text"))
        answer = item.get("answer")
        if isinstance(answer, list):
            answer_text = ", ".join(normalize_text(v) for v in answer if normalize_text(v))
        else:
            answer_text = normalize_text(answer)
        parts.append(f"{question}: {answer_text or '-'}")
    return "; ".join(parts) or "-"


def eval_export_rows(evaluations: list[dict[str, object]]) -> tuple[list[str], list[list[str]]]:
    headers = [
        "No", "Tanggal", "Jam", "Hari", "Jenis Misa", "Nama Misa", "Pengisi", "Role Pengisi",
        "Penilaian Umum", "Petugas Jadwal & Aktual", "Petugas Tambahan", "Evaluasi Per Petugas",
        "Kendala Teknis", "Kendala Non-Teknis", "Checklist Kondisi Pelayanan", "Pertanyaan Tambahan",
        "Catatan Penutup", "Waktu Submit",
    ]
    rows: list[list[str]] = []
    for idx, e in enumerate(evaluations, start=1):
        rows.append([
            str(idx),
            eval_export_value(e.get("date")),
            eval_export_value(e.get("time")),
            eval_export_value(e.get("dayName")),
            eval_export_value(e.get("kindLabel")),
            eval_export_value(e.get("misaName")),
            eval_export_value(e.get("evaluatorName")),
            eval_export_value(e.get("evaluatorRole")),
            eval_export_value(e.get("generalAssessment")),
            eval_staff_export_text(e.get("staff") or []),
            eval_extra_staff_export_text(e.get("extraStaff") or []),
            eval_staff_evaluation_export_text(e.get("staffEvaluations") or []),
            eval_export_value(e.get("technicalIssue")),
            eval_export_value(e.get("nontechnicalIssue")),
            eval_checklist_export_text(e.get("checklist") or {}),
            eval_dynamic_answers_export_text(e.get("dynamicAnswers") or []),
            eval_export_value(e.get("finalNote")),
            eval_export_value((e.get("submittedAt") or "").replace("T", " ")[:16]),
        ])
    return headers, rows






def create_streaming_evaluation_reminder_notifications() -> int:
    """Kirim pengingat evaluasi streaming H+1 setiap hari sampai evaluasi terisi.

    Perbaikan penting:
    - Backfill reminder harian yang terlewat. Misalnya hari ini 14 Mei dan jadwal
      10 Mei belum dievaluasi, sistem akan membuat reminder untuk 11, 12, 13,
      dan 14 Mei jika belum pernah dibuat.
    - Berlaku untuk Misa Biasa dan Misa Besar.
    - Dikirim ke setiap petugas pada sesi tersebut, termasuk user, admin, super_admin.
    - Jika satu evaluasi sudah masuk untuk sesi itu, reminder berhenti untuk semua petugas.
    - Dedupe per tanggal reminder + jadwal + member, sehingga aman dipanggil berkali-kali.
    """
    ensure_streaming_evaluation_schema()
    ensure_notifications_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    sent = 0
    try:
        today = datetime.now().date()
        settings = eval_get_settings(cursor)
        start = eval_start_date_from_settings(settings)
        # Pengingat mulai H+1, jadi jadwal yang dicek maksimal kemarin.
        end = today - timedelta(days=1)
        if end < start:
            conn.commit()
            return 0

        schedules = eval_all_schedules(cursor, start, end, "all")
        evals = eval_evaluation_map(cursor, start.isoformat(), end.isoformat())

        for schedule in schedules:
            dt = eval_datetime_from_parts(schedule.get("date"), schedule.get("time"))
            if not dt or dt.date() >= today:
                continue
            if not eval_schedule_has_staff(schedule):
                continue
            # Jika salah satu petugas sudah submit evaluasi untuk sesi ini, stop pengingat.
            if evals.get((schedule.get("kind"), schedule.get("scheduleKey"))):
                continue

            schedule_id = normalize_text(schedule.get("id"))
            misa_name = normalize_text(schedule.get("misaName")) or "Jadwal Streaming"
            display_dt = normalize_text(schedule.get("displayDateTime")) or eval_format_period_id(schedule.get("date"), schedule.get("time"))
            kind_label = normalize_text(schedule.get("kindLabel")) or "Jadwal Streaming"

            # Backfill dari H+1 sampai hari ini. Dibatasi 31 hari agar tidak membanjiri
            # database jika ada jadwal sangat lama yang belum dievaluasi.
            first_reminder_day = dt.date() + timedelta(days=1)
            if (today - first_reminder_day).days > 31:
                first_reminder_day = today - timedelta(days=31)

            reminder_days = []
            walk_day = first_reminder_day
            while walk_day <= today:
                reminder_days.append(walk_day)
                walk_day += timedelta(days=1)

            for reminder_day in reminder_days:
                reminder_date_key = reminder_day.isoformat()
                elapsed_days = max((reminder_day - dt.date()).days, 1)
                sent_members_for_schedule: set[str] = set()
                for staff in schedule.get("staff") or []:
                    if not isinstance(staff, dict):
                        continue
                    member_id = normalize_text(staff.get("memberId"))
                    if not member_id or member_id in sent_members_for_schedule:
                        continue
                    sent_members_for_schedule.add(member_id)

                    member_role = normalize_role_value(staff.get("accountRole") or "user")
                    role_name = normalize_text(staff.get("role")) or "Petugas"
                    url = "/form-evaluasi-streaming.html"
                    dedupe_key = f"eval-reminder:{reminder_date_key}:{schedule_id}:{member_id}"

                    cursor.execute(
                        """
                        SELECT `id` FROM `notifications`
                        WHERE `type` = %s
                          AND (`data` LIKE %s OR `data` LIKE %s)
                        LIMIT 1
                        """,
                        (
                            "evaluasi",
                            f'%"dedupe_key": "{dedupe_key}"%',
                            f'%"dedupe_key":"{dedupe_key}"%',
                        ),
                    )
                    already_exists = cursor.fetchone() is not None

                    if elapsed_days == 1:
                        overdue_label = "H+1"
                    else:
                        overdue_label = f"H+{elapsed_days}"

                    title = f"Pengingat Evaluasi Streaming {overdue_label}: {misa_name}"
                    body = (
                        f"Form evaluasi untuk <b>{html.escape(misa_name)}</b> ({html.escape(kind_label)}) pada "
                        f"{html.escape(display_dt)} belum diisi. Anda terdaftar sebagai "
                        f"<b>{html.escape(role_name)}</b>. Silakan isi evaluasi streaming; cukup salah satu petugas "
                        f"pada sesi ini yang mengisi agar pengingat berhenti."
                    )
                    create_notification_once(
                        cursor,
                        "evaluasi",
                        title,
                        body,
                        url,
                        {
                            "target_user_id": member_id,
                            "notification_kind": "streaming_evaluation_reminder",
                            "schedule_id": schedule_id,
                            "schedule_kind": schedule.get("kind"),
                            "schedule_key": schedule.get("scheduleKey"),
                            "misa_type": schedule.get("kind"),
                            "misa_name": misa_name,
                            "misa_date": schedule.get("date"),
                            "misa_time": schedule.get("time"),
                            "role": role_name,
                            "reminder_date": reminder_date_key,
                            "overdue_days": elapsed_days,
                            "overdue_label": overdue_label,
                        },
                        target_role=None,
                        dedupe_key=dedupe_key,
                    )
                    if not already_exists:
                        sent += 1

        conn.commit()
        return sent
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()





# ===== Activity Log Backend =====
ACTIVITY_ROLE_LABELS = {
    "super_admin": "Super Admin",
    "admin": "Admin",
    "user": "Anggota",
}

ACTIVITY_MODULE_BY_PATH = [
    ("/api/password", "Autentikasi"),
    ("/login", "Autentikasi"),
    ("/logout", "Autentikasi"),
    ("/api/anggota", "Keanggotaan"),
    ("/api/admin", "Keanggotaan"),
    ("/api/membership", "Keanggotaan"),
    ("/api/sertifikat", "Sertifikat"),
    ("/api/streaming", "Tugas Streaming"),
    ("/api/misa-besar", "Tugas Streaming"),
    ("/api/request-tugas", "Request Tugas"),
    ("/api/cancel-tugas", "Pembatalan Tugas"),
    ("/api/task-exchanges", "Tukar Jadwal"),
    ("/api/evaluasi-streaming", "Evaluasi Streaming"),
    ("/api/monitoring", "Monitoring Tugas"),
    ("/api/inventory", "Inventaris"),
    ("/api/pengajuan", "Peminjaman"),
    ("/api/loan", "Peminjaman"),
    ("/api/kerusakan", "Kerusakan Barang"),
    ("/api/news", "Pengumuman"),
    ("/api/agenda", "Agenda"),
    ("/api/forms", "Form Pendaftaran"),
    ("/api/form", "Form Pendaftaran"),
    ("/api/tentang", "Konten Website"),
    ("/api/youtube", "Konten Website"),
    ("/api/google", "Konten Website"),
    ("/api/instagram", "Konten Website"),
    ("/api/carousel", "Konten Website"),
]

def ensure_activity_log_schema(cursor=None) -> None:
    own_conn = None
    own_cursor = cursor
    if own_cursor is None:
        own_conn = mysql_connection()
        own_cursor = own_conn.cursor()
    own_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `activity_logs` (
          `id` bigint(20) NOT NULL AUTO_INCREMENT,
          `actor_id` int(11) DEFAULT NULL,
          `actor_name` varchar(255) DEFAULT NULL,
          `actor_username` varchar(150) DEFAULT NULL,
          `actor_role` varchar(50) DEFAULT NULL,
          `action` varchar(50) NOT NULL,
          `module` varchar(120) NOT NULL,
          `description` text DEFAULT NULL,
          `route` varchar(255) DEFAULT NULL,
          `method` varchar(12) DEFAULT NULL,
          `target_user_id` int(11) DEFAULT NULL,
          `target_label` varchar(255) DEFAULT NULL,
          `meta` longtext DEFAULT NULL,
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `idx_activity_actor` (`actor_id`),
          KEY `idx_activity_role` (`actor_role`),
          KEY `idx_activity_action` (`action`),
          KEY `idx_activity_module` (`module`),
          KEY `idx_activity_created_at` (`created_at`),
          KEY `idx_activity_target_user` (`target_user_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )
    for col, definition in {
        "actor_id": "`actor_id` int(11) DEFAULT NULL",
        "actor_name": "`actor_name` varchar(255) DEFAULT NULL",
        "actor_username": "`actor_username` varchar(150) DEFAULT NULL",
        "actor_role": "`actor_role` varchar(50) DEFAULT NULL",
        "action": "`action` varchar(50) NOT NULL DEFAULT 'ACTION'",
        "module": "`module` varchar(120) NOT NULL DEFAULT 'Sistem'",
        "description": "`description` text DEFAULT NULL",
        "route": "`route` varchar(255) DEFAULT NULL",
        "method": "`method` varchar(12) DEFAULT NULL",
        "target_user_id": "`target_user_id` int(11) DEFAULT NULL",
        "target_label": "`target_label` varchar(255) DEFAULT NULL",
        "meta": "`meta` longtext DEFAULT NULL",
        "created_at": "`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }.items():
        ensure_column(own_cursor, "activity_logs", col, definition)
    if own_conn is not None:
        own_conn.commit()
        own_cursor.close()
        own_conn.close()

def activity_role_label(role_value: str) -> str:
    return ACTIVITY_ROLE_LABELS.get(normalize_role_value(role_value), "Anggota")

def activity_current_role() -> str:
    return normalize_role_value(session.get("role") or "user")

def activity_current_user_id() -> int | None:
    try:
        if session.get("user_id") in (None, ""):
            return None
        return int(session.get("user_id"))
    except (TypeError, ValueError):
        return None

def activity_visible_role_values(current_role: str | None = None) -> list[str]:
    role = normalize_role_value(current_role or session.get("role") or "user")
    if role == "super_admin":
        return ["super_admin", "admin", "user"]
    if role == "admin":
        return ["admin", "user"]
    return ["user"]

def activity_scope_where(alias: str = "l") -> tuple[str, list[object]]:
    role = activity_current_role()
    actor_id = activity_current_user_id()
    prefix = f"{alias}." if alias else ""
    if role == "super_admin":
        return "1=1", []
    if role == "admin":
        return f"({prefix}`actor_role` = 'user' OR {prefix}`actor_id` = %s)", [actor_id or 0]
    return f"{prefix}`actor_id` = %s", [actor_id or 0]

def activity_normalize_sort(sort_value: str) -> str:
    raw = normalize_text(sort_value).lower()
    if raw in {"oldest", "terlama", "date_asc", "asc"}:
        return "oldest"
    return "newest"

def activity_month_year_defaults() -> tuple[int, int]:
    now = datetime.now()
    return now.month, now.year

def activity_period_bounds_from_args(args) -> tuple[datetime, datetime, int | str, int]:
    default_month, default_year = activity_month_year_defaults()
    raw_month = normalize_text(args.get("month"))
    raw_year = normalize_text(args.get("year"))
    year = parse_required_int(raw_year, default_year) or default_year
    if raw_month.lower() in {"all", "semua", "0"}:
        start = datetime(year, 1, 1)
        end = datetime(year + 1, 1, 1)
        return start, end, "all", year
    month = parse_required_int(raw_month, default_month) or default_month
    month = min(max(month, 1), 12)
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end, month, year

def activity_module_from_path(path_value: str) -> str:
    path_lower = normalize_text(path_value).lower()
    for prefix, module_name in ACTIVITY_MODULE_BY_PATH:
        if path_lower.startswith(prefix):
            return module_name
    return "Sistem"

def activity_action_from_request(method: str, path_value: str, endpoint_name: str | None = None) -> str:
    method = (method or "").upper()
    path_lower = normalize_text(path_value).lower()
    endpoint_lower = normalize_text(endpoint_name).lower()
    if path_lower.startswith("/login") and method == "POST":
        return "LOGIN"
    if path_lower.startswith("/logout"):
        return "LOGOUT"
    if "approve" in path_lower or "setujui" in path_lower or "approve" in endpoint_lower:
        return "APPROVE"
    if "reject" in path_lower or "tolak" in path_lower or "reject" in endpoint_lower:
        return "REJECT"
    if "cancel" in path_lower or "batal" in path_lower or "cancel" in endpoint_lower:
        return "CANCEL"
    if "export" in path_lower or "download" in path_lower:
        return "EXPORT"
    if "reset" in path_lower:
        return "RESET"
    if method == "POST":
        return "CREATE"
    if method in {"PUT", "PATCH"}:
        return "UPDATE"
    if method == "DELETE":
        return "DELETE"
    return "ACCESS"

def activity_description_from_request(action: str, module_name: str, path_value: str) -> str:
    if action == "LOGIN":
        return "Login ke sistem"
    if action == "LOGOUT":
        return "Logout dari sistem"
    if action == "EXPORT":
        return f"Mengekspor data {module_name}"
    if action == "CREATE":
        return f"Menambahkan atau mengirim data pada modul {module_name}"
    if action == "UPDATE":
        return f"Memperbarui data pada modul {module_name}"
    if action == "DELETE":
        return f"Menghapus data pada modul {module_name}"
    if action == "APPROVE":
        return f"Menyetujui data pada modul {module_name}"
    if action == "REJECT":
        return f"Menolak data pada modul {module_name}"
    if action == "CANCEL":
        return f"Membatalkan data pada modul {module_name}"
    if action == "RESET":
        return f"Melakukan reset pada modul {module_name}"
    return f"Aktivitas pada modul {module_name}"

def activity_log_row_to_dict(row: dict[str, object]) -> dict[str, object]:
    created = row.get("created_at")
    created_iso = created.isoformat() if hasattr(created, "isoformat") else normalize_text(created)
    role_value = normalize_role_value(row.get("actor_role") or "user")
    return {
        "id": row.get("id"),
        "createdAt": created_iso,
        "timestamp": created_iso,
        "actorId": row.get("actor_id"),
        "actorName": row.get("actor_name") or "Pengguna",
        "actorUsername": row.get("actor_username") or "",
        "actorRole": role_value,
        "actorRoleLabel": activity_role_label(role_value),
        "action": row.get("action") or "-",
        "module": row.get("module") or "-",
        "description": row.get("description") or "-",
        "route": row.get("route") or "-",
        "method": row.get("method") or "",
        "targetUserId": row.get("target_user_id"),
        "targetLabel": row.get("target_label") or "",
        "meta": safe_json_loads(row.get("meta"), {}),
    }

def insert_activity_log(
    cursor,
    *,
    actor_id=None,
    actor_name: str | None = None,
    actor_username: str | None = None,
    actor_role: str | None = None,
    action: str = "ACTION",
    module: str = "Sistem",
    description: str = "",
    route: str | None = None,
    method: str | None = None,
    target_user_id=None,
    target_label: str | None = None,
    meta: dict | None = None,
):
    ensure_activity_log_schema(cursor)
    cursor.execute(
        """
        INSERT INTO `activity_logs`
          (`actor_id`, `actor_name`, `actor_username`, `actor_role`, `action`, `module`, `description`,
           `route`, `method`, `target_user_id`, `target_label`, `meta`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            actor_id,
            normalize_text(actor_name) or None,
            normalize_text(actor_username) or None,
            normalize_role_value(actor_role or "user"),
            normalize_text(action).upper() or "ACTION",
            normalize_text(module) or "Sistem",
            normalize_text(description),
            normalize_text(route) or None,
            normalize_text(method).upper() or None,
            target_user_id,
            normalize_text(target_label) or None,
            json.dumps(meta or {}, ensure_ascii=False),
        ),
    )

def record_activity(
    action: str,
    module: str,
    description: str,
    route: str | None = None,
    *,
    method: str | None = None,
    target_user_id=None,
    target_label: str | None = None,
    meta: dict | None = None,
    actor: dict[str, object] | None = None,
):
    if actor is None:
        if not session.get("logged_in"):
            return
        actor = {
            "id": activity_current_user_id(),
            "nama": session.get("nama") or session.get("username") or "Pengguna",
            "username": session.get("username") or "",
            "role": activity_current_role(),
        }
    conn = None
    cursor = None
    try:
        conn = mysql_connection()
        cursor = conn.cursor()
        insert_activity_log(
            cursor,
            actor_id=actor.get("id"),
            actor_name=actor.get("nama") or actor.get("name") or "Pengguna",
            actor_username=actor.get("username") or "",
            actor_role=actor.get("role") or "user",
            action=action,
            module=module,
            description=description,
            route=route,
            method=method or (request.method if request else ""),
            target_user_id=target_user_id,
            target_label=target_label,
            meta=meta,
        )
        conn.commit()
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"[WARN] Gagal mencatat log aktivitas: {exc}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def record_activity_for_member(member_id, action: str, module: str, description: str, route: str | None = None, *, meta: dict | None = None):
    conn = None
    cursor = None
    try:
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nama, username, role FROM anggota WHERE id = %s LIMIT 1", (member_id,))
        member = cursor.fetchone()
        if not member:
            return
        insert_activity_log(
            cursor,
            actor_id=member.get("id"),
            actor_name=member.get("nama") or "Pengguna",
            actor_username=member.get("username") or "",
            actor_role=member.get("role") or "user",
            action=action,
            module=module,
            description=description,
            route=route,
            method=request.method if request else None,
            meta=meta,
        )
        conn.commit()
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"[WARN] Gagal mencatat log aktivitas member: {exc}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def activity_should_auto_log(response) -> bool:
    try:
        if response.status_code >= 400:
            return False
        path = request.path or ""
        if path.startswith("/static/") or path.startswith("/uploads/") or path == "/favicon.ico":
            return False
        if path.startswith("/api/activity-logs"):
            return False
        if path.startswith("/api/monitoring-kewajiban-tugas/"):
            return False
        if path == "/api/evaluasi-streaming/reminders/run":
            return False
        if not session.get("logged_in"):
            return False
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            return True
        if path in {"/logout"}:
            return True
        return False
    except Exception:
        return False

@app.after_request
def activity_auto_logger(response):
    if not activity_should_auto_log(response):
        return response
    try:
        action = activity_action_from_request(request.method, request.path, request.endpoint)
        module_name = activity_module_from_path(request.path)
        description = activity_description_from_request(action, module_name, request.path)
        record_activity(
            action,
            module_name,
            description,
            route=request.endpoint or request.path,
            method=request.method,
            meta={
                "path": request.path,
                "query": request.query_string.decode("utf-8", errors="ignore"),
                "status": response.status_code,
            },
        )
    except Exception as exc:
        print(f"[WARN] activity_auto_logger skipped: {exc}")
    return response

def require_activity_log_auth():
    if not session.get("logged_in"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    return None

def activity_visible_users(cursor) -> list[dict[str, object]]:
    role = activity_current_role()
    actor_id = activity_current_user_id()
    if role == "super_admin":
        cursor.execute(
            """
            SELECT id, nama, username, role
            FROM anggota
            ORDER BY FIELD(role, 'super_admin', 'admin', 'user'), nama ASC, username ASC
            """
        )
    elif role == "admin":
        cursor.execute(
            """
            SELECT id, nama, username, role
            FROM anggota
            WHERE role = 'user' OR id = %s
            ORDER BY FIELD(role, 'admin', 'user'), nama ASC, username ASC
            """,
            (actor_id or 0,),
        )
    else:
        cursor.execute(
            """
            SELECT id, nama, username, role
            FROM anggota
            WHERE id = %s
            LIMIT 1
            """,
            (actor_id or 0,),
        )
    rows = cursor.fetchall() or []
    return [
        {
            "id": row.get("id"),
            "name": row.get("nama") or row.get("username") or "Pengguna",
            "username": row.get("username") or "",
            "role": normalize_role_value(row.get("role") or "user"),
            "roleLabel": activity_role_label(row.get("role") or "user"),
            "label": f"{row.get('nama') or row.get('username') or 'Pengguna'} ({row.get('username') or '-'}) - {activity_role_label(row.get('role') or 'user')}",
        }
        for row in rows
    ]

def activity_filter_query(args, *, include_pagination: bool = True) -> tuple[str, list[object], dict[str, object]]:
    ensure_auth_schema()
    start, end, month, year = activity_period_bounds_from_args(args)
    where_clauses = []
    params: list[object] = []

    scope_sql, scope_params = activity_scope_where("l")
    where_clauses.append(scope_sql)
    params.extend(scope_params)

    where_clauses.append("l.`created_at` >= %s AND l.`created_at` < %s")
    params.extend([start, end])

    search = normalize_text(args.get("search"))
    if search:
        like = f"%{search}%"
        where_clauses.append(
            """
            (
              l.`actor_name` LIKE %s OR l.`actor_username` LIKE %s OR l.`actor_role` LIKE %s OR
              l.`action` LIKE %s OR l.`module` LIKE %s OR l.`description` LIKE %s OR l.`route` LIKE %s
            )
            """
        )
        params.extend([like, like, like, like, like, like, like])

    user_id_raw = normalize_text(args.get("user_id") or args.get("userId") or args.get("actor_id") or args.get("account"))
    if user_id_raw and user_id_raw.lower() != "all":
        try:
            user_id = int(user_id_raw)
            where_clauses.append("l.`actor_id` = %s")
            params.append(user_id)
        except ValueError:
            pass

    role_raw = normalize_text(args.get("role"))
    if role_raw and role_raw.lower() != "all":
        role_value = normalize_role_value(role_raw)
        where_clauses.append("l.`actor_role` = %s")
        params.append(role_value)

    action_raw = normalize_text(args.get("action"))
    if action_raw and action_raw.lower() != "all":
        where_clauses.append("l.`action` = %s")
        params.append(action_raw.upper())

    module_raw = normalize_text(args.get("module"))
    if module_raw and module_raw.lower() != "all":
        where_clauses.append("l.`module` = %s")
        params.append(module_raw)

    sort_mode = activity_normalize_sort(args.get("sort"))
    order_sql = "l.`created_at` ASC, l.`id` ASC" if sort_mode == "oldest" else "l.`created_at` DESC, l.`id` DESC"

    page = max(1, parse_required_int(args.get("page"), 1))
    per_page = parse_required_int(args.get("limit") or args.get("per_page") or args.get("perPage"), 20)
    if per_page not in {10, 20, 50}:
        per_page = 20

    metadata = {
        "page": page,
        "perPage": per_page,
        "sort": sort_mode,
        "month": month,
        "year": year,
        "start": start,
        "end": end,
    }
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    sql = f"""
        FROM `activity_logs` l
        WHERE {where_sql}
    """
    return sql, params, metadata | {"orderSql": order_sql}



def activity_export_rows(logs: list[dict[str, object]]) -> tuple[list[str], list[list[str]]]:
    headers = ["No", "Waktu", "Pengguna", "Username", "Role", "Aksi", "Modul", "Deskripsi", "Route", "Method"]
    rows: list[list[str]] = []
    for idx, row in enumerate(logs, start=1):
        rows.append([
            str(idx),
            normalize_text(row.get("createdAt") or row.get("timestamp")),
            normalize_text(row.get("actorName")),
            normalize_text(row.get("actorUsername")),
            normalize_text(row.get("actorRoleLabel")),
            normalize_text(row.get("action")),
            normalize_text(row.get("module")),
            normalize_text(row.get("description")),
            normalize_text(row.get("route")),
            normalize_text(row.get("method")),
        ])
    return headers, rows

def fetch_activity_logs_for_export(cursor, args) -> list[dict[str, object]]:
    base_sql, params, meta = activity_filter_query(args, include_pagination=False)
    cursor.execute(
        f"""
        SELECT l.*
        {base_sql}
        ORDER BY {meta["orderSql"]}
        """,
        tuple(params),
    )
    return [activity_log_row_to_dict(row) for row in cursor.fetchall() or []]




_EVAL_REMINDER_AUTO_RUN_DATE: str | None = None


@app.before_request
def auto_run_streaming_evaluation_reminders_once_per_day():
    """Menjalankan pengingat evaluasi sekali per hari saat aplikasi menerima request.

    Catatan: untuk produksi, endpoint `/api/evaluasi-streaming/reminders/run` tetap bisa dipanggil
    lewat cron harian. Hook ini membantu mode lokal/dev agar notifikasi tetap dibuat otomatis
    tanpa harus membuka dashboard tertentu terlebih dahulu.
    """
    global _EVAL_REMINDER_AUTO_RUN_DATE
    path = request.path or ""
    if path.startswith("/static/") or path.startswith("/uploads/") or path == "/favicon.ico":
        return
    if path == "/api/evaluasi-streaming/reminders/run":
        return
    today_key = datetime.now().date().isoformat()
    if _EVAL_REMINDER_AUTO_RUN_DATE == today_key:
        return
    try:
        create_streaming_evaluation_reminder_notifications()
        _EVAL_REMINDER_AUTO_RUN_DATE = today_key
    except Exception as exc:
        # Jangan sampai halaman utama gagal hanya karena generator notif bermasalah.
        print(f"[WARN] Gagal auto-run pengingat evaluasi streaming: {exc}")



def bootstrap_database() -> None:
    """Menjalankan bootstrap tabel utama seperti pada app.py server lama."""
    try:
        ensure_auth_schema()
        ensure_news_schema()
        ensure_agenda_schema()
        ensure_notifications_schema()
        ensure_activity_log_schema()
        ensure_misa_besar_schema()
    except Exception as exc:
        print(f"[WARN] MySQL bootstrap skipped: {exc}")
