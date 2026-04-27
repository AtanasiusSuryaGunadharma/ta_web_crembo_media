import sqlite3

# Koneksi ke database
conn = sqlite3.connect("crembo.db")
cursor = conn.cursor()

# Buat tabel anggota kalau belum ada
cursor.execute('''
CREATE TABLE IF NOT EXISTS anggota (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    username TEXT UNIQUE,
    telp TEXT,
    password TEXT
)
''')

# Buka file anggota_list.txt dan baca baris per baris
with open("anggota_list.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:  # skip baris kosong
            username, nama, telp, password = line.split("|")
            try:
                cursor.execute(
                    "INSERT INTO anggota (username, nama, telp, password) VALUES (?, ?, ?, ?)",
                    (username, nama, telp, password)
                )
            except sqlite3.IntegrityError:
                print(f"[!] Username '{username}' sudah ada, dilewati.")

# Simpan dan tutup koneksi
conn.commit()
conn.close()

print("✅ Data anggota berhasil dimasukkan ke crembo.db.")
