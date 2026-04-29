from pathlib import Path
import os
import re

import mysql.connector
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

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




def template_exists(template_name: str) -> bool:
    return (FRONTEND_DIR / template_name).is_file()


def mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)


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


@app.route("/")
def index():
    home_page_data = {
        "carouselSlides": [
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
            },
            {
                "id": "default-3",
                "title": "Pengumuman Agenda",
                "slug": "agenda-terbaru",
                "description": "Pantau agenda dan pengumuman terbaru komunitas Crembo Media.",
                "link": "agenda.html",
                "buttonText": "Lihat Agenda",
                "backgroundImage": "",
                "order": 3,
                "active": True,
            },
        ],
        "aboutContent": {
            "description": "Ringkasan profil organisasi, visi pelayanan multimedia, serta peran Crembo dalam mendukung kegiatan liturgi dan agenda komunitas. Konten ini nantinya diatur dari panel admin setelah login.",
            "buttonText": "Pelajari Lebih Lanjut",
            "buttonLink": "profil.html",
            "autoSeconds": 5,
            "images": [],
        },
        "bigMassSchedules": [],
        "profileMenu": [
            {"id": "sejarah", "label": "Sejarah"},
            {"id": "tentang-crembo", "label": "Tentang Crembo"},
            {"id": "struktur", "label": "Struktur"},
            {"id": "visi-misi", "label": "Visi & Misi"},
        ],
    }
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
        if candidate == "manajemen-anggota.html":
            extra_context["member_rows"] = read_members_for_admin() if session.get("logged_in") else []
        return render_template(candidate, **extra_context)

    abort(404)


# --- TENTANG CREMBO ENDPOINTS ---

@app.route("/api/tentang/config", methods=["GET"])
def get_tentang_config():
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
    cursor.execute("""
        UPDATE `tentang_crembo_config` 
        SET `description`=%s, `button_text`=%s, `button_link`=%s, `auto_seconds`=%s 
                (id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/tentang/media", methods=["GET"])
def get_tentang_media():
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

import werkzeug.utils

@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    if file:
        filename = werkzeug.utils.secure_filename(file.filename)
        # Ensure uploads dir exists
        upload_folder = os.path.join(app.root_path, 'frontend', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Make filename unique
        import time
        import random
        base, ext = os.path.splitext(filename)
        new_filename = f"{base}_{int(time.time())}{ext}"
        
        filepath = os.path.join(upload_folder, new_filename)
        file.save(filepath)
        
        return jsonify({
            "success": True, 
            "url": f"uploads/{new_filename}"
        })


if __name__ == "__main__":
    try:
        ensure_auth_schema()
    except Exception as exc:
        print(f"[WARN] MySQL bootstrap skipped: {exc}")
    app.run(debug=True)
        
