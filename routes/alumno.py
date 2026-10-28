import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import qrcode
import hashlib
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
    current_app,
)

from Class.User import User
from Class.PDFManager import PdfQrAlumno
from db.Conection import obtener_cursor
from utils.helpers import (
    login_requerido,
    obtener_foto_usuario,
    limpiar_metadatos_imagen,
)

alumno_bp = Blueprint("alumno", __name__)
usuario = User()


@alumno_bp.route("/menu_alumno")
def menu_alumno():
    if not login_requerido("alumno", "externo"):
        return redirect(url_for("auth.index"))

    foto = obtener_foto_usuario(session["matricula"])
    grupos_disponibles = []
    datos_usuario = usuario.obtener_mis_datos(session["matricula"], session["tipo"])

    if session["tipo"] == "alumno":
        grupos_disponibles = usuario.obtener_grupos_disponibles_para_alumno(
            session["matricula"]
        )

    return render_template(
        "Alm/menu.html",
        nombre=session["nombre"],
        matricula=session["matricula"],
        email=session["email"],
        foto=foto,
        grupos_disponibles=grupos_disponibles,
        datos_usuario=datos_usuario,
    )


@alumno_bp.route("/asistencia_directa")
def asistencia_directa():
    token_recibido = request.args.get("token", "").strip()
    grupo_id = request.args.get("grupo", type=int)
    sesion_id = request.args.get("sesion", type=int)

    if not token_recibido or not sesion_id:
        return redirect(url_for("alumno.menu_alumno", r="invalid_qr"))

    # 1. Si no hay sesión iniciada en el smartphone, se guarda el intento y se redirige al login
    if "matricula" not in session or session.get("tipo") not in ["alumno", "externo"]:
        session["asistencia_pendiente"] = {
            "token": token_recibido,
            "grupo_id": grupo_id,
            "sesion_id": sesion_id,
        }
        return redirect(url_for("auth.index", r="login_required_for_attendance"))

    # 2. Si ya está autenticado, validar la sesión de pase de lista en BD
    conexion, cursor = obtener_cursor()

    cursor.execute(
        """
        SELECT * FROM sesiones_tutoria
        WHERE id = %s AND activa = 1 AND fecha_expiracion > NOW()
    """,
        (sesion_id,),
    )
    sesion = cursor.fetchone()

    if not sesion:
        cursor.close()
        conexion.close()
        return redirect(url_for("alumno.menu_alumno", r="qr_expired"))

    # 3. Comprobar si la asistencia ya se encontraba registrada
    cursor.execute(
        "SELECT * FROM asistencias_tutoria WHERE sesion_id = %s AND alumno_matricula = %s",
        (sesion_id, session["matricula"]),
    )
    if cursor.fetchone():
        cursor.close()
        conexion.close()
        return redirect(url_for("alumno.menu_alumno", r="already_registered"))

    # 4. Registrar la asistencia del estudiante
    cursor.execute(
        """
        INSERT INTO asistencias_tutoria 
        (sesion_id, grupo_id, alumno_matricula, nombre_alumno, fecha_asistencia)
        VALUES (%s, %s, %s, %s, NOW())
    """,
        (sesion_id, grupo_id, session["matricula"], session.get("nombre", "")),
    )

    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect(url_for("alumno.menu_alumno", r="attendance_ok"))


@alumno_bp.route("/generar_qr_alumno")
def generar_qr_alumno():
    if not login_requerido("alumno", "externo"):
        return redirect(url_for("auth.index"))

    contenido = f'{session["matricula"]}-{session["email"]}'

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")


@alumno_bp.route("/descargar_qr_pdf")
def descargar_qr_pdf():
    if not login_requerido("alumno", "externo"):
        return redirect(url_for("auth.index"))

    nombre_alumno = session["nombre"]
    matricula = session["matricula"]
    email = session["email"]
    carrera = session["carrera"] if session.get("carrera") else "Externo"

    contenido_qr = f"{matricula}-{email}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(contenido_qr)
    qr.make(fit=True)

    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    pdf = PdfQrAlumno(
        logo_path="static/resources/logo.png",
        nombre_escuela="Instituto Tecnológico Superior de Atlixco - ITSA",
        nombre_alumno=nombre_alumno,
        matricula=matricula,
        email=email,
        carrera=carrera,
        qr_buffer=qr_buffer,
    )

    pdf_buffer = pdf.construir()

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"QR_{matricula}.pdf",
        mimetype="application/pdf",
    )


@alumno_bp.route("/subir_imagen_alumno", methods=["POST"])
def subir_imagen_alumno():
    if not login_requerido("alumno", "externo"):
        return redirect(url_for("auth.index"))

    if "foto" not in request.files:
        return redirect(url_for("alumno.menu_alumno", r="image_empty"))

    archivo = request.files["foto"]

    if archivo.filename == "":
        return redirect(url_for("alumno.menu_alumno", r="image_empty"))

    extension = (
        archivo.filename.rsplit(".", 1)[1].lower() if "." in archivo.filename else ""
    )

    extensiones_validas = ["png", "jpg", "jpeg", "webp"]
    if extension not in extensiones_validas:
        return redirect(url_for("alumno.menu_alumno", r="image_wrong"))

    matricula = session["matricula"]
    carpeta = current_app.config["UPLOAD_FOLDER"]

    for ext in extensiones_validas:
        ruta_vieja = os.path.join(carpeta, f"{matricula}.{ext}")
        if os.path.exists(ruta_vieja):
            os.remove(ruta_vieja)

    try:
        buffer_limpio = limpiar_metadatos_imagen(archivo, max_size=(500, 500))
        nombre_final = f"{matricula}.jpg"
        ruta_final = os.path.join(carpeta, nombre_final)

        with open(ruta_final, "wb") as f:
            f.write(buffer_limpio.read())

        return redirect(url_for("alumno.menu_alumno", r="image_ok"))
    except Exception:
        return redirect(url_for("alumno.menu_alumno", r="error"))


@alumno_bp.route("/inscribirme_grupo/<int:grupo_id>", methods=["POST"])
def inscribirme_grupo(grupo_id):
    if not login_requerido("alumno"):
        return redirect(url_for("auth.index"))

    resultado = usuario.inscribir_alumno_a_grupo(session["matricula"], grupo_id)

    if resultado["status"] == "ok":
        return redirect(url_for("alumno.menu_alumno", r="group_joined"))

    if resultado["status"] == "student_not_found":
        return redirect(url_for("alumno.menu_alumno", r="student_not_found"))

    if resultado["status"] == "group_not_found":
        return redirect(url_for("alumno.menu_alumno", r="group_not_found"))

    if resultado["status"] == "wrong_career":
        return redirect(url_for("alumno.menu_alumno", r="wrong_career"))

    if resultado["status"] == "exists":
        return redirect(url_for("alumno.menu_alumno", r="student_group_exists"))

    return redirect(url_for("alumno.menu_alumno", r="error"))


@alumno_bp.route("/escanear_qr_rotativo", methods=["POST"])
def escanear_qr_rotativo():
    if not login_requerido("alumno"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

    contenido_qr = data.get("contenido_qr", "").strip()

    # Si viene desde la app web o si viene desde una URL completa escaneada por la cámara
    if "asistencia_directa" in contenido_qr and "token=" in contenido_qr:
        import urllib.parse

        parsed_url = urllib.parse.urlparse(contenido_qr)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        token_recibido = query_params.get("token", [""])[0]
        sesion_id = int(query_params.get("sesion", [0])[0])
        grupo_id = int(query_params.get("grupo", [0])[0])
    elif contenido_qr.startswith("TUTORIA|"):
        partes = contenido_qr.split("|")
        if len(partes) != 4:
            return (
                jsonify({"status": "error", "message": "Estructura de QR incorrecta"}),
                400,
            )
        token_recibido = partes[1]
        grupo_id = int(partes[2])
        sesion_id = int(partes[3])
    else:
        return jsonify({"status": "error", "message": "Formato de QR inválido"}), 400

    token_hash = hashlib.sha256(token_recibido.encode()).hexdigest()

    conexion, cursor = obtener_cursor()

    cursor.execute(
        """
        SELECT st.*, g.id as grupo_id 
        FROM sesiones_tutoria st
        JOIN grupos g ON st.grupo_id = g.id
        WHERE st.id = %s 
        AND st.token_actual = %s
        AND st.activa = 1 
        AND st.fecha_expiracion > NOW()
    """,
        (sesion_id, token_hash),
    )

    sesion = cursor.fetchone()

    if not sesion:
        cursor.close()
        conexion.close()
        return jsonify({"status": "error", "message": "QR inválido o expirado"}), 400

    grupo_id = sesion["grupo_id"]

    cursor.execute(
        "SELECT * FROM alumnos_grupo WHERE grupo_id = %s AND alumno_matricula = %s AND activo = 1",
        (grupo_id, session["matricula"]),
    )

    if not cursor.fetchone():
        cursor.close()
        conexion.close()
        return (
            jsonify({"status": "error", "message": "No perteneces a este grupo"}),
            400,
        )

    cursor.execute(
        "SELECT * FROM asistencias_tutoria WHERE sesion_id = %s AND alumno_matricula = %s",
        (sesion_id, session["matricula"]),
    )

    if cursor.fetchone():
        cursor.close()
        conexion.close()
        return jsonify({"status": "error", "message": "Ya registraste asistencia"}), 400

    nombre_alumno = session.get("nombre", "")
    cursor.execute(
        """
        INSERT INTO asistencias_tutoria 
        (sesion_id, grupo_id, alumno_matricula, nombre_alumno, fecha_asistencia)
        VALUES (%s, %s, %s, %s, NOW())
    """,
        (sesion_id, grupo_id, session["matricula"], nombre_alumno),
    )

    import secrets
    import string

    nuevo_token_raw = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16)
    )
    nuevo_token_hash = hashlib.sha256(nuevo_token_raw.encode()).hexdigest()

    cursor.execute(
        """
        UPDATE sesiones_tutoria 
        SET token_actual = %s,
            token_anterior = token_actual,
            fecha_expiracion = DATE_ADD(NOW(), INTERVAL 2 MINUTE)
        WHERE id = %s
    """,
        (nuevo_token_hash, sesion_id),
    )

    conexion.commit()
    cursor.close()
    conexion.close()

    return jsonify(
        {"status": "ok", "message": "✅ Asistencia registrada correctamente"}
    )
