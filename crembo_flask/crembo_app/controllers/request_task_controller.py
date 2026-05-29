"""Request Task Controller.

File ini berisi route/controller yang dipisahkan dari app.py server lama.
Logika helper tetap dipanggil dari crembo_app.services.core agar perilaku produksi tetap sama.
"""

from crembo_app.services import core as _core

globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})


# Route dari app.py server: /api/request-tugas/me
@app.route("/api/request-tugas/me", methods=["GET"])
def api_request_tugas_me():
    ensure_auth_schema()
    viewer = current_user_context()
    return jsonify({"success": True, "currentUser": viewer})


# Route dari app.py server: /api/request-tugas/schedules
@app.route("/api/request-tugas/schedules", methods=["GET"])
def api_request_tugas_schedules():
    ensure_task_request_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error

        month = parse_required_int(request.args.get("month"), datetime.now().month)
        year = parse_required_int(request.args.get("year"), datetime.now().year)
        kind = normalize_text(request.args.get("type")) or "biasa"
        status_filter = (normalize_text(request.args.get("slot")) or "all").lower()
        search_text = normalize_text(request.args.get("search")).lower()

        if kind == "besar":
            items = request_task_big_items(cursor, month, year, member["id"])
        elif kind == "all":
            items = request_task_regular_items(cursor, month, year, member["id"]) + request_task_big_items(cursor, month, year, member["id"])
        else:
            kind = "biasa"
            items = request_task_regular_items(cursor, month, year, member["id"])

        if status_filter in {"open", "terbuka"}:
            items = [item for item in items if item.get("canRequest")]
        elif status_filter in {"closed", "tertutup"}:
            items = [item for item in items if not item.get("canRequest")]

        if search_text:
            def haystack(item):
                role_texts = []
                for role in item.get("roles") or []:
                    role_texts.append(normalize_text(role.get("role")))
                    for member_row in role.get("members") or []:
                        role_texts.append(normalize_text(member_row.get("memberName")))
                    if role.get("memberName"):
                        role_texts.append(normalize_text(role.get("memberName")))
                return " ".join([
                    normalize_text(item.get("typeLabel")),
                    normalize_text(item.get("misaName")),
                    normalize_text(item.get("dateLabel")),
                    normalize_text(item.get("dayName")),
                    normalize_text(item.get("time")),
                    normalize_text(item.get("statusReason")),
                    " ".join(role_texts),
                ]).lower()
            items = [item for item in items if search_text in haystack(item)]

        items.sort(key=lambda item: (item.get("date") or "", item.get("time") or "", item.get("misaName") or ""))
        return jsonify({
            "success": True,
            "currentUser": {"id": member["id"], "name": member["name"]},
            "items": items,
        })
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/request-tugas/claim
@app.route("/api/request-tugas/claim", methods=["POST"])
def api_request_tugas_claim():
    ensure_task_request_schema()
    ensure_notifications_schema()
    data = request.get_json(silent=True) or {}
    kind = normalize_text(data.get("type"))
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        member_id = member["id"]

        if kind == "besar":
            misa_id = parse_required_int(data.get("misaId"), 0)
            role_id = parse_required_int(data.get("roleId"), 0)
            if not misa_id or not role_id:
                return jsonify({"success": False, "error": "Jadwal Misa Besar dan role wajib dipilih."}), 400

            cursor.execute(
                """
                SELECT mb.id, mb.misa_name, DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS misa_date,
                       DATE_FORMAT(mb.misa_time, '%H:%i') AS misa_time, mb.allow_member_request, mb.status,
                       n.id AS role_id, n.role_name, n.required_count
                FROM misa_besar mb
                JOIN misa_besar_names n ON n.misa_id = mb.id
                WHERE mb.id = %s AND n.id = %s
                LIMIT 1
                """,
                (misa_id, role_id),
            )
            event = cursor.fetchone()
            if not event:
                return jsonify({"success": False, "error": "Jadwal atau role Misa Besar tidak ditemukan."}), 404
            if normalize_misa_besar_status(event.get("status")) != "published":
                return jsonify({"success": False, "error": "Misa Besar belum dipublish."}), 400
            if not bool(event.get("allow_member_request")):
                return jsonify({"success": False, "error": "Request anggota untuk Misa Besar ini sedang ditutup."}), 400
            if request_task_is_past(event.get("misa_date"), event.get("misa_time")):
                return jsonify({"success": False, "error": "Jadwal Misa Besar sudah lewat."}), 400

            cursor.execute(
                """
                SELECT n.role_name
                FROM misa_besar_assignments a
                JOIN misa_besar_names n ON n.id = a.role_id
                WHERE n.misa_id = %s AND a.member_id = %s
                LIMIT 1
                """,
                (misa_id, member_id),
            )
            existing = cursor.fetchone()
            if existing:
                return jsonify({"success": False, "error": f"Anda sudah bertugas sebagai {existing.get('role_name')} di Misa Besar ini."}), 409

            cursor.execute("SELECT COUNT(*) AS filled FROM misa_besar_assignments WHERE role_id = %s", (role_id,))
            filled = parse_required_int((cursor.fetchone() or {}).get("filled"), 0)
            required_count = max(1, parse_required_int(event.get("required_count"), 1))
            if filled >= required_count:
                return jsonify({"success": False, "error": "Slot role ini sudah penuh."}), 409

            cursor.execute(
                """
                INSERT INTO misa_besar_assignments (role_id, member_id, request_source, created_at)
                VALUES (%s, %s, 'member_request', CURRENT_TIMESTAMP)
                """,
                (role_id, member_id),
            )
            message = f"Anda berhasil terdaftar sebagai {event.get('role_name')} untuk {event.get('misa_name')}."
            create_task_success_notification(
                cursor,
                member_id=member_id,
                member_role=member.get("role") or "user",
                misa_type="misa_besar",
                misa_name=event.get("misa_name") or "Misa Besar",
                role_name=event.get("role_name") or "Role",
                date_text=event.get("misa_date"),
                time_text=event.get("misa_time"),
                source="member_request",
                misa_besar_id=misa_id,
            )

        else:
            kind = "biasa"
            date_text = parse_optional_date(data.get("date"))
            time_text = format_time_hhmm(data.get("time"))
            role_name = normalize_text(data.get("role"))
            if not date_text or not time_text or not role_name:
                return jsonify({"success": False, "error": "Jadwal dan role wajib dipilih."}), 400

            cfg = request_task_get_regular_cfg(cursor, date_text, time_text)
            if not cfg:
                return jsonify({"success": False, "error": "Jadwal Misa Biasa tidak ditemukan."}), 404
            blocked_reason = request_task_regular_slot_blocked(cursor, date_text, time_text)
            if blocked_reason:
                return jsonify({"success": False, "error": blocked_reason}), 400
            if request_task_is_past(date_text, time_text):
                return jsonify({"success": False, "error": "Jadwal Misa Biasa sudah lewat."}), 400
            cursor.execute("SELECT 1 FROM streaming_roles WHERE role_name = %s LIMIT 1", (role_name,))
            if not cursor.fetchone():
                return jsonify({"success": False, "error": "Role tidak ditemukan di konfigurasi jadwal streaming."}), 404

            cursor.execute(
                """
                SELECT role_name FROM streaming_assignments
                WHERE schedule_date = %s AND DATE_FORMAT(schedule_time, '%H:%i') = %s AND member_id = %s
                LIMIT 1
                """,
                (date_text, time_text, member_id),
            )
            existing = cursor.fetchone()
            if existing:
                return jsonify({"success": False, "error": f"Anda sudah bertugas sebagai {existing.get('role_name')} di jadwal ini."}), 409

            cursor.execute(
                """
                SELECT member_id FROM streaming_assignments
                WHERE schedule_date = %s AND DATE_FORMAT(schedule_time, '%H:%i') = %s AND role_name = %s
                LIMIT 1
                """,
                (date_text, time_text, role_name),
            )
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Slot role ini sudah terisi."}), 409

            cursor.execute(
                """
                INSERT INTO streaming_assignments (schedule_date, schedule_time, role_name, member_id, request_source, created_at)
                VALUES (%s, %s, %s, %s, 'member_request', CURRENT_TIMESTAMP)
                """,
                (date_text, time_text, role_name, member_id),
            )
            message = f"Anda berhasil terdaftar sebagai {role_name} untuk {cfg.get('mass_name') or 'Misa Biasa'}."
            create_task_success_notification(
                cursor,
                member_id=member_id,
                member_role=member.get("role") or "user",
                misa_type="misa_biasa",
                misa_name=cfg.get("mass_name") or "Misa Biasa",
                role_name=role_name,
                date_text=date_text,
                time_text=time_text,
                source="member_request",
            )

        conn.commit()
        return jsonify({"success": True, "message": message})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/request-tugas/history
@app.route("/api/request-tugas/history", methods=["GET"])
def api_request_tugas_history():
    ensure_task_request_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        member_id = member["id"]
        page = max(1, parse_required_int(request.args.get("page"), 1))
        page_size = max(1, min(25, parse_required_int(request.args.get("pageSize"), 5)))
        kind_filter = (normalize_text(request.args.get("type")) or "all").lower()
        role_filter = normalize_text(request.args.get("role")).lower()
        search_text = normalize_text(request.args.get("search")).lower()
        month_filter = normalize_text(request.args.get("month")) or str(datetime.now().month)
        year_filter = normalize_text(request.args.get("year")) or str(datetime.now().year)
        period_filter = (normalize_text(request.args.get("period")) or "all").lower()
        sort_mode = (normalize_text(request.args.get("sort")) or "date_desc").lower()

        rows: list[dict[str, object]] = []
        cursor.execute(
            """
            SELECT DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                   sa.role_name AS role,
                   COALESCE(sa.request_source, 'admin') AS request_source,
                   sa.created_at,
                   cfg.mass_name
            FROM streaming_assignments sa
            LEFT JOIN streaming_weekly_config cfg
              ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                ELSE 'Minggu' END
              AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
            WHERE sa.member_id = %s
            """,
            (member_id,),
        )
        for row in cursor.fetchall() or []:
            date_text = normalize_text(row.get("date"))
            time_text = format_time_hhmm(row.get("time"))
            rows.append({
                "type": "biasa",
                "typeLabel": "Misa Biasa",
                "misaName": normalize_text(row.get("mass_name")) or "Misa Biasa",
                "date": date_text,
                "dateLabel": request_task_format_date(date_text),
                "dayName": request_task_day_name(date_text),
                "time": time_text,
                "role": normalize_text(row.get("role")),
                "status": "Terdaftar",
                "source": normalize_text(row.get("request_source")) or "admin",
                "createdAt": row.get("created_at").isoformat() if row.get("created_at") else None,
            })

        cursor.execute(
            """
            SELECT mb.misa_name, DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                   n.role_name AS role,
                   COALESCE(a.request_source, 'admin') AS request_source,
                   a.created_at
            FROM misa_besar_assignments a
            JOIN misa_besar_names n ON n.id = a.role_id
            JOIN misa_besar mb ON mb.id = n.misa_id
            WHERE a.member_id = %s
            """,
            (member_id,),
        )
        for row in cursor.fetchall() or []:
            date_text = normalize_text(row.get("date"))
            time_text = format_time_hhmm(row.get("time"))
            rows.append({
                "type": "besar",
                "typeLabel": "Misa Besar",
                "misaName": normalize_text(row.get("misa_name")) or "Misa Besar",
                "date": date_text,
                "dateLabel": request_task_format_date(date_text),
                "dayName": request_task_day_name(date_text),
                "time": time_text,
                "role": normalize_text(row.get("role")),
                "status": "Terdaftar",
                "source": normalize_text(row.get("request_source")) or "admin",
                "createdAt": row.get("created_at").isoformat() if row.get("created_at") else None,
            })

        if kind_filter in {"biasa", "besar"}:
            rows = [item for item in rows if item.get("type") == kind_filter]

        if month_filter.lower() != "all":
            month_int = min(12, max(1, parse_required_int(month_filter, datetime.now().month)))
            rows = [item for item in rows if normalize_text(item.get("date"))[5:7] == f"{month_int:02d}"]

        if year_filter.lower() != "all":
            year_int = parse_required_int(year_filter, datetime.now().year)
            rows = [item for item in rows if normalize_text(item.get("date"))[:4] == str(year_int)]

        today_text = datetime.now().strftime("%Y-%m-%d")
        if period_filter in {"upcoming", "akan_datang", "future"}:
            rows = [item for item in rows if normalize_text(item.get("date")) >= today_text]
        elif period_filter in {"past", "lewat", "passed"}:
            rows = [item for item in rows if normalize_text(item.get("date")) < today_text]

        if role_filter:
            rows = [item for item in rows if role_filter in normalize_text(item.get("role")).lower()]
        if search_text:
            rows = [item for item in rows if search_text in " ".join([
                normalize_text(item.get("typeLabel")), normalize_text(item.get("misaName")),
                normalize_text(item.get("dateLabel")), normalize_text(item.get("dayName")),
                normalize_text(item.get("time")), normalize_text(item.get("role")),
                normalize_text(item.get("source")),
                normalize_text(item.get("sourceLabel")), normalize_text(item.get("description")),
            ]).lower()]

        def request_history_schedule_key(item):
            return (normalize_text(item.get("date")), normalize_text(item.get("time")), normalize_text(item.get("misaName")), normalize_text(item.get("role")))

        if sort_mode == "date_asc":
            rows.sort(key=request_history_schedule_key)
        elif sort_mode == "created_desc":
            rows.sort(key=lambda item: (normalize_text(item.get("createdAt")), normalize_text(item.get("date")), normalize_text(item.get("time"))), reverse=True)
        elif sort_mode == "created_asc":
            rows.sort(key=lambda item: (normalize_text(item.get("createdAt")), normalize_text(item.get("date")), normalize_text(item.get("time"))))
        else:
            rows.sort(key=request_history_schedule_key, reverse=True)
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = rows[start:end]
        for idx, item in enumerate(page_items, start=start + 1):
            item["no"] = idx
            item["sourceLabel"] = "Request Mandiri" if item.get("source") == "member_request" else "Ditugaskan Admin"
            item["description"] = "Request otomatis masuk ke daftar petugas." if item.get("source") == "member_request" else "Nama Anda terdaftar pada jadwal tugas."

        return jsonify({
            "success": True,
            "items": page_items,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": max(1, (total + page_size - 1) // page_size),
            },
            "filters": {
                "type": kind_filter,
                "month": month_filter,
                "year": year_filter,
                "period": period_filter,
                "sort": sort_mode,
            },
        })
    finally:
        cursor.close()
        conn.close()

