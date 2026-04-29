from pathlib import Path

from flask import Flask, abort, render_template, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR),
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = "dev-secret-change-me"


def template_exists(template_name: str) -> bool:
    return (FRONTEND_DIR / template_name).is_file()


@app.route("/")
def index():
    home_page_data = {
        "carouselSlides": [
            {
                "id": "default-1",
                "title": "Jadwal Misa Mingguan",
                "slug": "jadwal-misa",
                "description": "Lihat jadwal pelayanan streaming mingguan terbaru dari tim multimedia.",
                "link": "jadwal-streaming.html",
                "buttonText": "Lihat Jadwal",
                "backgroundImage": "",
                "order": 1,
                "active": True,
            },
            {
                "id": "default-2",
                "title": "Open Recruitment Petugas",
                "slug": "open-recruitment",
                "description": "Bergabung sebagai petugas multimedia untuk mendukung pelayanan misa.",
                "link": "form-pendaftaran.html",
                "buttonText": "Daftar Sekarang",
                "backgroundImage": "",
                "order": 2,
                "active": True,
            },
            {
                "id": "default-3",
                "title": "Pengumuman Agenda",
                "slug": "agenda-terbaru",
                "description": "Pantau agenda dan pengumuman terbaru komunitas Crembo Media.",
                "link": "agenda.html",
                "buttonText": "Lihat Agenda",
                "backgroundImage": "",
                "order": 3,
                "active": True,
            },
        ],
        "aboutContent": {
            "description": "Ringkasan profil organisasi, visi pelayanan multimedia, serta peran Crembo dalam mendukung kegiatan liturgi dan agenda komunitas. Konten ini nantinya diatur dari panel admin setelah login.",
            "buttonText": "Pelajari Lebih Lanjut",
            "buttonLink": "profil.html",
            "autoSeconds": 5,
            "images": [],
        },
        "bigMassSchedules": [],
        "profileMenu": [
            {"id": "sejarah", "label": "Sejarah"},
            {"id": "tentang-crembo", "label": "Tentang Crembo"},
            {"id": "struktur", "label": "Struktur"},
            {"id": "visi-misi", "label": "Visi & Misi"},
        ],
    }
    return render_template("home.html", home_page_data=home_page_data)


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

    if template_exists(candidate):
        return render_template(candidate)

    abort(404)


if __name__ == "__main__":
    app.run(debug=True)
