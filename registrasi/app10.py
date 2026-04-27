from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os
#from werkzeug.security import check_password_hash
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import calendar
from flask import request
import logging
from datetime import datetime
import requests


last_user_logged = {'user': None}

def get_log_filename():
    now = datetime.now()
    return f"log_{now.year}_{now.month:02}.log"

def tulis_log(aktivitas):
    now = datetime.now()
    tanggal_jam = now.strftime('%A, %d %B %Y %H:%M:%S')

    # Terjemahan Indonesia
    hari = {
        'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
        'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
    }
    bulan = {
        'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
        'April': 'April', 'May': 'Mei', 'June': 'Juni',
        'July': 'Juli', 'August': 'Agustus', 'September': 'September',
        'October': 'Oktober', 'November': 'November', 'December': 'Desember'
    }

    for en, idn in hari.items():
        tanggal_jam = tanggal_jam.replace(en, idn)
    for en, idn in bulan.items():
        tanggal_jam = tanggal_jam.replace(en, idn)

    ip = request.remote_addr
    route = request.path
    user = session.get('username', 'anonymous')

    log_entry = f"[{tanggal_jam}] IP: {ip} | Route: {route} | Aktivitas: {aktivitas}\n"

    filename = get_log_filename()
    with open(filename, 'a') as f:
        if last_user_logged['user'] != user:
            f.write("\n")
            last_user_logged['user'] = user
        f.write(log_entry)


app = Flask(__name__)
app.secret_key = 'rahasia'

DB_NAME = 'crembo.db'

#====================== INTEGRASI WABLAS
WABLAS_API_TOKEN = 'bDmEVwpaHTI8lZZHZEpcezldDLaZkat4yVGjEwd4VCE2Psmiw4gINNZ'  # sama seperti reminder-awal.py
WABLAS_URL = 'https://sby.wablas.com/api/v2/send-message'

def normalisasi_nomor(telp):
    telp = telp.replace(' ', '').replace('-', '')
    if telp.startswith('+62'):
        return '62' + telp[3:]
    elif telp.startswith('08'):
        return '62' + telp[1:]
    return telp

#def kirim_wa(nomor, pesan):
#3    headers = {
#        'Authorization': WABLAS_API_TOKEN,
#        'Content-Type': 'application/json'
#    }
#    data = {
#        "phone": nomor,
#        "message": pesan,
#        "secret": False,
#        "priority": True
#    }
#    try:
#        resp = requests.post(WABLAS_URL, json=data, headers=headers, timeout=10)
#        print(f"[WA] to {nomor}: {resp.status_code} - {resp.text}")
#        return resp.ok
#    except Exception as e:
#        print(f"[WA ERROR] Gagal kirim ke {nomor}: {e}")
#        return False

def kirim_wa(nomor, pesan):
    headers = {
        'Authorization': WABLAS_API_TOKEN,
        'Content-Type': 'application/json'
    }

    data = {
        "data": [
            {
                "phone": nomor,
                "message": pesan,
                "secret": False,
                "priority": True
            }
        ]
    }

    try:
        resp = requests.post(WABLAS_URL, json=data, headers=headers, timeout=10)
        print(f"[WA] to {nomor}: {resp.status_code} - {resp.text}")
        return resp.ok
    except Exception as e:
        print(f"[WA ERROR] Gagal kirim ke {nomor}: {e}")
        return False

# ========= DB INIT =========
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS anggota (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT DEFAULT 'user'
                    )''')
        conn.commit()

# ========= FUNGSI BANTU =========
def buat_tabel_tugas_if_not_exists(bulan, tahun):
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
        conn.commit()

def simpan_tugas_bulanan(name, date, time, position):
    dt = datetime.strptime(date, '%Y-%m-%d')
    bulan = dt.month
    tahun = dt.year
    buat_tabel_tugas_if_not_exists(bulan, tahun)

    nama_tabel = f"tugas_{tahun}_{bulan:02}"
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(f'''INSERT INTO {nama_tabel} (username, date, time, position)
                      VALUES (?, ?, ?, ?)''', (name, date, time, position))
        conn.commit()

import calendar
from datetime import datetime
import sqlite3

def get_tugas_bulanan(bulan, tahun):
    nama_tabel = f"tugas_{tahun}_{bulan:02}"
    posisi_list = ['Operator', 'Kameramen', 'Supervisor']
    data_db = {}

    # Ambil data dari DB
    with sqlite3.connect('crembo.db') as conn:
        c = conn.cursor()
        try:
            c.execute(f"SELECT username, date, time, position FROM {nama_tabel}")
            for username, date, time, position in c.fetchall():
                if date not in data_db:
                    data_db[date] = {}
                if time not in data_db[date]:
                    data_db[date][time] = {}
                data_db[date][time][position] = username
        except sqlite3.OperationalError:
            pass

    hasil = []
    jumlah_hari = calendar.monthrange(tahun, bulan)[1]

    for hari in range(1, jumlah_hari + 1):
        tanggal = datetime(tahun, bulan, hari)
        tanggal_str = tanggal.strftime('%Y-%m-%d')
        hari_dalam_minggu = tanggal.strftime('%A')

        if hari_dalam_minggu == 'Sunday':
            jam_list = ['08:00', '10:00', '17:00', '19:00']
        else:
            jam_list = ['18:00']

        tugas_per_jam = {}
        for jam in jam_list:
            tugas_per_jam[jam] = {
                pos: data_db.get(tanggal_str, {}).get(jam, {}).get(pos, '') for pos in posisi_list
            }

        hasil.append({'date': tanggal_str, 'tasks': tugas_per_jam})

    return list(enumerate(hasil, start=1))


# ========= ROUTES =========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Koneksi ke database
        conn = sqlite3.connect('crembo.db')
        c = conn.cursor()

        # Ambil data user berdasarkan username
        c.execute("SELECT * FROM anggota WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user:
            stored_hash = user[4]  # kolom ke-5 = password_hash
            if check_password_hash(stored_hash, password):
                session['logged_in'] = True
                session['username'] = user[2]  # username
                session['role'] = user[5]      # role
#                flash("Login berhasil!")
                tulis_log(f"Login berhasil oleh {username}")

                return redirect(url_for('dashboard'))  # ganti dengan halaman sesuai
            else:
                flash("Password salah.")
        else:
            flash("Username tidak ditemukan.")

    return render_template('login.html')

@app.route('/logout')
def logout():
#    tulis_log(f"Logout {username} berhasil")
    session.clear()
#    tulis_log(f"Logout oleh {catat} berhasil")
    return redirect(url_for('index'))
# +++++++++++++++++++++++++++++++++++++++++++++++DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']

    # Ambil nama dari DB berdasarkan username
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT nama FROM anggota WHERE username = ?", (username,))
        row = c.fetchone()

    nama = row[0] if row else 'User'

    return render_template('dashboard.html', role=session['role'], nama=nama)

#@app.route('/register_tugas', methods=['GET', 'POST'])
#def register_tugas():
#    if 'username' not in session:
#        flash("Login sebagai user untuk daftar tugas")
#        return redirect(url_for('login'))
#
#    if request.method == 'POST':
#        name = session['username']
#        date = request.form['date']
#        time = request.form['time']
#        position = request.form['position']
#        simpan_tugas_bulanan(name, date, time, position)
#        flash('Tugas berhasil disimpan')
#
#    return render_template('register.html')
@app.route('/register_tugas', methods=['GET', 'POST'])
def register_tugas():
    if 'username' not in session:
        flash("Login sebagai user untuk daftar tugas")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = session['username']
        date = request.form['date']
        time = request.form['time']
        position = request.form['position']

        # Cek apakah sudah ada tugas di tanggal+jam+posisi yang sama
        dt = datetime.strptime(date, '%Y-%m-%d')
        bulan = dt.month
        tahun = dt.year
        nama_tabel = f"tugas_{tahun}_{bulan:02}"

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # pastikan tabel sudah ada
            c.execute(f'''CREATE TABLE IF NOT EXISTS {nama_tabel} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT,
                            date TEXT,
                            time TEXT,
                            position TEXT
                        )''')
            # cek bentrok
            c.execute(f'''SELECT COUNT(*) FROM {nama_tabel}
                          WHERE date = ? AND time = ? AND position = ?''', (date, time, position))
            count = c.fetchone()[0]

            if count > 0:
                flash(f"Maaf, posisi '{position}' pada {date} jam {time} sudah terisi.")
            else:
                # simpan data
                c.execute(f'''INSERT INTO {nama_tabel} (username, date, time, position)
                              VALUES (?, ?, ?, ?)''', (name, date, time, position))
                conn.commit()
                flash('Tugas berhasil disimpan.')
#                tulis_log(f"{username} melakukan pendaftaran tugas untuk tgl {date} jam {time}")
    return render_template('register.html')

#@app.route('/lihat_tugas', methods=['GET', 'POST'])
#def lihat_tugas():
#    if 'username' not in session:
#        return redirect(url_for('login'))
#
#    data = []
#    if request.method == 'POST':
#        bulan = int(request.form['bulan'])
#        tahun = int(request.form['tahun'])
#        try:
#            data = get_tugas_bulanan(bulan, tahun)
#        except:
#            flash('Belum ada data untuk bulan tersebut')
#
#    return render_template('lihat.html', data=data)
@app.route('/lihat_tugas', methods=['GET', 'POST'])
def lihat_tugas():
#    if 'username' not in session:
#        return redirect(url_for('login'))

    data = []
    no_data = False

    # Buat daftar bulan
    #bulan_list = list(range(1, 13))  # Atau bisa pakai: ['Januari', ..., 'Desember']
    bulan_dict = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}

    if request.method == 'POST':
        bulan = int(request.form['bulan'])
        tahun = int(request.form['tahun'])
        try:
            data = get_tugas_bulanan(bulan, tahun)
            if not data:
                no_data = True
        except:
            no_data = True
            flash('Belum ada data untuk bulan tersebut')
 #   tulis_log(f"{username} melihat jadwal tugas")
    #return render_template('lihat.html', data=data, bulan_list=bulan_list, no_data=no_data)
    return render_template('lihat.html', data=data, bulan_dict=bulan_dict, no_data=no_data)


#@app.route('/ubah_role', methods=['GET', 'POST'])
#def ubah_role():
#    if 'username' not in session or session['role'] != 'admin':
#        return redirect(url_for('login'))
#
#    with sqlite3.connect(DB_NAME) as conn:
#        c = conn.cursor()
#        if request.method == 'POST':
#            uname = request.form['username']
#            new_role = request.form['role']
#            c.execute("UPDATE users SET role=? WHERE username=?", (new_role, uname))
#            conn.commit()
#            flash(f"Role {uname} diubah jadi {new_role}")
#
#        c.execute("SELECT username, role FROM anggota")
#        users = c.fetchall()
#
#    return render_template('dashboard.html', users=users, role=session['role'])
@app.route('/ubah_role', methods=['GET', 'POST'])
def ubah_role():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        if request.method == 'POST':
            uname = request.form['username']
            new_role = request.form['role']
            c.execute("UPDATE anggota SET role=? WHERE username=?", (new_role, uname))
            conn.commit()
            flash(f"Role {uname} diubah jadi {new_role}")

        c.execute("SELECT nama, username, role FROM anggota")
        users = c.fetchall()
  #  tulis_log(f"{username} sebagai Admin mengubah role user")
    return render_template('role.html', users=users)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++PROFIL++++++++++
@app.route('/profil')
def profil():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT nama, username, tgl_lahir, telp, email FROM anggota WHERE username = ?", (username,))
        row = c.fetchone()

    if row:
        return render_template('profil.html', nama=row[0], username=row[1], tgl_lahir=row[2], telp=row[3], email=row[4])
    else:
        flash("Data tidak ditemukan.")
        return redirect(url_for('dashboard'))

#++++++++++++++++++++++++++++++++++++++++++++++++++++++ update profil +++++++++++
@app.route('/update_profil', methods=['GET', 'POST'])
def update_profil():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT nama, tgl_lahir, telp, email, password FROM anggota WHERE username = ?", (username,))
        row = c.fetchone()

    if not row:
        flash("Data tidak ditemukan.")
        return redirect(url_for('dashboard'))

    nama_lama, tgl_lahir_lama, telp_lama, email_lama, pass_hash = row

    if request.method == 'POST':
        nama_baru = request.form.get('nama','').strip()
        tgl_lahir_baru = request.form.get('tgl_lahir','').strip()
        telp_baru = request.form.get('telp','').strip()
        email_baru = request.form.get('email', '').strip()
        pass_lama = request.form.get('pass_lama','')
        pass_baru = request.form.get('pass_baru','')
        pass_konfirmasi = request.form.get('pass_konfirmasi','')

        print("DEBUG - Tanggal lahir dari form:", tgl_lahir_baru)
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("UPDATE anggota SET nama = ?, tgl_lahir = ?, telp = ?, email = ?  WHERE username = ?",
                      (nama_baru, tgl_lahir_baru, telp_baru, email_baru, username))

            if pass_lama:
                if not pass_hash:
                    flash("Password lama salah.")
                    return redirect(url_for('update_profil'))
            try:
                if not check_password_hash(pass_hash, pass_lama):
                    flash("Password lama salah.")
                    return redirect(url_for('update_profil'))
            except Exception as e:
                flash("Terjadi kesalahan saat memverifiksi password.")
                print("ERROR saat cek hash:", e)
                return redirect(url_for('update_profil'))

            if pass_baru != pass_konfirmasi:
                flash("Konfirmasi password baru tidak cocok.")
                return redirect(url_for('update_profil'))

            hash_baru = generate_password_hash(pass_baru)
            c.execute("UPDATE anggota SET password = ? WHERE username = ?", (hash_baru, username))

            conn.commit()
            flash("Profil berhasil diperbarui.")
            return redirect(url_for('profil'))
   # tulis_log(f"{username} meng-update profilnya")
    return render_template('update_profil.html', nama=nama_lama, tgl_lahir=tgl_lahir_lama or '', telp=telp_lama or '', email=email_lama or '')

#++++++++++++++++++++++++++++++ tambah anggota ++++++++++++++++++++++++++++++++
@app.route('/tambah_anggota', methods=['GET', 'POST'])
def tambah_anggota():
    # Hanya admin
    if 'username' not in session or session.get('role') != 'admin':
        flash("Hanya admin yang boleh menambah anggota.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama      = request.form.get('nama', '').strip()
        username  = request.form.get('username', '').strip()
        tgl_lahir = request.form.get('tgl_lahir', '').strip()
        telp      = request.form.get('telp', '').strip()
        email     = request.form.get('email', '').strip()
        password  = request.form.get('password', '').strip()

        # Validasi minimal
        if not nama or not username or not telp or not password:
            flash("Nama, Username, Telepon, dan Password wajib diisi.")
            return redirect(url_for('tambah_anggota'))

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Cek username sudah dipakai atau belum
            c.execute("SELECT 1 FROM anggota WHERE username = ?", (username,))
            if c.fetchone():
                flash("Username sudah terdaftar. Gunakan username lain.")
                return redirect(url_for('tambah_anggota'))

            pass_hash = generate_password_hash(password)

            # FIX: jumlah kolom = jumlah value = 7
            c.execute("""
                INSERT INTO anggota (nama, username, tgl_lahir, telp, email, password, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nama, username, tgl_lahir, telp, email, pass_hash, 'user'))

            conn.commit()

        # WA
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

        flash(f"Josss, '{nama}' sudah berhasil ditambahkan dan notifikasi WA sudah dikirim.")
        return redirect(url_for('ubah_role'))

    return render_template('tambah_anggota.html')


@app.context_processor
def inject_nama_dan_tanggal():
    nama = None
    if 'username' in session:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT nama FROM anggota WHERE username = ?", (session['username'],))
            row = c.fetchone()
            if row:
                nama = row[0]

    # Format tanggal hari ini (misal: Kamis, 18 Juli 2025)
    hari_ini = datetime.now().strftime('%A, %d %B %Y')

    # Ubah nama hari dan bulan ke Bahasa Indonesia (optional)
    indo_hari = {
        'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
        'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
    }
    indo_bulan = {
        'January': 'Januari', 'February': 'Februari', 'March': 'Maret',
        'April': 'April', 'May': 'Mei', 'June': 'Juni',
        'July': 'Juli', 'August': 'Agustus', 'September': 'September',
        'October': 'Oktober', 'November': 'November', 'December': 'Desember'
    }

    for eng, indo in indo_hari.items():
        hari_ini = hari_ini.replace(eng, indo)
    for eng, indo in indo_bulan.items():
        hari_ini = hari_ini.replace(eng, indo)

    return dict(nama=nama, hari_ini=hari_ini)


@app.route('/testnav')
def testnav():
    return render_template('test_nav.html')

# ==========================================================TAMBAHAN=====================================
# =========================================================
# === KEGIATAN FORM (JSON BASED, SINGLE TABLE)
# =========================================================
import json
from datetime import timedelta

def init_kegiatan_table():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS kegiatan_form (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT,
                slug TEXT UNIQUE,
                jumlah_hari INTEGER,
                jumlah_misa INTEGER,
                jml_kamera INTEGER,
                jml_supervisor INTEGER,
                jml_fotografer INTEGER,
                misa_terakhir DATE,
                form_json TEXT,
                is_published INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()

def slugify(text):
    return text.lower().replace(' ', '-')

# ---------------------------------------------------------
# ADMIN: LIST KEGIATAN
# ---------------------------------------------------------
@app.route('/admin/kegiatan')
def admin_kegiatan_list():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    init_kegiatan_table()

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, judul, is_published, misa_terakhir
            FROM kegiatan_form
            ORDER BY id DESC
        """)
        data = c.fetchall()

    return render_template('admin_kegiatan_list.html', data=data)

# ---------------------------------------------------------
# ADMIN: TAMBAH / EDIT KEGIATAN
# ---------------------------------------------------------
@app.route('/admin/kegiatan/form', methods=['GET', 'POST'])
def admin_kegiatan_form():
    # ====== AUTH (sesuaikan kalau role kamu beda) ======
    if 'username' not in session:
        return redirect(url_for('index'))
    if session.get('role') != 'admin':
        abort(403)

    # ====== ambil data dropdown anggota (wajib) ======
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT username, nama FROM anggota ORDER BY username ASC")
        rows = c.fetchall()
    anggota_options = [{"username": r["username"], "nama": r["nama"]} for r in rows]

    # ====== mode tambah / edit (kalau nanti kamu pakai) ======
    kegiatan = None
    misa_list = []

    # kalau kamu belum punya edit, biarkan kosong dulu.
    # nanti kalau sudah ada tabel kegiatan dan mau edit, baru isi.

    if request.method == 'POST':
        # sementara biarkan POST belum dipakai kalau kamu belum pasang parsing-nya
        # minimal jangan error dulu
        flash("POST belum diaktifkan. Fokus stabilkan tampilan form dulu.", "info")
        return redirect(url_for('admin_kegiatan_form'))

    # ====== render template dengan variabel yang BENAR ======
    return render_template(
        'admin_kegiatan_form.html',
        kegiatan=kegiatan,
        misa_list=misa_list,
        anggota_options=anggota_options
    )

# ---------------------------------------------------------
# PUBLIC PAGE
# ---------------------------------------------------------
@app.route('/kegiatan/<slug>')
def kegiatan_public(slug):
    init_kegiatan_table()

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT judul, form_json, misa_terakhir
            FROM kegiatan_form
            WHERE slug=? AND is_published=1
        """, (slug,))
        row = c.fetchone()

    if not row:
        return "Tidak ditemukan", 404

    misa_terakhir = datetime.strptime(row[2], '%Y-%m-%d')
    if datetime.now() > misa_terakhir + timedelta(days=3):
        return "Pengumuman telah berakhir", 404

    return render_template(
        'kegiatan_public.html',
        judul=row[0],
        data=json.loads(row[1])
    )



# ========= MAIN =========
if __name__ == '__main__':
    init_db()
    app.run(debug=True)

