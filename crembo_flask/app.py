from pathlib import Path

from flask import Flask, abort, render_template, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
MOCKUP_DIR = BASE_DIR.parent / "Mockup_hifi"

app = Flask(
    __name__,
    template_folder=str(MOCKUP_DIR),
    static_folder=str(MOCKUP_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = "dev-secret-change-me"


def template_exists(template_name: str) -> bool:
    return (MOCKUP_DIR / template_name).is_file()


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/<path:page>")
def render_mockup_page(page: str):
    if page in {"favicon.ico"}:
        abort(404)

    asset_path = MOCKUP_DIR / page
    if asset_path.is_file() and not page.endswith(".html"):
        return send_from_directory(MOCKUP_DIR, page)

    candidate = page
    if not candidate.endswith(".html"):
        candidate = f"{candidate}.html"

    if template_exists(candidate):
        return render_template(candidate)

    abort(404)


if __name__ == "__main__":
    app.run(debug=True)
