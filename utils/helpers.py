import os
import io
from PIL import Image, ImageOps
from flask import session, url_for, current_app
from flask import session


def login_requerido(*tipos_permitidos):
    if "matricula" not in session:
        return False
    if not tipos_permitidos:
        return True
    return session.get("tipo") in tipos_permitidos


def limpiar_metadatos_imagen(file_storage, max_size=(1024, 1024), quality=85):
    imagen = Image.open(file_storage)
    try:
        imagen = ImageOps.exif_transpose(imagen)
    except Exception:
        pass

    if imagen.mode in ("RGBA", "P"):
        imagen = imagen.convert("RGB")

    imagen.thumbnail(max_size, Image.Resampling.LANCZOS)

    buffer_limpio = io.BytesIO()
    imagen.save(buffer_limpio, format="JPEG", quality=quality, optimize=True)
    buffer_limpio.seek(0)
    return buffer_limpio


def obtener_foto_usuario(matricula):
    carpeta = current_app.config["UPLOAD_FOLDER"]
    extensiones = ["png", "jpg", "jpeg", "webp"]

    for ext in extensiones:
        ruta = os.path.join(carpeta, f"{matricula}.{ext}")
        if os.path.exists(ruta):
            version = int(os.path.getmtime(ruta))
            return url_for("static", filename=f"uploads/{matricula}.{ext}", v=version)

    return url_for("static", filename="uploads/none.png")
