from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
import pandas as pd
from flask import send_file
import logging


app = Flask(__name__)
app.secret_key = 'registrasi_tugas'

# Konfigurasi file penyimpanan
BASE_DIR = os.path.dirname(__file__)
ANGGOTA_FILE = os.path.join(BASE_DIR, 'nimda', 'anggota', 'anggota_list.txt')
TUGAS_FILE = os.path.join(BASE_DIR, 'tabel_streaming.txt')
ADMIN_FILE = os.path.join(BASE_DIR, 'nimda', 'nimda', 'admin_list.txt')  # Lokasi admin
file_path = 'tabel_streaming.txt'

# Fungsi cek admin
def validate_admin(username, password):
    if not os.path.exists(ADMIN_FILE):
        return False
    with open(ADMIN_FILE, 'r') as f:
        for line in f:
            data = line.strip().split('|')
            if len(data) == 2 and data[0] == username and data[1] == password:
                return True
    return False

# Fungsi simpan admin baru
def save_admin(username, password):
    with open(ADMIN_FILE, 'a') as f:
        f.write(f"{username}|{password}\n")

# Fungsi simpan anggota baru
def save_anggota(nama, username, telp, password):
    with open(ANGGOTA_FILE, 'a') as f:
        f.write(f"{nama}|{username}|{telp}|{password}\n")

# Fungsi cek user login
def validate_user(username, password):
    if not os.path.exists(ANGGOTA_FILE):
        return False
    with open(ANGGOTA_FILE, 'r') as f:
        for line in f:
            data = line.strip().split('|')
            if len(data) >= 4 and data[1] == username and data[3] == password:
                return True
    return False

# Fungsi cek username anggota sudah ada
def is_username_exists(username):
    if not os.path.exists(ANGGOTA_FILE):
        return False
    with open(ANGGOTA_FILE, 'r') as f:
        for line in f:
            data = line.strip().split('|')
            if len(data) >= 2 and data[1] == username:
                return True
    return False

# Fungsi simpan data tugas
def save_tugas(data):
    with open(TUGAS_FILE, 'a') as f:
        f.write(data + '\n')

# Fungsi baca semua data tugas
def read_all_tugas():
    if not os.path.exists(TUGAS_FILE):
        return []
    all_data = {}
    with open(TUGAS_FILE, 'r') as f:
        for line in f:
            fields = line.strip().split('|')
            if len(fields) == 5:
                name, date, time, position, phone = fields
                if date not in all_data:
                    all_data[date] = {'date': date, 'tasks': {}}
                if time not in all_data[date]['tasks']:
                    all_data[date]['tasks'][time] = {'Operator': '', 'Kameramen': '', 'Supervisor': ''}
                all_data[date]['tasks'][time][position] = name
    sorted_dates = sorted(all_data.keys(), key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
    return [(idx + 1, all_data[date]) for idx, date in enumerate(sorted_dates)]

# Fungsi cek posisi sudah terisi
def is_position_taken(date, time, position):
    data = read_all_tugas()
    for _, item in data:
        if item['date'] == date and time in item['tasks'] and item['tasks'][time][position]:
            return True
    return False

# Landing Page
@app.route('/')
def landing():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

# Login User
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if validate_user(username, password):
            session['logged_in'] = True
            session['role'] = 'user'
            session['username'] = username
            session.pop('_flashes', None)
            flash('Login berhasil sebagai user!')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah!')
            return redirect(url_for('login'))

    return render_template('login.html')

# Login Admin
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if validate_admin(username, password):
            session['logged_in'] = True
            session['role'] = 'admin'
            session['username'] = username
            flash('Login berhasil sebagai admin!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password admin salah!')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.')
    return redirect(url_for('landing'))

# Dashboard User
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in') or session.get('role') != 'user':
        flash('Silakan login sebagai user terlebih dahulu.')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Dashboard Admin
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Silakan login sebagai admin terlebih dahulu.')
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# Daftar Admin Baru
@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Hanya admin yang dapat mendaftar admin baru.')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        save_admin(username, password)
        flash('Admin baru berhasil ditambahkan!')
        return redirect(url_for('admin_dashboard'))

    return render_template('register_admin.html')

# Daftar Anggota Baru oleh Admin
@app.route('/register_anggota_admin', methods=['GET', 'POST'])
def register_anggota_admin():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Hanya admin yang dapat mendaftar anggota baru.')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        nama = request.form.get('nama')
        username = request.form.get('username')
        telp = request.form.get('telp')
        password = request.form.get('password')

        if is_username_exists(username):
            flash('Username sudah terdaftar!')
            return redirect(url_for('register_anggota_admin'))

        save_anggota(nama, username, telp, password)
        flash('Anggota baru berhasil ditambahkan!')
        return redirect(url_for('admin_dashboard'))

    return render_template('register_anggota_admin.html')

# Registrasi Tugas (User)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('logged_in') or session.get('role') != 'user':
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = session.get('username')
        date = request.form.get('date')
        time = request.form.get('time')
        position = request.form.get('position')
        phone = request.form.get('phone')

        if is_position_taken(date, time, position):
            flash('Posisi sudah terisi. Silakan pilih waktu atau posisi lain.')
            return redirect(url_for('register'))

        formatted_data = f"{name}|{date}|{time}|{position}|{phone}"
        save_tugas(formatted_data)
        flash(f'Registrasi berhasil untuk {name} pada {date} jam {time} di posisi {position}.')
        return redirect(url_for('register'))

    data = read_all_tugas()
    return render_template('register.html', data=data)

# Lihat Jadwal
@app.route('/lihat')
def lihat():
    if not session.get('logged_in') or session.get('role') != 'user':
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))

    data = read_all_tugas()
    return render_template('lihat.html', data=data)

#Ubah data oleh user sendiri
@app.route('/ubah_data', methods=['GET', 'POST'])
def ubah_data():
    if not session.get('logged_in') or session.get('role') != 'user':
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))

    username = session.get('username')

    if request.method == 'POST':
        nama_baru = request.form.get('nama')
        telp_baru = request.form.get('telp')
        password_baru = request.form.get('password')

        # Update data di anggota.txt
        lines = []
        with open(ANGGOTA_FILE, 'r') as f:
            for line in f:
                data = line.strip().split('|')
                if len(data) >= 4 and data[1] == username:
                    lines.append(f"{nama_baru}|{username}|{telp_baru}|{password_baru}\n")
                else:
                    lines.append(line)
        with open(ANGGOTA_FILE, 'w') as f:
            f.writelines(lines)

        flash('Data berhasil diperbarui!')
        return redirect(url_for('dashboard'))

    # Ambil data lama untuk diisi di form
    nama, telp, password = '', '', ''
    with open(ANGGOTA_FILE, 'r') as f:
        for line in f:
            data = line.strip().split('|')
            if len(data) >= 4 and data[1] == username:
                nama = data[0]
                telp = data[2]
                password = data[3]
                break

    return render_template('ubah_data.html', nama=nama, telp=telp, password=password)

#Ubah jadwal tugas
@app.route('/hapus_tugas/<date>/<time>', methods=['GET'])
def hapus_tugas(date, time):
    if not session.get('logged_in') or session.get('role') != 'user':
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))

    username = session.get('username')
    lines = []
    deleted = False

    with open(TUGAS_FILE, 'r') as f:
        for line in f:
            fields = line.strip().split('|')
            if len(fields) == 5 and fields[0] == username and fields[1] == date and fields[2] == time:
                deleted = True
                continue  # Hapus baris ini
            lines.append(line)

    with open(TUGAS_FILE, 'w') as f:
        f.writelines(lines)

    if deleted:
        flash('Tugas berhasil dihapus.')
    else:
        flash('Tugas tidak ditemukan atau Anda tidak punya izin untuk menghapus.')

    return redirect(url_for('register'))

@app.route('/download_excel')
def download_excel():
    if not os.path.exists(file_path):
        flash('Belum ada data untuk diunduh.')
        return redirect(url_for('lihat'))

    # Baca data dari file
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            fields = line.strip().split('|')
            if len(fields) == 5:
                name, date, time, position, phone = fields
                data.append({'Nama': name, 'Tanggal': date, 'Jam': time, 'Posisi': position, 'Telepon': phone})

    # Convert ke DataFrame
    df = pd.DataFrame(data)

    # Simpan ke Excel
    excel_path = 'jadwal_streaming.xlsx'
    print('Data:', data)

    df.to_excel(excel_path, index=False)

    # Download file
    return send_file(excel_path, as_attachment=True)

#Lihat data admin
@app.route('/nimda/nimda')
def daftar_admin():
    admin_list = []
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'r') as f:
            for line in f:
                fields = line.strip().split('|')
                if len(fields) == 2:
                    username, password = fields
                    admin_list.append({'username': username, 'password': password})
    return render_template('daftar_admin.html', admins=admin_list)

#Lihat data anggota
@app.route('/nimda/anggota')
def daftar_anggota():
    anggota_list = []
    if os.path.exists(ANGGOTA_FILE):
        with open(ANGGOTA_FILE, 'r') as f:
            for line in f:
                fields = line.strip().split('|')
                if len(fields) == 4:
                    nama, telepon, username, password = fields
                    anggota_list.append({'nama': nama, 'telepon': telepon, 'username': username, 'password': password})
    return render_template('daftar_anggota.html', anggota=anggota_list)

# Buat folder logs jika belum ada
if not os.path.exists('logs'):
    os.makedirs('logs')

# Konfigurasi logging
logging.basicConfig(
    filename='logs/activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
