from pathlib import Path
import json
from datetime import datetime
from io import BytesIO
import os
import re
import time
import uuid

import mysql.connector
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
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
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".pdf",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".txt", ".csv",
}
PREVIEWABLE_ATTACHMENT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".pdf",
}
INVENTORY_DEFAULT_CATEGORIES = ["Kamera", "Audio", "Aksesori", "Switcher", "Kabel", "Lighting", "Lainnya"]
INVENTORY_DEFAULT_ITEMS = [
    # {
    #     "id": "inv-001",
    #     "code": "CAM-001",
    #     "name": "Kamera Sony A6400",
    #     "category": "Kamera",
    #     "location": "Lemari Studio A",
    #     "purchaseDate": "2025-11-12",
    #     "purchasePrice": 12500000,
    #     "totalUnit": 2,
    #     "availableUnit": 1,
    #     "hasMultiple": True,
    #     "canBorrow": True,
    #     "condition": "Baik",
    #     "status": "Dipinjam",
    #     "notes": "Satu unit sedang dipakai untuk dokumentasi agenda.",
    #     "photos": [],
    #     "unitDetails": [],
    # },
    # {
    #     "id": "inv-002",
    #     "code": "AUD-004",
    #     "name": "Wireless Microphone Set",
    #     "category": "Audio",
    #     "location": "Rak Audio 2",
    #     "purchaseDate": "2025-12-03",
    #     "purchasePrice": None,
    #     "totalUnit": 4,
    #     "availableUnit": 4,
    #     "hasMultiple": True,
    #     "canBorrow": True,
    #     "condition": "Baik",
    #     "status": "Tersedia",
    #     "notes": "Baterai cadangan tersedia 8 pcs.",
    #     "photos": [],
    #     "unitDetails": [],
    # },
    # {
    #     "id": "inv-003",
    #     "code": "TRI-002",
    #     "name": "Tripod Heavy Duty",
    #     "category": "Aksesori",
    #     "location": "Gudang Perlengkapan",
    #     "purchaseDate": "2025-10-28",
    #     "purchasePrice": 850000,
    #     "totalUnit": 3,
    #     "availableUnit": 2,
    #     "hasMultiple": True,
    #     "canBorrow": True,
    #     "condition": "Rusak Ringan",
    #     "status": "Tersedia",
    #     "notes": "1 unit perlu pengencangan lock kaki.",
    #     "photos": [],
    #     "unitDetails": [],
    # },
    # {
    #     "id": "inv-004",
    #     "code": "SWI-001",
    #     "name": "Video Switcher ATEM Mini",
    #     "category": "Switcher",
    #     "location": "Meja Kontrol",
    #     "purchaseDate": "2025-09-19",
    #     "purchasePrice": 7600000,
    #     "totalUnit": 1,
    #     "availableUnit": 0,
    #     "hasMultiple": False,
    #     "canBorrow": True,
    #     "condition": "Baik",
    #     "status": "Dipinjam",
    #     "notes": "Dipakai untuk misa Kamis malam.",
    #     "photos": [],
    #     "unitDetails": [],
    # },
    # {
    #     "id": "inv-005",
    #     "code": "CAB-015",
    #     "name": "Kabel HDMI 10m",
    #     "category": "Kabel",
    #     "location": "Laci Kabel",
    #     "purchaseDate": "2025-11-30",
    #     "purchasePrice": 450000,
    #     "totalUnit": 6,
    #     "availableUnit": 5,
    #     "hasMultiple": True,
    #     "canBorrow": True,
    #     "condition": "Baik",
    #     "status": "Tersedia",
    #     "notes": "Label kabel sudah diperbarui.",
    #     "photos": [],
    #     "unitDetails": [],
    # },
]

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
    """Helper method to remove a physical file from the uploads directory."""
    if not file_url:
        return
    try:
        # Gunakan Pathlib untuk safety cross-platform path resolution
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


INVENTORY_UNIT_STATUSES = {"Tersedia", "Dipinjam", "Perbaikan", "Hilang"}


def inventory_unit_reason_for_status(status: str) -> str:
    return {
        "Dipinjam": "Sedang digunakan",
        "Perbaikan": "Sedang diperbaiki",
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
    return "; ".join(parts)


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
        "condition": normalize_text(row.get("condition")) or "Baik",
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


def inventory_filter_items(items: list[dict[str, object]], search: str = "", category: str = "all", condition: str = "all", status: str = "all", sort_mode: str = "updated-desc") -> list[dict[str, object]]:
    keyword = normalize_text(search).lower()
    category_value = normalize_text(category) or "all"
    condition_value = normalize_text(condition) or "all"
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
        matches_condition = condition_value == "all" or normalize_text(item.get("condition")) == condition_value
        matches_status = status_value == "all" or normalize_text(item.get("status")) == status_value
        if matches_keyword and matches_category and matches_condition and matches_status:
            filtered.append(item)

    return inventory_sort_items(filtered, sort_mode)


def inventory_request_filters(args) -> dict[str, str]:
    return {
        "search": normalize_text(args.get("search")),
        "category": normalize_text(args.get("category")) or "all",
        "condition": normalize_text(args.get("condition")) or "all",
        "status": normalize_text(args.get("status")) or "all",
        "sort": normalize_text(args.get("sort")) or "updated-desc",
    }


def ensure_column(cursor, table_name: str, column_name: str, definition: str) -> None:
    """Ensure a column exists in a table. If not, add it using ALTER TABLE."""
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (MYSQL_CONFIG["database"], table_name, column_name),
    )
    row = cursor.fetchone()
    
    # PERBAIKAN: Menangani cursor dictionary maupun tuple agar tidak memicu KeyError: 0
    if isinstance(row, dict):
        exists = list(row.values())[0] > 0
    else:
        exists = row[0] > 0 if row else False
        
    if not exists:
        cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {definition}")

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
          `condition` varchar(50) NOT NULL DEFAULT 'Baik',
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
    
    # PERBAIKAN: Indentasi disejajarkan ke kiri (sejajar dengan cursor.execute)
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

    cursor.execute("SELECT COUNT(*) FROM `inventory_items`")
    if cursor.fetchone()[0] == 0:
        for index, item in enumerate(INVENTORY_DEFAULT_ITEMS, start=1):
            cursor.execute(
                """
                INSERT INTO `inventory_items`
                (`id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`, `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `condition`, `status`, `notes`, `photos`, `unit_details`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    item.get("id") or f"inv-{index:03d}",
                    item.get("code") or f"INV-{index:03d}",
                    item.get("name") or f"Barang {index}",
                    item.get("category") or "Lainnya",
                    item.get("location") or "Gudang",
                    item.get("purchaseDate"),
                    item.get("purchasePrice"),
                    int(item.get("totalUnit") or 1),
                    int(item.get("availableUnit") or 1),
                    1 if item.get("hasMultiple") else 0,
                    1 if item.get("canBorrow", True) else 0,
                    item.get("condition") or "Baik",
                    item.get("status") or "Tersedia",
                    item.get("notes") or "",
                    json.dumps(item.get("photos") or [], ensure_ascii=False),
                    json.dumps(
                        normalize_inventory_unit_details(
                            item.get("unitDetails"),
                            int(item.get("totalUnit") or 1),
                            int(item.get("availableUnit") or 1),
                            fallback_status=item.get("status") or "Tersedia",
                        ),
                        ensure_ascii=False,
                    ),
                ),
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
    condition = normalize_text(data.get("condition")) or "Baik"
    if condition not in {"Baik", "Rusak Ringan", "Rusak Berat", "Hilang"}:
        condition = "Baik"
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
        "condition": condition,
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
        "Tanggal Pembelian",
        "Harga Pembelian",
        "Total Unit",
        "Unit Tersedia",
        "Dipinjam",
        "Bisa Dipinjam",
        "Kondisi",
        "Status",
        "Rincian Unit",
        "Foto",
        "Keterangan",
        "Update Terakhir",
    ]
    rows = []
    
    # PERBAIKAN: Format domain utama (Sesuaikan URL jika di-online-kan)
    base_url = "http://127.0.0.1:5000" 

    for item in items:
        photos = item.get("photos") or []
        
        # PERBAIKAN: Ubah array foto menjadi link URL penuh yang dapat di-klik atau dipreview
        photo_links = []
        for p in photos:
            if isinstance(p, dict) and p.get("url"):
                url = str(p.get("url"))
                # Ubah relative url jadi absolute
                if url.startswith("/"):
                    url = f"{base_url}{url}"
                photo_links.append(url)
                
        photo_label = ", ".join(photo_links) if photo_links else "-"
        
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
            normalize_text(item.get("condition")),
            normalize_text(item.get("status")),
            inventory_unit_details_text(item.get("unitDetails") or []),
            photo_label,
            normalize_text(item.get("notes")) or "-",
            normalize_text(item.get("updatedAt")) or "-",
        ])
    return headers, rows


def inventory_export_filename(extension: str) -> str:
    return f"laporan-data-inventaris-barang.{extension}"


def fetch_inventory_items_for_report(cursor, filters: dict[str, str]) -> list[dict[str, object]]:
    cursor.execute(
        """
        SELECT `id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`,
                   `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `condition`, `status`,
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
        condition=filters.get("condition", "all"),
        status=filters.get("status", "all"),
        sort_mode=filters.get("sort", "updated-desc"),
    )

# TAMBAHKAN PERBAIKAN INI di atas endpoint get_inventory_categories
# Fungsi format_currency ini sebelumnya crash jika menerima data null saat akan diexport PDF
def format_currency(value):
    if value is None or value == "" or str(value).lower() == "none":
        return "-"
    try:
        val = int(value)
        return f"Rp {val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "-"

@app.route("/api/inventory/categories", methods=["GET"])
def get_inventory_categories():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT `name` FROM `inventory_categories` ORDER BY `order_index` ASC, `name` ASC")
        categories = [row["name"] for row in cursor.fetchall() or [] if row.get("name")]
        if not categories:
            categories = INVENTORY_DEFAULT_CATEGORIES[:]
        return jsonify({"success": True, "categories": categories})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/categories", methods=["POST"])
def create_inventory_category():
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    category_name = normalize_text(data.get("name"))
    if not category_name:
        return jsonify({"success": False, "error": "Nama kategori wajib diisi."}), 400

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        ensure_inventory_category(cursor, category_name)
        conn.commit()
        return jsonify({"success": True, "name": category_name})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/categories/<category_name>", methods=["PUT"])
def update_inventory_category(category_name):
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    new_name = normalize_text(data.get("name"))
    old_name = normalize_text(category_name)
    if not old_name or not new_name:
        return jsonify({"success": False, "error": "Nama kategori tidak valid."}), 400

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT `id` FROM `inventory_categories` WHERE `name` = %s LIMIT 1", (old_name,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "Kategori tidak ditemukan."}), 404
        if new_name != old_name:
            cursor.execute("SELECT COUNT(*) FROM `inventory_categories` WHERE `name` = %s", (new_name,))
            if fetch_scalar_value(cursor.fetchone(), 0) > 0:
                return jsonify({"success": False, "error": "Nama kategori sudah dipakai."}), 400

        cursor.execute("UPDATE `inventory_categories` SET `name` = %s WHERE `name` = %s", (new_name, old_name))
        cursor.execute("UPDATE `inventory_items` SET `category` = %s WHERE `category` = %s", (new_name, old_name))
        conn.commit()
        return jsonify({"success": True, "name": new_name})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/categories/<category_name>", methods=["DELETE"])
def delete_inventory_category(category_name):
    ensure_auth_schema()
    old_name = normalize_text(category_name)
    if not old_name:
        return jsonify({"success": False, "error": "Kategori tidak valid."}), 400

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) FROM `inventory_items` WHERE `category` = %s", (old_name,))
        if fetch_scalar_value(cursor.fetchone(), 0) > 0:
            return jsonify({"success": False, "error": "Kategori ini masih dipakai oleh data inventaris."}), 409
        cursor.execute("DELETE FROM `inventory_categories` WHERE `name` = %s", (old_name,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/items", methods=["GET"])
def get_inventory_items():
    ensure_auth_schema()
    filters = inventory_request_filters(request.args)
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
             SELECT `id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`,
                 `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `condition`, `status`,
                 `notes`, `photos`, `unit_details`, `created_at`, `updated_at`
            FROM `inventory_items`
            ORDER BY `updated_at` DESC, `code` ASC
            """
        )
        raw_items = [inventory_item_row_to_dict(row) for row in cursor.fetchall() or []]
        categories = []
        cursor.execute("SELECT `name` FROM `inventory_categories` ORDER BY `order_index` ASC, `name` ASC")
        for row in cursor.fetchall() or []:
            if row.get("name"):
                categories.append(row["name"])

        items = inventory_filter_items(
            raw_items,
            search=filters["search"],
            category=filters["category"],
            condition=filters["condition"],
            status=filters["status"],
            sort_mode=filters["sort"],
        )
        return jsonify({
            "success": True,
            "items": items,
            "categories": categories or INVENTORY_DEFAULT_CATEGORIES[:],
            "summary": inventory_summary_from_items(items),
            "filters": filters,
        })
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/items/<item_id>", methods=["GET"])
def get_inventory_item(item_id):
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
             SELECT `id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`,
                 `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `condition`, `status`,
                 `notes`, `photos`, `unit_details`, `created_at`, `updated_at`
            FROM `inventory_items`
            WHERE `id` = %s
            LIMIT 1
            """,
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Barang inventaris tidak ditemukan."}), 404
        return jsonify({"success": True, "item": inventory_item_row_to_dict(row)})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/items", methods=["POST"])
def create_inventory_item():
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        payload = inventory_item_payload_from_request(data)
        cursor.execute("SELECT COUNT(*) FROM `inventory_items` WHERE `code` = %s", (payload["code"],))
        if fetch_scalar_value(cursor.fetchone(), 0) > 0:
            return jsonify({"success": False, "error": "Kode barang sudah dipakai."}), 400

        ensure_inventory_category(cursor, payload["category"])
        item_id = normalize_text(data.get("id")) or f"inv-{int(time.time() * 1000)}"
        cursor.execute(
            """
            INSERT INTO `inventory_items`
            (`id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`, `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `condition`, `status`, `notes`, `photos`, `unit_details`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                item_id,
                payload["code"],
                payload["name"],
                payload["category"],
                payload["location"],
                payload["purchase_date"],
                payload["purchase_price"],
                payload["total_unit"],
                payload["available_unit"],
                payload["has_multiple"],
                payload["can_borrow"],
                payload["condition"],
                payload["status"],
                payload["notes"],
                json.dumps(payload["photos"], ensure_ascii=False),
                json.dumps(payload["unit_details"], ensure_ascii=False),
            ),
        )
        conn.commit()
        return jsonify({"success": True, "item": get_inventory_item_response(cursor, item_id)})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


def get_inventory_item_response(cursor, item_id: str) -> dict[str, object]:
    cursor.execute(
        """
        SELECT `id`, `code`, `name`, `category`, `location`, `purchase_date`, `purchase_price`,
         `total_unit`, `available_unit`, `has_multiple`, `can_borrow`, `condition`, `status`,
         `notes`, `photos`, `unit_details`, `created_at`, `updated_at`
        FROM `inventory_items`
        WHERE `id` = %s
        LIMIT 1
        """,
        (item_id,),
    )
    row = cursor.fetchone() or {}
    return inventory_item_row_to_dict(row)


@app.route("/api/inventory/items/<item_id>", methods=["PUT"])
def update_inventory_item(item_id):
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `inventory_items` WHERE `id` = %s LIMIT 1", (item_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "Barang inventaris tidak ditemukan."}), 404

        payload = inventory_item_payload_from_request(data, existing)
        cursor.execute(
            "SELECT COUNT(*) FROM `inventory_items` WHERE `code` = %s AND `id` <> %s",
            (payload["code"], item_id),
        )
        if fetch_scalar_value(cursor.fetchone(), 0) > 0:
            return jsonify({"success": False, "error": "Kode barang sudah dipakai."}), 400

        ensure_inventory_category(cursor, payload["category"])
        old_photos = normalize_inventory_photos(safe_json_loads(existing.get("photos"), []))
        new_photos = payload["photos"]

        cursor.execute(
            """
            UPDATE `inventory_items`
            SET `code` = %s,
                `name` = %s,
                `category` = %s,
                `location` = %s,
                `purchase_date` = %s,
                `purchase_price` = %s,
                `total_unit` = %s,
                `available_unit` = %s,
                `has_multiple` = %s,
                `can_borrow` = %s,
                `condition` = %s,
                `status` = %s,
                `notes` = %s,
                `photos` = %s,
                `unit_details` = %s
            WHERE `id` = %s
            """,
            (
                payload["code"],
                payload["name"],
                payload["category"],
                payload["location"],
                payload["purchase_date"],
                payload["purchase_price"],
                payload["total_unit"],
                payload["available_unit"],
                payload["has_multiple"],
                payload["can_borrow"],
                payload["condition"],
                payload["status"],
                payload["notes"],
                json.dumps(new_photos, ensure_ascii=False),
                json.dumps(payload["unit_details"], ensure_ascii=False),
                item_id,
            ),
        )
        conn.commit()

        old_urls = {photo.get("url") for photo in old_photos if photo.get("url")}
        new_urls = {photo.get("url") for photo in new_photos if photo.get("url")}
        for removed_url in old_urls - new_urls:
            remove_physical_file(removed_url)

        return jsonify({"success": True, "item": get_inventory_item_response(cursor, item_id)})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/items/<item_id>", methods=["DELETE"])
def delete_inventory_item(item_id):
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT `photos`, `name` FROM `inventory_items` WHERE `id` = %s LIMIT 1", (item_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "Barang inventaris tidak ditemukan."}), 404

        cursor.execute("DELETE FROM `inventory_items` WHERE `id` = %s", (item_id,))
        conn.commit()

        for photo in normalize_inventory_photos(safe_json_loads(existing.get("photos"), [])):
            remove_physical_file(photo.get("url") or "")

        return jsonify({"success": True})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Hapus dan Gantikan endpoint /api/inventory/export.xlsx dengan yang berikut ini:
@app.route("/api/inventory/export.xlsx", methods=["GET"])
def export_inventory_excel():
    ensure_auth_schema()
    filters = inventory_request_filters(request.args)
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        items = fetch_inventory_items_for_report(cursor, filters)

        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill

        headers, rows = inventory_export_rows(items)
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Inventaris"
        worksheet.append(headers)
        for row in rows:
            worksheet.append(row)

        header_fill = PatternFill("solid", fgColor="7F0000")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                try:
                    cell_value = str(cell.value or "")
                    if len(cell_value) > max_length:
                        max_length = len(cell_value)
                except Exception:
                    continue
            worksheet.column_dimensions[column_letter].width = min(max_length + 4, 40)

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        
        # PERBAIKAN: as_attachment True untuk Excel karena bukan file untuk dipreview browser
        return send_file(
            buffer,
            as_attachment=True,
            download_name=inventory_export_filename("xlsx"),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    finally:
        cursor.close()
        conn.close()


@app.route("/api/inventory/export.pdf", methods=["GET"])
def export_inventory_pdf():
    ensure_auth_schema()
    filters = inventory_request_filters(request.args)
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        items = fetch_inventory_items_for_report(cursor, filters)

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

        headers, rows = inventory_export_rows(items)
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=8 * mm,
            leftMargin=8 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("InventoryTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=14, leading=16, textColor=colors.HexColor("#7F0000"))
        normal_style = ParagraphStyle("InventoryNormal", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10)

        elements = [
            Paragraph("Laporan Data Inventaris Barang", title_style),
            Spacer(1, 4 * mm),
            Paragraph(f"Filter: {filters.get('category', 'all')} | Cari: {filters.get('search', '') or '-'} | Urutan: {filters.get('sort', 'updated-desc')}", normal_style),
            Spacer(1, 4 * mm),
        ]

        table_data = [headers] + rows if rows else [headers, ["-" for _ in headers]]
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7F0000")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#FFFFFF")]),
                ]
            )
        )
        elements.append(table)
        document.build(elements)
        buffer.seek(0)
        
        # PERBAIKAN: as_attachment=False agar browser langsung mem-preview PDF di tab baru
        return send_file(
            buffer,
            as_attachment=False, 
            download_name=inventory_export_filename("pdf"),
            mimetype="application/pdf",
        )
    finally:
        cursor.close()
        conn.close()

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
    # Ensure loan requests schema exists and provide current session info
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
          `tanggal_selesai` date DEFAULT NULL,
          `tujuan` text DEFAULT NULL,
          `status` varchar(50) NOT NULL DEFAULT 'pending',
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `idx_loan_status` (`status`),
          KEY `idx_loan_member` (`member_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )

# --- LOAN REQUESTS ENDPOINTS ---

@app.route("/api/pengajuan", methods=["GET"])
def list_pengajuan():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_loan_schema(cursor)
        
        status_filter = request.args.get('status')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        query = "SELECT * FROM `loan_requests` WHERE 1=1"
        params = []
        
        # PERBAIKAN: Jika bukan admin, hanya ambil data milik user yang sedang login
        role = session.get("role") or ""
        if role not in ["admin", "super_admin"]:
            user_id = session.get("user_id")
            if not user_id:
                return jsonify({"success": True, "items": []})
            query += " AND `member_id` = %s"
            params.append(str(user_id))
        
        if status_filter and status_filter != 'all':
            query += " AND `status` = %s"
            params.append(status_filter)
        if from_date:
            query += " AND `tanggal_mulai` >= %s"
            params.append(from_date)
        if to_date:
            query += " AND `tanggal_mulai` <= %s"
            params.append(to_date)
            
        query += " ORDER BY `created_at` DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall() or []
        items = []
        for r in rows:
            items.append({
                "id": r.get("id"),
                "memberId": r.get("member_id"),
                "barangId": r.get("barang_id"),
                "barangNama": r.get("barang_name"),
                "barangCode": r.get("barang_code"),
                "barangFoto": r.get("barang_photo"),
                "jumlahDiminta": r.get("jumlah"),
                "tanggalPengajuan": r.get("tanggal_pengajuan"),
                "tanggalMulai": r.get("tanggal_mulai"),
                "tanggalSelesai": r.get("tanggal_selesai"),
                "tujuan": r.get("tujuan"),
                "status": r.get("status"),
                "adminNote": r.get("admin_note", ""),
                "approvedBy": r.get("approved_by", ""),
                "approvedAt": r.get("approved_at"),
                "createdAt": r.get("created_at"),
                "updatedAt": r.get("updated_at"),
            })
        return jsonify({"success": True, "items": items})
    finally:
        cursor.close()
        conn.close()

@app.route("/api/pengajuan", methods=["POST"])
def create_pengajuan():
    ensure_auth_schema()
    data = request.get_json(silent=True) or {}
    barang_id = data.get("barangId")
    barang_nama = data.get("barangNama")
    jumlah = int(data.get("jumlahDiminta") or data.get("jumlah") or 0)
    tanggal_mulai = data.get("tanggalMulai")
    tanggal_selesai = data.get("tanggalSelesai")
    tujuan = data.get("tujuan")

    if not barang_id or not barang_nama or not jumlah or not tanggal_mulai or not tanggal_selesai or not tujuan:
        return jsonify({"success": False, "error": "Field tidak lengkap"}), 400

    try:
        if datetime.fromisoformat(tanggal_mulai) >= datetime.fromisoformat(tanggal_selesai):
            return jsonify({"success": False, "error": "Tanggal selesai harus lebih besar dari tanggal mulai"}), 400
    except Exception:
        pass

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        ensure_loan_schema(cursor)
        pengajuan_id = f"pjn-{int(datetime.utcnow().timestamp() * 1000)}"

        # try to get barang foto/code from inventory
        barang_foto = None
        barang_code = None
        try:
            c2 = conn.cursor(dictionary=True)
            c2.execute("SELECT `code`, `photos` FROM `inventory_items` WHERE `id` = %s LIMIT 1", (barang_id,))
            row = c2.fetchone()
            if row:
                barang_code = row.get("code")
                photos_raw = row.get("photos")
                try:
                    photos = json.loads(photos_raw) if photos_raw else []
                    if isinstance(photos, list) and photos:
                        first = photos[0]
                        if isinstance(first, dict):
                            barang_foto = first.get("url") or first.get("uri") or None
                        elif isinstance(first, str):
                            barang_foto = first
                except Exception:
                    pass
            c2.close()
        except Exception:
            pass

        cursor.execute(
            """
            INSERT INTO `loan_requests` (`id`, `member_id`, `barang_id`, `barang_name`, `barang_code`, `barang_photo`, `jumlah`, `tanggal_pengajuan`, `tanggal_mulai`, `tanggal_selesai`, `tujuan`, `status`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pengajuan_id,
                session.get("user_id") or None,
                barang_id,
                barang_nama,
                barang_code,
                barang_foto,
                jumlah,
                datetime.utcnow().date(),
                tanggal_mulai,
                tanggal_selesai,
                tujuan,
                "pending",
            ),
        )
        conn.commit()
        
        # Admin Notification
        try:
            ensure_notifications_schema()
            nc = conn.cursor()
            try:
                # PERBAIKAN: Sertakan target_role="admin"
                create_notification(nc, "form", f"Pengajuan Peminjaman Baru: {barang_nama}", f"Pengajuan oleh user ID {session.get('user_id')}", url_for('dashboard') if False else "/persetujuan-peminjaman.html", {"pengajuan_id": pengajuan_id}, target_role="admin")
                conn.commit()
            finally:
                nc.close()
        except Exception:
            pass
            
        return jsonify({"success": True, "id": pengajuan_id})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/pengajuan/<pengajuan_id>/cancel", methods=["POST"])
def cancel_pengajuan(pengajuan_id):
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        ensure_loan_schema(cursor)
        cursor.execute("SELECT `status` FROM `loan_requests` WHERE `id` = %s LIMIT 1", (pengajuan_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Pengajuan tidak ditemukan"}), 404
        status = row[0]
        if status != "pending":
            return jsonify({"success": False, "error": "Hanya pengajuan dengan status pending dapat dibatalkan"}), 400
        cursor.execute("UPDATE `loan_requests` SET `status` = %s WHERE `id` = %s", ("cancelled", pengajuan_id))
        conn.commit()
        return jsonify({"success": True})
    finally:
        cursor.close()
        conn.close()

@app.route("/api/admin/pengajuan/<pengajuan_id>/status", methods=["PUT"])
def update_pengajuan_status(pengajuan_id):
    role = session.get("role") or ""
    if not session.get("logged_in") or role not in ["admin", "super_admin"]:
        return jsonify({"success": False, "error": "Akses Ditolak. Anda bukan Admin."}), 403
        
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    admin_note = data.get("adminNote", "")
    
    if new_status not in ["approved", "rejected", "cancelled", "taken", "returned"]:
        return jsonify({"success": False, "error": "Status tidak valid"}), 400

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_column(cursor, "loan_requests", "admin_note", "`admin_note` text DEFAULT NULL")
        ensure_column(cursor, "loan_requests", "approved_by", "`approved_by` varchar(150) DEFAULT NULL")
        ensure_column(cursor, "loan_requests", "approved_at", "`approved_at` datetime DEFAULT NULL")

        cursor.execute("SELECT * FROM `loan_requests` WHERE `id` = %s LIMIT 1", (pengajuan_id,))
        req = cursor.fetchone()
        if not req:
            return jsonify({"success": False, "error": "Pengajuan tidak ditemukan"}), 404
            
        current_status = req.get("status")
        barang_id = req.get("barang_id")
        jumlah_req = int(req.get("jumlah", 1))
        
        # Validasi update status
        if current_status != "pending" and new_status in ["approved", "rejected"]:
             return jsonify({"success": False, "error": "Hanya pengajuan berstatus Pending yang dapat disetujui atau ditolak"}), 400

        # Jika Setujui (Approve), potong stok
        if new_status == "approved" and current_status == "pending":
            cursor.execute("SELECT `total_unit`, `available_unit`, `can_borrow`, `unit_details` FROM `inventory_items` WHERE `id` = %s LIMIT 1", (barang_id,))
            inv = cursor.fetchone()
            
            if not inv:
                 return jsonify({"success": False, "error": "Barang tidak ditemukan di inventaris"}), 404
            if not bool(inv.get("can_borrow", 1)):
                 return jsonify({"success": False, "error": "Barang tidak dapat dipinjam"}), 400
                 
            available = int(inv.get("available_unit", 0))
            if available < jumlah_req:
                 return jsonify({"success": False, "error": f"Stok tersedia ({available}) tidak mencukupi permintaan ({jumlah_req})"}), 400
                 
            # PERBAIKAN: Update unit_details JSON juga jika barang multiple unit
            unit_details_raw = safe_json_loads(inv.get("unit_details"), [])
            units_changed = 0
            
            for unit in unit_details_raw:
                 if unit.get("status") == "Tersedia" and units_changed < jumlah_req:
                      unit["status"] = "Dipinjam"
                      unit["reason"] = f"Dipinjam (Req ID: {pengajuan_id})"
                      unit["available"] = False
                      units_changed += 1
                      
            new_available = available - jumlah_req
            new_inv_status = "Dipinjam" if new_available <= 0 else "Tersedia"
            
            cursor.execute(
                 "UPDATE `inventory_items` SET `available_unit` = %s, `status` = %s, `unit_details` = %s WHERE `id` = %s", 
                 (new_available, new_inv_status, json.dumps(unit_details_raw, ensure_ascii=False), barang_id)
            )
            
        # Jika Cancelled/Returned, tetapi sebelumnya memotong stok (Pengembalian Stok)
        elif (new_status in ["cancelled", "returned"]) and (current_status in ["approved", "taken"]):
             cursor.execute("SELECT `total_unit`, `available_unit`, `unit_details` FROM `inventory_items` WHERE `id` = %s LIMIT 1", (barang_id,))
             inv = cursor.fetchone()
             if inv:
                 total = int(inv.get("total_unit", 1))
                 available = int(inv.get("available_unit", 0))
                 
                 # Kembalikan unit_details yang dipinjam oleh pengajuan ini
                 unit_details_raw = safe_json_loads(inv.get("unit_details"), [])
                 units_restored = 0
                 
                 for unit in unit_details_raw:
                      # Kembalikan unit yang ditandai dengan ID Pengajuan ini
                      if unit.get("reason") == f"Dipinjam (Req ID: {pengajuan_id})":
                           unit["status"] = "Tersedia"
                           unit["reason"] = ""
                           unit["available"] = True
                           units_restored += 1
                 
                 # Jika tidak ada yang pakai ID spesifik, kita restore secara general
                 if units_restored == 0:
                      for unit in unit_details_raw:
                           if unit.get("status") == "Dipinjam" and units_restored < jumlah_req:
                                unit["status"] = "Tersedia"
                                unit["reason"] = ""
                                unit["available"] = True
                                units_restored += 1
                 
                 new_available = min(total, available + jumlah_req)
                 new_inv_status = "Tersedia" if new_available > 0 else "Dipinjam"
                 
                 cursor.execute(
                      "UPDATE `inventory_items` SET `available_unit` = %s, `status` = %s, `unit_details` = %s WHERE `id` = %s", 
                      (new_available, new_inv_status, json.dumps(unit_details_raw, ensure_ascii=False), barang_id)
                 )
        
        # Simpan status ke tabel loan_requests
        admin_name = str(session.get("nama") or session.get("username") or "Admin")
        approved_at = datetime.utcnow() if new_status != "pending" else None
        
        cursor.execute(
            """
            UPDATE `loan_requests` 
            SET `status` = %s, `admin_note` = %s, `approved_by` = %s, `approved_at` = COALESCE(`approved_at`, %s)
            WHERE `id` = %s
            """,
            (new_status, admin_note, admin_name, approved_at, pengajuan_id)
        )
        
        # --- PERBAIKAN: Kirim Notifikasi ke User/Anggota ---
        try:
            ensure_notifications_schema()
            # Ambil detail barang dan user dari pengajuan untuk isi notif
            barang_name = req.get("barang_name", "Barang")
            member_id = req.get("member_id")
            
            if member_id: # Pastikan pengajuan ini milik seorang user yang terdaftar
                status_label = "Disetujui" if new_status == "approved" else ("Ditolak" if new_status == "rejected" else ("Dibatalkan" if new_status == "cancelled" else new_status))
                
                notif_title = f"Peminjaman {status_label}: {barang_name}"
                notif_body = f"Pengajuan peminjaman Anda untuk {barang_name} telah {status_label.lower()} oleh Admin."
                if admin_note:
                    notif_body += f" Catatan: {admin_note}"

                # Buat notifikasi dengan tipe 'peminjaman' dan target_role 'user'
                # Kita letakkan member_id di data JSON agar frontend bisa memfilternya
                nid = create_notification(
                    cursor, 
                    "peminjaman", 
                    notif_title, 
                    notif_body, 
                    url_for('dashboard_anggota') if False else "/pengajuan-peminjaman-barang-anggota.html", 
                    {"pengajuan_id": pengajuan_id, "target_user_id": member_id}, 
                    target_role="user"
                )
        except Exception as e:
            print(f"[WARN] Gagal mengirim notifikasi update status peminjaman: {e}")
        # ---------------------------------------------------

        conn.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

def ensure_news_schema() -> None:
    """Ensure news/article tables exist in database."""
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

        # PERBAIKAN: Menghapus potongan schema inventory yang tersesat (notes, photos, dll)
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
        # PERBAIKAN: Menambahkan schema image_url, image_name, dan attachments
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
        # ALTER TABLE IF COLUMNS DONT EXIST YET
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
        # PERBAIKAN: Tambah kolom target_role agar bisa membedakan notif admin/user
        ensure_column(cursor, "notifications", "target_role", "`target_role` varchar(50) DEFAULT NULL")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def create_notification(cursor, type_value: str, title: str, body: str, url: str | None = None, data: dict | None = None, target_role: str | None = None):
    nid = f"notif-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
    cursor.execute(
        """
        INSERT INTO `notifications` (`id`, `type`, `title`, `body`, `url`, `data`, `target_role`)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            nid,
            str(type_value or ""),
            str(title or ""),
            str(body or ""),
            str(url or "") if url else None,
            json.dumps(data or {}, ensure_ascii=False),
            target_role # Bisa spesifik diset "admin"
        ),
    )
    return nid

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    ensure_notifications_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    user_key = None
    role = "user" # default
    
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
        role = viewer.get("role") or "user"
    else:
        if client_key:
            user_key = client_key

    limit = int(request.args.get("limit") or 50)
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # PERBAIKAN: Tampilkan notifikasi yang bersifat global (NULL) atau sesuai role-nya
        target_roles = ["admin", "super_admin"] if role in ["admin", "super_admin"] else ["user"]
        format_strings = ','.join(['%s'] * len(target_roles))
        
        query = f"""
            SELECT * FROM `notifications` 
            WHERE `target_role` IS NULL OR `target_role` IN ({format_strings}) 
            ORDER BY `created_at` DESC LIMIT %s
        """
        params = tuple(target_roles) + (limit,)
        
        cursor.execute(query, params)
        rows = cursor.fetchall() or []
        results = []
        for r in rows:
            is_read = False
            if user_key:
                cursor.execute("SELECT 1 FROM `notification_reads` WHERE `notification_id` = %s AND `user_key` = %s LIMIT 1", (r["id"], user_key))
                is_read = cursor.fetchone() is not None
            results.append({
                "id": r.get("id"),
                "type": r.get("type"),
                "title": r.get("title"),
                "body": r.get("body"),
                "url": r.get("url"),
                "data": json.loads(r.get("data") or "{}"),
                "createdAt": r.get("created_at").isoformat() if r.get("created_at") else None,
                "read": bool(is_read),
            })
        return jsonify(results)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/notifications/<notif_id>/mark_read", methods=["POST"])
def mark_notification_read(notif_id):
    ensure_notifications_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
    else:
        user_key = client_key or None
    if not user_key:
        return jsonify({"success": False, "error": "Missing client key"}), 400

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT IGNORE INTO `notification_reads` (`notification_id`, `user_key`) VALUES (%s, %s)", (notif_id, user_key))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/notifications/<notif_id>/toggle_read", methods=["POST"])
def toggle_notification_read(notif_id):
    ensure_notifications_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
    else:
        user_key = client_key or None
    if not user_key:
        return jsonify({"success": False, "error": "Missing client key"}), 400

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM `notification_reads` WHERE `notification_id` = %s AND `user_key` = %s LIMIT 1", (notif_id, user_key))
        if cursor.fetchone():
            cursor.execute("DELETE FROM `notification_reads` WHERE `notification_id` = %s AND `user_key` = %s", (notif_id, user_key))
            is_read = False
        else:
            cursor.execute("INSERT IGNORE INTO `notification_reads` (`notification_id`, `user_key`) VALUES (%s, %s)", (notif_id, user_key))
            is_read = True
        conn.commit()
        return jsonify({"success": True, "read": is_read})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route("/api/notifications/mark_all_read", methods=["POST"])
def mark_all_notifications_read():
    ensure_notifications_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
    else:
        user_key = client_key or None
    if not user_key:
        return jsonify({"success": False, "error": "Missing client key"}), 400

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT `id` FROM `notifications`")
        rows = cursor.fetchall() or []
        for r in rows:
            try:
                cursor.execute("INSERT IGNORE INTO `notification_reads` (`notification_id`, `user_key`) VALUES (%s, %s)", (r["id"], user_key))
            except Exception:
                pass
        conn.commit()
        return jsonify({"success": True})
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


def render_public_page(template_name: str, **context):
    if not template_exists(template_name):
        abort(404)
    return render_template(template_name, current_user=current_user_context(), **context)

@app.route("/pengumuman")
def public_news_page():
    return render_public_page("pengumuman.html")

@app.route("/pengumuman/kategori/<category_slug>")
def public_news_category_page(category_slug):
    # Menyertakan category_slug jika dibutuhkan oleh Jinja, walau JS di FE juga bisa parsing URL
    return render_public_page("pengumuman.html", category_slug=category_slug)

@app.route("/pengumuman/<news_id>")
def public_news_detail_page(news_id):
    return render_public_page("pengumuman-detail.html", news_id=news_id)


@app.route("/agenda")
def public_agenda_page():
    return render_public_page("agenda.html")

@app.route("/agenda/<agenda_id>")
def public_agenda_detail_page(agenda_id):
    # Mengirim parameter agenda_id ke template sehingga JS di client bisa membaca ID yang akan di load
    return render_public_page("agenda-detail.html", agenda_id=agenda_id)

@app.route("/form-pendaftaran")
def public_registration_forms_page():
    return render_public_page("form-pendaftaran.html")

@app.route("/form-pendaftaran/<form_id>")
def public_registration_form_detail_page(form_id):
    return render_public_page("form-pendaftaran-detail.html", form_id=form_id)

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
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT `attachment_url` FROM `organization_profiles` WHERE `id` = %s LIMIT 1", (profile_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "Profile not found"}), 404

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

        # Cleanup file lama yang sudah dihapus/diganti saat Edit
        if existing:
            try:
                old_atts_raw = existing.get("attachment_url") or "[]"
                old_atts = json.loads(old_atts_raw) if isinstance(old_atts_raw, str) else (old_atts_raw or [])
                new_att_urls = [a.get("url") for a in attachments if isinstance(a, dict) and a.get("url")]
                
                for oa in old_atts:
                    if isinstance(oa, dict) and oa.get("url") and oa.get("url") not in new_att_urls:
                        remove_physical_file(oa["url"])
            except Exception as e:
                print(f"[WARN] Failed to cleanup replaced files for profile {profile_id}: {e}")

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
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch data profil untuk mendapatkan list file yang harus dihapus
        cursor.execute("SELECT `attachment_url` FROM `organization_profiles` WHERE `id` = %s LIMIT 1", (profile_id,))
        profile = cursor.fetchone()
        
        if not profile:
            return jsonify({"success": False, "error": "Profile not found"}), 404

        # 2. Hapus record dari database
        cursor.execute("DELETE FROM `organization_profiles` WHERE `id` = %s", (profile_id,))
        conn.commit()

        # 3. Clean up physical files di folder
        try:
            atts_raw = profile.get("attachment_url") or "[]"
            atts = json.loads(atts_raw) if isinstance(atts_raw, str) else (atts_raw or [])
            for att in atts:
                if isinstance(att, dict) and att.get("url"):
                    remove_physical_file(att["url"])
        except Exception as e:
            print(f"[WARN] Error during physical file cleanup for profile {profile_id}: {e}")

        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


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


@app.route("/api/registration/forms", methods=["GET"])
def get_registration_forms():
    ensure_registration_form_schema()
    scope = (request.args.get("scope") or "public").strip().lower()
    viewer = current_user_context()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `registration_forms` ORDER BY `updated_at` DESC, `created_at` DESC")
        rows = cursor.fetchall() or []
        counts = registration_form_submission_counts(cursor)
        forms = [registration_form_row_to_dict(row, counts.get(str(row.get("id") or ""), 0)) for row in rows]

        if scope == "admin":
            if not can_manage_registration_forms():
                return jsonify({"success": False, "error": "Forbidden"}), 403
            return jsonify(forms)

        accessible_forms = []
        for form in forms:
            if form.get("visibility") == "draft":
                continue
            # if form.get("target") == "internal" and not viewer.get("logged_in"):
            #     continue
            accessible_forms.append(form)
        return jsonify(accessible_forms)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/registration/forms/<form_id>", methods=["GET"])
def get_registration_form_detail(form_id):
    ensure_registration_form_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        form = registration_form_lookup(cursor, form_id, include_counts=True)
        if not form:
            return jsonify({"success": False, "error": "Form not found"}), 404

        viewer = current_user_context()
        if form.get("visibility") == "draft" and not can_manage_registration_forms():
            return jsonify({"success": False, "error": "Forbidden"}), 403
        # if form.get("target") == "internal" and not viewer.get("logged_in") and not can_manage_registration_forms():
        #     return jsonify({"success": False, "error": "Forbidden"}), 403

        return jsonify(form)
    finally:
        cursor.close()
        conn.close()


# Di dalam app.py, cari fungsi create_registration_form()
@app.route("/api/registration/forms", methods=["POST"])
def create_registration_form():
    ensure_registration_form_schema()
    if not can_manage_registration_forms():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    data = request.json or {}
    values = registration_form_payload_to_db_values(data)
    if not values["title"] or not values["open_date"] or not values["close_date"]:
        return jsonify({"success": False, "error": "Judul, tanggal pembukaan, dan tanggal penutupan wajib diisi."}), 400
    if not values["fields_json"] or values["fields_json"] == "[]":
        return jsonify({"success": False, "error": "Tambahkan minimal 1 pertanyaan."}), 400

    try:
        open_date = datetime.strptime(values["open_date"], "%Y-%m-%d").date()
        close_date = datetime.strptime(values["close_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Format tanggal tidak valid."}), 400
    if close_date < open_date:
        return jsonify({"success": False, "error": "Tanggal penutupan harus sama atau setelah tanggal pembukaan."}), 400

    form_id = data.get("id") or f"registration-form-{int(time.time() * 1000)}"
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `registration_forms`
            (`id`, `title`, `description`, `target`, `visibility`, `open_date`, `close_date`, `quota`, `image_url`, `image_name`, `attachments`, `fields_json`, `created_by`, `created_by_name`, `created_by_role`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                form_id,
                values["title"],
                values["description"],
                values["target"],
                values["visibility"],
                values["open_date"],
                values["close_date"],
                values["quota"],
                values["image_url"],
                values["image_name"],
                values["attachments"],
                values["fields_json"],
                str(session.get("user_id") or ""),
                str(session.get("nama") or session.get("username") or ""),
                str(session.get("role") or ""),
            ),
        )
        conn.commit()
        try:
            ensure_notifications_schema()
            nc = conn.cursor()
            try:
                # PERBAIKAN: ubah url_for agar mengarah ke halaman public FE, bukan ke API
                create_notification(nc, "form", f"Form Pendaftaran Baru: {values['title']}", values.get('description') or "Terdapat form pendaftaran baru.", url_for('public_registration_form_detail_page', form_id=form_id), {"form_id": form_id})
                conn.commit()
            finally:
                nc.close()
        except Exception:
            pass
        return jsonify({"success": True, "id": form_id})
    except mysql.connector.IntegrityError:
        conn.rollback()
        return jsonify({"success": False, "error": "ID form sudah digunakan."}), 409
    except Exception as error:
        conn.rollback()
        return jsonify({"success": False, "error": str(error)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/registration/forms/<form_id>", methods=["PUT"])
def update_registration_form(form_id):
    ensure_registration_form_schema()
    if not can_manage_registration_forms():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    data = request.json or {}
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `registration_forms` WHERE `id` = %s LIMIT 1", (form_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "Form not found"}), 404

        values = registration_form_payload_to_db_values(data, existing)
        if not values["title"] or not values["open_date"] or not values["close_date"]:
            return jsonify({"success": False, "error": "Judul, tanggal pembukaan, dan tanggal penutupan wajib diisi."}), 400
        if not values["fields_json"] or values["fields_json"] == "[]":
            return jsonify({"success": False, "error": "Tambahkan minimal 1 pertanyaan."}), 400

        try:
            open_date = datetime.strptime(values["open_date"], "%Y-%m-%d").date()
            close_date = datetime.strptime(values["close_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Format tanggal tidak valid."}), 400
        if close_date < open_date:
            return jsonify({"success": False, "error": "Tanggal penutupan harus sama atau setelah tanggal pembukaan."}), 400

        cursor.execute(
            """
            UPDATE `registration_forms`
            SET `title` = %s,
                `description` = %s,
                `target` = %s,
                `visibility` = %s,
                `open_date` = %s,
                `close_date` = %s,
                `quota` = %s,
                `image_url` = %s,
                `image_name` = %s,
                `attachments` = %s,
                `fields_json` = %s
            WHERE `id` = %s
            """,
            (
                values["title"],
                values["description"],
                values["target"],
                values["visibility"],
                values["open_date"],
                values["close_date"],
                values["quota"],
                values["image_url"],
                values["image_name"],
                values["attachments"],
                values["fields_json"],
                form_id,
            ),
        )
        conn.commit()

        # Cleanup file lama yang sudah dihapus/diganti saat Edit
        if existing:
            try:
                # Cleanup Image
                if existing.get("image_url") and existing.get("image_url") != values["image_url"]:
                    remove_physical_file(existing["image_url"])
                
                # Cleanup Attachments
                old_atts_raw = existing.get("attachments") or "[]"
                old_atts = json.loads(old_atts_raw) if isinstance(old_atts_raw, str) else (old_atts_raw or [])
                new_atts_raw = values.get("attachments") or "[]"
                new_atts = json.loads(new_atts_raw) if isinstance(new_atts_raw, str) else (new_atts_raw or [])
                new_att_urls = [a.get("url") for a in new_atts if isinstance(a, dict) and a.get("url")]
                
                for oa in old_atts:
                    if isinstance(oa, dict) and oa.get("url") and oa.get("url") not in new_att_urls:
                        remove_physical_file(oa["url"])
            except Exception as e:
                print(f"[WARN] Failed to cleanup replaced files for registration form {form_id}: {e}")


        return jsonify({"success": True, "id": form_id})
    except Exception as error:
        conn.rollback()
        return jsonify({"success": False, "error": str(error)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/registration/forms/<form_id>", methods=["DELETE"])
def delete_registration_form(form_id):
    ensure_registration_form_schema()
    if not can_manage_registration_forms():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch form data first to get the files we need to delete
        cursor.execute("SELECT `image_url`, `attachments` FROM `registration_forms` WHERE `id` = %s LIMIT 1", (form_id,))
        form = cursor.fetchone()
        
        if not form:
            return jsonify({"success": False, "error": "Form not found"}), 404

        # Delete the record from the database
        cursor.execute("DELETE FROM `registration_forms` WHERE `id` = %s", (form_id,))
        conn.commit()

        # Clean up physical files
        try:
            # Delete image
            if form.get("image_url"):
                remove_physical_file(form["image_url"])
            
            # Delete attachments
            attachments_raw = form.get("attachments") or "[]"
            attachments = json.loads(attachments_raw) if isinstance(attachments_raw, str) else (attachments_raw or [])
            for att in attachments:
                if isinstance(att, dict) and att.get("url"):
                    remove_physical_file(att["url"])
        except Exception as e:
            print(f"[WARN] Error during physical file cleanup for form {form_id}: {e}")


        return jsonify({"success": True})
    except Exception as error:
        conn.rollback()
        return jsonify({"success": False, "error": str(error)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/registration/forms/<form_id>/submissions", methods=["GET"])
def get_registration_form_submissions(form_id):
    ensure_registration_form_schema()
    if not can_manage_registration_forms():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        form = registration_form_lookup(cursor, form_id, include_counts=True)
        if not form:
            return jsonify({"success": False, "error": "Form not found"}), 404

        cursor.execute("SELECT * FROM `registration_form_submissions` WHERE `form_id` = %s ORDER BY `submitted_at` DESC", (form_id,))
        submissions = [registration_submission_row_to_dict(row) for row in cursor.fetchall() or []]
        return jsonify({"form": form, "submissions": submissions, "submissionCount": len(submissions)})
    finally:
        cursor.close()
        conn.close()


def registration_export_rows(form: dict[str, object], submissions: list[dict[str, object]]):
    fields = form.get("fields") if isinstance(form.get("fields"), list) else []
    headers = ["No", "Waktu Submit", "Identitas", "Role"] + [str(field.get("label") or "Pertanyaan") for field in fields if isinstance(field, dict)]
    rows = []

    # Format domain utama (Contoh untuk local) Jika dionline sesuaikan URL-nya jika ingin url full
    base_url = "http://127.0.0.1:5000" 

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


@app.route("/api/registration/forms/<form_id>/export.xlsx", methods=["GET"])
def export_registration_form_excel(form_id):
    ensure_registration_form_schema()
    if not can_manage_registration_forms():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        form = registration_form_lookup(cursor, form_id, include_counts=True)
        if not form:
            return jsonify({"success": False, "error": "Form not found"}), 404
        cursor.execute("SELECT * FROM `registration_form_submissions` WHERE `form_id` = %s ORDER BY `submitted_at` DESC", (form_id,))
        submissions = [registration_submission_row_to_dict(row) for row in cursor.fetchall() or []]

        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill

        headers, rows = registration_export_rows(form, submissions)
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Pendaftar"
        worksheet.append(headers)
        for row in rows:
            worksheet.append(row)

        header_fill = PatternFill("solid", fgColor="7F0000")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                try:
                    cell_value = str(cell.value or "")
                    if len(cell_value) > max_length:
                        max_length = len(cell_value)
                except Exception:
                    continue
            worksheet.column_dimensions[column_letter].width = min(max_length + 4, 40)

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=registration_export_filename(form, "xlsx"),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    finally:
        cursor.close()
        conn.close()


@app.route("/api/registration/forms/<form_id>/export.pdf", methods=["GET"])
def export_registration_form_pdf(form_id):
    ensure_registration_form_schema()
    if not can_manage_registration_forms():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        form = registration_form_lookup(cursor, form_id, include_counts=True)
        if not form:
            return jsonify({"success": False, "error": "Form not found"}), 404
        cursor.execute("SELECT * FROM `registration_form_submissions` WHERE `form_id` = %s ORDER BY `submitted_at` DESC", (form_id,))
        submissions = [registration_submission_row_to_dict(row) for row in cursor.fetchall() or []]

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

        headers, rows = registration_export_rows(form, submissions)
        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=8 * mm, leftMargin=8 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("RegistrationTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=14, leading=16, textColor=colors.HexColor("#7F0000"))
        normal_style = ParagraphStyle("RegistrationNormal", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10)

        elements = [
            Paragraph(f"Data Pendaftar: {form.get('title')}", title_style),
            Spacer(1, 4 * mm),
            Paragraph(f"Total pendaftar: {len(submissions)}", normal_style),
            Spacer(1, 4 * mm),
        ]

        table_data = [headers] + rows if rows else [headers, ["-", "-", "-", "-"] + ["" for _ in headers[4:]]]
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7F0000")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#FFFFFF")]),
                ]
            )
        )
        elements.append(table)
        document.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=registration_export_filename(form, "pdf"),
            mimetype="application/pdf",
        )
    finally:
        cursor.close()
        conn.close()


@app.route("/api/registration/forms/<form_id>/submit", methods=["POST"])
def submit_registration_form(form_id):
    ensure_registration_form_schema()
    data = request.json or {}
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        form = registration_form_lookup(cursor, form_id, include_counts=True)
        if not form:
            return jsonify({"success": False, "error": "Form not found"}), 404

        submission_count = int(form.get("submissionCount") or 0)
        state = registration_form_status(form, submission_count)
        if not state["open"]:
            return jsonify({"success": False, "error": state["text"]}), 400

        submitter, error_payload = registration_submitter_context(form, data.get("submitter"))
        if error_payload:
            error_body, status_code = error_payload
            return jsonify(error_body), status_code

        answers, error_message = registration_submission_payload_to_rows(form, data.get("answers"))
        if error_message:
            return jsonify({"success": False, "error": error_message}), 400

        cursor.execute(
            "SELECT 1 FROM `registration_form_submissions` WHERE `form_id` = %s AND `submitter_key` = %s LIMIT 1",
            (form_id, submitter["key"]),
        )
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Anda sudah pernah mengirim jawaban untuk form ini."}), 409

        submission_id = f"submission-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
        cursor.execute(
            """
            INSERT INTO `registration_form_submissions`
            (`id`, `form_id`, `submitter_key`, `submitter_identifier`, `submitter_role`, `submitter_user_id`, `submitter_source`, `answers_json`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                submission_id,
                form_id,
                submitter["key"],
                submitter["identifier"],
                submitter["role"],
                submitter["user_id"],
                submitter["source"],
                json.dumps(answers, ensure_ascii=False),
            ),
        )
        conn.commit()
        return jsonify({"success": True, "id": submission_id})
    except Exception as error:
        conn.rollback()
        return jsonify({"success": False, "error": str(error)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/api/registration/submissions/me", methods=["GET"])
def get_my_registration_submissions():
    ensure_registration_form_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()

    if viewer.get("logged_in"):
        submitter_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'public'}"
    else:
        if not client_key:
            return jsonify([])
        submitter_key = client_key

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM `registration_form_submissions` WHERE `submitter_key` = %s ORDER BY `submitted_at` DESC",
            (submitter_key,),
        )
        submissions = [registration_submission_row_to_dict(row) for row in cursor.fetchall() or []]
        return jsonify(submissions)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/session", methods=["GET"])
def get_session_context():
    return jsonify(current_user_context())


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
        try:
            ensure_notifications_schema()
            nc = conn.cursor()
            try:
                create_notification(nc, "agenda", f"Agenda Baru: {values['title']}", values.get('description') or "Terdapat agenda kegiatan baru.", url_for('get_agendas') if False else f"/agenda/{agenda_id}", {"agenda_id": agenda_id})
                conn.commit()
            finally:
                nc.close()
        except Exception:
            pass
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
        
        # Cleanup file lama yang sudah dihapus/diganti saat Edit
        if existing:
            try:
                # Cleanup Image
                if existing.get("image_url") and existing.get("image_url") != values["image_url"]:
                    remove_physical_file(existing["image_url"])
                
                # Cleanup Attachments
                old_atts_raw = existing.get("attachments") or "[]"
                old_atts = json.loads(old_atts_raw) if isinstance(old_atts_raw, str) else (old_atts_raw or [])
                new_atts_raw = values.get("attachments") or "[]"
                new_atts = json.loads(new_atts_raw) if isinstance(new_atts_raw, str) else (new_atts_raw or [])
                new_att_urls = [a.get("url") for a in new_atts if isinstance(a, dict) and a.get("url")]
                
                for oa in old_atts:
                    if isinstance(oa, dict) and oa.get("url") and oa.get("url") not in new_att_urls:
                        remove_physical_file(oa["url"])
            except Exception as e:
                print(f"[WARN] Failed to cleanup replaced files for agenda {agenda_id}: {e}")

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
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch agenda data first to get the files we need to delete
        cursor.execute("SELECT `image_url`, `attachments` FROM `agendas` WHERE `id` = %s LIMIT 1", (agenda_id,))
        agenda = cursor.fetchone()
        
        if not agenda:
            return jsonify({"success": False, "error": "Agenda not found"}), 404

        # 2. Delete the record from the database
        cursor.execute("DELETE FROM `agendas` WHERE `id` = %s", (agenda_id,))
        conn.commit()

        # 3. Clean up physical files
        try:
            # Delete image
            if agenda.get("image_url"):
                remove_physical_file(agenda["image_url"])
            
            # Delete attachments
            attachments_raw = agenda.get("attachments") or "[]"
            attachments = json.loads(attachments_raw) if isinstance(attachments_raw, str) else (attachments_raw or [])
            for att in attachments:
                if isinstance(att, dict) and att.get("url"):
                    remove_physical_file(att["url"])
        except Exception as e:
            print(f"[WARN] Error during physical file cleanup for agenda {agenda_id}: {e}")

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
        try:
            ensure_notifications_schema()
            nc = conn.cursor()
            try:
                create_notification(nc, "news", f"Pengumuman Baru: {title}", summary or "Terdapat pengumuman baru.", f"/pengumuman/{news_id}", {"news_id": news_id})
                conn.commit()
            finally:
                nc.close()
        except Exception:
            pass
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
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `news` WHERE `id` = %s LIMIT 1", (news_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "News not found"}), 404

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

        # Clean up old files if they are replaced
        try:
            old_thumbs_raw = existing.get("thumbnails") or "[]"
            old_thumbs = json.loads(old_thumbs_raw) if isinstance(old_thumbs_raw, str) else (old_thumbs_raw or [])
            new_thumb_urls = [t.get("url") for t in thumbnails if isinstance(t, dict) and t.get("url")]
            for ot in old_thumbs:
                if isinstance(ot, dict) and ot.get("url") and ot.get("url") not in new_thumb_urls:
                    remove_physical_file(ot["url"])
                    
            old_atts_raw = existing.get("attachments") or "[]"
            old_atts = json.loads(old_atts_raw) if isinstance(old_atts_raw, str) else (old_atts_raw or [])
            new_att_urls = [a.get("url") for a in attachments if isinstance(a, dict) and a.get("url")]
            for oa in old_atts:
                if isinstance(oa, dict) and oa.get("url") and oa.get("url") not in new_att_urls:
                    remove_physical_file(oa["url"])
        except Exception as e:
            print(f"[WARN] Failed to cleanup replaced files for news {news_id}: {e}")

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
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch news data first to get the files we need to delete
        cursor.execute("SELECT `thumbnails`, `attachments` FROM `news` WHERE `id` = %s LIMIT 1", (news_id,))
        news = cursor.fetchone()
        
        if not news:
            return jsonify({"success": False, "error": "News not found"}), 404
            
        # 2. Delete mappings and record
        cursor.execute("DELETE FROM `news_category_mapping` WHERE `news_id` = %s", (news_id,))
        cursor.execute("DELETE FROM `news` WHERE `id` = %s", (news_id,))
        conn.commit()
        
        # 3. Clean up physical files
        try:
            # Clean thumbnails
            thumbnails_raw = news.get("thumbnails") or "[]"
            thumbnails = json.loads(thumbnails_raw) if isinstance(thumbnails_raw, str) else (thumbnails_raw or [])
            for thumb in thumbnails:
                if isinstance(thumb, dict) and thumb.get("url"):
                    remove_physical_file(thumb["url"])
                    
            # Clean attachments
            attachments_raw = news.get("attachments") or "[]"
            attachments = json.loads(attachments_raw) if isinstance(attachments_raw, str) else (attachments_raw or [])
            for att in attachments:
                if isinstance(att, dict) and att.get("url"):
                    remove_physical_file(att["url"])
        except Exception as e:
            print(f"[WARN] Error during physical file cleanup for news {news_id}: {e}")

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
        ensure_notifications_schema()
    except Exception as exc:
        print(f"[WARN] MySQL bootstrap skipped: {exc}")
    app.run(debug=True)