"""Task Exchange Controller.

File ini berisi route/controller yang dipisahkan dari app.py server lama.
Logika helper tetap dipanggil dari crembo_app.services.core agar perilaku produksi tetap sama.
"""

from crembo_app.services import core as _core

globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})


# Route dari app.py server: /api/task-exchanges/me
@app.route("/api/task-exchanges/me", methods=["GET"])
def api_task_exchanges_me():
    ensure_task_exchange_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = exchange_current_member(cursor)
        if error:
            return error
        return jsonify({"success": True, "member": {"id": member["id"], "name": member["name"], "role": member["roleNormalized"]}})
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/task-exchanges/options
@app.route("/api/task-exchanges/options", methods=["GET"])
def api_task_exchanges_options():
    ensure_task_exchange_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        exchange_expire_pending_requests(cursor)
        conn.commit()
        now = datetime.now()
        month = min(12, max(1, parse_required_int(request.args.get("month"), now.month)))
        year = parse_required_int(request.args.get("year"), now.year)
        kind = normalize_text(request.args.get("type")) or "biasa"
        if kind not in {"biasa", "besar"}:
            kind = "biasa"
        my_tasks = exchange_fetch_user_tasks(cursor, member_id=member["id"], kind=kind, month=month, year=year)
        target_tasks = exchange_fetch_target_tasks(cursor, current_member_id=member["id"], kind=kind, month=month, year=year)
        active_members = exchange_fetch_active_members(cursor, exclude_member_id=member["id"])
        for task in my_tasks:
            task["hasPendingRequest"] = exchange_has_pending_for_assignment(cursor, member["id"], task.get("type"), task.get("assignmentId"))
            task["assignedMemberIds"] = exchange_schedule_member_ids(
                cursor,
                kind=task.get("type"),
                date_text=task.get("date"),
                time_text=task.get("time"),
                misa_id=task.get("misaId"),
            )
        return jsonify({"success": True, "myTasks": my_tasks, "targetTasks": target_tasks, "members": active_members, "filters": {"month": month, "year": year, "type": kind}})
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/task-exchanges
@app.route("/api/task-exchanges", methods=["POST"])
def api_task_exchanges_create():
    ensure_task_exchange_schema()
    data = request.get_json(silent=True) or {}
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        requester_id = member["id"]
        mode = normalize_text(data.get("mode") or data.get("requestMode") or "swap").lower()
        if mode in {"tukeran", "swap"}:
            mode = "swap"
        elif mode in {"menggantikan", "substitute"}:
            mode = "substitute"
        else:
            return jsonify({"success": False, "error": "Tipe request tidak valid."}), 400
        kind = normalize_text(data.get("type") or data.get("kind") or "biasa").lower()
        if kind not in {"biasa", "besar"}:
            return jsonify({"success": False, "error": "Jenis misa tidak valid."}), 400
        my_assignment_id = parse_optional_int(data.get("myAssignmentId"))
        if my_assignment_id is None:
            return jsonify({"success": False, "error": "Pilih jadwal Anda terlebih dahulu."}), 400
        reason = normalize_text(data.get("reason"))
        if not reason:
            return jsonify({"success": False, "error": "Alasan wajib diisi."}), 400
        my_task = exchange_fetch_assignment(cursor, kind=kind, assignment_id=my_assignment_id, member_id=requester_id, for_update=True)
        if not my_task:
            return jsonify({"success": False, "error": "Jadwal Anda tidak ditemukan atau bukan milik Anda."}), 404
        if not exchange_date_is_eligible(my_task.get("date")):
            return jsonify({"success": False, "error": "Penukaran hanya bisa diajukan minimal H-1. Jadwal hari ini atau yang sudah lewat tidak bisa diajukan."}), 400
        if exchange_has_pending_for_assignment(cursor, requester_id, kind, my_assignment_id):
            return jsonify({"success": False, "error": "Jadwal ini sudah memiliki request aktif. Batalkan request sebelumnya terlebih dahulu."}), 409

        target_task = None
        target_user_id = None
        if mode == "swap":
            target_assignment_id = parse_optional_int(data.get("targetAssignmentId"))
            if target_assignment_id is None:
                return jsonify({"success": False, "error": "Pilih jadwal teman yang ingin diajak tukeran."}), 400
            target_task = exchange_fetch_assignment(cursor, kind=kind, assignment_id=target_assignment_id, for_update=True)
            if not target_task:
                return jsonify({"success": False, "error": "Jadwal teman tidak ditemukan."}), 404
            if str(target_task.get("memberId")) == str(requester_id):
                return jsonify({"success": False, "error": "Anda tidak bisa memilih jadwal sendiri sebagai jadwal tukar."}), 400
            if not exchange_date_is_eligible(target_task.get("date")):
                return jsonify({"success": False, "error": "Jadwal teman harus jadwal yang akan datang minimal H-1."}), 400
            if exchange_member_already_in_schedule(cursor, kind=kind, member_id=requester_id, date_text=target_task.get("date"), time_text=target_task.get("time"), misa_id=target_task.get("misaId")):
                return jsonify({"success": False, "error": "Jadwal teman tidak bisa dipilih karena Anda sudah bertugas pada sesi tersebut."}), 409
            if exchange_member_already_in_schedule(cursor, kind=kind, member_id=target_task.get("memberId"), date_text=my_task.get("date"), time_text=my_task.get("time"), misa_id=my_task.get("misaId")):
                return jsonify({"success": False, "error": "Teman tersebut sudah bertugas pada sesi jadwal Anda, sehingga tidak bisa ditukar."}), 409
            target_user_id = str(target_task.get("memberId"))
        else:
            target_user_id = normalize_text(data.get("targetUserId"))
            if not target_user_id:
                return jsonify({"success": False, "error": "Pilih teman pengganti."}), 400
            if str(target_user_id) == str(requester_id):
                return jsonify({"success": False, "error": "Teman pengganti tidak boleh diri sendiri."}), 400
            cursor.execute("SELECT id, nama, role, status_akun FROM anggota WHERE id = %s LIMIT 1", (target_user_id,))
            target_member = cursor.fetchone()
            if not target_member or normalize_status(target_member.get("status_akun") or "aktif") != "aktif":
                return jsonify({"success": False, "error": "Teman pengganti tidak ditemukan atau tidak aktif."}), 404
            if exchange_member_already_in_schedule(cursor, kind=kind, member_id=target_user_id, date_text=my_task.get("date"), time_text=my_task.get("time"), misa_id=my_task.get("misaId")):
                return jsonify({"success": False, "error": "Teman pengganti sudah bertugas pada sesi tersebut, sehingga tidak bisa memegang 2 role."}), 409
            target_task = {"memberId": target_user_id, "memberName": normalize_text(target_member.get("nama")) or "Teman"}

        cursor.execute(
            """
            INSERT INTO task_exchange_requests
            (requester_id, target_user_id, kind, request_mode,
             my_assignment_id, my_misa_id, my_role_id, my_type_label, my_misa_name, my_role_name, my_schedule_date, my_schedule_time,
             target_assignment_id, target_misa_id, target_role_id, target_type_label, target_misa_name, target_role_name, target_schedule_date, target_schedule_time,
             reason, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """,
            (
                requester_id, target_user_id, kind, mode,
                my_task.get("assignmentId"), my_task.get("misaId"), my_task.get("roleId"), my_task.get("typeLabel"), my_task.get("misaName"), my_task.get("role"), my_task.get("date"), format_time_hhmm(my_task.get("time")),
                target_task.get("assignmentId") if mode == "swap" else None,
                target_task.get("misaId") if mode == "swap" else None,
                target_task.get("roleId") if mode == "swap" else None,
                target_task.get("typeLabel") if mode == "swap" else None,
                target_task.get("misaName") if mode == "swap" else None,
                target_task.get("role") if mode == "swap" else None,
                target_task.get("date") if mode == "swap" else None,
                format_time_hhmm(target_task.get("time")) if mode == "swap" else None,
                reason,
            ),
        )
        req_id = cursor.lastrowid
        row = exchange_fetch_request_row(cursor, req_id)
        exchange_notify_new_request(cursor, row)
        conn.commit()
        return jsonify({"success": True, "message": "Request berhasil dikirim.", "request": exchange_request_to_dict(row, direction="outgoing")})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/task-exchanges/incoming
@app.route("/api/task-exchanges/incoming", methods=["GET"])
def api_task_exchanges_incoming():
    return exchange_list_requests(direction="incoming")


# Route dari app.py server: /api/task-exchanges/outgoing
@app.route("/api/task-exchanges/outgoing", methods=["GET"])
def api_task_exchanges_outgoing():
    return exchange_list_requests(direction="outgoing")


# Route dari app.py server: /api/task-exchanges/pending-actions
@app.route("/api/task-exchanges/pending-actions", methods=["GET"])
def api_task_exchanges_pending_actions():
    ensure_task_exchange_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = exchange_current_member(cursor)
        if error:
            return error
        exchange_expire_pending_requests(cursor)
        conn.commit()
        limit = max(1, min(20, parse_required_int(request.args.get("limit"), 5)))
        cursor.execute(
            """
            SELECT er.*, req.nama AS requester_name, tgt.nama AS target_name,
                   req.role AS requester_role, tgt.role AS target_role
            FROM task_exchange_requests er
            LEFT JOIN anggota req ON req.id = er.requester_id
            LEFT JOIN anggota tgt ON tgt.id = er.target_user_id
            WHERE er.target_user_id = %s AND er.status = 'pending' AND er.my_schedule_date > CURDATE()
            ORDER BY er.created_at DESC
            LIMIT %s
            """,
            (member["id"], limit),
        )
        items = [exchange_request_to_dict(row, direction="incoming") for row in (cursor.fetchall() or [])]
        return jsonify({"success": True, "items": items})
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/task-exchanges/<int:request_id>/respond
@app.route("/api/task-exchanges/<int:request_id>/respond", methods=["POST"])
def api_task_exchanges_respond(request_id):
    ensure_task_exchange_schema()
    data = request.get_json(silent=True) or {}
    action = normalize_text(data.get("action") or "").lower()
    if action not in {"accept", "reject"}:
        return jsonify({"success": False, "error": "Aksi tidak valid."}), 400
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = exchange_current_member(cursor)
        if error:
            return error
        exchange_expire_pending_requests(cursor)
        row = exchange_fetch_request_row(cursor, request_id, for_update=True)
        if not row:
            return jsonify({"success": False, "error": "Request tidak ditemukan."}), 404
        if str(row.get("target_user_id")) != str(member["id"]):
            return jsonify({"success": False, "error": "Request ini bukan untuk Anda."}), 403
        if normalize_text(row.get("status")) != "pending":
            return jsonify({"success": False, "error": f"Request sudah berstatus {exchange_status_label(row.get('status'))}."}), 400
        if not exchange_date_is_eligible(normalize_text(row.get("my_schedule_date"))):
            cursor.execute("UPDATE task_exchange_requests SET status = 'auto_cancelled', auto_cancelled_at = NOW(), updated_at = NOW() WHERE id = %s", (request_id,))
            row["status"] = "auto_cancelled"
            exchange_notify_requester_result(cursor, row, "auto_cancelled")
            conn.commit()
            return jsonify({"success": False, "error": "Request otomatis batal karena sudah masuk hari-H atau jadwal sudah lewat."}), 400
        if action == "reject":
            cursor.execute("UPDATE task_exchange_requests SET status = 'rejected', responded_at = NOW(), updated_at = NOW() WHERE id = %s", (request_id,))
            row["status"] = "rejected"
            exchange_notify_requester_result(cursor, row, "rejected")
            conn.commit()
            return jsonify({"success": True, "message": "Request berhasil ditolak."})

        kind = normalize_text(row.get("kind") or "biasa")
        mode = normalize_text(row.get("request_mode") or "swap")
        my_task = exchange_fetch_assignment(cursor, kind=kind, assignment_id=row.get("my_assignment_id"), member_id=row.get("requester_id"), for_update=True)
        if not my_task:
            return jsonify({"success": False, "error": "Jadwal pengaju sudah tidak valid."}), 409
        if not exchange_date_is_eligible(my_task.get("date")):
            return jsonify({"success": False, "error": "Jadwal pengaju sudah masuk hari-H atau lewat."}), 400
        if mode == "swap":
            target_task = exchange_fetch_assignment(cursor, kind=kind, assignment_id=row.get("target_assignment_id"), member_id=member["id"], for_update=True)
            if not target_task:
                return jsonify({"success": False, "error": "Jadwal Anda untuk ditukar sudah tidak valid."}), 409
            if not exchange_date_is_eligible(target_task.get("date")):
                return jsonify({"success": False, "error": "Jadwal Anda sudah masuk hari-H atau lewat."}), 400
            if exchange_member_already_in_schedule(cursor, kind=kind, member_id=row.get("requester_id"), date_text=target_task.get("date"), time_text=target_task.get("time"), misa_id=target_task.get("misaId")):
                return jsonify({"success": False, "error": "Pengaju sudah bertugas pada sesi jadwal Anda. Request tidak bisa diterima karena akan membuat double role."}), 409
            if exchange_member_already_in_schedule(cursor, kind=kind, member_id=member["id"], date_text=my_task.get("date"), time_text=my_task.get("time"), misa_id=my_task.get("misaId")):
                return jsonify({"success": False, "error": "Anda sudah bertugas pada sesi jadwal pengaju. Request tidak bisa diterima karena akan membuat double role."}), 409
            if kind == "besar":
                cursor.execute("UPDATE misa_besar_assignments SET member_id = %s, request_source = 'exchange', created_at = NOW() WHERE id = %s", (member["id"], my_task.get("assignmentId")))
                cursor.execute("UPDATE misa_besar_assignments SET member_id = %s, request_source = 'exchange', created_at = NOW() WHERE id = %s", (row.get("requester_id"), target_task.get("assignmentId")))
            else:
                cursor.execute("UPDATE streaming_assignments SET member_id = %s, request_source = 'exchange', created_at = NOW() WHERE id = %s", (member["id"], my_task.get("assignmentId")))
                cursor.execute("UPDATE streaming_assignments SET member_id = %s, request_source = 'exchange', created_at = NOW() WHERE id = %s", (row.get("requester_id"), target_task.get("assignmentId")))
        else:
            if exchange_member_already_in_schedule(cursor, kind=kind, member_id=member["id"], date_text=my_task.get("date"), time_text=my_task.get("time"), misa_id=my_task.get("misaId"), exclude_assignment_id=my_task.get("assignmentId")):
                return jsonify({"success": False, "error": "Anda sudah bertugas pada jadwal/misa tersebut."}), 409
            if kind == "besar":
                cursor.execute("UPDATE misa_besar_assignments SET member_id = %s, request_source = 'exchange', created_at = NOW() WHERE id = %s", (member["id"], my_task.get("assignmentId")))
            else:
                cursor.execute("UPDATE streaming_assignments SET member_id = %s, request_source = 'exchange', created_at = NOW() WHERE id = %s", (member["id"], my_task.get("assignmentId")))
        cursor.execute("UPDATE task_exchange_requests SET status = 'accepted', responded_at = NOW(), updated_at = NOW() WHERE id = %s", (request_id,))
        row["status"] = "accepted"
        exchange_notify_requester_result(cursor, row, "accepted")
        conn.commit()
        return jsonify({"success": True, "message": "Request berhasil diterima dan jadwal sudah diperbarui."})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/task-exchanges/<int:request_id>/cancel
@app.route("/api/task-exchanges/<int:request_id>/cancel", methods=["POST"])
def api_task_exchanges_cancel(request_id):
    ensure_task_exchange_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        row = exchange_fetch_request_row(cursor, request_id, for_update=True)
        if not row:
            return jsonify({"success": False, "error": "Request tidak ditemukan."}), 404
        if str(row.get("requester_id")) != str(member["id"]):
            return jsonify({"success": False, "error": "Anda hanya bisa membatalkan request keluar milik Anda."}), 403
        if normalize_text(row.get("status")) != "pending":
            return jsonify({"success": False, "error": "Request ini sudah tidak bisa dibatalkan."}), 400
        cursor.execute("UPDATE task_exchange_requests SET status = 'cancelled', cancelled_at = NOW(), updated_at = NOW() WHERE id = %s", (request_id,))
        row["status"] = "cancelled"
        target_role = row.get("target_role")
        exchange_insert_notification(
            cursor,
            target_user_id=row.get("target_user_id"),
            target_role=target_role,
            title="Permintaan Tukar Jadwal Dibatalkan",
            body=f"Permintaan tukar/ganti tugas dari <b>{html.escape(member['name'])}</b> telah dibatalkan oleh pengaju.",
            request_id=request_id,
            status="cancelled",
            url=None if normalize_role_value(target_role or "user") in {"admin", "super_admin"} else "/penukaran-jadwal-tugas-anggota.html",
        )
        exchange_notify_requester_result(cursor, row, "cancelled")
        conn.commit()
        return jsonify({"success": True, "message": "Request berhasil dibatalkan."})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()

