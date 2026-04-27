import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = 'crembo.db'

nama = 'Baladeva'
username = 'Deva'
telp = '083113186247'
tgl_lahir = ''
password = 'deva123'
role = 'user'

password_hash = generate_password_hash(password)

with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute('''INSERT INTO anggota (nama, username, telp, password, role, tgl_lahir)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (nama, username, telp, password_hash, role, tgl_lahir))
    conn.commit()

print("Data anggota berhasil ditambahkan.")
