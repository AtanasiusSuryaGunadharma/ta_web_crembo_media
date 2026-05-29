from pathlib import Path
import os


def _load_env_file(path: Path) -> None:
    """Membaca file .env tanpa wajib memakai dependensi python-dotenv."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


BASE_DIR = Path(__file__).resolve().parents[2]
_load_env_file(BASE_DIR / ".env")

FRONTEND_DIR = BASE_DIR / "frontend"
PUBLIC_FAVICON_PATH = FRONTEND_DIR / "LOGO CREMBO PUTIH yg bagus.png"

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
SESSION_LIFETIME_DAYS = int(os.getenv("SESSION_LIFETIME_DAYS", "30"))

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "crembo_db_new"),
    "autocommit": False,
}

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or "crembomedia123@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or "leezqsrjqdphonev"
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Crembo Media")

_email_logo_value = os.getenv("EMAIL_LOGO_PATH", "frontend/LOGO CREMBO PUTIH yg bagus.png")
EMAIL_LOGO_PATH = Path(_email_logo_value)
if not EMAIL_LOGO_PATH.is_absolute():
    EMAIL_LOGO_PATH = BASE_DIR / EMAIL_LOGO_PATH

PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or os.getenv("SITE_BASE_URL") or "https://crembomedia.com").rstrip("/")
SITE_BASE_URL = PUBLIC_BASE_URL
NOTIFICATION_EMAIL_ENABLED = os.getenv("NOTIFICATION_EMAIL_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}
NOTIFICATION_EMAIL_RETRY_COUNT = max(1, int(os.getenv("NOTIFICATION_EMAIL_RETRY_COUNT", "3")))
NOTIFICATION_EMAIL_RETRY_DELAY_SECONDS = max(0.2, float(os.getenv("NOTIFICATION_EMAIL_RETRY_DELAY_SECONDS", "2.5")))
NOTIFICATION_EMAIL_SEND_DELAY_SECONDS = max(0.0, float(os.getenv("NOTIFICATION_EMAIL_SEND_DELAY_SECONDS", "0.8")))
NOTIFICATION_EMAIL_ROW_WAIT_ATTEMPTS = max(1, int(os.getenv("NOTIFICATION_EMAIL_ROW_WAIT_ATTEMPTS", "12")))
NOTIFICATION_EMAIL_ROW_WAIT_SECONDS = max(0.1, float(os.getenv("NOTIFICATION_EMAIL_ROW_WAIT_SECONDS", "0.35")))

PASSWORD_RESET_OTP_MINUTES = int(os.getenv("PASSWORD_RESET_OTP_MINUTES", "5"))
PASSWORD_RESET_RESEND_SECONDS = int(os.getenv("PASSWORD_RESET_RESEND_SECONDS", "120"))
PASSWORD_RESET_MAX_ATTEMPTS = int(os.getenv("PASSWORD_RESET_MAX_ATTEMPTS", "5"))
