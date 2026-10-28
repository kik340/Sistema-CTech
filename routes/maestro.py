import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import base64
import secrets
import hashlib
import string
import qrcode
from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)

from Class.User import User
from Class.Tutor import TutorManager
from db.Conection import obtener_cursor
from utils.helpers import login_requerido

maestro_bp = Blueprint("maestro", __name__)

usuario = User()
tutor_manager = TutorManager()


@maestro_bp.route("/menu_maestro")
def menu_maestro():
    if not login_requerido("tutor", "maestro"):
        return redirect(url_for("auth.index"))

    grupos = tutor_manager.obtener_grupos_tutor(session["matricula"])
    datos_usuario = usuario.obtener_mis_datos(
        session["matricula"], session.get("tipo", "tutor")
    )
    grupos_con_alumnos = []

    for g in grupos:
        alumnos_grupo = tutor_manager.obtener_alumnos_por_grupo(g["id"])
        grupo_temp = dict(g)
        grupo_temp["alumnos"] = alumnos_grupo
        grupos_con_alumnos.append(grupo_temp)

    return render_template(
        "Maestro/menu.html",
        nombre=session["nombre"],
        grupos=grupos_con_alumnos,
        datos_usuario=datos_usuario,
    )


@maestro_bp.route("/obtener_info_grupo/<int:grupo_id>")
def obtener_info_grupo(grupo_id):
    if not login_requerido("tutor", "maestro"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    alumnos = tutor_manager.obtener_alumnos_por_grupo(grupo_id)
    total = len(alumnos) if alumnos else 0

    return jsonify({"status": "ok", "total_alumnos": total})


@maestro_bp.route("/iniciar_sesion_qr/<int:grupo_id>", methods=["POST"])
def iniciar_sesion_qr(grupo_id):
    if not login_requerido("tutor", "maestro"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    data = request.get_json(silent=True)
    parcial = data.get("parcial", "1") if data else "1"

    conexion, cursor = obtener_cursor()
    cursor.execute(
        "SELECT * FROM grupos WHERE id = %s AND tutor_matricula = %s",
        (grupo_id, session["matricula"]),
    )

    if not cursor.fetchone():
        cursor.close()
        conexion.close()
        return (
            jsonify(
                {"status": "error", "message": "No tienes permiso para este grupo"}
            ),
            403,
        )

    try:
        token_raw = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16)
        )
        token_hash = hashlib.sha256(token_raw.encode()).hexdigest()

        cursor.execute(
            """
            INSERT INTO sesiones_tutoria 
            (token_actual, grupo_id, tutor_matricula, parcial, fecha_inicio, fecha_expiracion, activa)
            VALUES (%s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 60 MINUTE), 1)
        """,
            (token_hash, grupo_id, session["matricula"], parcial),
        )

        conexion.commit()
        sesion_id = cursor.lastrowid
        cursor.close()
        conexion.close()

        # Generar enlace HTTP para lectura con cámara nativa en red local
        host_local = request.host
        contenido_qr = f"http://{host_local}/alumno/asistencia_directa?token={token_raw}&grupo={grupo_id}&sesion={sesion_id}"

        qr = qrcode.QRCode(version=1, box_size=15, border=4)
        qr.add_data(contenido_qr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return jsonify(
            {
                "status": "ok",
                "sesion_id": sesion_id,
                "qr_base64": qr_base64,
                "parcial": parcial,
                "message": f"Sesión iniciada correctamente - {parcial}° Parcial",
            }
        )

    except Exception as e:
        conexion.rollback()
        if "cursor" in locals():
            cursor.close()
        conexion.close()
        return jsonify({"status": "error", "message": str(e)})


@maestro_bp.route("/obtener_qr_sesion/<int:sesion_id>")
def obtener_qr_sesion(sesion_id):
    if not login_requerido("tutor", "maestro"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    conexion, cursor = obtener_cursor()
    cursor.execute(
        """
        SELECT st.*, COUNT(a.id) as total_asistencias
        FROM sesiones_tutoria st
        LEFT JOIN asistencias_tutoria a ON st.id = a.sesion_id
        WHERE st.id = %s
        GROUP BY st.id
    """,
        (sesion_id,),
    )

    sesion = cursor.fetchone()
    cursor.close()

    if not sesion or sesion.get("activa") == 0:
        conexion.close()
        return jsonify(
            {"status": "sesion_terminada", "message": "La sesión ha terminado"}
        )

    temp_token = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16)
    )
    temp_token_hash = hashlib.sha256(temp_token.encode()).hexdigest()

    conn2, cursor2 = obtener_cursor()
    cursor2.execute(
        """
        UPDATE sesiones_tutoria 
        SET token_actual = %s, fecha_expiracion = DATE_ADD(NOW(), INTERVAL 5 MINUTE)
        WHERE id = %s
    """,
        (temp_token_hash, sesion_id),
    )
    conn2.commit()
    cursor2.close()
    conn2.close()

    host_local = request.host
    contenido_qr = f"http://{host_local}/alumno/asistencia_directa?token={temp_token}&grupo={sesion['grupo_id']}&sesion={sesion_id}"

    qr = qrcode.QRCode(version=1, box_size=15, border=4)
    qr.add_data(contenido_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    conexion.close()
    return jsonify(
        {
            "status": "ok",
            "qr_base64": qr_base64,
            "total_asistencias": sesion["total_asistencias"] or 0,
            "activa": sesion["activa"] == 1,
        }
    )


@maestro_bp.route("/obtener_asistencias_sesion/<int:sesion_id>")
def obtener_asistencias_sesion(sesion_id):
    if not login_requerido("tutor", "maestro"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    conexion, cursor = obtener_cursor()

    # Traemos la fecha completa sin usar DATE_FORMAT() para evitar interferencias con '%'
    cursor.execute(
        """
        SELECT 
            a.alumno_matricula,
            a.fecha_asistencia,
            a.nombre_alumno,
            u.nombre,
            u.ap_paterno
        FROM asistencias_tutoria a
        LEFT JOIN alumnos u ON a.alumno_matricula = u.matricula
        WHERE a.sesion_id = %s
        ORDER BY a.fecha_asistencia DESC
    """,
        (sesion_id,),
    )

    filas = cursor.fetchall()
    cursor.close()
    conexion.close()

    asistencias_limpias = []
    for f in filas:
        if isinstance(f, dict):
            matricula = f.get("alumno_matricula")
            fecha_dt = f.get("fecha_asistencia")
            usr_nom = (
                f"{f.get('nombre', '') or ''} {f.get('ap_paterno', '') or ''}".strip()
            )
            nom = f.get("nombre_alumno") or usr_nom or "Alumno"
        else:
            matricula = f[0]
            fecha_dt = f[1]
            usr_nom = f"{f[3] or ''} {f[4] or ''}".strip()
            nom = f[2] or usr_nom or "Alumno"

        # Formatear la hora desde Python directamente
        hora_str = ""
        if fecha_dt:
            if hasattr(fecha_dt, "strftime"):
                hora_str = fecha_dt.strftime("%H:%M:%S")
            else:
                hora_str = str(fecha_dt)

        asistencias_limpias.append(
            {"matricula": matricula, "hora": hora_str, "nombre": nom}
        )

    return jsonify({"status": "ok", "asistencias": asistencias_limpias})


@maestro_bp.route("/detener_sesion_qr/<int:sesion_id>", methods=["POST"])
def detener_sesion_qr(sesion_id):
    if not login_requerido("tutor", "maestro"):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    conexion, cursor = obtener_cursor()
    cursor.execute(
        "UPDATE sesiones_tutoria SET activa = 0 WHERE id = %s AND tutor_matricula = %s",
        (sesion_id, session["matricula"]),
    )
    conexion.commit()
    cursor.close()
    conexion.close()

    return jsonify({"status": "ok", "message": "Sesión finalizada correctamente"})
