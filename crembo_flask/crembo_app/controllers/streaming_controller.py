from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Streaming Controller

# Source legacy app.py lines 10007-10025 | routes: /api/streaming/roles
@app.route("/api/streaming/roles", methods=["GET", "POST"])
def manage_streaming_roles():
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == "POST":
            payload = request.json or []
            cursor.execute("DELETE FROM `streaming_roles`")
            for idx, r in enumerate(payload):
                cursor.execute("INSERT INTO `streaming_roles` (role_name, order_index) VALUES (%s, %s)", (r['name'], idx+1))
            conn.commit()
            return jsonify({"success": True})
        
        cursor.execute("SELECT role_name as name FROM `streaming_roles` ORDER BY order_index ASC")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10027-10056 | routes: /api/streaming/config/weekly
@app.route("/api/streaming/config/weekly", methods=["GET", "POST"])
def manage_weekly_config():
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == "POST":
            payload = request.json or {}
            cursor.execute("DELETE FROM `streaming_weekly_config`")
            for day, times in payload.items():
                for t in times:
                    parts = t.split(' - ')
                    jam = parts[0].strip()
                    nama = parts[1].strip() if len(parts) > 1 else "Misa"
                    cursor.execute("INSERT INTO `streaming_weekly_config` (day_name, start_time, mass_name) VALUES (%s, %s, %s)", (day, jam, nama))
            conn.commit()
            return jsonify({"success": True})
        
        cursor.execute("SELECT * FROM `streaming_weekly_config` ORDER BY FIELD(day_name, 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'), start_time ASC")
        rows = cursor.fetchall()
        result = {}
        for r in rows:
            day = r['day_name']
            if day not in result: result[day] = []
            jam_str = format_time_hhmm(r['start_time'])
            result[day].append(f"{jam_str} - {r['mass_name']}")
        return jsonify(result)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10058-10087 | routes: /api/streaming/cancelled
@app.route("/api/streaming/cancelled", methods=["GET", "POST", "DELETE"])
def manage_cancelled_mass():
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == "POST":
            data = request.json
            cursor.execute("INSERT INTO `streaming_cancelled` (mass_date, mass_time) VALUES (%s, %s)", (data['date'], data['time']))
            conn.commit()
            return jsonify({"success": True})
        
        if request.method == "DELETE":
            data = request.json
            # Perbaikan: Langsung bandingkan mass_time tanpa DATE_FORMAT (MySQL otomatis konversi '18:00' ke TIME)
            cursor.execute("DELETE FROM `streaming_cancelled` WHERE mass_date = %s AND mass_time = %s", (data['date'], data['time'][:5]))
            conn.commit()
            return jsonify({"success": True})

        # Perbaikan: Ambil string dengan DATE_FORMAT otomatis dari DB, hindari format GMT 
        cursor.execute("SELECT mass_date as date, DATE_FORMAT(mass_time, '%H:%i') as time FROM `streaming_cancelled` ORDER BY mass_date DESC")
        rows = cursor.fetchall()
        # Flask serializes datetime.date as HTTP-date ("Thu, 01 May ..."), harus dikonversi ke ISO
        for r in rows:
            if hasattr(r['date'], 'isoformat'):
                r['date'] = r['date'].isoformat()
        return jsonify(rows)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10089-10184 | routes: /api/streaming/schedule
@app.route("/api/streaming/schedule", methods=["GET"])
def get_streaming_schedule():
    ensure_streaming_schema()
    ensure_misa_besar_schema()
    month = int(request.args.get("month", datetime.now().month))
    year = int(request.args.get("year", datetime.now().year))
    
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT role_name AS name FROM `streaming_roles` ORDER BY order_index ASC, id ASC")
        roles = [row["name"] for row in (cursor.fetchall() or []) if row.get("name")]

        cursor.execute("SELECT * FROM `streaming_weekly_config` ORDER BY start_time ASC")
        weekly_configs = cursor.fetchall() or []
        
        cursor.execute(
            """
            SELECT DATE_FORMAT(mass_date, '%Y-%m-%d') AS mass_date,
                   DATE_FORMAT(mass_time, '%H:%i') AS mass_time
            FROM `streaming_cancelled`
            WHERE MONTH(mass_date) = %s AND YEAR(mass_date) = %s
            """,
            (month, year),
        )
        cancelled_list = cursor.fetchall() or []
        cancelled_set = {f"{c['mass_date']}_{c['mass_time']}" for c in cancelled_list}

        cursor.execute(
            """
            SELECT DATE_FORMAT(misa_date, '%Y-%m-%d') AS misa_date,
                   DATE_FORMAT(misa_time, '%H:%i') AS misa_time,
                   misa_name
            FROM `misa_besar`
            WHERE status = 'published' AND MONTH(misa_date) = %s AND YEAR(misa_date) = %s
            """,
            (month, year),
        )
        big_mass_rows = cursor.fetchall() or []
        big_mass_conflict_set = {f"{row['misa_date']}_{row['misa_time']}" for row in big_mass_rows}

        cursor.execute(
            """
            SELECT DATE_FORMAT(sa.schedule_date, '%Y-%m-%d') AS schedule_date,
                   DATE_FORMAT(sa.schedule_time, '%H:%i') AS schedule_time,
                   sa.role_name,
                   sa.member_id,
                   COALESCE(a.nama, CONCAT('ID ', sa.member_id)) AS member_name
            FROM `streaming_assignments` sa
            LEFT JOIN `anggota` a ON a.id = sa.member_id
            WHERE MONTH(sa.schedule_date) = %s AND YEAR(sa.schedule_date) = %s
            """,
            (month, year),
        )
        assignment_rows = cursor.fetchall() or []
        assignment_map: dict[tuple[str, str], dict[str, str]] = {}
        assignment_id_map: dict[tuple[str, str], dict[str, str]] = {}
        for row in assignment_rows:
            key = (row["schedule_date"], row["schedule_time"])
            assignment_map.setdefault(key, {})[row["role_name"]] = row.get("member_name") or ""
            assignment_id_map.setdefault(key, {})[row["role_name"]] = str(row.get("member_id") or "")
        
        day_map = {0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis', 4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'}
        
        schedule = []
        num_days = calendar.monthrange(year, month)[1]
        
        for day in range(1, num_days + 1):
            date_obj = datetime(year, month, day)
            day_name = day_map[date_obj.weekday()]
            date_str = date_obj.strftime("%Y-%m-%d")
            
            for cfg in weekly_configs:
                if cfg['day_name'] == day_name:
                    jam_str = format_time_hhmm(cfg['start_time'])
                    key = f"{date_str}_{jam_str}"
                    if key in cancelled_set or key in big_mass_conflict_set:
                        continue
                    assignment_key = (date_str, jam_str)
                    assignments = {role_name: assignment_map.get(assignment_key, {}).get(role_name, "") for role_name in roles}
                    assignment_ids = {role_name: assignment_id_map.get(assignment_key, {}).get(role_name, "") for role_name in roles}
                    schedule.append({
                        "date": date_str,
                        "time": jam_str,
                        "massName": cfg['mass_name'],
                        "dayName": day_name,
                        "roles": roles,
                        "assignments": assignments,
                        "assignmentIds": assignment_ids,
                    })
        
        schedule.sort(key=lambda x: (x['date'], x['time']))
        return jsonify({"success": True, "schedule": schedule, "roles": roles})
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10186-10196 | routes: /api/streaming/active-members
@app.route("/api/streaming/active-members", methods=["GET"])
def get_active_members():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nama as name, role FROM anggota WHERE status_akun = 'aktif' ORDER BY nama ASC")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10198-10208 | routes: /api/streaming/assignments
@app.route("/api/streaming/assignments", methods=["GET"])
def get_current_assignments():
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT DATE_FORMAT(schedule_date, '%Y-%m-%d') as schedule_date, DATE_FORMAT(schedule_time, '%H:%i') as schedule_time, role_name, member_id FROM streaming_assignments")
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10210-10269 | routes: /api/streaming/assignments/save
@app.route("/api/streaming/assignments/save", methods=["POST"])
def save_assignments():
    ensure_streaming_schema()
    payload = request.json or [] 
    
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute("SELECT schedule_date, schedule_time, role_name, member_id FROM streaming_assignments")
        existing_assignments = {}
        for r in cursor.fetchall():
            t_str = format_time_hhmm(r['schedule_time'])
            d_str = str(r['schedule_date'])
            existing_assignments[(d_str, t_str, r['role_name'])] = str(r['member_id'])
            
        ensure_notifications_schema()
        DAYS_INDO = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        
        for item in payload:
            d_str = item.get('date')
            t_str = item.get('time')
            r_str = item.get('role')
            m_id = str(item.get('memberId')) if item.get('memberId') else None
            m_name = item.get('massName') or 'Misa'
            
            key = (d_str, t_str, r_str)
            
            if m_id:
                cursor.execute("""
                    INSERT INTO streaming_assignments (schedule_date, schedule_time, role_name, member_id, request_source, created_at)
                    VALUES (%s, %s, %s, %s, 'admin', CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        created_at = IF(member_id <> VALUES(member_id), CURRENT_TIMESTAMP, created_at),
                        request_source = IF(member_id <> VALUES(member_id), 'admin', request_source),
                        member_id = VALUES(member_id)
                """, (d_str, t_str, r_str, m_id))
                
                if existing_assignments.get(key) != m_id:
                    date_obj = datetime.strptime(d_str, "%Y-%m-%d")
                    day_name = DAYS_INDO[date_obj.weekday()]
                    date_formatted = date_obj.strftime("%d/%m/%Y")
                    
                    title = f"Tugas Baru: {r_str}"
                    body = f"Anda ditugaskan sebagai <b>{r_str}</b> untuk <b>{m_name}</b> pada hari {day_name}, {date_formatted} jam {t_str} WIB."
                    
                    create_notification(cursor, "tugas", title, body, "/jadwal-tugas-misa-anggota.html", {"target_user_id": m_id}, target_role=None)
            else:
                cursor.execute("""
                    DELETE FROM streaming_assignments 
                    WHERE schedule_date = %s AND schedule_time = %s AND role_name = %s
                """, (d_str, t_str, r_str))
        
        conn.commit()
        return jsonify({"success": True, "message": "Penugasan berhasil disimpan"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10272-10352 | routes: /api/misa-besar/public
@app.route("/api/misa-besar/public", methods=["GET"])
def api_misa_besar_public():
    """Daftar Misa Besar untuk halaman Jadwal Streaming anggota.

    Endpoint ini sengaja hanya mengembalikan Misa Besar berstatus published,
    sehingga anggota biasa tidak menerima data draft. Response juga menyertakan
    penanda jika user sesi saat ini sedang bertugas pada misa tersebut.
    """
    ensure_misa_besar_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        month = parse_optional_int(request.args.get("month"))
        year = parse_optional_int(request.args.get("year"))
        current_user_id = normalize_text(session.get("user_id"))

        query = """
            SELECT id,
                   misa_name AS misaName,
                   DATE_FORMAT(misa_date, '%Y-%m-%d') AS misaDate,
                   DATE_FORMAT(misa_time, '%H:%i') AS misaTime,
                   misa_note AS misaNote,
                   allow_member_request AS allowMemberRequest,
                   status,
                   created_at AS updatedAt
            FROM misa_besar
            WHERE status = 'published'
        """
        params: list[object] = []
        if month:
            query += " AND MONTH(misa_date) = %s"
            params.append(month)
        if year:
            query += " AND YEAR(misa_date) = %s"
            params.append(year)
        query += " ORDER BY misa_date ASC, misa_time ASC, id ASC"

        cursor.execute(query, tuple(params))
        events = cursor.fetchall() or []

        for ev in events:
            cursor.execute(
                """
                SELECT id, role_name AS role, required_count AS count
                FROM misa_besar_names
                WHERE misa_id = %s
                ORDER BY id ASC
                """,
                (ev["id"],),
            )
            roles = cursor.fetchall() or []
            current_user_roles: list[str] = []
            for role in roles:
                cursor.execute(
                    """
                    SELECT a.id, a.nama AS name
                    FROM misa_besar_assignments bma
                    JOIN anggota a ON bma.member_id = a.id
                    WHERE bma.role_id = %s
                    ORDER BY a.nama ASC
                    """,
                    (role["id"],),
                )
                members_data = cursor.fetchall() or []
                role["members"] = [str(member.get("id")) for member in members_data if member.get("id") is not None]
                role["memberIds"] = role["members"]
                role["memberNames"] = [normalize_text(member.get("name")) for member in members_data if normalize_text(member.get("name"))]
                role["count"] = parse_required_int(role.get("count"), 1)
                if current_user_id and current_user_id in set(role["memberIds"]):
                    current_user_roles.append(normalize_text(role.get("role")) or "Role")

            ev["allowMemberRequest"] = bool(ev.get("allowMemberRequest"))
            ev["status"] = "published"
            ev["roles"] = roles
            ev["currentUserRoles"] = current_user_roles
            ev["isCurrentUserAssigned"] = bool(current_user_roles)

        return jsonify({"success": True, "items": events})
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10355-10421 | routes: /api/misa-besar
@app.route("/api/misa-besar", methods=["GET", "POST"])
def api_misa_besar():
    ensure_misa_besar_schema()
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        if request.method == "POST":
            data = request.json
            allow_req = 1 if data.get('allowMemberRequest') else 0
            cursor.execute("""
                INSERT INTO misa_besar (misa_name, misa_date, misa_time, misa_note, allow_member_request, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data['misaName'], data['misaDate'], data['misaTime'], data.get('misaNote',''), allow_req, data['status']))
            misa_id = cursor.lastrowid
            
            for r in data.get('roles', []):
                cursor.execute("INSERT INTO misa_besar_names (misa_id, role_name, required_count) VALUES (%s, %s, %s)",
                               (misa_id, r['role'], r['count']))
                role_id = cursor.lastrowid
                
                # Simpan list member ID langsung (yang tidak kosong)
                for m_id in r.get('members', []):
                    if str(m_id).strip():
                        cursor.execute("INSERT IGNORE INTO misa_besar_assignments (role_id, member_id) VALUES (%s, %s)", (role_id, m_id))

            removed_regular_assignments = clear_streaming_assignments_for_published_misa_besar(
                cursor, data.get('misaDate'), data.get('misaTime'), data.get('status')
            )
            new_snapshot = fetch_misa_besar_notification_snapshot(cursor, misa_id)
            notified_count = notify_misa_besar_assignment_changes(cursor, None, new_snapshot)
            open_role_notified_count = notify_misa_besar_open_roles_if_newly_published(cursor, None, new_snapshot)
            
            conn.commit()
            return jsonify({
                "success": True,
                "id": misa_id,
                "notifiedCount": notified_count,
                "openRoleNotifiedCount": open_role_notified_count,
                "removedRegularAssignments": removed_regular_assignments,
            })

        # GET DATA
        cursor.execute("SELECT id, misa_name as misaName, DATE_FORMAT(misa_date, '%Y-%m-%d') as misaDate, DATE_FORMAT(misa_time, '%H:%i') as misaTime, misa_note as misaNote, allow_member_request as allowMemberRequest, status, created_at as updatedAt FROM misa_besar ORDER BY misa_date DESC")
        events = cursor.fetchall()
        
        for ev in events:
            cursor.execute("SELECT id, role_name as role, required_count as count FROM misa_besar_names WHERE misa_id = %s", (ev['id'],))
            roles = cursor.fetchall()
            for r in roles:
                cursor.execute("""
                    SELECT a.id, a.nama as name 
                    FROM misa_besar_assignments bma 
                    JOIN anggota a ON bma.member_id = a.id 
                    WHERE bma.role_id = %s
                """, (r['id'],))
                members_data = cursor.fetchall()
                # Sesuaikan response dengan format Frontend
                r['members'] = [str(m['id']) for m in members_data]
                r['memberNames'] = [m['name'] for m in members_data]
                r['multi'] = r['count'] > 1
            ev['roles'] = roles
            
        return jsonify(events)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10423-10476 | routes: /api/misa-besar/<int:misa_id>
@app.route("/api/misa-besar/<int:misa_id>", methods=["PUT", "DELETE"])
def api_misa_besar_detail(misa_id):
    ensure_misa_besar_schema()
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        if request.method == "DELETE":
            cursor.execute("DELETE FROM misa_besar WHERE id = %s", (misa_id,))
            conn.commit()
            return jsonify({"success": True})
        
        if request.method == "PUT":
            data = request.json
            old_snapshot = fetch_misa_besar_notification_snapshot(cursor, misa_id)
            allow_req = 1 if data.get('allowMemberRequest') else 0
            
            # Update header Misa
            cursor.execute("""
                UPDATE misa_besar SET misa_name=%s, misa_date=%s, misa_time=%s, misa_note=%s, allow_member_request=%s, status=%s
                WHERE id=%s
            """, (data['misaName'], data['misaDate'], data['misaTime'], data.get('misaNote',''), allow_req, data['status'], misa_id))
            
            # Reset roles untuk mempermudah handling list members tanpa error FK constraint
            # Karena tabel misa_besar_names punya constraint ON DELETE CASCADE, assignments otomatis terhapus
            cursor.execute("DELETE FROM misa_besar_names WHERE misa_id = %s", (misa_id,))
            
            # Insert Ulang Roles dan Assignments
            for r in data.get('roles', []):
                cursor.execute("INSERT INTO misa_besar_names (misa_id, role_name, required_count) VALUES (%s, %s, %s)",
                               (misa_id, r['role'], r['count']))
                role_id = cursor.lastrowid
                
                for m_id in r.get('members', []):
                    if str(m_id).strip():
                        cursor.execute("INSERT IGNORE INTO misa_besar_assignments (role_id, member_id) VALUES (%s, %s)", (role_id, m_id))

            removed_regular_assignments = clear_streaming_assignments_for_published_misa_besar(
                cursor, data.get('misaDate'), data.get('misaTime'), data.get('status')
            )
            new_snapshot = fetch_misa_besar_notification_snapshot(cursor, misa_id)
            notified_count = notify_misa_besar_assignment_changes(cursor, old_snapshot, new_snapshot)
            open_role_notified_count = notify_misa_besar_open_roles_if_newly_published(cursor, old_snapshot, new_snapshot)
            
            conn.commit()
            return jsonify({
                "success": True,
                "notifiedCount": notified_count,
                "openRoleNotifiedCount": open_role_notified_count,
                "removedRegularAssignments": removed_regular_assignments,
            })
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10478-10523 | routes: /api/misa-besar/<int:misa_id>/status
@app.route("/api/misa-besar/<int:misa_id>/status", methods=["PUT"])
def api_misa_besar_status(misa_id):
    """Endpoint khusus untuk mengubah status ke Draft atau Published dengan cepat"""
    ensure_misa_besar_schema()
    ensure_streaming_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        data = request.json or {}
        old_snapshot = fetch_misa_besar_notification_snapshot(cursor, misa_id)
        new_status = normalize_misa_besar_status(data.get('status', 'draft'))
        
        cursor.execute("UPDATE misa_besar SET status = %s WHERE id = %s", (new_status, misa_id))
        removed_regular_assignments = 0
        if new_status == "published":
            cursor.execute(
                """
                SELECT DATE_FORMAT(misa_date, '%Y-%m-%d') AS misaDate,
                       DATE_FORMAT(misa_time, '%H:%i') AS misaTime
                FROM misa_besar
                WHERE id = %s
                LIMIT 1
                """,
                (misa_id,),
            )
            event_row = cursor.fetchone()
            if event_row:
                removed_regular_assignments = clear_streaming_assignments_for_published_misa_besar(
                    cursor, event_row.get("misaDate"), event_row.get("misaTime"), new_status
                )
        new_snapshot = fetch_misa_besar_notification_snapshot(cursor, misa_id)
        notified_count = notify_misa_besar_assignment_changes(cursor, old_snapshot, new_snapshot)
        open_role_notified_count = notify_misa_besar_open_roles_if_newly_published(cursor, old_snapshot, new_snapshot)
        conn.commit()
        return jsonify({
            "success": True,
            "notifiedCount": notified_count,
            "openRoleNotifiedCount": open_role_notified_count,
            "removedRegularAssignments": removed_regular_assignments,
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10525-10559 | routes: /api/misa-besar/assign
@app.route("/api/misa-besar/assign", methods=["POST"])
def api_misa_besar_assign():
    ensure_misa_besar_schema()
    ensure_streaming_schema()
    data = request.json or {}
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        old_snapshot = fetch_misa_besar_notification_snapshot(cursor, int(data['misaId']))
        cursor.execute("""
            SELECT n.role_name FROM misa_besar_assignments a 
            JOIN misa_besar_names n ON a.role_id = n.id 
            WHERE n.misa_id = %s AND a.member_id = %s
        """, (data['misaId'], data['memberId']))
        existing = cursor.fetchone()
        if existing:
            return jsonify({"success": False, "message": f"Gagal: Orang tersebut sudah bertugas sebagai {existing['role_name']} di jadwal ini."}), 400

        cursor.execute("INSERT INTO misa_besar_assignments (role_id, member_id) VALUES (%s, %s)", (data['roleId'], data['memberId']))
        removed_regular_assignments = 0
        new_snapshot = fetch_misa_besar_notification_snapshot(cursor, int(data['misaId']))
        if new_snapshot:
            removed_regular_assignments = clear_streaming_assignments_for_published_misa_besar(
                cursor, new_snapshot.get("misaDate"), new_snapshot.get("misaTime"), new_snapshot.get("status")
            )
        notified_count = notify_misa_besar_assignment_changes(cursor, old_snapshot, new_snapshot)
        conn.commit()
        return jsonify({
            "success": True,
            "notifiedCount": notified_count,
            "removedRegularAssignments": removed_regular_assignments,
        })
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 10561-10572 | routes: /api/misa-besar/unassign
@app.route("/api/misa-besar/unassign", methods=["POST"])
def api_misa_besar_unassign():
    data = request.json
    conn = mysql_connection()
    cursor = conn.cursor(buffered=True)
    try:
        cursor.execute("DELETE FROM misa_besar_assignments WHERE role_id = %s AND member_id = %s", (data['roleId'], data['memberId']))
        conn.commit()
        return jsonify({"success": True})
    finally:
        cursor.close()
        conn.close()


