from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Notification Controller

# Source legacy app.py lines 3494-3619 | routes: /api/notifications
@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    ensure_notifications_schema()
    try:
        create_due_task_reminder_notifications()
    except Exception as exc:
        print(f"[WARN] Gagal membuat notifikasi pengingat tugas: {exc}")
    try:
        create_monthly_requirement_notifications()
    except Exception as exc:
        print(f"[WARN] Gagal membuat notifikasi target bulanan: {exc}")
    try:
        create_streaming_evaluation_reminder_notifications()
    except Exception as exc:
        print(f"[WARN] Gagal membuat notifikasi pengingat evaluasi streaming: {exc}")
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    user_key = None
    role = "user" 
    
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
        role = viewer.get("role") or "user"
    else:
        if client_key:
            user_key = client_key

    limit = int(request.args.get("limit") or 50)
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        target_roles = ["admin", "super_admin"] if role in ["admin", "super_admin"] else ["user"]
        format_strings = ','.join(['%s'] * len(target_roles))

        # Filter target_user_id langsung di SQL, bukan hanya di frontend.
        # Sebelumnya API mengambil 50 notifikasi global terlebih dahulu, lalu dashboard
        # memfilter target_user_id di browser. Jika ada banyak notifikasi milik user lain,
        # notifikasi evaluasi milik user yang sedang login bisa tidak ikut terbawa limit.
        user_id = normalize_text(viewer.get("user_id")) if viewer.get("logged_in") else ""
        target_user_clause = ""
        target_user_params = []
        if user_id:
            target_user_clause = """
              AND (
                `data` LIKE %s
                OR `data` LIKE %s
                OR `data` LIKE %s
                OR `data` LIKE %s
                OR `target_role` IS NOT NULL
                OR `type` NOT IN ('tugas','evaluasi','tukar','keanggotaan','peminjaman','kerusakan')
              )
            """
            target_user_params = [
                f'%"target_user_id": "{user_id}"%',
                f'%"target_user_id":"{user_id}"%',
                f'%"target_user_id": {user_id}%',
                f'%"target_user_id":{user_id}%',
            ]

        inactive_type_clause = ""
        if viewer.get("logged_in") and normalize_role_value(role) == "user" and normalize_status(viewer.get("status_akun") or "aktif") == "nonaktif":
            inactive_type_clause = " AND `type` = 'keanggotaan'"

        query = f"""
            SELECT * FROM `notifications`
            WHERE (`target_role` IS NULL OR `target_role` IN ({format_strings}))
            {target_user_clause}
            {inactive_type_clause}
            ORDER BY `created_at` DESC, `id` DESC LIMIT %s
        """
        params = tuple(target_roles) + tuple(target_user_params) + (limit,)

        cursor.execute(query, params)
        rows = cursor.fetchall() or []
        results = []
        viewer_user_id = normalize_text(viewer.get("user_id")) if viewer.get("logged_in") else ""
        viewer_created_at = None
        if viewer_user_id:
            try:
                cursor.execute("SELECT created_at FROM anggota WHERE id = %s LIMIT 1", (viewer_user_id,))
                member_created_row = cursor.fetchone()
                viewer_created_at = member_created_row.get("created_at") if member_created_row else None
            except Exception:
                viewer_created_at = None

        user_scoped_types = {"tugas", "evaluasi", "tukar", "keanggotaan", "peminjaman", "kerusakan", "akun"}
        for r in rows:
            try:
                payload = json.loads(r.get("data") or "{}")
            except Exception:
                payload = {}

            # Filter ulang di Python supaya notifikasi lama/orphan tidak bocor ke user baru.
            payload_target_user = normalize_text(payload.get("target_user_id"))
            notif_type = normalize_text(r.get("type"))
            notif_created = r.get("created_at")

            if viewer_user_id:
                if payload_target_user and payload_target_user != viewer_user_id:
                    continue
                # Notifikasi personal seperti Tugas Baru lama yang belum punya target_user_id
                # tidak boleh tampil ke semua anggota. Broadcast tetap boleh jika target_role diisi.
                if notif_type in user_scoped_types and not payload_target_user and not normalize_text(r.get("target_role")):
                    continue
                # Jika id user pernah dipakai/akun baru dibuat setelah notifikasi lama, jangan tampilkan.
                if viewer_created_at and notif_created and notif_created < viewer_created_at and notif_type in user_scoped_types:
                    continue

            is_read = False
            if user_key:
                cursor.execute("SELECT 1 FROM `notification_reads` WHERE `notification_id` = %s AND `user_key` = %s LIMIT 1", (r["id"], user_key))
                is_read = cursor.fetchone() is not None
            results.append({
                "id": r.get("id"),
                "type": r.get("type"),
                "title": r.get("title"),
                "body": r.get("body"),
                "url": r.get("url"),
                "data": payload,
                "createdAt": r.get("created_at").isoformat() if r.get("created_at") else None,
                "read": bool(is_read),
            })
        return jsonify(results)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 4154-4177 | routes: /api/notifications/<notif_id>/mark_read
@app.route("/api/notifications/<notif_id>/mark_read", methods=["POST"])
def mark_notification_read(notif_id):
    ensure_notifications_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
    else:
        user_key = client_key or None
    if not user_key:
        return jsonify({"success": False, "error": "Missing client key"}), 400

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT IGNORE INTO `notification_reads` (`notification_id`, `user_key`) VALUES (%s, %s)", (notif_id, user_key))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 4179-4208 | routes: /api/notifications/<notif_id>/toggle_read
@app.route("/api/notifications/<notif_id>/toggle_read", methods=["POST"])
def toggle_notification_read(notif_id):
    ensure_notifications_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
    else:
        user_key = client_key or None
    if not user_key:
        return jsonify({"success": False, "error": "Missing client key"}), 400

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM `notification_reads` WHERE `notification_id` = %s AND `user_key` = %s LIMIT 1", (notif_id, user_key))
        if cursor.fetchone():
            cursor.execute("DELETE FROM `notification_reads` WHERE `notification_id` = %s AND `user_key` = %s", (notif_id, user_key))
            is_read = False
        else:
            cursor.execute("INSERT IGNORE INTO `notification_reads` (`notification_id`, `user_key`) VALUES (%s, %s)", (notif_id, user_key))
            is_read = True
        conn.commit()
        return jsonify({"success": True, "read": is_read})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 4210-4236 | routes: /api/notifications/mark_all_read
@app.route("/api/notifications/mark_all_read", methods=["POST"])
def mark_all_notifications_read():
    ensure_notifications_schema()
    viewer = current_user_context()
    client_key = str(request.args.get("clientKey") or request.headers.get("X-Registration-Client-Key") or "").strip()
    if viewer.get("logged_in"):
        user_key = f"member:{viewer.get('user_id') or viewer.get('username') or viewer.get('email') or 'member'}"
    else:
        user_key = client_key or None
    if not user_key:
        return jsonify({"success": False, "error": "Missing client key"}), 400

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT `id` FROM `notifications`")
        rows = cursor.fetchall() or []
        for r in rows:
            try:
                cursor.execute("INSERT IGNORE INTO `notification_reads` (`notification_id`, `user_key`) VALUES (%s, %s)", (r["id"], user_key))
            except Exception:
                pass
        conn.commit()
        return jsonify({"success": True})
    finally:
        cursor.close()
        conn.close()


