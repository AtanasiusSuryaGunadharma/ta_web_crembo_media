from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Request Task Controller

# Source legacy app.py lines 10920-10924 | routes: /api/request-tugas/me
@app.route("/api/request-tugas/me", methods=["GET"])
def api_request_tugas_me():
    ensure_auth_schema()
    viewer = current_user_context()
    return jsonify({"success": True, "currentUser": viewer})


# Source legacy app.py lines 10927-10984 | routes: /api/request-tugas/schedules
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


# Source legacy app.py lines 10987-11140 | routes: /api/request-tugas/claim
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


# Source legacy app.py lines 11149-11393 | routes: /api/riwayat-tugas-saya
@app.route("/api/riwayat-tugas-saya", methods=["GET"])
def api_riwayat_tugas_saya():
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
        month_filter = normalize_text(request.args.get("month")) or "all"
        year_filter = normalize_text(request.args.get("year")) or "all"
        search_text = normalize_text(request.args.get("search")).lower()
        sort_mode = (normalize_text(request.args.get("sort")) or "date_desc").lower().replace("-", "_")
        stats_range = (normalize_text(request.args.get("statsRange")) or "month").lower()

        def source_label(source_value: object) -> str:
            source = normalize_text(source_value).lower()
            if source in {"member_request", "request", "mandiri", "self"}:
                return "Request Mandiri"
            if source in {"exchange", "swap", "tukar", "replacement", "replace", "ganti", "pengganti"}:
                return "Penukaran / Pengganti"
            return "Ditugaskan Admin"

        def status_for(date_text: str, time_text: str, cancelled: bool = False) -> str:
            if cancelled:
                return "Dibatalkan"
            try:
                schedule_dt = datetime.strptime(f"{date_text} {format_time_hhmm(time_text)}", "%Y-%m-%d %H:%M")
                return "Selesai" if schedule_dt < datetime.now() else "Terdaftar"
            except Exception:
                return "Terdaftar"

        def build_item(kind: str, type_label: str, misa_name: str, date_text: str, time_text: str, role_name: str, request_source: object, created_at: object = None, *, cancelled: bool = False, note: str = "") -> dict[str, object]:
            time_clean = format_time_hhmm(time_text)
            source = normalize_text(request_source) or "admin"
            status = status_for(date_text, time_clean, cancelled)
            day_name = request_task_day_name(date_text)
            created_iso = created_at.isoformat() if hasattr(created_at, "isoformat") else (normalize_text(created_at) or None)
            return {
                "type": kind,
                "typeLabel": type_label,
                "misaName": normalize_text(misa_name) or type_label,
                "date": normalize_text(date_text),
                "dateLabel": request_task_format_date(date_text),
                "dayName": day_name,
                "time": time_clean,
                "role": normalize_text(role_name) or "-",
                "status": status,
                "source": source,
                "sourceLabel": source_label(source),
                "isExchange": source_label(source) == "Penukaran / Pengganti",
                "createdAt": created_iso,
                "note": normalize_text(note) or "Nama Anda tercatat pada jadwal tugas streaming.",
                "scheduleLabel": f"{day_name}, {request_task_format_date(date_text)} jam {time_clean} WIB",
            }

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
            rows.append(build_item(
                "biasa",
                "Misa Biasa",
                row.get("mass_name") or "Misa Biasa",
                normalize_text(row.get("date")),
                format_time_hhmm(row.get("time")),
                row.get("role"),
                row.get("request_source"),
                row.get("created_at"),
            ))

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
            WHERE a.member_id = %s AND mb.status = 'published'
            """,
            (member_id,),
        )
        for row in cursor.fetchall() or []:
            rows.append(build_item(
                "besar",
                "Misa Besar",
                row.get("misa_name") or "Misa Besar",
                normalize_text(row.get("date")),
                format_time_hhmm(row.get("time")),
                row.get("role"),
                row.get("request_source"),
                row.get("created_at"),
            ))

        # Riwayat pembatalan ikut ditampilkan sebagai status Dibatalkan agar histori tugas tetap lengkap.
        try:
            ensure_task_cancellation_schema(cursor)
            cursor.execute(
                """
                SELECT kind, COALESCE(type_label, IF(kind='besar','Misa Besar','Misa Biasa')) AS type_label,
                       DATE_FORMAT(schedule_date, '%Y-%m-%d') AS date,
                       DATE_FORMAT(schedule_time, '%H:%i') AS time,
                       misa_name, role_name, request_source, cancelled_at, note
                FROM task_cancellations
                WHERE member_id = %s
                """,
                (member_id,),
            )
            for row in cursor.fetchall() or []:
                kind = "besar" if normalize_text(row.get("kind")).lower() == "besar" else "biasa"
                rows.append(build_item(
                    kind,
                    "Misa Besar" if kind == "besar" else "Misa Biasa",
                    row.get("misa_name") or row.get("type_label") or "Misa",
                    normalize_text(row.get("date")),
                    format_time_hhmm(row.get("time")),
                    row.get("role_name"),
                    row.get("request_source"),
                    row.get("cancelled_at"),
                    cancelled=True,
                    note=row.get("note") or "Tugas ini sudah dibatalkan.",
                ))
        except Exception as exc:
            print(f"[WARN] Gagal memuat riwayat pembatalan tugas: {exc}")

        if kind_filter in {"biasa", "besar"}:
            rows = [item for item in rows if item.get("type") == kind_filter]

        if month_filter.lower() != "all":
            month_int = min(12, max(1, parse_required_int(month_filter, datetime.now().month)))
            rows = [item for item in rows if normalize_text(item.get("date"))[5:7] == f"{month_int:02d}"]

        if year_filter.lower() != "all":
            year_int = parse_required_int(year_filter, datetime.now().year)
            rows = [item for item in rows if normalize_text(item.get("date"))[:4] == str(year_int)]

        if search_text:
            def matches(item):
                haystack = " ".join([
                    normalize_text(item.get("misaName")),
                    normalize_text(item.get("typeLabel")),
                    normalize_text(item.get("role")),
                    normalize_text(item.get("status")),
                    normalize_text(item.get("sourceLabel")),
                    normalize_text(item.get("date")),
                    normalize_text(item.get("time")),
                    normalize_text(item.get("note")),
                ]).lower()
                return search_text in haystack
            rows = [item for item in rows if matches(item)]

        def schedule_dt(item):
            try:
                return datetime.strptime(f"{item.get('date')} {format_time_hhmm(item.get('time'))}", "%Y-%m-%d %H:%M")
            except Exception:
                return datetime(1970, 1, 1)

        if sort_mode in {"date_asc", "tanggal_terlama"}:
            rows.sort(key=schedule_dt)
        elif sort_mode in {"role_asc"}:
            rows.sort(key=lambda item: normalize_text(item.get("role")).lower())
        elif sort_mode in {"status_asc"}:
            rows.sort(key=lambda item: normalize_text(item.get("status")).lower())
        elif sort_mode in {"type_asc", "jenis_asc"}:
            rows.sort(key=lambda item: (normalize_text(item.get("typeLabel")).lower(), schedule_dt(item)))
        else:
            rows.sort(key=schedule_dt, reverse=True)

        total = len(rows)
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages)
        start = (page - 1) * page_size
        paged_rows = rows[start:start + page_size]

        now = datetime.now()
        def in_stats_range(item):
            try:
                item_date = datetime.strptime(normalize_text(item.get("date")), "%Y-%m-%d")
            except Exception:
                return False
            if stats_range == "year":
                return item_date.year == now.year
            if stats_range == "week":
                week_start = now - timedelta(days=now.weekday())
                week_start = datetime(week_start.year, week_start.month, week_start.day)
                week_end = week_start + timedelta(days=7)
                return week_start <= item_date < week_end
            return item_date.year == now.year and item_date.month == now.month

        summary_rows = [item for item in rows if in_stats_range(item)]
        summary = {
            "total": len(summary_rows),
            "completed": sum(1 for item in summary_rows if item.get("status") == "Selesai"),
            "exchange": sum(1 for item in summary_rows if item.get("isExchange")),
            "upcoming": sum(1 for item in summary_rows if item.get("status") == "Terdaftar"),
            "cancelled": sum(1 for item in summary_rows if item.get("status") == "Dibatalkan"),
        }

        return jsonify({
            "success": True,
            "items": paged_rows,
            "summary": summary,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
            },
            "filters": {
                "type": kind_filter,
                "month": month_filter,
                "year": year_filter,
                "sort": sort_mode,
                "search": search_text,
            },
        })
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 11395-11550 | routes: /api/request-tugas/history
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


# Source legacy app.py lines 11789-11801 | routes: /api/cancel-tugas/me
@app.route("/api/cancel-tugas/me", methods=["GET"])
def api_cancel_tugas_me():
    ensure_task_cancellation_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        return jsonify({"success": True, "member": {"id": member.get("id"), "name": member.get("name"), "role": "user"}})
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 11804-11890 | routes: /api/cancel-tugas/active
@app.route("/api/cancel-tugas/active", methods=["GET"])
def api_cancel_tugas_active():
    ensure_task_cancellation_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        member_id = member["id"]
        today = datetime.now().date()
        min_cancel_date = (today + timedelta(days=3)).strftime("%Y-%m-%d")
        month = request.args.get("month")
        year = request.args.get("year")
        if month in (None, "", "current"):
            month = str(today.month)
        if year in (None, "", "current"):
            year = str(today.year)
        month_int = parse_required_int(month, today.month)
        year_int = parse_required_int(year, today.year)
        month_int = min(12, max(1, month_int))
        start_date = f"{year_int:04d}-{month_int:02d}-01"
        last_day = calendar.monthrange(year_int, month_int)[1]
        end_date = f"{year_int:04d}-{month_int:02d}-{last_day:02d}"
        kind_filter = (normalize_text(request.args.get("type")) or "all").lower()
        search_text = normalize_text(request.args.get("search"))
        sort_mode = normalize_text(request.args.get("sort")) or "date_asc"
        page = max(1, parse_required_int(request.args.get("page"), 1))
        page_size = max(1, min(25, parse_required_int(request.args.get("pageSize"), 5)))

        items: list[dict[str, object]] = []
        if kind_filter in {"all", "biasa"}:
            cursor.execute(
                """
                SELECT sa.id AS assignment_id, DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                       DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                       sa.role_name AS role, COALESCE(sa.request_source, 'admin') AS request_source,
                       COALESCE(cfg.mass_name, 'Misa Biasa') AS mass_name
                FROM streaming_assignments sa
                LEFT JOIN streaming_weekly_config cfg
                  ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                    WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                    WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                    ELSE 'Minggu' END
                  AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
                WHERE sa.member_id = %s
                  AND sa.schedule_date BETWEEN %s AND %s
                  AND sa.schedule_date >= %s
                """,
                (member_id, start_date, end_date, min_cancel_date),
            )
            for row in cursor.fetchall() or []:
                items.append(cancel_task_build_item(row, kind="biasa"))

        if kind_filter in {"all", "besar"}:
            cursor.execute(
                """
                SELECT a.id AS assignment_id, mb.id AS misa_id, n.id AS role_id,
                       mb.misa_name, DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                       DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                       n.role_name AS role, COALESCE(a.request_source, 'admin') AS request_source
                FROM misa_besar_assignments a
                JOIN misa_besar_names n ON n.id = a.role_id
                JOIN misa_besar mb ON mb.id = n.misa_id
                WHERE a.member_id = %s
                  AND mb.status = 'published'
                  AND mb.misa_date BETWEEN %s AND %s
                  AND mb.misa_date >= %s
                """,
                (member_id, start_date, end_date, min_cancel_date),
            )
            for row in cursor.fetchall() or []:
                items.append(cancel_task_build_item(row, kind="besar"))

        items = cancel_task_filter_items(items, search_text=search_text, kind_filter=kind_filter)
        items = cancel_task_sort_items(items, sort_mode, history=False)
        page_items, pagination = cancel_task_paginate(items, page, page_size)
        return jsonify({
            "success": True,
            "items": page_items,
            "pagination": pagination,
            "filters": {"month": month_int, "year": year_int, "type": kind_filter},
            "rule": {"minCancelDate": min_cancel_date, "description": "Pembatalan hanya bisa dilakukan paling lambat H-3 sebelum jadwal."},
        })
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 11893-11968 | routes: /api/cancel-tugas/history
@app.route("/api/cancel-tugas/history", methods=["GET"])
def api_cancel_tugas_history():
    ensure_task_cancellation_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        member_id = member["id"]
        kind_filter = (normalize_text(request.args.get("type")) or "all").lower()
        month = normalize_text(request.args.get("month")) or "all"
        year = normalize_text(request.args.get("year")) or "all"
        search_text = normalize_text(request.args.get("search"))
        sort_mode = normalize_text(request.args.get("sort")) or "cancelled_desc"
        page = max(1, parse_required_int(request.args.get("page"), 1))
        page_size = max(1, min(25, parse_required_int(request.args.get("pageSize"), 5)))

        conditions = ["member_id = %s"]
        params: list[object] = [member_id]
        if kind_filter in {"biasa", "besar"}:
            conditions.append("kind = %s")
            params.append(kind_filter)
        if month != "all":
            month_int = min(12, max(1, parse_required_int(month, 1)))
            conditions.append("MONTH(schedule_date) = %s")
            params.append(month_int)
        if year != "all":
            year_int = parse_required_int(year, datetime.now().year)
            conditions.append("YEAR(schedule_date) = %s")
            params.append(year_int)
        where_clause = " AND ".join(conditions)
        cursor.execute(
            f"""
            SELECT id, kind, type_label, misa_id, role_id, assignment_id,
                   DATE_FORMAT(schedule_date, '%Y-%m-%d') AS date,
                   DATE_FORMAT(schedule_time, '%H:%i') AS time,
                   misa_name, role_name AS role, request_source,
                   cancelled_at, status
            FROM task_cancellations
            WHERE {where_clause}
            """,
            tuple(params),
        )
        items = []
        for row in cursor.fetchall() or []:
            date_text = normalize_text(row.get("date"))
            time_text = format_time_hhmm(row.get("time"))
            kind = normalize_text(row.get("kind")) or "biasa"
            type_label = normalize_text(row.get("type_label")) or ("Misa Besar" if kind == "besar" else "Misa Biasa")
            cancelled_at = row.get("cancelled_at")
            items.append({
                "id": row.get("id"),
                "type": kind,
                "typeLabel": type_label,
                "misaId": row.get("misa_id"),
                "roleId": row.get("role_id"),
                "assignmentId": row.get("assignment_id"),
                "misaName": normalize_text(row.get("misa_name")) or type_label,
                "date": date_text,
                "dateLabel": request_task_format_date(date_text),
                "dayName": request_task_day_name(date_text),
                "time": time_text,
                "role": normalize_text(row.get("role")) or "Role",
                "source": normalize_text(row.get("request_source")) or "admin",
                "status": "Batal",
                "cancelledAt": cancelled_at.isoformat() if hasattr(cancelled_at, "isoformat") else normalize_text(cancelled_at),
                "cancelledAtLabel": cancelled_at.strftime("%d/%m/%Y %H:%M:%S") if hasattr(cancelled_at, "strftime") else normalize_text(cancelled_at),
            })
        items = cancel_task_filter_items(items, search_text=search_text, kind_filter=kind_filter)
        items = cancel_task_sort_items(items, sort_mode, history=True)
        page_items, pagination = cancel_task_paginate(items, page, page_size)
        return jsonify({"success": True, "items": page_items, "pagination": pagination})
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 11971-12086 | routes: /api/cancel-tugas/cancel
@app.route("/api/cancel-tugas/cancel", methods=["POST"])
def api_cancel_tugas_cancel():
    ensure_task_cancellation_schema()
    data = request.get_json(silent=True) or {}
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = require_active_request_member(cursor)
        if error:
            return error
        member_id = member["id"]
        kind = (normalize_text(data.get("type")) or "biasa").lower()
        assignment_id = parse_optional_int(data.get("assignmentId"))

        if kind == "besar":
            misa_id = parse_optional_int(data.get("misaId"))
            role_id = parse_optional_int(data.get("roleId"))
            if assignment_id is not None:
                cursor.execute(
                    """
                    SELECT a.id AS assignment_id, mb.id AS misa_id, n.id AS role_id,
                           mb.misa_name, DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                           DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                           n.role_name AS role, COALESCE(a.request_source, 'admin') AS request_source
                    FROM misa_besar_assignments a
                    JOIN misa_besar_names n ON n.id = a.role_id
                    JOIN misa_besar mb ON mb.id = n.misa_id
                    WHERE a.id = %s AND a.member_id = %s
                    LIMIT 1
                    """,
                    (assignment_id, member_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT a.id AS assignment_id, mb.id AS misa_id, n.id AS role_id,
                           mb.misa_name, DATE_FORMAT(mb.misa_date, '%Y-%m-%d') AS date,
                           DATE_FORMAT(mb.misa_time, '%H:%i') AS time,
                           n.role_name AS role, COALESCE(a.request_source, 'admin') AS request_source
                    FROM misa_besar_assignments a
                    JOIN misa_besar_names n ON n.id = a.role_id
                    JOIN misa_besar mb ON mb.id = n.misa_id
                    WHERE mb.id = %s AND n.id = %s AND a.member_id = %s
                    LIMIT 1
                    """,
                    (misa_id, role_id, member_id),
                )
            row = cursor.fetchone()
            if not row:
                return jsonify({"success": False, "error": "Tugas Misa Besar tidak ditemukan atau bukan milik Anda."}), 404
            item = cancel_task_build_item(row, kind="besar")
            if not cancel_task_can_cancel(item.get("date")):
                return jsonify({"success": False, "error": "Tugas ini sudah melewati batas pembatalan H-3."}), 400
            cancel_task_insert_history(cursor, member=member, item=item)
            cursor.execute("DELETE FROM misa_besar_assignments WHERE id = %s AND member_id = %s", (item.get("assignmentId"), member_id))
        else:
            date_text = parse_optional_date(data.get("date"))
            time_text = format_time_hhmm(data.get("time"))
            role_name = normalize_text(data.get("role"))
            if assignment_id is not None:
                cursor.execute(
                    """
                    SELECT sa.id AS assignment_id, DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                           DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                           sa.role_name AS role, COALESCE(sa.request_source, 'admin') AS request_source,
                           COALESCE(cfg.mass_name, 'Misa Biasa') AS mass_name
                    FROM streaming_assignments sa
                    LEFT JOIN streaming_weekly_config cfg
                      ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                        WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                        WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                        ELSE 'Minggu' END
                      AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
                    WHERE sa.id = %s AND sa.member_id = %s
                    LIMIT 1
                    """,
                    (assignment_id, member_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT sa.id AS assignment_id, DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS date,
                           DATE_FORMAT(sa.schedule_time, '%H:%i') AS time,
                           sa.role_name AS role, COALESCE(sa.request_source, 'admin') AS request_source,
                           COALESCE(cfg.mass_name, 'Misa Biasa') AS mass_name
                    FROM streaming_assignments sa
                    LEFT JOIN streaming_weekly_config cfg
                      ON cfg.day_name = CASE WEEKDAY(sa.schedule_date)
                        WHEN 0 THEN 'Senin' WHEN 1 THEN 'Selasa' WHEN 2 THEN 'Rabu'
                        WHEN 3 THEN 'Kamis' WHEN 4 THEN 'Jumat' WHEN 5 THEN 'Sabtu'
                        ELSE 'Minggu' END
                      AND DATE_FORMAT(cfg.start_time, '%H:%i') = DATE_FORMAT(sa.schedule_time, '%H:%i')
                    WHERE sa.schedule_date = %s AND DATE_FORMAT(sa.schedule_time, '%H:%i') = %s
                      AND sa.role_name = %s AND sa.member_id = %s
                    LIMIT 1
                    """,
                    (date_text, time_text, role_name, member_id),
                )
            row = cursor.fetchone()
            if not row:
                return jsonify({"success": False, "error": "Tugas Misa Biasa tidak ditemukan atau bukan milik Anda."}), 404
            item = cancel_task_build_item(row, kind="biasa")
            if not cancel_task_can_cancel(item.get("date")):
                return jsonify({"success": False, "error": "Tugas ini sudah melewati batas pembatalan H-3."}), 400
            cancel_task_insert_history(cursor, member=member, item=item)
            cursor.execute("DELETE FROM streaming_assignments WHERE id = %s AND member_id = %s", (item.get("assignmentId"), member_id))

        cancel_task_notify(cursor, member=member, item=item)
        conn.commit()
        return jsonify({"success": True, "message": "Tugas berhasil dibatalkan.", "item": item})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


