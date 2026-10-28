import os
from flask import Flask

from routes.auth import auth_bp
from routes.alumno import alumno_bp
from routes.laboratorista import laboratorista_bp
from routes.maestro import maestro_bp


app = Flask(__name__)
app.secret_key = "clave_secreta_123"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Registro de Blueprints con prefijo de URL
app.register_blueprint(auth_bp)
app.register_blueprint(alumno_bp, url_prefix="/alumno")
app.register_blueprint(laboratorista_bp, url_prefix="/laboratorista")
app.register_blueprint(maestro_bp, url_prefix="/maestro")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3500, debug=True)
