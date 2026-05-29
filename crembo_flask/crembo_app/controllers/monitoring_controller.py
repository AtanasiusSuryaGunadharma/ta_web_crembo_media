from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Monitoring Controller

# Source legacy app.py lines 13433-13524 | routes: /api/monitoring-tugas
@app.route("/api/monitoring-tugas", methods=["GET"])
def api_monitoring_tugas():
    auth_error = monitoring_require_admin()
    if auth_error:
        return auth_error
    ensure_auth_schema()
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        ensure_monthly_monitoring_schema(cursor)
        now = datetime.now()
        month = max(1, min(12, parse_required_int(request.args.get("month"), now.month)))
        year = parse_required_int(request.args.get("year"), now.year)
        search_text = normalize_text(request.args.get("search")).lower()
        role_filter = normalize_text(request.args.get("role") or "all")
        status_filter = normalize_text(request.args.get("status") or "all")
        sort_mode = normalize_text(request.args.get("sort") or "name_asc")
        target = monitoring_get_target_minimum(cursor)
        counts = monitoring_count_regular_assignments(cursor, year, month)
        members = monitoring_fetch_members(cursor, year, month)

        items: list[dict[str, object]] = []
        for member in members:
            total = counts.get(int(member.get("id") or 0), 0)
            label, class_name, shortage = monitoring_status(total, target)
            item = {
                "id": member.get("id"),
                "name": member.get("name"),
                "accountRole": member.get("accountRole"),
                "accountRoleLabel": member.get("accountRoleLabel"),
                "totalTasks": total,
                "shortage": shortage,
                "status": label,
                "statusClass": class_name,
                "canSchedule": shortage > 0,
            }
            items.append(item)

        if role_filter != "all":
            items = [i for i in items if normalize_text(i.get("accountRole")) == role_filter]
        if status_filter != "all":
            items = [i for i in items if normalize_text(i.get("status")) == status_filter]
        if search_text:
            items = [i for i in items if search_text in (normalize_text(i.get("name")) + " " + normalize_text(i.get("accountRoleLabel"))).lower()]

        if sort_mode == "name_desc":
            items.sort(key=lambda i: normalize_text(i.get("name")).lower(), reverse=True)
        elif sort_mode == "total_asc":
            items.sort(key=lambda i: (i.get("totalTasks") or 0, normalize_text(i.get("name")).lower()))
        elif sort_mode == "total_desc":
            items.sort(key=lambda i: (i.get("totalTasks") or 0, normalize_text(i.get("name")).lower()), reverse=True)
        elif sort_mode == "shortage_asc":
            items.sort(key=lambda i: (i.get("shortage") or 0, normalize_text(i.get("name")).lower()))
        elif sort_mode == "shortage_desc":
            items.sort(key=lambda i: (i.get("shortage") or 0, normalize_text(i.get("name")).lower()), reverse=True)
        elif sort_mode == "status_asc":
            order = {"Aman": 0, "Perlu Tambahan": 1, "Kritis": 2}
            items.sort(key=lambda i: (order.get(normalize_text(i.get("status")), 9), normalize_text(i.get("name")).lower()))
        elif sort_mode == "status_desc":
            order = {"Aman": 0, "Perlu Tambahan": 1, "Kritis": 2}
            items.sort(key=lambda i: (order.get(normalize_text(i.get("status")), 9), normalize_text(i.get("name")).lower()), reverse=True)
        else:
            items.sort(key=lambda i: normalize_text(i.get("name")).lower())

        # Ringkasan dihitung dari seluruh anggota aktif pada periode tersebut, bukan hanya hasil search.
        all_statuses = []
        for member in members:
            total = counts.get(int(member.get("id") or 0), 0)
            label, class_name, shortage = monitoring_status(total, target)
            all_statuses.append((label, shortage))
        summary = {
            "totalMembers": len(members),
            "completedMembers": sum(1 for label, shortage in all_statuses if shortage == 0),
            "shortage1Members": sum(1 for label, shortage in all_statuses if shortage == 1),
            "shortageMultiMembers": sum(1 for label, shortage in all_statuses if shortage > 1),
            "targetMinimum": target,
        }
        return jsonify({
            "success": True,
            "items": items,
            "summary": summary,
            "period": {"month": month, "year": year},
            "roles": [
                {"value": "user", "label": "Anggota"},
                {"value": "admin", "label": "Admin"},
                {"value": "super_admin", "label": "Super Admin"},
            ],
        })
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 13527-13550 | routes: /api/monitoring-tugas/target
@app.route("/api/monitoring-tugas/target", methods=["POST"])
def api_monitoring_tugas_target():
    auth_error = monitoring_require_admin()
    if auth_error:
        return auth_error
    payload = request.get_json(silent=True) or {}
    target = max(1, min(99, parse_required_int(payload.get("targetMinimum"), 2)))
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_monthly_monitoring_schema(cursor)
        cursor.execute(
            """
            INSERT INTO monthly_task_settings (`id`, `target_minimum`)
            VALUES ('default', %s)
            ON DUPLICATE KEY UPDATE target_minimum = VALUES(target_minimum), updated_at = CURRENT_TIMESTAMP
            """,
            (target,),
        )
        conn.commit()
        return jsonify({"success": True, "targetMinimum": target})
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 13553-13580 | routes: /api/monitoring-tugas/slots
@app.route("/api/monitoring-tugas/slots", methods=["GET"])
def api_monitoring_tugas_slots():
    auth_error = monitoring_require_admin()
    if auth_error:
        return auth_error
    ensure_auth_schema()
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        ensure_monthly_monitoring_schema(cursor)
        now = datetime.now()
        month = max(1, min(12, parse_required_int(request.args.get("month"), now.month)))
        year = parse_required_int(request.args.get("year"), now.year)
        member_id = request.args.get("memberId")
        if not member_id:
            return jsonify({"success": False, "error": "Member wajib dipilih."}), 400
        cursor.execute("SELECT id, nama, role, status_akun FROM anggota WHERE id = %s LIMIT 1", (member_id,))
        member = cursor.fetchone()
        if not member:
            return jsonify({"success": False, "error": "Anggota tidak ditemukan."}), 404
        if normalize_status(member.get("status_akun") or "aktif") != "aktif":
            return jsonify({"success": False, "error": "Anggota sedang nonaktif."}), 400
        slots = monitoring_open_regular_slots(cursor, year, month, member_id=member_id)
        return jsonify({"success": True, "slots": slots, "member": {"id": member.get("id"), "name": member.get("nama")}})
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 13583-13681 | routes: /api/monitoring-tugas/schedule
@app.route("/api/monitoring-tugas/schedule", methods=["POST"])
def api_monitoring_tugas_schedule():
    auth_error = monitoring_require_admin()
    if auth_error:
        return auth_error
    payload = request.get_json(silent=True) or {}
    member_id = normalize_text(payload.get("memberId"))
    date_text = normalize_text(payload.get("date"))
    time_text = format_time_hhmm(payload.get("time"))
    role_name = normalize_text(payload.get("role"))
    if not member_id or not date_text or not time_text or not role_name:
        return jsonify({"success": False, "error": "Anggota, tanggal, jam, dan role wajib dipilih."}), 400
    try:
        date_obj = datetime.strptime(date_text, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"success": False, "error": "Tanggal tidak valid."}), 400
    if date_obj <= datetime.now().date():
        return jsonify({"success": False, "error": "Hanya jadwal mulai besok dan seterusnya yang bisa dipilih."}), 400

    ensure_auth_schema()
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute("SELECT id, nama, role, status_akun FROM anggota WHERE id = %s LIMIT 1", (member_id,))
        member = cursor.fetchone()
        if not member:
            return jsonify({"success": False, "error": "Anggota tidak ditemukan."}), 404
        if normalize_status(member.get("status_akun") or "aktif") != "aktif":
            return jsonify({"success": False, "error": "Anggota sedang nonaktif."}), 400
        cursor.execute("SELECT role_name FROM streaming_roles WHERE role_name = %s LIMIT 1", (role_name,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Role tidak valid."}), 400
        cfg = request_task_get_regular_cfg(cursor, date_text, time_text)
        if not cfg:
            return jsonify({"success": False, "error": "Jadwal Misa Biasa tidak ditemukan pada tanggal/jam tersebut."}), 400
        if monitoring_regular_slot_conflict(cursor, date_text, time_text):
            return jsonify({"success": False, "error": "Jadwal diblokir/ditiadakan atau bentrok Misa Besar."}), 400
        cursor.execute(
            """
            SELECT role_name FROM streaming_assignments
            WHERE schedule_date = %s AND DATE_FORMAT(schedule_time, '%H:%i') = %s AND member_id = %s
            LIMIT 1
            """,
            (date_text, time_text, member_id),
        )
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Anggota ini sudah bertugas di sesi yang sama."}), 400
        cursor.execute(
            """
            SELECT member_id FROM streaming_assignments
            WHERE schedule_date = %s AND DATE_FORMAT(schedule_time, '%H:%i') = %s AND role_name = %s
            LIMIT 1
            """,
            (date_text, time_text, role_name),
        )
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Role ini sudah terisi."}), 409
        cursor.execute(
            """
            INSERT INTO streaming_assignments (schedule_date, schedule_time, role_name, member_id, request_source, created_at)
            VALUES (%s, %s, %s, %s, 'admin', CURRENT_TIMESTAMP)
            """,
            (date_text, time_text, role_name, member_id),
        )
        ensure_notifications_schema()
        day_name = request_task_day_name(date_text)
        date_label = request_task_format_date(date_text)
        misa_name = normalize_text(cfg.get("mass_name")) or "Misa Biasa"
        title = f"Tugas Baru: {role_name}"
        body = (
            f"Anda dijadwalkan sebagai <b>{html.escape(role_name)}</b> untuk <b>{html.escape(misa_name)}</b> "
            f"pada hari {html.escape(day_name)}, {html.escape(date_label)} jam {html.escape(time_text)} WIB."
        )
        create_notification(
            cursor,
            "tugas",
            title,
            body,
            notification_target_url_for_member_role(member.get("role"), default_user_url="/jadwal-tugas-misa-anggota.html"),
            {
                "target_user_id": str(member_id),
                "notification_kind": "monitoring_admin_schedule",
                "misa_type": "misa_biasa",
                "misa_name": misa_name,
                "misa_date": date_text,
                "misa_time": time_text,
                "role": role_name,
            },
            target_role=None,
        )
        conn.commit()
        return jsonify({"success": True, "message": f"{member.get('nama')} berhasil dijadwalkan sebagai {role_name}."})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 14045-14072 | routes: /api/monitoring-kewajiban-tugas/profile
@app.route("/api/monitoring-kewajiban-tugas/profile", methods=["GET"])
def api_member_monitoring_profile():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = member_monitoring_current_user(cursor)
        if error:
            return error
        now = datetime.now()
        return jsonify({
            "success": True,
            "member": {
                "id": member.get("id"),
                "name": member.get("name"),
                "username": member.get("username") or "",
                "role": member.get("roleNormalized"),
                "roleLabel": member.get("roleLabel"),
                "initial": (member.get("name") or "A")[:1].upper(),
            },
            "current": {"month": now.month, "year": now.year},
            "years": member_monitoring_available_years(cursor, member.get("id")),
        })
    except Exception as exc:
        return member_monitoring_api_error(exc)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 14074-14135 | routes: /api/monitoring-kewajiban-tugas/summary
@app.route("/api/monitoring-kewajiban-tugas/summary", methods=["GET"])
def api_member_monitoring_summary():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        ensure_monthly_monitoring_schema(cursor)
        member, error = member_monitoring_current_user(cursor)
        if error:
            return error
        now = datetime.now()
        member_id = member.get("id")
        target = monitoring_get_target_minimum(cursor)
        progress_month = member_monitoring_parse_month(request.args.get("progressMonth"), now.month)
        progress_year = member_monitoring_parse_year(request.args.get("progressYear"), now.year)
        shortage_month = member_monitoring_parse_month(request.args.get("shortageMonth"), now.month)
        shortage_year = member_monitoring_parse_year(request.args.get("shortageYear"), now.year)
        total_month = member_monitoring_parse_month(request.args.get("totalMonth"), now.month)
        total_year = member_monitoring_parse_year(request.args.get("totalYear"), now.year)

        progress_tasks = member_monitoring_fetch_all_tasks(cursor, member_id, month=progress_month, year=progress_year, include_big=True)
        progress_total = len(progress_tasks)
        progress_completed = sum(1 for task in progress_tasks if task.get("completed"))
        progress_percentage = min(100, round((progress_completed / progress_total) * 100)) if progress_total else 0

        shortage_periods = member_monitoring_period_list(cursor, member_id, month=shortage_month, year=shortage_year)
        shortage_total_value = 0
        shortage_regular_total = 0
        for y, m in shortage_periods:
            total_regular = member_monitoring_regular_count_for_period(cursor, member_id, y, m)
            shortage_regular_total += total_regular
            shortage_total_value += max(0, target - total_regular)

        total_tasks = member_monitoring_fetch_all_tasks(cursor, member_id, month=total_month, year=total_year, include_big=True)
        total_scheduled = len(total_tasks)
        total_completed = sum(1 for task in total_tasks if task.get("completed"))

        return jsonify({
            "success": True,
            "targetMinimum": target,
            "progress": {
                "completed": progress_completed,
                "total": progress_total,
                "percentage": progress_percentage,
                "periodLabel": member_monitoring_period_label(progress_month, progress_year),
            },
            "shortage": {
                "shortage": shortage_total_value,
                "regularTotal": shortage_regular_total,
                "periodLabel": member_monitoring_period_label(shortage_month, shortage_year),
            },
            "total": {
                "scheduled": total_scheduled,
                "completed": total_completed,
                "periodLabel": member_monitoring_period_label(total_month, total_year),
            },
        })
    except Exception as exc:
        return member_monitoring_api_error(exc)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 14137-14178 | routes: /api/monitoring-kewajiban-tugas/progress
@app.route("/api/monitoring-kewajiban-tugas/progress", methods=["GET"])
def api_member_monitoring_progress():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        member, error = member_monitoring_current_user(cursor)
        if error:
            return error
        now = datetime.now()
        month = member_monitoring_parse_month(request.args.get("month"), now.month)
        year = member_monitoring_parse_year(request.args.get("year"), now.year)
        search_text = normalize_text(request.args.get("search")).lower()
        sort_mode = normalize_text(request.args.get("sort")) or "date-desc"
        tasks = member_monitoring_fetch_all_tasks(cursor, member.get("id"), month=month, year=year, include_big=True)
        if search_text:
            tasks = [task for task in tasks if search_text in " ".join([
                normalize_text(task.get("typeLabel")),
                normalize_text(task.get("misaName")),
                normalize_text(task.get("role")),
                normalize_text(task.get("date")),
                normalize_text(task.get("time")),
                normalize_text(task.get("status")),
            ]).lower()]
        if sort_mode == "date-asc":
            tasks.sort(key=lambda task: member_monitoring_schedule_dt(task.get("date"), task.get("time")))
        elif sort_mode == "status":
            tasks.sort(key=lambda task: (normalize_text(task.get("status")), member_monitoring_schedule_dt(task.get("date"), task.get("time"))))
        else:
            tasks.sort(key=lambda task: member_monitoring_schedule_dt(task.get("date"), task.get("time")), reverse=True)
        groups = member_monitoring_progress_group(tasks)
        return jsonify({
            "success": True,
            "items": groups,
            "tasks": tasks,
            "period": {"month": month, "year": year, "label": member_monitoring_period_label(month, year)},
        })
    except Exception as exc:
        return member_monitoring_api_error(exc)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 14180-14232 | routes: /api/monitoring-kewajiban-tugas/shortage
@app.route("/api/monitoring-kewajiban-tugas/shortage", methods=["GET"])
def api_member_monitoring_shortage():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        ensure_monthly_monitoring_schema(cursor)
        member, error = member_monitoring_current_user(cursor)
        if error:
            return error
        now = datetime.now()
        month = member_monitoring_parse_month(request.args.get("month"), None)
        if not normalize_text(request.args.get("month")):
            month = "all"
        year = member_monitoring_parse_year(request.args.get("year"), now.year)
        status_filter = normalize_text(request.args.get("status") or "all").lower()
        sort_mode = normalize_text(request.args.get("sort") or "month_asc").lower()
        target = monitoring_get_target_minimum(cursor)
        periods = member_monitoring_period_list(cursor, member.get("id"), month=month, year=year, default_all_months=(month == "all"))
        rows = []
        for y, m in periods:
            total = member_monitoring_regular_count_for_period(cursor, member.get("id"), y, m)
            shortage = max(0, target - total)
            fulfilled = shortage == 0
            rows.append({
                "month": m,
                "year": y,
                "period": f"{y}-{m:02d}",
                "monthText": f"{member_monitoring_month_name(m)} {y}",
                "targetMinimum": target,
                "totalTasks": total,
                "shortage": shortage,
                "status": "Terpenuhi" if fulfilled else f"Kurang {shortage} tugas",
                "statusClass": "ok" if fulfilled else "danger",
            })
        if status_filter == "fulfilled":
            rows = [row for row in rows if row.get("shortage") == 0]
        elif status_filter == "unfulfilled":
            rows = [row for row in rows if row.get("shortage") > 0]
        if sort_mode == "month_desc":
            rows.sort(key=lambda row: (row.get("year"), row.get("month")), reverse=True)
        elif sort_mode == "shortage_desc":
            rows.sort(key=lambda row: (row.get("shortage"), row.get("year"), row.get("month")), reverse=True)
        elif sort_mode == "shortage_asc":
            rows.sort(key=lambda row: (row.get("shortage"), row.get("year"), row.get("month")))
        else:
            rows.sort(key=lambda row: (row.get("year"), row.get("month")))
        return jsonify({"success": True, "items": rows, "targetMinimum": target})
    except Exception as exc:
        return member_monitoring_api_error(exc)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 14234-14274 | routes: /api/monitoring-kewajiban-tugas/stats
@app.route("/api/monitoring-kewajiban-tugas/stats", methods=["GET"])
def api_member_monitoring_stats():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        ensure_monthly_monitoring_schema(cursor)
        member, error = member_monitoring_current_user(cursor)
        if error:
            return error
        now = datetime.now()
        month = member_monitoring_parse_month(request.args.get("month"), now.month)
        year = member_monitoring_parse_year(request.args.get("year"), now.year)
        target = monitoring_get_target_minimum(cursor)
        periods = member_monitoring_period_list(cursor, member.get("id"), month=month, year=year)
        rows = []
        for y, m in periods:
            regular_tasks = member_monitoring_fetch_regular_tasks(cursor, member.get("id"), month=str(m), year=str(y))
            total_tasks = len(regular_tasks)
            completed = sum(1 for task in regular_tasks if task.get("completed"))
            shortage = max(0, target - total_tasks)
            percentage = 100 if total_tasks >= target else (round((total_tasks / target) * 100) if target else 0)
            rows.append({
                "month": m,
                "year": y,
                "period": f"{y}-{m:02d}",
                "monthText": f"{member_monitoring_month_name(m)} {y}",
                "targetMinimum": target,
                "targetTasks": total_tasks,
                "completedTasks": completed,
                "shortage": shortage,
                "percentage": min(100, percentage),
                "statusClass": "ok" if shortage == 0 else ("warn" if shortage == 1 else "danger"),
            })
        rows.sort(key=lambda row: (row.get("year"), row.get("month")), reverse=True)
        return jsonify({"success": True, "items": rows, "targetMinimum": target})
    except Exception as exc:
        return member_monitoring_api_error(exc)
    finally:
        cursor.close()
        conn.close()


