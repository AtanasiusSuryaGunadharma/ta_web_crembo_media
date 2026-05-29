from crembo_app.services import core as _core

# Memuat seluruh helper, service, dan objek Flask dari core agar potongan kode route
# tetap kompatibel setelah dipisah dari app.py monolitik.
globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})

# Controller: Page Controller

# Source legacy app.py lines 6621-6627 | routes: /dashboard
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") == "user":
        return redirect(url_for("dashboard_anggota"))
    return render_template("dashboard.html", current_user=current_user_context())


# Source legacy app.py lines 6630-6636 | routes: /dashboard-anggota
@app.route("/dashboard-anggota")
def dashboard_anggota():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") != "user":
        return redirect(url_for("dashboard"))
    return render_template("dashboard-anggota.html", current_user=current_user_context())


# Source legacy app.py lines 6639-6645 | routes: /profil
@app.route("/profil")
def profil():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if (session.get("role") or "user") == "user":
        return render_template("profil-anggota.html", current_user=current_user_context())
    return render_template("profil-admin.html", current_user=current_user_context())


# Source legacy app.py lines 7490-7493 | routes: /unduh-sertifikat-anggota, /unduh-sertifikat-anggota.html
@app.route("/unduh-sertifikat-anggota")
@app.route("/unduh-sertifikat-anggota.html")
def legacy_certificate_page():
    return redirect(url_for("render_mockup_page", page="sertifikat-anggota"), code=301)


# Source legacy app.py lines 7496-7552 | routes: /<path:page>
@app.route("/<path:page>")
def render_mockup_page(page: str):
    if page in {"favicon.ico"}:
        abort(404)

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


# Source legacy app.py lines 7560-7562 | routes: /pengumuman
@app.route("/pengumuman")
def public_news_page():
    return render_public_page("pengumuman.html")


# Source legacy app.py lines 7564-7567 | routes: /pengumuman/kategori/<category_slug>
@app.route("/pengumuman/kategori/<category_slug>")
def public_news_category_page(category_slug):
    # Menyertakan category_slug jika dibutuhkan oleh Jinja, walau JS di FE juga bisa parsing URL
    return render_public_page("pengumuman.html", category_slug=category_slug)


# Source legacy app.py lines 7569-7571 | routes: /pengumuman/<news_id>
@app.route("/pengumuman/<news_id>")
def public_news_detail_page(news_id):
    return render_public_page("pengumuman-detail.html", news_id=news_id)


# Source legacy app.py lines 7574-7576 | routes: /agenda
@app.route("/agenda")
def public_agenda_page():
    return render_public_page("agenda.html")


# Source legacy app.py lines 7578-7581 | routes: /agenda/<agenda_id>
@app.route("/agenda/<agenda_id>")
def public_agenda_detail_page(agenda_id):
    # Mengirim parameter agenda_id ke template sehingga JS di client bisa membaca ID yang akan di load
    return render_public_page("agenda-detail.html", agenda_id=agenda_id)


# Source legacy app.py lines 7583-7585 | routes: /form-pendaftaran
@app.route("/form-pendaftaran")
def public_registration_forms_page():
    return render_public_page("form-pendaftaran.html")


# Source legacy app.py lines 7587-7589 | routes: /form-pendaftaran/<form_id>
@app.route("/form-pendaftaran/<form_id>")
def public_registration_form_detail_page(form_id):
    return render_public_page("form-pendaftaran-detail.html", form_id=form_id)


# Source legacy app.py lines 7713-7716 | routes: /uploads/<path:filename>
@app.route("/uploads/<path:filename>")
def serve_uploaded_file(filename: str):
    upload_folder = ensure_upload_folder()
    return send_from_directory(upload_folder, filename)


