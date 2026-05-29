from crembo_app.app_factory import create_app

app = create_app()

# Import controller setelah app dibuat agar seluruh route terdaftar.
from crembo_app.controllers import main_controller as _main_controller  # noqa: E402,F401


if __name__ == "__main__":
    try:
        from crembo_app.services.bootstrap import bootstrap_database

        bootstrap_database()
    except Exception as exc:
        print(f"[WARN] MySQL bootstrap skipped: {exc}")
    app.run(debug=True)
