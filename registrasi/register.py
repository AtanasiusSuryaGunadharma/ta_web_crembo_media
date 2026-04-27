from flask import Flask, request, render_template, redirect, url_for, flash
from datetime import datetime
import os
import sys

app = Flask(__name__)
app.secret_key = 'registrasi_tugas'

# Direktori penyimpanan file
file_dir = 'tugas_streaming/'
os.makedirs(file_dir, exist_ok=True)

# Fungsi untuk menyimpan data
def save_data(data):
    month = datetime.now().strftime('%B')
    file_name = f'Tugas-{month}.txt'
    file_path = os.path.join(file_dir, file_name)
    try:
        with open(file_path, 'a') as f:
            f.write(data + '\n')
    except Exception as e:
        flash(f'Error saat menyimpan data: {str(e)}')

# Fungsi untuk memeriksa apakah posisi sudah terisi
def is_position_taken(date, time, position):
    month = datetime.now().strftime('%B')
    file_name = f'Tugas-{month}.txt'
    file_path = os.path.join(file_dir, file_name)
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r') as f:
            for line in f:
                fields = line.strip().split(',')
                if len(fields) >= 4 and fields[1] == date and fields[2] == time and fields[3] == position:
                    return True
    except Exception as e:
        flash(f'Error saat memeriksa posisi: {str(e)}')
    return False

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        time = request.form['time']
        position = request.form['position']
        phone = request.form['phone']

        # Validasi posisi
        if is_position_taken(date, time, position):
            flash('Posisi sudah terisi. Silakan pilih waktu atau posisi lain.')
            return redirect(url_for('register'))

        # Simpan data
        data = f'{name},{date},{time},{position},{phone}'
        save_data(data)
        flash('Registrasi berhasil!')
        return redirect(url_for('register'))

    return render_template('register.html')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except SystemExit:
        sys.exit(0)
