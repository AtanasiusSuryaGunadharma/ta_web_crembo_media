import sqlite3

# Lokasi file
txt_file = 'tabel_streaming.txt'
db_file = 'crembo.db'
nama_tabel = 'tugas_2025_07'

# Buat koneksi ke database
conn = sqlite3.connect(db_file)
c = conn.cursor()

# Buat tabel jika belum ada
c.execute(f'''
    CREATE TABLE IF NOT EXISTS {nama_tabel} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        tanggal TEXT,
        jam TEXT,
        posisi TEXT
    )
''')

# Baca file txt dan masukkan ke tabel
with open(txt_file, 'r') as file:
    for line in file:
        parts = line.strip().split('|')
        if len(parts) == 5:
            username, tanggal, jam, posisi, telp = parts
            c.execute(f'''
                INSERT INTO {nama_tabel} (username, tanggal, jam, posisi)
                VALUES (?, ?, ?, ?)
            ''', (username, tanggal, jam, posisi))

# Simpan dan tutup koneksi
conn.commit()
conn.close()

print("Data berhasil dikonversi ke database.")
