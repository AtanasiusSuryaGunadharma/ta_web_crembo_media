"""Page Controller.

File ini berisi route/controller yang dipisahkan dari app.py server lama.
Logika helper tetap dipanggil dari crembo_app.services.core agar perilaku produksi tetap sama.
"""

from crembo_app.services import core as _core

globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})


# Route dari app.py server: /favicon.ico
@app.route("/favicon.ico")
def favicon():
    if PUBLIC_FAVICON_PATH.is_file():
        return send_file(PUBLIC_FAVICON_PATH, mimetype="image/png")
    abort(404)


# Route dari app.py server: /
@app.route("/")
def index():
    home_page_data = build_home_page_data()
    return render_template("home.html", home_page_data=home_page_data, current_user=current_user_context())


# Route dari app.py server: /dashboard
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") == "user":
        return redirect(url_for("dashboard_anggota"))
    return render_template("dashboard.html", current_user=current_user_context())


# Route dari app.py server: /dashboard-anggota
@app.route("/dashboard-anggota")
def dashboard_anggota():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") != "user":
        return redirect(url_for("dashboard"))
    return render_template("dashboard-anggota.html", current_user=current_user_context())


# Route dari app.py server: /profil
@app.route("/profil")
def profil():
    profile_slug = (request.args.get("profil") or "").strip()
    if profile_slug or not session.get("logged_in"):
        return render_template("profil.html", current_user=current_user_context())
    if (session.get("role") or "user") == "user":
        return render_template("profil-anggota.html", current_user=current_user_context())
    return render_template("profil-admin.html", current_user=current_user_context())


# Route dari app.py server: /unduh-sertifikat-anggota, /unduh-sertifikat-anggota.html
@app.route("/unduh-sertifikat-anggota")
@app.route("/unduh-sertifikat-anggota.html")
def legacy_certificate_page():
    return redirect(url_for("render_mockup_page", page="sertifikat-anggota"), code=301)


# Route dari app.py server: /<path:page>
@app.route("/<path:page>")
def render_mockup_page(page: str):
    if page in {"favicon.ico"}:
        abort(404)

    if page.endswith(".html"):
        clean_page = page[:-5]
        if clean_page == "home":
            return redirect(url_for("render_mockup_page", page=""), code=301)
        return redirect(url_for("render_mockup_page", page=clean_page), code=301)

    asset_path = FRONTEND_DIR / page
    if asset_path.is_file() and not page.endswith(".html"):
        return send_from_directory(FRONTEND_DIR, page)

    candidate = page
    if not candidate.endswith(".html"):
        candidate = f"{candidate}.html"

    if candidate == "login.html":
        session.clear()

    # Role-aware dashboard guard for direct .html URLs.
    # Without this, /dashboard.html is served by the generic template router
    # and user/anggota accounts can accidentally see the admin dashboard.
    if candidate in {"dashboard.html", "dashboard-anggota.html"}:
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        current_role = session.get("role") or "user"
        if candidate == "dashboard.html" and current_role == "user":
            return redirect(url_for("dashboard_anggota"))
        if candidate == "dashboard-anggota.html" and current_role != "user":
            return redirect(url_for("dashboard"))

    if candidate in {"log-aktivitas.html", "log-aktivitas-saya.html"}:
        if not session.get("logged_in"):
            return redirect(url_for("login"))

    if candidate == "kelola-data-admin.html":
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        if normalize_role_value(session.get("role") or "") != "super_admin":
            abort(403)

    module_key = ADMIN_PAGE_MODULE_MAP.get(candidate)
    if module_key:
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        if not admin_has_module_access(module_key):
            abort(403)

    if session.get("logged_in") and current_member_is_inactive() and not is_inactive_member_page_allowed(candidate):
        return redirect(url_for("dashboard_anggota", inactive="1"))

    if template_exists(candidate):
        extra_context = {"current_user": current_user_context()}
        if candidate == "home.html":
            extra_context["home_page_data"] = build_home_page_data()
        if candidate == "manajemen-anggota.html":
            extra_context["member_rows"] = read_members_for_admin() if session.get("logged_in") else []
        return render_template(candidate, **extra_context)

    abort(404)


# Route dari app.py server: /pengumuman
@app.route("/pengumuman")
def public_news_page():
    return render_public_page("pengumuman.html")


# Route dari app.py server: /pengumuman/kategori/<category_slug>
@app.route("/pengumuman/kategori/<category_slug>")
def public_news_category_page(category_slug):
    # Menyertakan category_slug jika dibutuhkan oleh Jinja, walau JS di FE juga bisa parsing URL
    return render_public_page("pengumuman.html", category_slug=category_slug)


# Route dari app.py server: /pengumuman/<news_id>
@app.route("/pengumuman/<news_id>")
def public_news_detail_page(news_id):
    return render_public_page("pengumuman-detail.html", news_id=news_id)


# Route dari app.py server: /agenda
@app.route("/agenda")
def public_agenda_page():
    return render_public_page("agenda.html")


# Route dari app.py server: /agenda/<agenda_id>
@app.route("/agenda/<agenda_id>")
def public_agenda_detail_page(agenda_id):
    # Mengirim parameter agenda_id ke template sehingga JS di client bisa membaca ID yang akan di load
    return render_public_page("agenda-detail.html", agenda_id=agenda_id)


# Route dari app.py server: /form-pendaftaran
@app.route("/form-pendaftaran")
def public_registration_forms_page():
    return render_public_page("form-pendaftaran.html")


# Route dari app.py server: /form-pendaftaran/<form_id>
@app.route("/form-pendaftaran/<form_id>")
def public_registration_form_detail_page(form_id):
    return render_public_page("form-pendaftaran-detail.html", form_id=form_id)


# Route dari app.py server: /uploads/<path:filename>
@app.route("/uploads/<path:filename>")
def serve_uploaded_file(filename: str):
    upload_folder = ensure_upload_folder()
    return send_from_directory(upload_folder, filename)


# Route dari app.py server: /api/upload_image
@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    ensure_auth_schema()
    incoming_files = request.files.getlist("files")
    if not incoming_files:
        single_file = request.files.get("file")
        incoming_files = [single_file] if single_file and single_file.filename else []

    if not incoming_files:
        return jsonify({"success": False, "error": "No selected file"}), 400

    saved_files: list[dict[str, object]] = []
    try:
        for file in incoming_files:
            if not file or not file.filename:
                continue
            saved_files.append(save_uploaded_attachment(file))
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    if not saved_files:
        return jsonify({"success": False, "error": "No selected file"}), 400

    return jsonify({
        "success": True,
        "files": saved_files,
        "url": saved_files[0]["url"],
    })


# Route dari app.py server: /api/gmaps
@app.route("/api/gmaps", methods=["GET"])
def api_get_gmaps():
    return jsonify({"url": load_gmaps_url()})


# Route dari app.py server: /api/gmaps
@app.route("/api/gmaps", methods=["POST"])
def api_set_gmaps():
    ensure_auth_schema()
    url = request.json.get("url", "")
    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE `google_maps_embed` SET `url` = %s WHERE `id` = 1", (url,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# Route dari app.py server: /api/search
@app.route("/api/search", methods=["GET"])
def api_search():
    """
    Global search endpoint. Mencari di: pengumuman (news), agenda, jadwal streaming, profil.
    Query params:
        q      : kata kunci pencarian
        type   : filter tipe (Pengumuman | Agenda | Jadwal | Profil) â€” kosong = semua
        sort   : newest | oldest | az | za
        page   : halaman (mulai 1)
        per_page: jumlah per halaman (default 10)
    """
    query   = (request.args.get("q") or "").strip().lower()
    ftype   = (request.args.get("type") or "").strip()
    sort    = (request.args.get("sort") or "newest").strip()
    page    = max(1, int(request.args.get("page") or 1))
    per_page = min(50, max(1, int(request.args.get("per_page") or 10)))

    results = []

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # â”€â”€ 1. Pengumuman (news) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if not ftype or ftype == "Pengumuman":
            try:
                cursor.execute("""
                    SELECT id, title, summary, content, thumbnails, published_at, created_at, status
                    FROM `news`
                    WHERE status = 'published'
                    ORDER BY published_at DESC, created_at DESC
                """)
                for row in (cursor.fetchall() or []):
                    title_val   = (row.get("title") or "")
                    summary_val = (row.get("summary") or "")
                    content_raw = re.sub(r'<[^>]+>', ' ', row.get("content") or "")
                    haystack    = (title_val + " " + summary_val + " " + content_raw).lower()
                    if query and query not in haystack:
                        continue
                    snippet = (summary_val or content_raw[:200]).strip()
                    date_val = row.get("published_at") or row.get("created_at")
                    date_str = date_val.strftime("%d %b %Y") if date_val else ""
                    # Ambil URL thumbnail pertama dari JSON
                    thumb_url = ""
                    try:
                        thumbs = json.loads(row.get("thumbnails") or "[]")
                        if thumbs and isinstance(thumbs, list) and isinstance(thumbs[0], dict):
                            thumb_url = thumbs[0].get("url") or ""
                    except Exception:
                        pass
                    results.append({
                        "type":    "Pengumuman",
                        "title":   title_val,
                        "snippet": snippet[:220] if snippet else "",
                        "date":    date_str,
                        "date_ts": date_val.timestamp() if date_val else 0,
                        "url":     f"/pengumuman/{row['id']}",
                        "thumb":   thumb_url,
                    })
            except Exception as e:
                pass  # Tabel belum ada atau error, skip

        # â”€â”€ 2. Agenda â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if not ftype or ftype == "Agenda":
            try:
                cursor.execute("""
                    SELECT id, title, description, start_date, location, status, image_url
                    FROM `agendas`
                    WHERE status = 'active'
                    ORDER BY start_date DESC
                """)
                for row in (cursor.fetchall() or []):
                    title_val   = (row.get("title") or "")
                    desc_val    = re.sub(r'<[^>]+>', ' ', row.get("description") or "")
                    loc_val     = (row.get("location") or "")
                    haystack    = (title_val + " " + desc_val + " " + loc_val).lower()
                    if query and query not in haystack:
                        continue
                    date_val = row.get("start_date")
                    date_str = date_val.strftime("%d %b %Y") if hasattr(date_val, "strftime") else str(date_val or "")
                    import datetime as _dt
                    date_ts = _dt.datetime.combine(date_val, _dt.time.min).timestamp() if isinstance(date_val, _dt.date) else 0
                    snippet = desc_val[:220].strip() if desc_val.strip() else loc_val
                    results.append({
                        "type":    "Agenda",
                        "title":   title_val,
                        "snippet": snippet,
                        "date":    date_str,
                        "date_ts": date_ts,
                        "url":     f"/agenda/{row['id']}",
                        "thumb":   row.get("image_url") or "",
                    })
            except Exception:
                pass

        # â”€â”€ 3. Form Pendaftaran â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if not ftype or ftype == "FormPendaftaran":
            try:
                cursor.execute("""
                    SELECT id, title, description, visibility, image_url, updated_at, created_at
                    FROM `registration_forms`
                    WHERE visibility != 'draft'
                    ORDER BY updated_at DESC, created_at DESC
                """)
                for row in (cursor.fetchall() or []):
                    title_val = (row.get("title") or "")
                    desc_raw  = re.sub(r'<[^>]+>', ' ', row.get("description") or "")
                    haystack  = (title_val + " " + desc_raw).lower()
                    if query and query not in haystack:
                        continue
                    upd = row.get("updated_at") or row.get("created_at")
                    date_ts = upd.timestamp() if hasattr(upd, "timestamp") else 0
                    date_str = upd.strftime("%d %b %Y") if upd else ""
                    results.append({
                        "type":    "FormPendaftaran",
                        "title":   title_val,
                        "snippet": desc_raw[:220].strip(),
                        "date":    date_str,
                        "date_ts": date_ts,
                        "url":     f"/form-pendaftaran-detail.html?id={row['id']}",
                        "thumb":   row.get("image_url") or "",
                    })
            except Exception:
                pass

        # â”€â”€ 4. Profil Organisasi â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if not ftype or ftype == "Profil":
            try:
                cursor.execute("""
                    SELECT id, title, description, updated_at
                    FROM `organization_profiles`
                    WHERE is_visible = 1
                    ORDER BY order_index ASC
                """)
                for row in (cursor.fetchall() or []):
                    title_val = (row.get("title") or "")
                    desc_raw  = re.sub(r'<[^>]+>', ' ', row.get("description") or "")
                    haystack  = (title_val + " " + desc_raw).lower()
                    if query and query not in haystack:
                        continue
                    upd = row.get("updated_at")
                    date_ts = upd.timestamp() if hasattr(upd, "timestamp") else 0
                    slug_id = str(row.get("id") or "").replace("profile-", "").lower()
                    safe_id = re.sub(r'[^a-z0-9\-]', '-', title_val.lower())
                    results.append({
                        "type":    "Profil",
                        "title":   title_val,
                        "snippet": desc_raw[:220].strip(),
                        "date":    "â€“",
                        "date_ts": date_ts,
                        "url":     f"/profil.html?profil={row['id']}",
                        "thumb":   "",
                    })
            except Exception:
                pass

    finally:
        cursor.close()
        conn.close()

    # â”€â”€ Sorting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if sort == "az":
        results.sort(key=lambda r: (r["title"] or "").lower())
    elif sort == "za":
        results.sort(key=lambda r: (r["title"] or "").lower(), reverse=True)
    elif sort == "oldest":
        results.sort(key=lambda r: r["date_ts"])
    else:  # newest (default)
        results.sort(key=lambda r: r["date_ts"], reverse=True)

    # Hitung count per tipe (SEBELUM pagination)
    counts = {"Pengumuman": 0, "Agenda": 0, "FormPendaftaran": 0, "Profil": 0}
    for r in results:
        t = r.get("type", "")
        if t in counts:
            counts[t] += 1
    total = len(results)

    # â”€â”€ Pagination â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    paged = results[start: start + per_page]

    # Bersihkan date_ts dari output
    for r in paged:
        r.pop("date_ts", None)

    return jsonify({
        "query":       (request.args.get("q") or "").strip(),
        "type":        ftype,
        "sort":        sort,
        "page":        page,
        "per_page":    per_page,
        "total":       total,
        "total_pages": total_pages,
        "counts":      counts,
        "results":     paged,
    })


# Route dari app.py server: /api/riwayat-tugas-saya
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


# Route dari app.py server: /api/cancel-tugas/me
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


# Route dari app.py server: /api/cancel-tugas/active
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


# Route dari app.py server: /api/cancel-tugas/history
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


# Route dari app.py server: /api/cancel-tugas/cancel
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

