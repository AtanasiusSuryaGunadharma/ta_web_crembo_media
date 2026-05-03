# Crembo Flask App

Project baru untuk menggabungkan Flask dengan frontend mockup di folder `Mockup_hifi`.

## Run

Dari folder ini, jalankan:

```powershell
& "D:\SURYA\UAJY\Semester 8\TA\ta_crembo_media_6\.venv\Scripts\python.exe" app.py
```

Lalu buka:

`http://127.0.0.1:5000/`

## Catatan

- Folder `registrasi` tetap dibiarkan sebagai source lama.
- Frontend HTML dan aset statis sudah disalin ke `crembo_flask/frontend`.
- Schema MySQL ada di `crembo_db_new.sql`.
- Migrasi data SQLite lama ke MySQL bisa dijalankan dengan:

```powershell
& "c:\xampp\htdocs\ta_crembo_media\.venv\Scripts\python.exe" migrate_sqlite_to_mysql.py --mysql-user root --mysql-password "" --mysql-database crembo_db_new
```

- Script migrasi membaca SQLite lama dari `registrasi/crembo.db` dan menyalin tabel `anggota`, `kegiatan`, `kegiatan_form`, `tugas_form`, `tugas_form_slot`, `tugas_form_audit`, plus tabel tugas bulanan `tugas_YYYY_MM`.
