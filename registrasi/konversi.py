import sqlite3
from datetime import datetime
import os

DB_NAME = 'crembo.db'
TXT_FILE = 'tabel_streaming.txt'

def buat_tabel_tugas_if_not_exists(bulan, tahun):
    nama_tabel = f"tugas_{tahun}_{bulan:02}"
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS {nama_tabel} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                date TEXT,
                time TEXT,
                position TEXT
            )
        ''')
        conn.commit()

def simpan_tugas_bulanan(username, date, time, position):
    dt = datetime.strptime(date, '%Y-%m-%d')
    bulan = dt.month
    tahun = dt.year
    buat_tabel_tugas_if_not_exists(bulan, tahun)

    nama_tabel = f"tugas_{tahun}_{bulan:02}"
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(f'''
            INSERT INTO {nama_tabel} (username, date, time, position)
            VALUES (?, ?, ?, ?)
        ''', (username, date, time, position))
        conn.commit()

def migrasi_dari_txt_ke_db(file_path):
    if not os.path.exists(file_path):
        print(f"File '{file_path}' tidak ditemukan.")
        return

    count = 0
    with open(file_path, 'r') as f:
        for baris in f:
            parts = baris.strip().split('|')
            if len(parts) != 5:
                print("Format salah:", baris)
                continue

            username, tanggal, jam, posisi, _ = parts

            simpan_tugas_bulanan(username, tanggal, jam, posisi)
            count += 1

    print(f"Migrasi selesai. {count} tugas berhasil dimasukkan ke database.")

if __name__ == '__main__':
    migrasi_dari_txt_ke_db(TXT_FILE)
