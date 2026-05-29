from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Content Controller

# Source legacy app.py lines 7593-7609 | routes: /api/tentang/config
@app.route("/api/tentang/config", methods=["GET"])
def get_tentang_config():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `tentang_crembo_config` LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return jsonify({
            "description": row["description"],
            "buttonText": row["button_text"],
            "buttonLink": row["button_link"],
            "autoSeconds": row["auto_seconds"]
        })
    return jsonify({})


# Source legacy app.py lines 7611-7640 | routes: /api/tentang/config
@app.route("/api/tentang/config", methods=["POST"])
def set_tentang_config():
    ensure_auth_schema()
    data = request.json or {}
    description = data.get("description", "")
    button_text = data.get("buttonText", "")
    button_link = data.get("buttonLink", "")
    try:
        auto_seconds = int(data.get("autoSeconds", 5))
    except (ValueError, TypeError):
        auto_seconds = 5

    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO `tentang_crembo_config` (`id`, `description`, `button_text`, `button_link`, `auto_seconds`)
        VALUES (1, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          `description` = VALUES(`description`),
          `button_text` = VALUES(`button_text`),
          `button_link` = VALUES(`button_link`),
          `auto_seconds` = VALUES(`auto_seconds`)
        """,
        (description, button_text, button_link, auto_seconds),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})


# Source legacy app.py lines 7642-7661 | routes: /api/tentang/media
@app.route("/api/tentang/media", methods=["GET"])
def get_tentang_media():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT `id`, `type`, `url`, `order_index`, `is_visible` FROM `tentang_crembo_media` ORDER BY `order_index` ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "type": r["type"],
            "url": r["url"],
            "order": r["order_index"],
            "active": bool(r["is_visible"])
        })
    return jsonify(out)


# Source legacy app.py lines 7663-7692 | routes: /api/tentang/media/sync
@app.route("/api/tentang/media/sync", methods=["POST"])
def sync_tentang_media():
    ensure_auth_schema()
    payload = request.json
    if not isinstance(payload, list):
        return jsonify({"success": False, "error": "Invalid payload format"}), 400
        
    conn = mysql_connection()
    cursor = conn.cursor()
    
    # Simple sync: delete all and insert fresh order
    cursor.execute("DELETE FROM `tentang_crembo_media`")
    
    for item in payload:
        item_id = item.get("id", "")
        item_type = item.get("type", "image")
        url = item.get("url", "")
        order = int(item.get("order", 0))
        active = 1 if item.get("active", True) else 0
        
        if item_id:
            cursor.execute("""
                INSERT INTO `tentang_crembo_media` (`id`, `type`, `url`, `order_index`, `is_visible`)
                VALUES (%s, %s, %s, %s, %s)
            """, (item_id, item_type, url, order, active))
            
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "count": len(payload)})


# Source legacy app.py lines 7695-7698 | routes: /api/instagram/posts
@app.route("/api/instagram/posts", methods=["GET"])
def get_instagram_posts():
    ensure_auth_schema()
    return jsonify({"ok": True, "posts": load_instagram_posts_from_db(limit=None, active_only=False)})


# Source legacy app.py lines 7701-7709 | routes: /api/instagram/posts/sync
@app.route("/api/instagram/posts/sync", methods=["POST"])
def sync_instagram_posts():
    ensure_auth_schema()
    payload = request.get_json(silent=True)
    if not isinstance(payload, list):
        return jsonify({"ok": False, "message": "Invalid payload format"}), 400

    saved_count = save_instagram_posts_payload(payload)
    return jsonify({"ok": True, "count": saved_count})


# Source legacy app.py lines 7719-7746 | routes: /api/upload_image
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


# Source legacy app.py lines 7748-7766 | routes: /api/youtube
@app.route("/api/youtube", methods=["GET"])
def get_youtube():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `youtube_embeds` ORDER BY `order_index` ASC")
    rows = cursor.fetchall() or []
    conn.close()
    return jsonify([
        {
            "id": r["id"],
            "url": r["url"],
            "type": normalize_youtube_embed_type(r.get("embed_type")),
            "title": r.get("title") or "",
            "order": r["order_index"],
            "active": bool(r["is_visible"]),
        }
        for r in rows
    ])


# Source legacy app.py lines 7768-7812 | routes: /api/youtube/sync
@app.route("/api/youtube/sync", methods=["POST"])
def sync_youtube():
    ensure_auth_schema()
    payload = request.json or []
    if not isinstance(payload, list):
        return jsonify({"success": False, "error": "Payload YouTube tidak valid."}), 400

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        ensure_column(cursor, "youtube_embeds", "embed_type", "`embed_type` varchar(30) NOT NULL DEFAULT 'video'")
        ensure_column(cursor, "youtube_embeds", "title", "`title` varchar(255) DEFAULT NULL")
        try:
            cursor.execute("ALTER TABLE `youtube_embeds` MODIFY COLUMN `url` text NOT NULL")
        except Exception:
            pass

        cursor.execute("DELETE FROM `youtube_embeds`")
        for idx, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                continue
            item_id = normalize_text(item.get("id")) or f"yt-{uuid.uuid4().hex[:12]}"
            item_url = normalize_text(item.get("url"))
            if not item_url:
                continue
            item_type = normalize_youtube_embed_type(item.get("type") or item.get("embed_type"))
            item_title = normalize_text(item.get("title"))[:255]
            item_order = parse_required_int(item.get("order"), idx)
            item_active = 1 if item.get("active", True) else 0
            cursor.execute(
                """
                INSERT INTO `youtube_embeds`
                (`id`, `url`, `embed_type`, `title`, `order_index`, `is_visible`)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (item_id, item_url, item_type, item_title, item_order, item_active),
            )
        conn.commit()
        return jsonify({"success": True})
    except Exception as exc:
        conn.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 7814-7816 | routes: /api/gmaps
@app.route("/api/gmaps", methods=["GET"])
def api_get_gmaps():
    return jsonify({"url": load_gmaps_url()})


# Source legacy app.py lines 7818-7827 | routes: /api/gmaps
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


# Source legacy app.py lines 7829-7847 | routes: /api/carousel
@app.route("/api/carousel", methods=["GET"])
def get_carousel():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `carousel_slides` ORDER BY `order_index` ASC")
    rows = cursor.fetchall() or []
    conn.close()
    return jsonify([{
        "id": r["id"],
        "title": r["title"],
        "slug": r["slug"],
        "description": r["description"],
        "buttonText": r["button_text"],
        "link": r["button_link"],
        "backgroundImage": r["background_image"],
        "order": r["order_index"],
        "active": bool(r["is_visible"])
    } for r in rows])


# Source legacy app.py lines 7849-7868 | routes: /api/carousel/sync
@app.route("/api/carousel/sync", methods=["POST"])
def sync_carousel():
    ensure_auth_schema()
    payload = request.json
    conn = mysql_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM `carousel_slides`")
    for item in payload:
        cursor.execute("""
            INSERT INTO `carousel_slides` 
            (`id`, `title`, `slug`, `description`, `button_text`, `button_link`, `background_image`, `order_index`, `is_visible`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            item.get("id"), item.get("title"), item.get("slug"), item.get("description"),
            item.get("buttonText"), item.get("link"), item.get("backgroundImage"),
            item.get("order"), 1 if item.get("active") else 0
        ))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# Source legacy app.py lines 8641-8838 | routes: /api/search
@app.route("/api/search", methods=["GET"])
def api_search():
    """
    Global search endpoint. Mencari di: pengumuman (news), agenda, jadwal streaming, profil.
    Query params:
        q      : kata kunci pencarian
        type   : filter tipe (Pengumuman | Agenda | Jadwal | Profil) — kosong = semua
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
        # ── 1. Pengumuman (news) ─────────────────────────────────────────────────
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

        # ── 2. Agenda ────────────────────────────────────────────────────────────
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

        # ── 3. Form Pendaftaran ───────────────────────────────────────────────────
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

        # ── 4. Profil Organisasi ─────────────────────────────────────────────────
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
                        "date":    "–",
                        "date_ts": date_ts,
                        "url":     f"/profil.html?profil={row['id']}",
                        "thumb":   "",
                    })
            except Exception:
                pass

    finally:
        cursor.close()
        conn.close()

    # ── Sorting ──────────────────────────────────────────────────────────────────
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

    # ── Pagination ───────────────────────────────────────────────────────────────
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


# Source legacy app.py lines 8909-8920 | routes: /api/agendas
@app.route("/api/agendas", methods=["GET"])
def get_agendas():
    ensure_agenda_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `agendas` ORDER BY `order_index` ASC, `updated_at` DESC")
        rows = cursor.fetchall() or []
        return jsonify([agenda_row_to_dict(row) for row in rows])
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 8923-8936 | routes: /api/agendas/<agenda_id>
@app.route("/api/agendas/<agenda_id>", methods=["GET"])
def get_agenda_detail(agenda_id):
    ensure_agenda_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `agendas` WHERE `id` = %s LIMIT 1", (agenda_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Agenda not found"}), 404
        return jsonify(agenda_row_to_dict(row))
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 8939-8991 | routes: /api/agendas
@app.route("/api/agendas", methods=["POST"])
def create_agenda():
    ensure_agenda_schema()
    data = request.json or {}
    values = agenda_payload_to_db_values(data)
    if not values["title"] or not values["start_date"] or not values["start_time"]:
        return jsonify({"success": False, "error": "Judul, tanggal mulai, dan waktu mulai wajib diisi."}), 400

    agenda_id = f"agenda-{int(time.time() * 1000)}"
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `agendas`
            (`id`, `title`, `description`, `start_date`, `start_time`, `end_date`, `end_time`, `location`, `registration_link`, `image_url`, `image_name`, `attachments`, `status`, `order_index`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                agenda_id,
                values["title"],
                values["description"],
                values["start_date"],
                values["start_time"],
                values["end_date"],
                values["end_time"],
                values["location"],
                values["registration_link"],
                values["image_url"],
                values["image_name"],
                values["attachments"],
                values["status"],
                values["order_index"],
            ),
        )
        conn.commit()
        try:
            ensure_notifications_schema()
            nc = conn.cursor()
            try:
                create_notification(nc, "agenda", f"Agenda Baru: {values['title']}", values.get('description') or "Terdapat agenda kegiatan baru.", url_for('get_agendas') if False else f"/agenda/{agenda_id}", {"agenda_id": agenda_id})
                conn.commit()
            finally:
                nc.close()
        except Exception:
            pass
        return jsonify({"success": True, "id": agenda_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 8994-9073 | routes: /api/agendas/<agenda_id>
@app.route("/api/agendas/<agenda_id>", methods=["PUT"])
def update_agenda(agenda_id):
    ensure_agenda_schema()
    data = request.json or {}
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `agendas` WHERE `id` = %s LIMIT 1", (agenda_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "Agenda not found"}), 404

        values = agenda_payload_to_db_values(data, existing)
        if not values["title"] or not values["start_date"] or not values["start_time"]:
            return jsonify({"success": False, "error": "Judul, tanggal mulai, dan waktu mulai wajib diisi."}), 400

        cursor.execute(
            """
            UPDATE `agendas`
            SET `title` = %s,
                `description` = %s,
                `start_date` = %s,
                `start_time` = %s,
                `end_date` = %s,
                `end_time` = %s,
                `location` = %s,
                `registration_link` = %s,
                `image_url` = %s,
                `image_name` = %s,
                `attachments` = %s,
                `status` = %s,
                `order_index` = %s
            WHERE `id` = %s
            """,
            (
                values["title"],
                values["description"],
                values["start_date"],
                values["start_time"],
                values["end_date"],
                values["end_time"],
                values["location"],
                values["registration_link"],
                values["image_url"],
                values["image_name"],
                values["attachments"],
                values["status"],
                values["order_index"],
                agenda_id,
            ),
        )
        conn.commit()
        
        # Cleanup file lama yang sudah dihapus/diganti saat Edit
        if existing:
            try:
                # Cleanup Image
                if existing.get("image_url") and existing.get("image_url") != values["image_url"]:
                    remove_physical_file(existing["image_url"])
                
                # Cleanup Attachments
                old_atts_raw = existing.get("attachments") or "[]"
                old_atts = json.loads(old_atts_raw) if isinstance(old_atts_raw, str) else (old_atts_raw or [])
                new_atts_raw = values.get("attachments") or "[]"
                new_atts = json.loads(new_atts_raw) if isinstance(new_atts_raw, str) else (new_atts_raw or [])
                new_att_urls = [a.get("url") for a in new_atts if isinstance(a, dict) and a.get("url")]
                
                for oa in old_atts:
                    if isinstance(oa, dict) and oa.get("url") and oa.get("url") not in new_att_urls:
                        remove_physical_file(oa["url"])
            except Exception as e:
                print(f"[WARN] Failed to cleanup replaced files for agenda {agenda_id}: {e}")

        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9076-9114 | routes: /api/agendas/<agenda_id>
@app.route("/api/agendas/<agenda_id>", methods=["DELETE"])
def delete_agenda(agenda_id):
    ensure_agenda_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch agenda data first to get the files we need to delete
        cursor.execute("SELECT `image_url`, `attachments` FROM `agendas` WHERE `id` = %s LIMIT 1", (agenda_id,))
        agenda = cursor.fetchone()
        
        if not agenda:
            return jsonify({"success": False, "error": "Agenda not found"}), 404

        # 2. Delete the record from the database
        cursor.execute("DELETE FROM `agendas` WHERE `id` = %s", (agenda_id,))
        conn.commit()

        # 3. Clean up physical files
        try:
            # Delete image
            if agenda.get("image_url"):
                remove_physical_file(agenda["image_url"])
            
            # Delete attachments
            attachments_raw = agenda.get("attachments") or "[]"
            attachments = json.loads(attachments_raw) if isinstance(attachments_raw, str) else (attachments_raw or [])
            for att in attachments:
                if isinstance(att, dict) and att.get("url"):
                    remove_physical_file(att["url"])
        except Exception as e:
            print(f"[WARN] Error during physical file cleanup for agenda {agenda_id}: {e}")

        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9118-9135 | routes: /api/news-categories
@app.route("/api/news-categories", methods=["GET"])
def get_news_categories():
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `news_categories` ORDER BY `order_index`, `name`")
        categories = cursor.fetchall()
        return jsonify([{
            "id": cat["id"],
            "name": cat["name"],
            "slug": cat["slug"],
            "description": cat["description"],
            "order": cat["order_index"]
        } for cat in categories])
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9137-9165 | routes: /api/news-categories
@app.route("/api/news-categories", methods=["POST"])
def create_news_category():
    ensure_news_schema()
    data = request.json or {}
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    category_id = f"cat-{int(time.time() * 1000)}"

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO `news_categories` (`id`, `name`, `slug`, `description`, `order_index`)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            category_id,
            name,
            slug,
            data.get("description", ""),
            int(data.get("order", 0))
        ))
        conn.commit()
        return jsonify({"success": True, "id": category_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9167-9195 | routes: /api/news-categories/<category_id>
@app.route("/api/news-categories/<category_id>", methods=["PUT"])
def update_news_category(category_id):
    ensure_news_schema()
    data = request.json or {}
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE `news_categories`
            SET `name` = %s, `slug` = %s, `description` = %s, `order_index` = %s
            WHERE `id` = %s
        """, (
            name,
            slug,
            data.get("description", ""),
            int(data.get("order", 0)),
            category_id
        ))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9197-9212 | routes: /api/news-categories/<category_id>
@app.route("/api/news-categories/<category_id>", methods=["DELETE"])
def delete_news_category(category_id):
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM `news_category_mapping` WHERE `category_id` = %s", (category_id,))
        cursor.execute("DELETE FROM `news_categories` WHERE `id` = %s", (category_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9214-9251 | routes: /api/news
@app.route("/api/news", methods=["GET"])
def get_news():
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM `news` ORDER BY `published_at` DESC, `created_at` DESC
        """)
        news_items = cursor.fetchall()
        
        result = []
        for item in news_items:
            # Get categories for this news
            cursor.execute("""
                SELECT c.id, c.name, c.slug FROM `news_category_mapping` m
                JOIN `news_categories` c ON m.category_id = c.id
                WHERE m.news_id = %s
            """, (item["id"],))
            categories = cursor.fetchall()
            
            result.append({
                "id": item["id"],
                "title": item["title"],
                "slug": item["slug"],
                "content": item["content"],
                "summary": item["summary"],
                "thumbnails": json.loads(item["thumbnails"] or "[]"),
                "attachments": json.loads(item["attachments"] or "[]"),
                "status": item["status"],
                "publishedAt": item["published_at"].isoformat() if item["published_at"] else None,
                "createdAt": item["created_at"].isoformat() if item["created_at"] else None,
                "categories": [{"id": c["id"], "name": c["name"], "slug": c["slug"]} for c in categories]
            })
        return jsonify(result)
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9253-9287 | routes: /api/news/<news_id>
@app.route("/api/news/<news_id>", methods=["GET"])
def get_news_detail(news_id):
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `news` WHERE `id` = %s", (news_id,))
        item = cursor.fetchone()
        if not item:
            return jsonify({"error": "News not found"}), 404

        # Get categories for this news
        cursor.execute("""
            SELECT c.id, c.name, c.slug FROM `news_category_mapping` m
            JOIN `news_categories` c ON m.category_id = c.id
            WHERE m.news_id = %s
        """, (news_id,))
        categories = cursor.fetchall()

        return jsonify({
            "id": item["id"],
            "title": item["title"],
            "slug": item["slug"],
            "content": item["content"],
            "summary": item["summary"],
            "thumbnails": json.loads(item["thumbnails"] or "[]"),
            "attachments": json.loads(item["attachments"] or "[]"),
            "status": item["status"],
            "publishedAt": item["published_at"].isoformat() if item["published_at"] else None,
            "createdAt": item["created_at"].isoformat() if item["created_at"] else None,
            "categories": [{"id": c["id"], "name": c["name"], "slug": c["slug"]} for c in categories]
        })
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9289-9345 | routes: /api/news
@app.route("/api/news", methods=["POST"])
def create_news():
    ensure_news_schema()
    data = request.json or {}
    news_id = f"news-{int(time.time() * 1000)}"
    
    title = (data.get("title") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    content = data.get("content", "")
    summary = data.get("summary", "")
    thumbnails = normalize_attachment_payload(data.get("thumbnails", []))
    attachments = normalize_attachment_payload(data.get("attachments", []))
    status = data.get("status", "draft")
    category_ids = data.get("categoryIds", [])

    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO `news` (`id`, `title`, `slug`, `content`, `summary`, `thumbnails`, `attachments`, `status`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            news_id,
            title,
            slug,
            content,
            summary,
            json.dumps(thumbnails, ensure_ascii=False),
            json.dumps(attachments, ensure_ascii=False),
            status
        ))

        # Add categories
        for cat_id in category_ids:
            cursor.execute("""
                INSERT IGNORE INTO `news_category_mapping` (`news_id`, `category_id`)
                VALUES (%s, %s)
            """, (news_id, cat_id))

        conn.commit()
        try:
            ensure_notifications_schema()
            nc = conn.cursor()
            try:
                create_notification(nc, "news", f"Pengumuman Baru: {title}", summary or "Terdapat pengumuman baru.", f"/pengumuman/{news_id}", {"news_id": news_id})
                conn.commit()
            finally:
                nc.close()
        except Exception:
            pass
        return jsonify({"success": True, "id": news_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9347-9419 | routes: /api/news/<news_id>
@app.route("/api/news/<news_id>", methods=["PUT"])
def update_news(news_id):
    ensure_news_schema()
    data = request.json or {}
    
    title = (data.get("title") or "").strip()
    slug = (data.get("slug") or "").strip() or re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    content = data.get("content", "")
    summary = data.get("summary", "")
    thumbnails = normalize_attachment_payload(data.get("thumbnails", []))
    attachments = normalize_attachment_payload(data.get("attachments", []))
    status = data.get("status", "draft")
    category_ids = data.get("categoryIds", [])

    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `news` WHERE `id` = %s LIMIT 1", (news_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "error": "News not found"}), 404

        cursor.execute("""
            UPDATE `news`
            SET `title` = %s, `slug` = %s, `content` = %s, `summary` = %s, 
                `thumbnails` = %s, `attachments` = %s, `status` = %s
            WHERE `id` = %s
        """, (
            title,
            slug,
            content,
            summary,
            json.dumps(thumbnails, ensure_ascii=False),
            json.dumps(attachments, ensure_ascii=False),
            status,
            news_id
        ))

        # Update categories
        cursor.execute("DELETE FROM `news_category_mapping` WHERE `news_id` = %s", (news_id,))
        for cat_id in category_ids:
            cursor.execute("""
                INSERT IGNORE INTO `news_category_mapping` (`news_id`, `category_id`)
                VALUES (%s, %s)
            """, (news_id, cat_id))

        conn.commit()

        # Clean up old files if they are replaced
        try:
            old_thumbs_raw = existing.get("thumbnails") or "[]"
            old_thumbs = json.loads(old_thumbs_raw) if isinstance(old_thumbs_raw, str) else (old_thumbs_raw or [])
            new_thumb_urls = [t.get("url") for t in thumbnails if isinstance(t, dict) and t.get("url")]
            for ot in old_thumbs:
                if isinstance(ot, dict) and ot.get("url") and ot.get("url") not in new_thumb_urls:
                    remove_physical_file(ot["url"])
                    
            old_atts_raw = existing.get("attachments") or "[]"
            old_atts = json.loads(old_atts_raw) if isinstance(old_atts_raw, str) else (old_atts_raw or [])
            new_att_urls = [a.get("url") for a in attachments if isinstance(a, dict) and a.get("url")]
            for oa in old_atts:
                if isinstance(oa, dict) and oa.get("url") and oa.get("url") not in new_att_urls:
                    remove_physical_file(oa["url"])
        except Exception as e:
            print(f"[WARN] Failed to cleanup replaced files for news {news_id}: {e}")

        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# Source legacy app.py lines 9421-9463 | routes: /api/news/<news_id>
@app.route("/api/news/<news_id>", methods=["DELETE"])
def delete_news(news_id):
    ensure_news_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch news data first to get the files we need to delete
        cursor.execute("SELECT `thumbnails`, `attachments` FROM `news` WHERE `id` = %s LIMIT 1", (news_id,))
        news = cursor.fetchone()
        
        if not news:
            return jsonify({"success": False, "error": "News not found"}), 404
            
        # 2. Delete mappings and record
        cursor.execute("DELETE FROM `news_category_mapping` WHERE `news_id` = %s", (news_id,))
        cursor.execute("DELETE FROM `news` WHERE `id` = %s", (news_id,))
        conn.commit()
        
        # 3. Clean up physical files
        try:
            # Clean thumbnails
            thumbnails_raw = news.get("thumbnails") or "[]"
            thumbnails = json.loads(thumbnails_raw) if isinstance(thumbnails_raw, str) else (thumbnails_raw or [])
            for thumb in thumbnails:
                if isinstance(thumb, dict) and thumb.get("url"):
                    remove_physical_file(thumb["url"])
                    
            # Clean attachments
            attachments_raw = news.get("attachments") or "[]"
            attachments = json.loads(attachments_raw) if isinstance(attachments_raw, str) else (attachments_raw or [])
            for att in attachments:
                if isinstance(att, dict) and att.get("url"):
                    remove_physical_file(att["url"])
        except Exception as e:
            print(f"[WARN] Error during physical file cleanup for news {news_id}: {e}")

        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


