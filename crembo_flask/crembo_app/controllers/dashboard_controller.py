from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Dashboard Controller

# Source legacy app.py lines 3989-4074 | routes: /api/dashboard/anggota-overview
@app.route("/api/dashboard/anggota-overview", methods=["GET"])
def api_dashboard_anggota_overview():
    ensure_auth_schema()
    ensure_task_request_schema()
    ensure_task_cancellation_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        ensure_monthly_monitoring_schema(cursor)
        ensure_streaming_evaluation_schema(cursor)
        member, error = member_monitoring_current_user(cursor)
        if error:
            return error
        member_id = member.get("id")
        now = datetime.now()

        schedule_range = normalize_text(request.args.get("scheduleRange") or "week").lower()
        done_range = normalize_text(request.args.get("doneRange") or "month").lower()
        chart_range = normalize_text(request.args.get("chartRange") or "month").lower()
        if schedule_range not in {"week", "month", "year"}:
            schedule_range = "week"
        if done_range not in {"week", "month", "year"}:
            done_range = "month"
        if chart_range not in {"week", "month", "year"}:
            chart_range = "month"

        task_month = min(12, max(1, parse_required_int(request.args.get("taskMonth"), now.month)))
        task_year = parse_required_int(request.args.get("taskYear"), now.year)
        task_type = member_dashboard_type_filter(request.args.get("taskType") or "all")

        # Metric 1: semua jadwal tersedia pada periode terpilih.
        schedule_start, schedule_end = dashboard_period_bounds(schedule_range)
        available_schedule_count = len(eval_all_schedules(cursor, schedule_start, schedule_end, "all"))

        # Target minimum berlaku untuk Misa Biasa bulan berjalan.
        target_minimum = monitoring_get_target_minimum(cursor)
        current_regular_count = member_monitoring_regular_count_for_period(cursor, member_id, now.year, now.month)
        pending_minimum = max(0, target_minimum - current_regular_count)

        # Metric tugas akan datang selalu bulan berjalan, semua jenis tugas.
        current_month_tasks = member_monitoring_fetch_all_tasks(cursor, member_id, month=str(now.month), year=str(now.year), include_big=True)
        upcoming_count = sum(1 for task in current_month_tasks if member_dashboard_schedule_dt(task.get("date"), task.get("time")) > now)

        # Metric selesai mengikuti select Minggu/Bulan/Tahun, semua jenis tugas.
        done_start, done_end = dashboard_period_bounds(done_range)
        done_tasks = member_monitoring_fetch_all_tasks(cursor, member_id, month="all", year=str(now.year), include_big=True)
        done_count = 0
        for task in done_tasks:
            task_dt = member_dashboard_schedule_dt(task.get("date"), task.get("time"))
            if done_start <= task_dt.date() <= done_end and task_dt <= now:
                done_count += 1

        request_chart = member_dashboard_request_chart(cursor, member_id, chart_range)
        recommendations = member_dashboard_recommended_tasks(cursor, member_id, target_minimum=target_minimum, regular_count=current_regular_count)
        registered_tasks = member_dashboard_registered_tasks(cursor, member_id, month=task_month, year=task_year, kind_filter=task_type)

        conn.commit()
        return jsonify({
            "success": True,
            "currentUser": current_user_context_from_row({
                "id": member.get("id"),
                "nama": member.get("name"),
                "username": member.get("username") or "",
                "role": member.get("role") or "user",
                "status_akun": member.get("status_akun") or "aktif",
            }),
            "metrics": {
                "availableSchedules": {"range": schedule_range, "total": available_schedule_count},
                "targetMinimum": target_minimum,
                "regularTasksThisMonth": current_regular_count,
                "pendingMinimum": pending_minimum,
                "upcomingThisMonth": upcoming_count,
                "doneTasks": {"range": done_range, "total": done_count},
            },
            "requestChart": request_chart,
            "tasksToTake": recommendations,
            "registeredTasks": registered_tasks,
            "filters": {"taskMonth": task_month, "taskYear": task_year, "taskType": task_type},
        })
    except Exception as exc:
        conn.rollback()
        print(f"[ERROR] Dashboard anggota gagal memuat data: {exc}")
        return jsonify({"success": False, "error": f"Gagal memuat dashboard anggota: {exc}"}), 500
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 4077-4151 | routes: /api/dashboard/admin-overview
@app.route("/api/dashboard/admin-overview", methods=["GET"])
def api_dashboard_admin_overview():
    role = normalize_role_value(session.get("role") or "")
    if not session.get("logged_in") or role not in {"admin", "super_admin"}:
        return jsonify({"success": False, "error": "Akses ditolak."}), 403

    metric_range = normalize_text(request.args.get("scheduleRange") or "week")
    schedule_chart_range = normalize_text(request.args.get("scheduleChartRange") or "week")
    loan_chart_range = normalize_text(request.args.get("loanChartRange") or "year")
    if metric_range not in {"week", "month", "year"}:
        metric_range = "week"
    if schedule_chart_range not in {"week", "month", "year"}:
        schedule_chart_range = "week"
    if loan_chart_range not in {"week", "month", "year"}:
        loan_chart_range = "year"

    # Beberapa ensure_* memakai koneksi sendiri, jadi jalankan sebelum query utama.
    ensure_agenda_schema()

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        ensure_loan_schema(cursor)
        ensure_activity_log_schema(cursor)
        ensure_streaming_evaluation_schema(cursor)
        conn.commit()

        schedule_total = dashboard_count_schedules_by_range(cursor, metric_range)
        schedule_chart = dashboard_schedule_series(cursor, schedule_chart_range)
        loan_chart = dashboard_loan_series(cursor, loan_chart_range)

        cursor.execute("SELECT COUNT(*) AS total FROM `loan_requests` WHERE `status` = 'pending'")
        loan_pending = int(fetch_scalar_value(cursor.fetchone(), 0) or 0)

        evaluation_pending = dashboard_pending_evaluation_count(cursor)

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM `agendas`
            WHERE LOWER(COALESCE(`status`, 'active')) = 'active'
              AND COALESCE(`end_date`, `start_date`) >= CURDATE()
            """
        )
        agenda_active = int(fetch_scalar_value(cursor.fetchone(), 0) or 0)

        scope_sql, scope_params = activity_scope_where("l")
        cursor.execute(
            f"""
            SELECT l.*
            FROM `activity_logs` l
            WHERE {scope_sql}
            ORDER BY l.`created_at` DESC, l.`id` DESC
            LIMIT 5
            """,
            tuple(scope_params),
        )
        logs = [activity_log_row_to_dict(row) for row in cursor.fetchall() or []]

        return jsonify({
            "success": True,
            "metrics": {
                "schedule": {"range": metric_range, "total": schedule_total},
                "loanPending": loan_pending,
                "evaluationPending": evaluation_pending,
                "agendaActive": agenda_active,
            },
            "scheduleChart": schedule_chart,
            "loanChart": loan_chart,
            "logs": logs,
            "currentUser": current_user_context(),
        })
    finally:
        cursor.close()
        conn.close()


