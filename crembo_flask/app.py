from pathlib import Path
import re

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
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

DEMO_ACCOUNTS = [
    {
        "id": 1001,
        "nama": "CREMBO Super Admin",
        "username": "superadmin",
        "telp": "081100000001",
        "email": "superadmin@crembo.test",
        "alamat": "Jl. Demo Super Admin 1, Baciro",
        "role": "super_admin",
        "status_akun": "aktif",
        "tgl_lahir": "1990-01-01",
        "password": "Testing123!",
    },
    {
        "id": 1002,
        "nama": "CREMBO Admin",
        "username": "admin.testing",
        "telp": "081100000002",
        "email": "admin@crembo.test",
        "alamat": "Jl. Demo Admin 2, Baciro",
        "role": "admin",
        "status_akun": "aktif",
        "tgl_lahir": "1992-02-02",
        "password": "Testing123!",
    },
    {
        "id": 1003,
        "nama": "CREMBO Anggota",
        "username": "anggota.testing",
        "telp": "081100000003",
        "email": "anggota@crembo.test",
        "alamat": "Jl. Demo Anggota 3, Baciro",
        "role": "user",
        "status_akun": "aktif",
        "tgl_lahir": "1995-03-03",
        "password": "Testing123!",
    },
]


def template_exists(template_name: str) -> bool:
    return (FRONTEND_DIR / template_name).is_file()


def mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)


def normalize_phone(value: str) -> str:
    cleaned = re.sub(r"[\s\-()]+", "", (value or "").strip())
    if cleaned.startswith("+62"):
        return "62" + cleaned[3:]
    if cleaned.startswith("08"):
        return "62" + cleaned[1:]
    return cleaned


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
          PRIMARY KEY (`id`),
          UNIQUE KEY `uniq_anggota_username` (`username`),
          UNIQUE KEY `uniq_anggota_email` (`email`),
          UNIQUE KEY `uniq_anggota_telp` (`telp`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `db_anggota` (
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
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
    )

    ensure_column(cursor, "anggota", "alamat", "`alamat` text DEFAULT NULL")
    ensure_column(cursor, "anggota", "status_akun", "`status_akun` varchar(20) NOT NULL DEFAULT 'aktif'")
    ensure_column(cursor, "db_anggota", "tgl_lahir", "`tgl_lahir` varchar(50) DEFAULT NULL")
    ensure_column(cursor, "db_anggota", "email", "`email` varchar(255) DEFAULT NULL")
    ensure_column(cursor, "db_anggota", "alamat", "`alamat` text DEFAULT NULL")
    ensure_column(cursor, "db_anggota", "status_akun", "`status_akun` varchar(20) NOT NULL DEFAULT 'aktif'")

    cursor.execute("UPDATE `anggota` SET `status_akun` = 'aktif' WHERE `status_akun` IS NULL OR `status_akun` = ''")
    cursor.execute("UPDATE `db_anggota` SET `status_akun` = 'aktif' WHERE `status_akun` IS NULL OR `status_akun` = ''")

    conn.commit()
    cursor.close()
    conn.close()


def seed_demo_accounts() -> None:
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)

    for account in DEMO_ACCOUNTS:
        hashed_password = generate_password_hash(account["password"])
        for table_name in ("anggota", "db_anggota"):
            cursor.execute(
                f"SELECT id FROM `{table_name}` WHERE username = %s OR email = %s OR telp = %s LIMIT 1",
                (account["username"], account["email"], account["telp"]),
            )
            if cursor.fetchone():
                continue

            cursor.execute(
                f"""
                INSERT INTO `{table_name}`
                (`id`, `nama`, `username`, `telp`, `password`, `role`, `tgl_lahir`, `email`, `alamat`, `status_akun`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    account["id"],
                    account["nama"],
                    account["username"],
                    account["telp"],
                    hashed_password,
                    account["role"],
                    account["tgl_lahir"],
                    account["email"],
                    account["alamat"],
                    account["status_akun"],
                ),
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
    return render_template("home.html", home_page_data=home_page_data)


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
        session["status_akun"] = member.get("status_akun") or "aktif"

        return redirect(login_target_for_role(session["role"]))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") == "user":
        return redirect(url_for("dashboard_anggota"))
    return render_template("dashboard.html", current_user=session)


@app.route("/dashboard-anggota")
def dashboard_anggota():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") != "user":
        return redirect(url_for("dashboard"))
    return render_template("dashboard-anggota.html", current_user=session)


@app.route("/profil")
def profil():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") == "user":
        return render_template("profil-anggota.html", current_user=session)
    return render_template("profil-admin.html", current_user=session)


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

    if template_exists(candidate):
        return render_template(candidate)

    abort(404)


if __name__ == "__main__":
    try:
        ensure_auth_schema()
        seed_demo_accounts()
    except Exception as exc:
        print(f"[WARN] MySQL bootstrap skipped: {exc}")
    app.run(debug=True)
