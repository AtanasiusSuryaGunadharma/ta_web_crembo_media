"""Membership Controller.

File ini berisi route/controller yang dipisahkan dari app.py server lama.
Logika helper tetap dipanggil dari crembo_app.services.core agar perilaku produksi tetap sama.
"""

from crembo_app.services import core as _core

globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})


# Route dari app.py server: /api/membership/my
@app.route("/api/membership/my", methods=["GET"])
def api_membership_my():
    """Ambil status keanggotaan user login sebagai JSON murni dan read-only.

    Endpoint ini dipanggil bersamaan dengan /api/profile/me dari halaman profil.
    Karena itu endpoint tidak menjalankan auto-transition/DDL agar tidak terjadi
    deadlock MySQL 1213 pada tabel anggota atau membership_status_requests.
    """
    if not session.get("logged_in"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    conn = None
    cursor = None
    try:
        conn = mysql_connection()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get("user_id")

        cursor.execute("SELECT * FROM `anggota` WHERE id = %s LIMIT 1", (user_id,))
        member = cursor.fetchone()
        if not member:
            session.clear()
            return jsonify({"ok": False, "message": "Akun login tidak ditemukan. Silakan login ulang."}), 404

        sync_session_from_member_row(member)

        cursor.execute(
            """
            SELECT * FROM `membership_status_requests`
            WHERE member_id = %s
            ORDER BY created_at DESC, updated_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        latest = cursor.fetchone()

        return jsonify({
            "ok": True,
            "member": member_row_to_dict(member),
            "request": membership_request_row_to_dict(latest) if latest else None,
            "currentUser": current_user_context_from_row(member),
        })
    except mysql.connector.Error as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        if getattr(exc, "errno", None) in {1205, 1213}:
            return jsonify({
                "ok": False,
                "message": "Database sedang sibuk memproses data keanggotaan. Silakan muat ulang halaman beberapa detik lagi."
            }), 503
        return jsonify({"ok": False, "message": f"Gagal memuat status keanggotaan: {exc}"}), 500
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"ok": False, "message": f"Gagal memuat status keanggotaan: {exc}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Route dari app.py server: /api/membership/inactive-request
@app.route("/api/membership/inactive-request", methods=["POST"])

def api_membership_submit_request():
    if not session.get("logged_in"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    if normalize_role_value(session.get("role") or "user") != "user":
        return jsonify({"ok": False, "message": "Pengajuan status nonaktif hanya untuk anggota biasa."}), 403

    ensure_auth_schema()
    ensure_notifications_schema()
    user_id = session.get("user_id")
    mode = "temporary" if normalize_text(request.form.get("inactiveType") or request.form.get("type")).lower() == "temporary" else "permanent"
    reason = normalize_text(request.form.get("reason"))
    start_date = parse_optional_date(request.form.get("effectiveDate") or request.form.get("startDate"))
    return_date = parse_optional_date(request.form.get("reactivateDate") or request.form.get("returnDate"))
    note = normalize_text(request.form.get("note"))
    request_id = normalize_text(request.form.get("id") or request.form.get("requestId"))

    if not reason or not start_date or not note:
        return jsonify({"ok": False, "message": "Alasan, tanggal mulai, dan catatan tambahan wajib diisi."}), 400
    if mode == "temporary":
        if not return_date:
            return jsonify({"ok": False, "message": "Tanggal aktif kembali wajib diisi untuk nonaktif berjangka."}), 400
        if return_date <= start_date:
            return jsonify({"ok": False, "message": "Tanggal aktif kembali harus sesudah tanggal mulai nonaktif."}), 400
    else:
        return_date = None

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        ensure_membership_columns(cursor)
        cursor.execute("SELECT id, nama FROM anggota WHERE id = %s LIMIT 1", (user_id,))
        member = cursor.fetchone()
        if not member:
            conn.rollback()
            return jsonify({"ok": False, "message": "Data anggota tidak ditemukan."}), 404

        existing = None
        if request_id:
            cursor.execute("SELECT * FROM membership_status_requests WHERE id = %s AND member_id = %s LIMIT 1", (request_id, user_id))
            existing = cursor.fetchone()
            if existing and membership_status_key(existing.get("status")) != MEMBERSHIP_PENDING:
                conn.rollback()
                return jsonify({"ok": False, "message": "Pengajuan yang sudah diproses admin tidak bisa diubah."}), 400

        if not existing:
            cursor.execute("SELECT * FROM membership_status_requests WHERE member_id = %s AND status = 'pending' ORDER BY created_at DESC LIMIT 1", (user_id,))
            existing = cursor.fetchone()

        file_storage = request.files.get("evidence") or request.files.get("bukti") or request.files.get("file")
        evidence_payload = None
        if file_storage and file_storage.filename:
            evidence_payload = save_uploaded_attachment(file_storage)
        elif existing:
            evidence_payload = membership_evidence_payload(existing.get("evidence_json"))

        if not evidence_payload:
            conn.rollback()
            return jsonify({"ok": False, "message": "Bukti pendukung wajib diupload."}), 400

        now = datetime.now()
        if existing:
            req_id = existing.get("id")
            cursor.execute(
                """
                UPDATE membership_status_requests
                SET inactive_type=%s, reason=%s, start_date=%s, return_date=%s, note=%s,
                    evidence_json=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s AND member_id=%s AND status='pending'
                """,
                (mode, reason, start_date, return_date, note, json.dumps([evidence_payload], ensure_ascii=False), req_id, user_id),
            )
            action_label = "diperbarui"
        else:
            req_id = f"nonaktif-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"
            cursor.execute(
                """
                INSERT INTO membership_status_requests
                (id, member_id, member_name, inactive_type, reason, start_date, return_date, note, evidence_json, status, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s)
                """,
                (req_id, user_id, member.get("nama") or session.get("nama") or "Anggota", mode, reason, start_date, return_date, note, json.dumps([evidence_payload], ensure_ascii=False), now, now),
            )
            action_label = "dikirim"

        create_notification(
            cursor,
            "keanggotaan",
            f"Pengajuan Nonaktif: {member.get('nama') or 'Anggota'}",
            f"{html.escape(member.get('nama') or 'Anggota')} mengajukan status nonaktif. Mohon tinjau di Manajemen Anggota.",
            "/manajemen-anggota.html",
            {"request_id": req_id},
            target_role="admin",
        )
        conn.commit()
        cursor.execute("SELECT * FROM membership_status_requests WHERE id = %s", (req_id,))
        row = cursor.fetchone()
        return jsonify({"ok": True, "message": f"Pengajuan nonaktif berhasil {action_label}.", "request": membership_request_row_to_dict(row)})
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/membership/inactive-request/<request_id>
@app.route("/api/membership/inactive-request/<request_id>", methods=["DELETE"])
def api_membership_cancel_request(request_id):
    if not session.get("logged_in"):
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    ensure_auth_schema()
    user_id = session.get("user_id")
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_membership_columns(cursor)
        cursor.execute("SELECT * FROM membership_status_requests WHERE id=%s AND member_id=%s LIMIT 1", (request_id, user_id))
        row = cursor.fetchone()
        if not row:
            return jsonify({"ok": False, "message": "Pengajuan tidak ditemukan."}), 404
        if membership_status_key(row.get("status")) != MEMBERSHIP_PENDING:
            return jsonify({"ok": False, "message": "Pengajuan yang sudah diproses admin tidak bisa dibatalkan."}), 400
        cursor.execute("UPDATE membership_status_requests SET status='cancelled', updated_at=CURRENT_TIMESTAMP WHERE id=%s", (request_id,))
        conn.commit()
        return jsonify({"ok": True, "message": "Pengajuan nonaktif berhasil dibatalkan."})
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/membership/admin/requests
@app.route("/api/membership/admin/requests", methods=["GET"])
def api_membership_admin_requests():
    if not can_manage_members():
        return jsonify({"ok": False, "message": "Unauthorized"}), 403
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        apply_membership_status_transitions(cursor)
        conn.commit()
        status_filter = membership_status_key(request.args.get("status") or "pending")
        search = normalize_text(request.args.get("search")).lower()
        sort_mode = normalize_text(request.args.get("sort")) or "newest"
        params = []
        where = "WHERE 1=1"
        if status_filter != "all":
            where += " AND r.status = %s"
            params.append(status_filter)
        if search:
            where += " AND (LOWER(r.member_name) LIKE %s OR LOWER(r.reason) LIKE %s OR LOWER(r.note) LIKE %s OR LOWER(r.status) LIKE %s)"
            like = f"%{search}%"
            params.extend([like, like, like, like])
        order = "ASC" if sort_mode == "oldest" else "DESC"
        cursor.execute(f"SELECT r.*, a.email, a.role, a.status_akun FROM membership_status_requests r LEFT JOIN anggota a ON a.id = r.member_id {where} ORDER BY r.created_at {order}, r.updated_at {order}", tuple(params))
        rows = cursor.fetchall() or []
        cursor.execute("SELECT status, COUNT(*) AS count FROM membership_status_requests GROUP BY status")
        counts = {membership_status_key(row.get("status")): int(row.get("count") or 0) for row in cursor.fetchall() or []}
        return jsonify({"ok": True, "items": [membership_request_row_to_dict(r) for r in rows], "counts": counts})
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/membership/admin/requests/<request_id>/respond
@app.route("/api/membership/admin/requests/<request_id>/respond", methods=["POST"])
def api_membership_admin_respond(request_id):
    if not can_manage_members():
        return jsonify({"ok": False, "message": "Unauthorized"}), 403
    payload = request.get_json(silent=True) or {}
    action = normalize_text(payload.get("action")).lower()
    admin_note = normalize_text(payload.get("adminNote") or payload.get("note"))
    if action not in {"approve", "reject"}:
        return jsonify({"ok": False, "message": "Aksi tidak valid."}), 400

    ensure_auth_schema()
    ensure_notifications_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        ensure_membership_columns(cursor)
        cursor.execute("SELECT * FROM membership_status_requests WHERE id=%s LIMIT 1", (request_id,))
        req = cursor.fetchone()
        if not req:
            conn.rollback()
            return jsonify({"ok": False, "message": "Pengajuan tidak ditemukan."}), 404
        if membership_status_key(req.get("status")) != MEMBERSHIP_PENDING:
            conn.rollback()
            return jsonify({"ok": False, "message": "Pengajuan sudah diproses."}), 400

        new_status = MEMBERSHIP_APPROVED if action == "approve" else MEMBERSHIP_REJECTED
        cursor.execute(
            """
            UPDATE membership_status_requests
            SET status=%s, admin_id=%s, admin_name=%s, admin_note=%s, decided_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (new_status, session.get("user_id"), session.get("nama") or session.get("username"), admin_note, request_id),
        )

        member_id = req.get("member_id")
        if action == "approve":
            today = datetime.now().date()
            start_date = req.get("start_date")
            return_date = req.get("return_date")
            inactive_type = normalize_text(req.get("inactive_type")).lower() or "permanent"

            # Jika pengajuan sudah disetujui, status anggota harus sinkron dari endpoint yang sama
            # baik diproses lewat Dashboard Admin maupun lewat Manajemen Anggota.
            # Untuk request berjangka yang tanggal aktif kembalinya sudah lewat/sama hari ini,
            # akun langsung dianggap aktif kembali; selain itu akun menjadi nonaktif.
            already_finished = bool(inactive_type == "temporary" and return_date and return_date <= today)
            if already_finished:
                cursor.execute(
                    """
                    UPDATE anggota
                    SET status_akun='aktif', inactive_from=NULL, inactive_until=NULL, inactive_type=NULL,
                        inactive_reason=NULL, inactive_note=NULL
                    WHERE id=%s
                    """,
                    (member_id,),
                )
                cursor.execute(
                    """
                    UPDATE membership_status_requests
                    SET applied_at = COALESCE(applied_at, CURRENT_TIMESTAMP),
                        manual_reactivated_at = COALESCE(manual_reactivated_at, CURRENT_TIMESTAMP),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (request_id,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE anggota
                    SET status_akun='nonaktif', inactive_from=%s, inactive_until=%s, inactive_type=%s,
                        inactive_reason=%s, inactive_note=%s
                    WHERE id=%s
                    """,
                    (start_date or today, return_date, inactive_type, req.get("reason"), req.get("note"), member_id),
                )
                cursor.execute(
                    """
                    UPDATE membership_status_requests
                    SET applied_at = COALESCE(applied_at, CURRENT_TIMESTAMP), updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (request_id,),
                )
                # Verifikasi ulang dari tabel request agar status anggota tidak tetap Aktif
                # ketika approve dilakukan dari halaman Manajemen Anggota.
                force_apply_effective_membership_status(cursor, member_id)
            create_notification_once(
                cursor,
                "keanggotaan",
                "Pengajuan Nonaktif Disetujui",
                "Pengajuan status nonaktif Anda telah disetujui oleh admin.",
                "/profil-anggota.html",
                {"target_user_id": member_id, "request_id": request_id},
                target_role="user",
                dedupe_key=f"membership-approved-{request_id}",
            )
        else:
            create_notification_once(
                cursor,
                "keanggotaan",
                "Pengajuan Nonaktif Ditolak",
                "Pengajuan status nonaktif Anda ditolak oleh admin." + (f" Catatan: {html.escape(admin_note)}" if admin_note else ""),
                "/profil-anggota.html",
                {"target_user_id": member_id, "request_id": request_id},
                target_role="user",
                dedupe_key=f"membership-rejected-{request_id}",
            )
        conn.commit()
        updated_member = None
        if member_id:
            fresh_conn = mysql_connection()
            fresh_cursor = fresh_conn.cursor(dictionary=True)
            try:
                fresh_cursor.execute(
                    """
                    SELECT id, nama, username, telp, password, role, tgl_lahir, email, alamat,
                           status_akun, inactive_until, inactive_from, inactive_type, inactive_reason, inactive_note,
                           created_at, updated_at
                    FROM anggota WHERE id = %s LIMIT 1
                    """,
                    (member_id,),
                )
                updated_row = fresh_cursor.fetchone()
                updated_member = member_row_to_dict(updated_row) if updated_row else None
            finally:
                fresh_cursor.close()
                fresh_conn.close()
        return jsonify({"ok": True, "message": "Pengajuan berhasil diproses.", "member": updated_member})
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/membership/admin/pending-actions
@app.route("/api/membership/admin/pending-actions", methods=["GET"])
def api_membership_admin_pending_actions():
    if not can_manage_members():
        return jsonify({"ok": False, "items": []}), 403
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_membership_columns(cursor)
        cursor.execute(
            """
            SELECT * FROM membership_status_requests
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 10
            """
        )
        return jsonify({"ok": True, "items": [membership_request_row_to_dict(r) for r in cursor.fetchall() or []]})
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/admin-users
@app.route("/api/admin-users", methods=["GET"])
def api_admin_users_list():
    forbidden = require_super_admin_api()
    if forbidden:
        return forbidden
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        admins = fetch_admin_users_for_super(cursor)
        return jsonify({"ok": True, "admins": admins, "total": len(admins)})
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/admin-users
@app.route("/api/admin-users", methods=["POST"])
def api_admin_users_create():
    forbidden = require_super_admin_api()
    if forbidden:
        return forbidden
    payload = request.get_json(silent=True) or {}
    values, error = validate_admin_user_payload(payload)
    if error:
        return jsonify({"ok": False, "message": error}), 400
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        unique_error = ensure_admin_user_unique(cursor, values["username"], values["email"], values["phone"])
        if unique_error:
            conn.rollback()
            return jsonify({"ok": False, "message": unique_error}), 400
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM anggota")
        next_id = int((cursor.fetchone() or {}).get("next_id") or 1)
        password_hash = hash_member_password("", values["birth_date"])
        cursor.execute(
            """
            INSERT INTO anggota
              (id, nama, username, telp, password, role, tgl_lahir, email, alamat, status_akun, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'admin', %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                next_id,
                values["full_name"],
                values["username"],
                values["phone"],
                password_hash,
                values["birth_date"],
                values["email"],
                values["address"],
                values["status"],
            ),
        )
        upsert_admin_permissions(cursor, next_id, values["permissions"])
        create_new_member_account_notification(
            cursor,
            next_id,
            full_name=values["full_name"],
            username=values["username"],
            email_value=values["email"],
            birth_date=values["birth_date"],
            role_value="admin",
        )
        conn.commit()
        admins = fetch_admin_users_for_super(cursor)
        return jsonify({"ok": True, "message": "Admin baru berhasil ditambahkan.", "admins": admins})
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/admin-users/<int:admin_id>
@app.route("/api/admin-users/<int:admin_id>", methods=["PUT"])
def api_admin_users_update(admin_id: int):
    forbidden = require_super_admin_api()
    if forbidden:
        return forbidden
    payload = request.get_json(silent=True) or {}
    values, error = validate_admin_user_payload(payload, existing_id=admin_id)
    if error:
        return jsonify({"ok": False, "message": error}), 400
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute("SELECT id, role FROM anggota WHERE id = %s LIMIT 1", (admin_id,))
        row = cursor.fetchone()
        if not row or normalize_role_value(row.get("role") or "") != "admin":
            conn.rollback()
            return jsonify({"ok": False, "message": "Data admin tidak ditemukan."}), 404
        unique_error = ensure_admin_user_unique(cursor, values["username"], values["email"], values["phone"], except_id=admin_id)
        if unique_error:
            conn.rollback()
            return jsonify({"ok": False, "message": unique_error}), 400
        cursor.execute(
            """
            UPDATE anggota
            SET nama = %s, username = %s, telp = %s, tgl_lahir = %s, email = %s,
                alamat = %s, status_akun = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND role = 'admin'
            """,
            (
                values["full_name"],
                values["username"],
                values["phone"],
                values["birth_date"],
                values["email"],
                values["address"],
                values["status"],
                admin_id,
            ),
        )
        upsert_admin_permissions(cursor, admin_id, values["permissions"])
        conn.commit()
        admins = fetch_admin_users_for_super(cursor)
        return jsonify({"ok": True, "message": "Data admin berhasil diperbarui.", "admins": admins})
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/admin-users/<int:admin_id>
@app.route("/api/admin-users/<int:admin_id>", methods=["DELETE"])
def api_admin_users_delete(admin_id: int):
    forbidden = require_super_admin_api()
    if forbidden:
        return forbidden
    if str(admin_id) == str(session.get("user_id") or ""):
        return jsonify({"ok": False, "message": "Anda tidak dapat menghapus akun sendiri dari halaman ini."}), 400
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute("SELECT id, role FROM anggota WHERE id = %s LIMIT 1", (admin_id,))
        row = cursor.fetchone()
        if not row or normalize_role_value(row.get("role") or "") != "admin":
            conn.rollback()
            return jsonify({"ok": False, "message": "Data admin tidak ditemukan."}), 404
        cursor.execute("DELETE FROM admin_module_permissions WHERE member_id = %s", (admin_id,))
        cursor.execute("DELETE FROM anggota WHERE id = %s AND role = 'admin'", (admin_id,))
        conn.commit()
        admins = fetch_admin_users_for_super(cursor)
        return jsonify({"ok": True, "message": "Data admin berhasil dihapus.", "admins": admins})
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/anggota
@app.route("/api/anggota", methods=["GET"])
def api_anggota_list():
    if not can_manage_members():
        return jsonify({"ok": False, "message": "Unauthorized"}), 403
    response = jsonify({"ok": True, "members": read_members_for_admin()})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


# Route dari app.py server: /api/anggota/sync
@app.route("/api/anggota/sync", methods=["POST"])
def api_anggota_sync():
    if not can_manage_members():
        return jsonify({"ok": False, "message": "Unauthorized"}), 403

    payload = request.get_json(silent=True) or {}
    members = payload.get("members")
    if not isinstance(members, list):
        return jsonify({"ok": False, "message": "Payload members harus array."}), 400

    try:
        sync_members_from_payload(members)
    except PermissionError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 403
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    return jsonify({"ok": True, "members": read_members_for_admin()})

