from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Certificate Controller

# Source legacy app.py lines 7869-7888 | routes: /api/sertifikat/config
@app.route("/api/sertifikat/config", methods=["GET"])
def get_sertifikat_config():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `sertifikat_config` LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return jsonify({
            "romoName": row.get("romo_name") or "Romo Paroki GKR Baciro",
            "pembinaName": row.get("pembina_name") or "Pembina Crembo Media",
            "ketuaName": row.get("ketua_name") or "Ketua Crembo Media",
            "romoSignUrl": row.get("romo_sign_url") or "",
            "pembinaSignUrl": row.get("pembina_sign_url") or "",
            "ketuaSignUrl": row.get("ketua_sign_url") or "",
            "updatedAt": row.get("updated_at")
        })
    return jsonify({})


# Source legacy app.py lines 7890-7916 | routes: /api/sertifikat/config
@app.route("/api/sertifikat/config", methods=["POST"])
def set_sertifikat_config():
    ensure_auth_schema()
    data = request.json or {}
    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE `sertifikat_config`
        SET `romo_name` = %s,
            `pembina_name` = %s,
            `ketua_name` = %s,
            `romo_sign_url` = %s,
            `pembina_sign_url` = %s,
            `ketua_sign_url` = %s
        WHERE `id` = 1
    """, (
        data.get("romoName", "Romo Paroki GKR Baciro"),
        data.get("pembinaName", ""),
        data.get("ketuaName", ""),
        data.get("romoSignUrl", ""),
        data.get("pembinaSignUrl", ""),
        data.get("ketuaSignUrl", "")
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})


