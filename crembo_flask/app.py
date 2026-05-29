"""Entry point aplikasi Crembo Media.

File ini sengaja dibuat ringkas. Semua inisialisasi aplikasi berada pada
package crembo_app, sedangkan route/controller dipisahkan per modul.
"""

from crembo_app import app
from crembo_app.services.core import bootstrap_database


if __name__ == "__main__":
    bootstrap_database()
    app.run(debug=True)
