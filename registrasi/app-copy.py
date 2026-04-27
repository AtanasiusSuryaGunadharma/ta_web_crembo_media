from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os
from werkzeug.security import check_password_hash
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'rahasia'

DB_NAME = 'crembo.db'

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

#def get_tugas_bulanan(bulan, tahun):
#    nama_tabel = f"tugas_{tahun}_{bulan:02}"
#    with sqlite3.connect(DB_NAME) as conn:
#        c = conn.cursor()
#        c.execute(f"SELECT username, date, time, position FROM {nama_tabel}")
#        data = c.fetchall()
#    return data

#def get_tugas_bulanan(bulan, tahun):
#    nama_tabel = f"tugas_{tahun}_{bulan:02}"
#
#    with sqlite3.connect('crembo.db') as conn:
#        c = conn.cursor()
#        try:
#            c.execute(f"SELECT username, date, time, position FROM {nama_tabel} ORDER BY date, time")
#            data = c.fetchall()
#        except sqlite3.OperationalError as e:
#            print("Error saat membaca tabel:", e)
#            return []
#
    # Susun data jadi format per tanggal dan jam
#    tugas_terstruktur = []
#    data_per_tanggal = {}
#
#    for row in data:
#        name, date, time, position = row
#        key = (date, time)
#        if date not in data_per_tanggal:
#            data_per_tanggal[date] = {}
#
#        if key not in data_per_tanggal[date]:
#            data_per_tanggal[date][time] = {'Operator': '', 'Kameramen': '', 'Supervisor': ''}
#
#        data_per_tanggal[date][time][position] = name
#
#    index = 1
#    for date in sorted(data_per_tanggal.keys()):
#        tugas_terstruktur.append({
#            'date': date,
#            'tasks': data_per_tanggal[date]
 #       })
#
#    return list(enumerate(tugas_terstruktur, start=1))
def get_tugas_bulanan(bulan, tahun):
    nama_tabel = f"tugas_{tahun}_{bulan:02}"

    with sqlite3.connect('crembo.db') as conn:
        c = conn.cursor()
        try:
            c.execute(f"SELECT username, date, time, position FROM {nama_tabel} ORDER BY date, time")
            data = c.fetchall()
        except sqlite3.OperationalError as e:
            print("Error saat membaca tabel:", e)
            return []

    tugas_terstruktur = []
    data_per_tanggal = {}

    for row in data:
        name, date, time, position = row

        if date not in data_per_tanggal:
            data_per_tanggal[date] = {}

        if time not in data_per_tanggal[date]:
            data_per_tanggal[date][time] = {
                'Operator': '', 'Kameramen': '', 'Supervisor': ''
            }

        data_per_tanggal[date][time][position] = name

    return list(enumerate([
        {'date': date, 'tasks': data_per_tanggal[date]}
        for date in sorted(data_per_tanggal.keys())
    ], start=1))



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
                return redirect(url_for('dashboard'))  # ganti dengan halaman sesuai
            else:
                flash("Password salah.")
        else:
            flash("Username tidak ditemukan.")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
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
    if 'username' not in session:
        return redirect(url_for('login'))

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

    return render_template('role.html', users=users)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++PROFIL++++++++++
@app.route('/profil')
def profil():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT nama, username, tgl_lahir, telp FROM anggota WHERE username = ?", (username,))
        row = c.fetchone()

    if row:
        return render_template('profil.html', nama=row[0], username=row[1], tgl_lahir=row[2], telp=row[3])
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
        c.execute("SELECT nama, tgl_lahir, telp, password FROM anggota WHERE username = ?", (username,))
        row = c.fetchone()

    if not row:
        flash("Data tidak ditemukan.")
        return redirect(url_for('dashboard'))

    nama_lama, tgl_lahir_lama, telp_lama, pass_hash = row

    if request.method == 'POST':
        nama_baru = request.form.get('nama','').strip()
        tgl_lahir_baru = request.form.get('tgl_lahir','').strip()
        telp_baru = request.form.get('telp','').strip()
        pass_lama = request.form.get('pass_lama','')
        pass_baru = request.form.get('pass_baru','')
        pass_konfirmasi = request.form.get('pass_konfirmasi','')

        print("DEBUG - Tanggal lahir dari form:", tgl_lahir_baru)
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("UPDATE anggota SET nama = ?, tgl_lahir = ?, telp = ? WHERE username = ?",
                      (nama_baru, tgl_lahir_baru, telp_baru, username))

            if pass_lama:
                if not check_password_hash(pass_hash, pass_lama):
                    flash("Password lama salah.")
                    return redirect(url_for('update_profil'))

                if pass_baru != pass_konfirmasi:
                    flash("Konfirmasi password baru tidak cocok.")
                    return redirect(url_for('update_profil'))

                hash_baru = generate_password_hash(pass_baru)
                c.execute("UPDATE anggota SET password = ? WHERE username = ?", (hash_baru, username))

            conn.commit()
            flash("Profil berhasil diperbarui.")
            return redirect(url_for('profil'))

    return render_template('update_profil.html', nama=nama_lama, tgl_lahir=tgl_lahir_lama or '', telp=telp_lama or '')



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

# ========= MAIN =========
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
