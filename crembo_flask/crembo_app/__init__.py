"""Factory sederhana aplikasi Crembo Media berbasis Flask."""

from crembo_app.services.core import app

# Import controller agar semua route terdaftar pada objek Flask.
from crembo_app import controllers  # noqa: F401,E402

__all__ = ["app"]
