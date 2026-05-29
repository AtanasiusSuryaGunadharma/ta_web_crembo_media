"""Application package Crembo Media."""

from crembo_app.services.core import app

# Import controller setelah app dibuat agar semua route terdaftar.
from crembo_app import controllers  # noqa: F401,E402

__all__ = ["app"]
