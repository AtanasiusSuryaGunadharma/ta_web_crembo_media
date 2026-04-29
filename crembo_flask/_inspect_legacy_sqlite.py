import json
import sqlite3
from pathlib import Path

for name in ["crembo.db", "crembo1.db", "crembo2.db"]:
    db_path = Path(r"c:\xampp\htdocs\ta_crembo_media\registrasi") / name
    print(f"=== {name} ===")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
    rows = cur.fetchall()
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    conn.close()
