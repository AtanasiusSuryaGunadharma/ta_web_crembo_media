from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3
from datetime import datetime, timedelta
import os
import calendar
import requests
import re
from werkzeug.security import check_password_hash, generate_password_hash

# =========================================================
# APP CONFIG
# =========================================================
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "rahasia")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "crembo.db")

# =========================================================
# WABLAS CONFIG
# =========================================================
WABLAS_API_TOKEN = os.environ.get(
    "WABLAS_API_TOKEN",
    "bDmEVwpaHTI8lZZHZEpcezldDLaZkat4yVGjEwd4VCE2Psmiw4gINNZ"
)
WABLAS_URL = os.environ.get("WABLAS_URL", "https://sby.wablas.com/api/v2/send-message")

# Broadcast target (nomor WA yang akan menerima pesan pengumuman, misal nomor admin/relay group)
WABLAS_GROUP_TARGET = os.environ.get("WABLAS_GROUP_TARGET", "628xxxxxxxxxx")  # wajib diisi


# =========================================================
# LOGGING AKTIVITAS (FILE PER BULAN)
# =========================================================
last_user_logged = {"user": None}

def get_log_filename():
    now = datetime.now()
    return os.path.join(BASE_DIR, f"log_{now.year}_{now.month:02}.log")

def tulis_log(aktivitas: str):
    now = datetime.now()
    tanggal_jam = now.strftime("%A, %d %B %Y %H:%M:%S")

    hari = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    bulan = {
        "January": "Januari", "February": "Februari", "March": "Maret",
        "April": "April", "May": "Mei", "June": "Juni",
        "July": "Juli", "August": "Agustus", "September": "September",
        "October": "Oktober", "November": "November", "December": "Desember"
    }
    for en, idn in hari.items():
        tanggal_jam = tanggal_jam.replace(en, idn)
    for en, idn in bulan.items():
        tanggal_jam = tanggal_jam.replace(en, idn)

    ip = request.remote_addr
    route = request.path
    user = session.get("username", "anonymous")

    log_entry = f"[{tanggal_jam}] IP: {ip} | Route: {route} | Aktivitas: {aktivitas}\n"

    filename = get_log_filename()
    with open(filename, "a", encoding="utf-8") as f:
        if last_user_logged["user"] != user:
            f.write("\n")
            last_user_logged["user"] = user
        f.write(log_entry)


# =========================================================
# DB HELPERS
# =========================================================
def db_connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db_connect() as conn:
        c = conn.cursor()

        # anggota
        c.execute("""
            CREATE TABLE IF NOT EXISTS anggota (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT,
                username TEXT UNIQUE,
                tgl_lahir TEXT,
                telp TEXT,
                email TEXT,
                password TEXT,
                role TEXT DEFAULT 'user'
            )
        """)

        # master form event (draft/published/archived)
        c.execute("""
            CREATE TABLE IF NOT EXISTS tugas_form (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                keterangan TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                sunday_times TEXT DEFAULT '08:00,10:00,17:00,19:00',
                weekday_time TEXT DEFAULT '18:00',
                status TEXT DEFAULT 'draft',        -- draft/published/archived
                created_at TEXT,
                published_at TEXT,
                expires_at TEXT                     -- hide otomatis (bukan hapus)
            )
        """)

        # slot per tanggal+jam
        c.execute("""
            CREATE TABLE IF NOT EXISTS tugas_form_slot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                operator_username TEXT,
                kameramen_username TEXT,
                supervisor_username TEXT,
                updated_at TEXT,
                UNIQUE(form_id, date, time)
            )
        """)

        # audit log perubahan slot
        c.execute("""
            CREATE TABLE IF NOT EXISTS tugas_form_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                slot_id INTEGER NOT NULL,
                actor_username TEXT,
                actor_role TEXT,
                actor_ip TEXT,
                actor_route TEXT,
                old_operator TEXT,
                old_kameramen TEXT,
                old_supervisor TEXT,
                new_operator TEXT,
                new_kameramen TEXT,
                new_supervisor TEXT,
                note TEXT,
                created_at TEXT
            )
        """)

        conn.commit()


# =========================================================
# WABLAS HELPERS
# =========================================================
def normalisasi_nomor(telp: str) -> str:
    telp = (telp or "").replace(" ", "").replace("-", "")
    if telp.startswith("+62"):
        return "62" + telp[3:]
    if telp.startswith("08"):
        return "62" + telp[1:]
    return telp

def kirim_wa(nomor: str, pesan: str) -> bool:
    headers = {"Authorization": WABLAS_API_TOKEN, "Content-Type": "application/json"}
    data = {"data": [{"phone": nomor, "message": pesan, "secret": False, "priority": True}]}
    try:
        resp = requests.post(WABLAS_URL, json=data, headers=headers, timeout=10)
        print(f"[WA] to {nomor}: {resp.status_code} - {resp.text}")
        return resp.ok
    except Exception as e:
        print(f"[WA ERROR] Gagal kirim ke {nomor}: {e}")
        return False

def kirim_wa_group(pesan: str) -> bool:
    nomor = normalisasi_nomor(WABLAS_GROUP_TARGET)
    return kirim_wa(nomor, pesan)


# =========================================================
# AUTH HELPERS
# =========================================================
def require_login():
    return "username" in session

def require_admin():
    return require_login() and session.get("role") == "admin"


# =========================================================
# TUGAS BULANAN (tugas_YYYY_MM) - fitur lama
# =========================================================
def get_tugas_bulanan(bulan, tahun):
    nama_tabel = f"tugas_{tahun}_{bulan:02}"
    posisi_list = ["Operator", "Kameramen", "Supervisor"]
    data_db = {}

    with db_connect() as conn:
        c = conn.cursor()
        try:
            c.execute(f"SELECT username, date, time, position FROM {nama_tabel}")
            for username, date, time, position in c.fetchall():
                data_db.setdefault(date, {}).setdefault(time, {})[position] = username
        except sqlite3.OperationalError:
            pass

    hasil = []
    jumlah_hari = calendar.monthrange(tahun, bulan)[1]

    for h in range(1, jumlah_hari + 1):
        tanggal = datetime(tahun, bulan, h)
        tanggal_str = tanggal.strftime("%Y-%m-%d")
        jam_list = ["08:00", "10:00", "17:00", "19:00"] if tanggal.strftime("%A") == "Sunday" else ["18:00"]

        tugas_per_jam = {}
        for jam in jam_list:
            tugas_per_jam[jam] = {pos: data_db.get(tanggal_str, {}).get(jam, {}).get(pos, "") for pos in posisi_list}

        hasil.append({"date": tanggal_str, "tasks": tugas_per_jam})

    return list(enumerate(hasil, start=1))


# =========================================================
# FORM EVENT HELPERS (draft->publish->public)
# =========================================================
def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60] or "form-tugas"

def daterange(start_date: datetime, end_date: datetime):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur += timedelta(days=1)

def build_slots_for_form(form_row):
    start_date = datetime.strptime(form_row["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(form_row["end_date"], "%Y-%m-%d")
    sunday_times = [t.strip() for t in (form_row["sunday_times"] or "").split(",") if t.strip()]
    weekday_time = (form_row["weekday_time"] or "18:00").strip()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_connect() as conn:
        c = conn.cursor()
        for d in daterange(start_date, end_date):
            date_str = d.strftime("%Y-%m-%d")
            times = sunday_times if d.strftime("%A") == "Sunday" else [weekday_time]
            for t in times:
                c.execute("""
                    INSERT OR IGNORE INTO tugas_form_slot
                    (form_id, date, time, operator_username, kameramen_username, supervisor_username, updated_at)
                    VALUES (?, ?, ?, '', '', '', ?)
                """, (form_row["id"], date_str, t, now_str))
        conn.commit()

def get_last_misa_date(form_id: int):
    # patokan misa terakhir = slot terakhir yang benar-benar ada
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT date FROM tugas_form_slot WHERE form_id=? ORDER BY date DESC, time DESC LIMIT 1", (form_id,))
        row = c.fetchone()
    if row and row["date"]:
        try:
            return datetime.strptime(row["date"], "%Y-%m-%d").date()
        except:
            return None
    return None

def is_form_visible_public(form_row) -> bool:
    if not form_row or form_row["status"] != "published":
        return False
    if form_row["expires_at"]:
        try:
            exp = datetime.strptime(form_row["expires_at"], "%Y-%m-%d").date()
            return datetime.now().date() <= exp
        except:
            return True
    return True

def audit_slot_change(form_id, slot_id, old_vals, new_vals, note=""):
    actor_username = session.get("username", "anonymous")
    actor_role = session.get("role", "")
    actor_ip = request.remote_addr
    actor_route = request.path
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO tugas_form_audit (
                form_id, slot_id,
                actor_username, actor_role, actor_ip, actor_route,
                old_operator, old_kameramen, old_supervisor,
                new_operator, new_kameramen, new_supervisor,
                note, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            form_id, slot_id,
            actor_username, actor_role, actor_ip, actor_route,
            old_vals.get("operator", ""), old_vals.get("kameramen", ""), old_vals.get("supervisor", ""),
            new_vals.get("operator", ""), new_vals.get("kameramen", ""), new_vals.get("supervisor", ""),
            note, now_str
        ))
        conn.commit()


# =========================================================
# ROUTES - LANDING + AUTH
# =========================================================
@app.route("/")
def index():
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, judul, slug, published_at, expires_at, status
            FROM tugas_form
            WHERE status='published'
            ORDER BY published_at DESC
        """)
        rows = [dict(r) for r in c.fetchall()]

    published_links = [r for r in rows if is_form_visible_public(r)]
    return render_template("index.html", published_links=published_links)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        with db_connect() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM anggota WHERE username = ?", (username,))
            user = c.fetchone()

        if user:
            stored_hash = user["password"]
            if stored_hash and check_password_hash(stored_hash, password):
                session["logged_in"] = True
                session["username"] = user["username"]
                session["role"] = user["role"]
                tulis_log(f"Login berhasil oleh {username}")
                return redirect(url_for("dashboard"))
            flash("Password salah.")
        else:
            flash("Username tidak ditemukan.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("index"))

    username = session["username"]
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT nama FROM anggota WHERE username = ?", (username,))
        row = c.fetchone()
    nama = row["nama"] if row else "User"

    # NOTE: di dashboard.html kamu tampilkan link admin:
    # url_for('admin_form_list')
    return render_template("dashboard.html", role=session.get("role"), nama=nama)


# =========================================================
# ROUTES - REGISTRASI TUGAS BULANAN (lama)
## =========================================================
#@app.route("/register_tugas", methods=["GET", "POST"])
#def register_tugas():
#    if "username" not in session:
#        flash("Login sebagai user untuk daftar tugas")
@app.route('/register_tugas', methods=['GET', 'POST'])
def register_tugas():
    if 'username' not in session:
        flash("Login sebagai user untuk daftar tugas")
        return redirect(url_for('login'))

    # default: tampilkan bulan berjalan
    now = datetime.now()
    bulan = now.month
    tahun = now.year

    if request.method == 'POST':
        name = session['username']
        date = request.form['date']
        time = request.form['time']
        position = request.form['position']

        # ambil bulan/tahun dari tanggal yang dipilih (biar tabelnya tepat)
        dt = datetime.strptime(date, '%Y-%m-%d')
        bulan = dt.month
        tahun = dt.year
        nama_tabel = f"tugas_{tahun}_{bulan:02}"

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute(f'''CREATE TABLE IF NOT EXISTS {nama_tabel} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            date TEXT,
                            time TEXT,
                            position TEXT
                        )''')

            c.execute(f'''SELECT COUNT(*) FROM {nama_tabel}
                          WHERE date = ? AND time = ? AND position = ?''', (date, time, position))
            count = c.fetchone()[0]

            if count > 0:
                flash(f"Maaf, posisi '{position}' pada {date} jam {time} sudah terisi.")
            else:
                c.execute(f'''INSERT INTO {nama_tabel} (username, date, time, position)
                              VALUES (?, ?, ?, ?)''', (name, date, time, position))
                conn.commit()
                flash('Tugas berhasil disimpan.')

    # penting: kirim data ke template
    data = get_tugas_bulanan(bulan, tahun)
    return render_template('register.html', data=data, bulan=bulan, tahun=tahun)


@app.route("/lihat_tugas", methods=["GET", "POST"])
def lihat_tugas():
    data = []
    no_data = False

    bulan_dict = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    if request.method == "POST":
        bulan = int(request.form["bulan"])
        tahun = int(request.form["tahun"])
        try:
            data = get_tugas_bulanan(bulan, tahun)
            if not data:
                no_data = True
        except:
            no_data = True
            flash("Belum ada data untuk bulan tersebut")

    return render_template("lihat.html", data=data, bulan_dict=bulan_dict, no_data=no_data)


# =========================================================
# ROUTES - ROLE (ADMIN)
# =========================================================
@app.route("/ubah_role", methods=["GET", "POST"])
def ubah_role():
    if not require_admin():
        return redirect(url_for("login"))

    with db_connect() as conn:
        c = conn.cursor()
        if request.method == "POST":
            uname = request.form["username"]
            new_role = request.form["role"]
            c.execute("UPDATE anggota SET role=? WHERE username=?", (new_role, uname))
            conn.commit()
            flash(f"Role {uname} diubah jadi {new_role}")

        c.execute("SELECT nama, username, role FROM anggota ORDER BY nama ASC")
        users = c.fetchall()

    return render_template("role.html", users=users)


# =========================================================
# ROUTES - PROFIL & UPDATE PROFIL (tanpa ganti password)
# =========================================================
@app.route("/profil")
def profil():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT nama, username, tgl_lahir, telp, email
            FROM anggota WHERE username=?
        """, (username,))
        row = c.fetchone()

    if row:
        return render_template("profil.html",
            nama=row["nama"], username=row["username"],
            tgl_lahir=row["tgl_lahir"], telp=row["telp"], email=row["email"]
        )

    flash("Data tidak ditemukan.")
    return redirect(url_for("dashboard"))

@app.route("/update_profil", methods=["GET", "POST"])
def update_profil():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT nama, tgl_lahir, telp, email FROM anggota WHERE username=?", (username,))
        row = c.fetchone()

    if not row:
        flash("Data tidak ditemukan.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nama_baru = (request.form.get("nama") or "").strip()
        tgl_lahir_baru = (request.form.get("tgl_lahir") or "").strip()
        telp_baru = (request.form.get("telp") or "").strip()
        email_baru = (request.form.get("email") or "").strip()

        with db_connect() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE anggota SET nama=?, tgl_lahir=?, telp=?, email=?
                WHERE username=?
            """, (nama_baru, tgl_lahir_baru, telp_baru, email_baru, username))
            conn.commit()

        flash("Profil berhasil diperbarui.")
        return redirect(url_for("profil"))

    return render_template("update_profil.html",
        nama=row["nama"] or "",
        tgl_lahir=row["tgl_lahir"] or "",
        telp=row["telp"] or "",
        email=row["email"] or ""
    )


# =========================================================
# ROUTES - TAMBAH ANGGOTA (ADMIN) + kirim WA kredensial
# =========================================================
@app.route("/tambah_anggota", methods=["GET", "POST"])
def tambah_anggota():
    if not require_admin():
        flash("Hanya admin yang boleh menambah anggota.")
        return redirect(url_for("login"))

    if request.method == "POST":
        nama = (request.form.get("nama") or "").strip()
        username = (request.form.get("username") or "").strip()
        tgl_lahir = (request.form.get("tgl_lahir") or "").strip()
        telp = (request.form.get("telp") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not nama or not username or not telp or not password:
            flash("Nama, Username, Telepon, dan Password wajib diisi.")
            return redirect(url_for("tambah_anggota"))

        with db_connect() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM anggota WHERE username=?", (username,))
            if c.fetchone():
                flash("Username sudah terdaftar. Gunakan username lain.")
                return redirect(url_for("tambah_anggota"))

            pass_hash = generate_password_hash(password)
            c.execute("""
                INSERT INTO anggota (nama, username, tgl_lahir, telp, email, password, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nama, username, tgl_lahir, telp, email, pass_hash, "user"))
            conn.commit()

        nomor_wa = normalisasi_nomor(telp)
        pesan = (
            f"Halo {nama},\n\n"
            f"Kamu sudah didaftarkan ke database CREMBO.\n\n"
            f"Username: {username}\n"
            f"Password: {password}\n"
            f"Role: user\n\n"
            f"Silakan login di: crembomedia.com/login\n\n"
            f"Pesan ini dikirim otomatis, tidak perlu dibalas 🙏"
        )
        kirim_wa(nomor_wa, pesan)

        flash(f"'{nama}' berhasil ditambahkan dan notifikasi WA sudah dikirim.")
        return redirect(url_for("ubah_role"))

    return render_template("tambah_anggota.html")


# =========================================================
# CONTEXT PROCESSOR
# =========================================================
@app.context_processor
def inject_nama_dan_tanggal():
    nama = None
    if "username" in session:
        with db_connect() as conn:
            c = conn.cursor()
            c.execute("SELECT nama FROM anggota WHERE username=?", (session["username"],))
            row = c.fetchone()
            if row:
                nama = row["nama"]

    hari_ini = datetime.now().strftime("%A, %d %B %Y")
    indo_hari = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    indo_bulan = {
        "January": "Januari", "February": "Februari", "March": "Maret",
        "April": "April", "May": "Mei", "June": "Juni",
        "July": "Juli", "August": "Agustus", "September": "September",
        "October": "Oktober", "November": "November", "December": "Desember"
    }
    for eng, indo in indo_hari.items():
        hari_ini = hari_ini.replace(eng, indo)
    for eng, indo in indo_bulan.items():
        hari_ini = hari_ini.replace(eng, indo)

    return dict(nama=nama, hari_ini=hari_ini)


# =========================================================
# ADMIN: FORM EVENT (list/new/edit/publish/audit)
# =========================================================
@app.route("/admin/form_tugas")
def admin_form_list():
    if not require_admin():
        return redirect(url_for("login"))

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, judul, slug, status, created_at, published_at, expires_at
            FROM tugas_form
            ORDER BY id DESC
        """)
        forms = c.fetchall()

    return render_template("admin_form_list.html", forms=forms)

@app.route("/admin/form_tugas/new", methods=["GET", "POST"])
def admin_form_new():
    if not require_admin():
        return redirect(url_for("login"))

    if request.method == "POST":
        judul = (request.form.get("judul") or "").strip()
        keterangan = (request.form.get("keterangan") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        sunday_times = (request.form.get("sunday_times") or "08:00,10:00,17:00,19:00").strip()
        weekday_time = (request.form.get("weekday_time") or "18:00").strip()

        if not judul or not start_date or not end_date:
            flash("Judul, Start Date, End Date wajib diisi.")
            return redirect(url_for("admin_form_new"))

        base_slug = slugify(judul)
        slug = base_slug
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with db_connect() as conn:
            c = conn.cursor()
            i = 2
            while True:
                c.execute("SELECT 1 FROM tugas_form WHERE slug=?", (slug,))
                if not c.fetchone():
                    break
                slug = f"{base_slug}-{i}"
                i += 1

            c.execute("""
                INSERT INTO tugas_form
                (judul, slug, keterangan, start_date, end_date, sunday_times, weekday_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?)
            """, (judul, slug, keterangan, start_date, end_date, sunday_times, weekday_time, now_str))
            conn.commit()

            form_id = c.lastrowid
            c.execute("SELECT * FROM tugas_form WHERE id=?", (form_id,))
            form_row = c.fetchone()

        build_slots_for_form(form_row)
        flash("Form tugas berhasil dibuat (draft).")
        return redirect(url_for("admin_form_edit", form_id=form_id))

    return render_template("admin_form_new.html")

@app.route("/admin/form_tugas/<int:form_id>/edit", methods=["GET", "POST"])
def admin_form_edit(form_id):
    if not require_admin():
        return redirect(url_for("login"))

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM tugas_form WHERE id=?", (form_id,))
        form_row = c.fetchone()
        if not form_row:
            abort(404)

    if request.method == "POST":
        judul = (request.form.get("judul") or "").strip()
        keterangan = (request.form.get("keterangan") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        sunday_times = (request.form.get("sunday_times") or "08:00,10:00,17:00,19:00").strip()
        weekday_time = (request.form.get("weekday_time") or "18:00").strip()

        with db_connect() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE tugas_form
                SET judul=?, keterangan=?, start_date=?, end_date=?, sunday_times=?, weekday_time=?
                WHERE id=?
            """, (judul, keterangan, start_date, end_date, sunday_times, weekday_time, form_id))
            conn.commit()

            c.execute("SELECT * FROM tugas_form WHERE id=?", (form_id,))
            form_row = c.fetchone()

        build_slots_for_form(form_row)
        flash("Setting form diperbarui.")

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT nama, username FROM anggota ORDER BY nama ASC")
        anggota = c.fetchall()

        c.execute("""
            SELECT * FROM tugas_form_slot
            WHERE form_id=?
            ORDER BY date ASC, time ASC
        """, (form_id,))
        slots = c.fetchall()

    return render_template("admin_form_edit.html", form=form_row, slots=slots, anggota=anggota)

@app.route("/admin/form_tugas/<int:form_id>/slot/<int:slot_id>/update", methods=["POST"])
def admin_slot_update(form_id, slot_id):
    if not require_admin():
        return redirect(url_for("login"))

    op = (request.form.get("operator_username") or "").strip()
    kam = (request.form.get("kameramen_username") or "").strip()
    sup = (request.form.get("supervisor_username") or "").strip()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT operator_username, kameramen_username, supervisor_username
            FROM tugas_form_slot
            WHERE id=? AND form_id=?
        """, (slot_id, form_id))
        old = c.fetchone()
        if not old:
            abort(404)

        old_vals = {
            "operator": old["operator_username"] or "",
            "kameramen": old["kameramen_username"] or "",
            "supervisor": old["supervisor_username"] or ""
        }
        new_vals = {"operator": op, "kameramen": kam, "supervisor": sup}

        if old_vals != new_vals:
            c.execute("""
                UPDATE tugas_form_slot
                SET operator_username=?, kameramen_username=?, supervisor_username=?, updated_at=?
                WHERE id=? AND form_id=?
            """, (op, kam, sup, now_str, slot_id, form_id))
            conn.commit()
            audit_slot_change(form_id, slot_id, old_vals, new_vals, note="admin update")

    flash("Slot diperbarui.")
    return redirect(url_for("admin_form_edit", form_id=form_id))

@app.route("/admin/form_tugas/<int:form_id>/publish", methods=["POST"])
def admin_form_publish(form_id):
    if not require_admin():
        return redirect(url_for("login"))

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM tugas_form WHERE id=?", (form_id,))
        form_row = c.fetchone()
        if not form_row:
            abort(404)

    last_date = get_last_misa_date(form_id)
    if not last_date:
        # fallback ke end_date
        try:
            last_date = datetime.strptime(form_row["end_date"], "%Y-%m-%d").date()
        except:
            last_date = datetime.now().date()

    expires_at = (last_date + timedelta(days=3)).strftime("%Y-%m-%d")
    published_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tugas_form
            SET status='published', published_at=?, expires_at=?
            WHERE id=?
        """, (published_at, expires_at, form_id))
        conn.commit()

    link = url_for("public_form_view", slug=form_row["slug"], _external=True)
    link_list = url_for("public_form_list", slug=form_row["slug"], _external=True)

    pesan = (
        f"📣 Jadwal tugas sudah PUBLISH\n\n"
        f"Form: {form_row['judul']}\n"
        f"Isi/lihat: {link}\n"
        f"List petugas: {link_list}\n\n"
        f"(Link akan disembunyikan otomatis setelah {expires_at})"
    )
    kirim_wa_group(pesan)

    flash("Form berhasil dipublish + pengumuman WA dikirim.")
    return redirect(url_for("admin_form_edit", form_id=form_id))

@app.route("/admin/form_tugas/<int:form_id>/audit")
def admin_form_audit(form_id):
    if not require_admin():
        return redirect(url_for("login"))

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT id, judul FROM tugas_form WHERE id=?", (form_id,))
        form_row = c.fetchone()
        if not form_row:
            abort(404)

        c.execute("""
            SELECT * FROM tugas_form_audit
            WHERE form_id=?
            ORDER BY id DESC
            LIMIT 500
        """, (form_id,))
        logs = c.fetchall()

    return render_template("admin_form_audit.html", form=form_row, logs=logs)


# =========================================================
# PUBLIC: FORM EVENT
# =========================================================
@app.route("/f/<slug>", methods=["GET", "POST"])
def public_form_view(slug):
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM tugas_form WHERE slug=?", (slug,))
        form_row = c.fetchone()
    if not form_row:
        abort(404)

    if not is_form_visible_public(dict(form_row)):
        return render_template("form_hidden.html", form=form_row), 404

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT nama, username FROM anggota ORDER BY nama ASC")
        anggota = c.fetchall()

        c.execute("""
            SELECT * FROM tugas_form_slot
            WHERE form_id=?
            ORDER BY date ASC, time ASC
        """, (form_row["id"],))
        slots = c.fetchall()

    # publik submit
    if request.method == "POST":
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_connect() as conn:
            c = conn.cursor()

            # ambil slot fresh utk old vals
            c.execute("""
                SELECT * FROM tugas_form_slot
                WHERE form_id=?
                ORDER BY date ASC, time ASC
            """, (form_row["id"],))
            slots_db = c.fetchall()

            for s in slots_db:
                sid = s["id"]
                op = (request.form.get(f"op_{sid}") or "").strip()
                kam = (request.form.get(f"kam_{sid}") or "").strip()
                sup = (request.form.get(f"sup_{sid}") or "").strip()

                old_vals = {
                    "operator": s["operator_username"] or "",
                    "kameramen": s["kameramen_username"] or "",
                    "supervisor": s["supervisor_username"] or ""
                }
                new_vals = {"operator": op, "kameramen": kam, "supervisor": sup}

                if old_vals != new_vals:
                    c.execute("""
                        UPDATE tugas_form_slot
                        SET operator_username=?, kameramen_username=?, supervisor_username=?, updated_at=?
                        WHERE id=? AND form_id=?
                    """, (op, kam, sup, now_str, sid, form_row["id"]))

                    conn.commit()
                    audit_slot_change(form_row["id"], sid, old_vals, new_vals, note="public submit")

        flash("Terima kasih, data petugas tersimpan.")
        return redirect(url_for("public_form_view", slug=slug))

    return render_template("public_form.html", form=form_row, slots=slots, anggota=anggota)

@app.route("/f/<slug>/list")
def public_form_list(slug):
    with db_connect() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM tugas_form WHERE slug=?", (slug,))
        form_row = c.fetchone()
    if not form_row:
        abort(404)

    if not is_form_visible_public(dict(form_row)):
        return render_template("form_hidden.html", form=form_row), 404

    with db_connect() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT s.*,
                   ao.nama as op_nama,
                   ak.nama as kam_nama,
                   asv.nama as sup_nama
            FROM tugas_form_slot s
            LEFT JOIN anggota ao ON ao.username = s.operator_username
            LEFT JOIN anggota ak ON ak.username = s.kameramen_username
            LEFT JOIN anggota asv ON asv.username = s.supervisor_username
            WHERE s.form_id=?
            ORDER BY s.date ASC, s.time ASC
        """, (form_row["id"],))
        slots = c.fetchall()

    return render_template("public_form_list.html", form=form_row, slots=slots)


# =========================================================
# TEST ROUTE
# =========================================================
@app.route("/testnav")
def testnav():
    return render_template("test_nav.html")


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    init_db()
    # Pastikan DB init saat app dijalankan oleh gunicorn (bukan hanya saat python app.py)
    try:
        init_db()
    except Exception as e:
        print("[INIT_DB ERROR]", e)

    app.run(debug=True)

