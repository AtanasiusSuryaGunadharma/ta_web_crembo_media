"""Model akses data anggota, admin, profil, dan status keanggotaan.

File ini disiapkan sebagai lapisan model. Helper umum memakai database.py.
Query detail yang kompleks masih dipanggil oleh service/controller hasil refactor
agar perilaku sistem tetap sama dengan kode produksi.
"""

from crembo_app.models.database import fetch_all, fetch_one, mysql_connection


__all__ = ["fetch_all", "fetch_one", "mysql_connection"]
