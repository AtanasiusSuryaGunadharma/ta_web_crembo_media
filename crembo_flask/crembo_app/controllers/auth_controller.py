"""Auth Controller.

File ini berisi route/controller yang dipisahkan dari app.py server lama.
Logika helper tetap dipanggil dari crembo_app.services.core agar perilaku produksi tetap sama.
"""

from crembo_app.services import core as _core

globals().update({
    name: getattr(_core, name)
    for name in dir(_core)
    if not (name.startswith("__") and name.endswith("__"))
})


# Route dari app.py server: /login
@app.route("/login", methods=["GET", "POST"])
def login():
    ensure_auth_schema()

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Username, email, atau nomor WhatsApp dan kata sandi wajib diisi.", "error")
            return render_template("login.html")

        member = fetch_member(identifier)
        if not member:
            flash("Akun tidak ditemukan.", "error")
            return render_template("login.html")

        if not check_password_hash(member["password"], password):
            flash("Kata sandi salah.", "error")
            return render_template("login.html")

        session.clear()
        session["logged_in"] = True
        session["user_id"] = member["id"]
        session["username"] = member.get("username")
        session["nama"] = member.get("nama")
        session["role"] = member.get("role") or "user"
        session["telp"] = member.get("telp")
        session["email"] = member.get("email")
        session["alamat"] = member.get("alamat")
        session["tgl_lahir"] = member.get("tgl_lahir")
        session["status_akun"] = member.get("status_akun") or "aktif"

        return redirect(login_target_for_role(session["role"]))

    return render_template("login.html", current_user=current_user_context())


# Route dari app.py server: /api/password/forgot
@app.route("/api/password/forgot", methods=["POST"])
def api_password_forgot():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_password_reset_schema(cursor)
        data = request.get_json(silent=True) or request.form
        identifier = normalize_text(data.get("identifier"))
        if not identifier:
            return jsonify({"ok": False, "message": "Username, email, atau nomor HP wajib diisi."}), 400

        member = fetch_member(identifier)
        if not member:
            return jsonify({"ok": False, "message": "Akun tidak ditemukan."}), 404

        email_value = normalize_text(member.get("email"))
        if not email_value or "@" not in email_value:
            return jsonify({"ok": False, "message": "Akun ini belum memiliki email terdaftar. Hubungi admin untuk reset password."}), 400

        # Batasi spam: jika OTP terakhir masih cooldown, minta user menunggu.
        cursor.execute(
            """
            SELECT `id`, `expires_at`, `resend_available_at`, `used_at`
            FROM `password_reset_otps`
            WHERE `member_id` = %s AND `used_at` IS NULL
            ORDER BY `created_at` DESC
            LIMIT 1
            """,
            (member.get("id"),),
        )
        last_reset = cursor.fetchone()
        if last_reset and seconds_until(last_reset.get("resend_available_at")) > 0 and seconds_until(last_reset.get("expires_at")) > 0:
            return jsonify({
                "ok": False,
                "message": f"Kode OTP sudah dikirim. Silakan tunggu {seconds_until(last_reset.get('resend_available_at'))} detik untuk kirim ulang.",
                "resetId": last_reset.get("id"),
                "maskedEmail": mask_email_address(email_value),
                "expiresIn": seconds_until(last_reset.get("expires_at")),
                "resendAfter": seconds_until(last_reset.get("resend_available_at")),
            }), 429

        reset_data = create_password_reset_otp(cursor, member, identifier)
        subject, text_body, html_body = build_reset_otp_email(member, reset_data["otp"], reset_data["expires_at"])
        send_email_message(email_value, normalize_text(member.get("nama")), subject, text_body, html_body)
        conn.commit()
        record_activity_for_member(
            member.get("id"),
            "REQUEST",
            "Autentikasi",
            "Meminta kode OTP reset password",
            "password.forgot",
            meta={"identifier": identifier, "email": mask_email_address(email_value)},
        )

        return jsonify(password_reset_response_payload(
            reset_data["reset_id"],
            email_value,
            reset_data["expires_at"],
            reset_data["resend_available_at"],
            {"message": f"Kode OTP berhasil dikirim ke {mask_email_address(email_value)}."},
        ))
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": f"Gagal mengirim OTP: {exc}"}), 500
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/password/resend
@app.route("/api/password/resend", methods=["POST"])
def api_password_resend():
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_password_reset_schema(cursor)
        data = request.get_json(silent=True) or request.form
        reset_id = normalize_text(data.get("resetId") or data.get("reset_id"))
        if not reset_id:
            return jsonify({"ok": False, "message": "Sesi reset password tidak valid."}), 400

        cursor.execute("SELECT * FROM `password_reset_otps` WHERE `id` = %s LIMIT 1", (reset_id,))
        reset_row = cursor.fetchone()
        if not reset_row or reset_row.get("used_at"):
            return jsonify({"ok": False, "message": "Sesi reset password tidak valid atau sudah digunakan."}), 400

        wait_seconds = seconds_until(reset_row.get("resend_available_at"))
        if wait_seconds > 0:
            return jsonify({"ok": False, "message": f"Tunggu {wait_seconds} detik sebelum kirim ulang OTP.", "resendAfter": wait_seconds}), 429

        cursor.execute("SELECT * FROM `anggota` WHERE `id` = %s LIMIT 1", (reset_row.get("member_id"),))
        member = cursor.fetchone()
        if not member:
            return jsonify({"ok": False, "message": "Akun tidak ditemukan."}), 404

        email_value = normalize_text(member.get("email") or reset_row.get("member_email"))
        otp_code = f"{secrets.randbelow(1000000):06d}"
        issued_at = now_utc()
        expires_at = issued_at + timedelta(minutes=PASSWORD_RESET_OTP_MINUTES)
        resend_available_at = issued_at + timedelta(seconds=PASSWORD_RESET_RESEND_SECONDS)

        subject, text_body, html_body = build_reset_otp_email(member, otp_code, expires_at)
        send_email_message(email_value, normalize_text(member.get("nama")), subject, text_body, html_body)

        cursor.execute(
            """
            UPDATE `password_reset_otps`
            SET `otp_hash` = %s,
                `expires_at` = %s,
                `resend_available_at` = %s,
                `verified_at` = NULL,
                `reset_token_hash` = NULL,
                `attempts` = 0,
                `updated_at` = CURRENT_TIMESTAMP
            WHERE `id` = %s
            """,
            (generate_password_hash(otp_code), expires_at, resend_available_at, reset_id),
        )
        conn.commit()

        return jsonify(password_reset_response_payload(
            reset_id,
            email_value,
            expires_at,
            resend_available_at,
            {"message": f"Kode OTP baru berhasil dikirim ke {mask_email_address(email_value)}."},
        ))
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": f"Gagal mengirim ulang OTP: {exc}"}), 500
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/password/verify
@app.route("/api/password/verify", methods=["POST"])
def api_password_verify():
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_password_reset_schema(cursor)
        data = request.get_json(silent=True) or request.form
        reset_id = normalize_text(data.get("resetId") or data.get("reset_id"))
        otp_code = normalize_text(data.get("otp"))
        if not reset_id or not re.fullmatch(r"\d{6}", otp_code or ""):
            return jsonify({"ok": False, "message": "Masukkan 6 digit kode OTP."}), 400

        cursor.execute("SELECT * FROM `password_reset_otps` WHERE `id` = %s LIMIT 1", (reset_id,))
        reset_row = cursor.fetchone()
        if not reset_row or reset_row.get("used_at"):
            return jsonify({"ok": False, "message": "Sesi reset password tidak valid atau sudah digunakan."}), 400
        if seconds_until(reset_row.get("expires_at")) <= 0:
            return jsonify({"ok": False, "message": "Kode OTP sudah kedaluwarsa. Silakan kirim ulang OTP."}), 400
        if int(reset_row.get("attempts") or 0) >= PASSWORD_RESET_MAX_ATTEMPTS:
            return jsonify({"ok": False, "message": "Percobaan OTP terlalu banyak. Silakan kirim ulang kode."}), 429

        if not check_password_hash(reset_row.get("otp_hash") or "", otp_code):
            cursor.execute("UPDATE `password_reset_otps` SET `attempts` = `attempts` + 1 WHERE `id` = %s", (reset_id,))
            conn.commit()
            return jsonify({"ok": False, "message": "Kode OTP salah. Periksa kembali."}), 400

        reset_token = secrets.token_urlsafe(32)
        reset_token_hash = generate_password_hash(reset_token)
        cursor.execute(
            """
            UPDATE `password_reset_otps`
            SET `verified_at` = %s,
                `reset_token_hash` = %s,
                `updated_at` = CURRENT_TIMESTAMP
            WHERE `id` = %s
            """,
            (now_utc(), reset_token_hash, reset_id),
        )
        conn.commit()

        return jsonify({
            "ok": True,
            "message": "OTP benar. Silakan buat password baru.",
            "resetId": reset_id,
            "resetToken": reset_token,
        })
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": f"Gagal memverifikasi OTP: {exc}"}), 500
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /api/password/reset
@app.route("/api/password/reset", methods=["POST"])
def api_password_reset():
    ensure_auth_schema()
    conn = mysql_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_password_reset_schema(cursor)
        data = request.get_json(silent=True) or request.form
        reset_id = normalize_text(data.get("resetId") or data.get("reset_id"))
        reset_token = normalize_text(data.get("resetToken") or data.get("reset_token"))
        new_password = str(data.get("password") or "")
        confirm_password = str(data.get("confirmPassword") or data.get("confirm_password") or "")

        if not reset_id or not reset_token:
            return jsonify({"ok": False, "message": "Sesi reset password tidak valid."}), 400
        if not new_password or not confirm_password:
            return jsonify({"ok": False, "message": "Password baru dan konfirmasi wajib diisi."}), 400
        if new_password != confirm_password:
            return jsonify({"ok": False, "message": "Konfirmasi password tidak cocok."}), 400

        rule_score = sum([
            len(new_password) >= 8,
            bool(re.search(r"[A-Z]", new_password)),
            bool(re.search(r"[0-9]", new_password)),
            bool(re.search(r"[^A-Za-z0-9]", new_password)),
        ])
        if rule_score < 3:
            return jsonify({"ok": False, "message": "Password terlalu lemah. Gunakan minimal 8 karakter dan kombinasi huruf besar, angka, atau simbol."}), 400

        cursor.execute("SELECT * FROM `password_reset_otps` WHERE `id` = %s LIMIT 1", (reset_id,))
        reset_row = cursor.fetchone()
        if not reset_row or reset_row.get("used_at"):
            return jsonify({"ok": False, "message": "Sesi reset password tidak valid atau sudah digunakan."}), 400
        if not reset_row.get("verified_at") or not reset_row.get("reset_token_hash"):
            return jsonify({"ok": False, "message": "OTP belum diverifikasi."}), 400
        if seconds_until(reset_row.get("expires_at")) <= 0:
            return jsonify({"ok": False, "message": "Sesi reset password sudah kedaluwarsa. Ulangi dari Lupa Sandi."}), 400
        if not check_password_hash(reset_row.get("reset_token_hash") or "", reset_token):
            return jsonify({"ok": False, "message": "Token reset password tidak valid."}), 400

        cursor.execute("SELECT `id`, `nama`, `email` FROM `anggota` WHERE `id` = %s LIMIT 1", (reset_row.get("member_id"),))
        member = cursor.fetchone()
        if not member:
            return jsonify({"ok": False, "message": "Akun tidak ditemukan."}), 404

        cursor.execute(
            """
            UPDATE `anggota`
            SET `password` = %s, `updated_at` = CURRENT_TIMESTAMP
            WHERE `id` = %s
            """,
            (generate_password_hash(new_password), reset_row.get("member_id")),
        )
        cursor.execute(
            "UPDATE `password_reset_otps` SET `used_at` = %s, `updated_at` = CURRENT_TIMESTAMP WHERE `id` = %s",
            (now_utc(), reset_id),
        )
        conn.commit()
        record_activity_for_member(
            reset_row.get("member_id"),
            "RESET",
            "Autentikasi",
            "Reset password berhasil melalui OTP",
            "password.reset",
        )

        return jsonify({"ok": True, "message": "Password berhasil diperbarui. Silakan login dengan password baru."})
    except Exception as exc:
        conn.rollback()
        return jsonify({"ok": False, "message": f"Gagal menyimpan password baru: {exc}"}), 500
    finally:
        cursor.close()
        conn.close()


# Route dari app.py server: /logout
@app.route("/logout")
def logout():
    try:
        record_activity("LOGOUT", "Autentikasi", "Logout dari sistem", "logout", method="GET")
    except Exception:
        pass
    session.clear()
    return redirect(url_for("login"))


# Route dari app.py server: /api/session
@app.route("/api/session", methods=["GET"])
def get_session_context():
    response = jsonify(current_user_context())
    # Hindari data profil/session lama terbaca ulang oleh browser saat berganti akun.
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

