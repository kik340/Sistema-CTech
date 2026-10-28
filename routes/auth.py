import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Blueprint, render_template, request, redirect, url_for, session
from Class.User import User
from Class.Tutor import TutorManager
from utils.helpers import login_requerido

auth_bp = Blueprint("auth", __name__)
usuario = User()
tutor_manager = TutorManager()


@auth_bp.route("/")
def index():
    session.clear()
    carreras = tutor_manager.obtener_carreras_activas()
    return render_template("index.html", carreras=carreras)


@auth_bp.route("/verificar_usuario", methods=["POST"])
def verificar_usuario():
    matricula = request.form.get("matricula", "").strip()
    password = request.form.get("password", "").strip()

    if matricula == "" or password == "":
        return redirect(url_for("auth.index", r="empty_login"))

    resultado = usuario.login_por_matricula(matricula, password)

    if resultado["status"] != "ok":
        return redirect(url_for("auth.index", r=resultado["status"]))

    session["matricula"] = resultado["matricula"]
    session["nombre"] = resultado["nombre"]
    session["email"] = resultado["email"]
    session["tipo"] = resultado["tipo"]
    session["carrera"] = resultado.get("carrera")

    # Si es alumno, revisar si venía de un escaneo con la cámara nativa
    if resultado["tipo"] in ["alumno", "externo"]:
        if "asistencia_pendiente" in session:
            pendiente = session.pop("asistencia_pendiente")
            return redirect(
                url_for(
                    "alumno.asistencia_directa",
                    token=pendiente["token"],
                    grupo=pendiente["grupo_id"],
                    sesion=pendiente["sesion_id"],
                )
            )
        return redirect(url_for("alumno.menu_alumno"))

    if resultado["tipo"] in ["tutor", "maestro"]:
        return redirect(url_for("maestro.menu_maestro"))
    if resultado["tipo"] == "laboratorista":
        return redirect(url_for("laboratorista.menu_laboratorista"))
    if resultado["tipo"] == "admin":
        return redirect(url_for("admin.menu_admin"))

    session.clear()
    return redirect(url_for("auth.index", r="tipo_wrong"))


@auth_bp.route("/solicitar_registro", methods=["POST"])
def solicitar_registro():
    nombre = request.form.get("nombre", "").strip()
    ap_paterno = request.form.get("ap_paterno", "").strip()
    ap_materno = request.form.get("ap_materno", "").strip()
    correo_temporal = request.form.get("correo_temporal", "").strip()
    password = request.form.get("password", "").strip()
    tipo_solicitud = request.form.get("tipo_solicitud", "").strip()
    carrera_id = request.form.get("carrera_id", "").strip()
    anio_ingreso = request.form.get("anio_ingreso", "").strip()
    motivo = request.form.get("motivo", "").strip()

    if (
        nombre == ""
        or ap_paterno == ""
        or ap_materno == ""
        or correo_temporal == ""
        or password == ""
        or tipo_solicitud == ""
    ):
        return redirect(url_for("auth.index", r="empty_request"))

    if tipo_solicitud == "alumno" and (carrera_id == "" or anio_ingreso == ""):
        return redirect(url_for("auth.index", r="empty_request"))

    if tipo_solicitud == "externo" and motivo == "":
        return redirect(url_for("auth.index", r="empty_request"))

    try:
        anio_ingreso_int = int(anio_ingreso) if anio_ingreso != "" else None
    except Exception:
        return redirect(url_for("auth.index", r="empty_request"))

    datos = {
        "nombre": nombre,
        "ap_paterno": ap_paterno,
        "ap_materno": ap_materno,
        "correo_temporal": correo_temporal,
        "password": password,
        "tipo_solicitud": tipo_solicitud,
        "carrera_id": int(carrera_id) if carrera_id != "" else None,
        "anio_ingreso": anio_ingreso_int,
        "motivo": motivo if motivo != "" else None,
    }

    resultado = usuario.crear_solicitud(datos)
    return redirect(url_for("auth.index", r=resultado["status"]))


@auth_bp.route("/cerrar_sesion")
def cerrar_sesion():
    session.clear()
    return redirect(url_for("auth.index"))


@auth_bp.route("/modificar_mi_usuario", methods=["POST"])
def modificar_mi_usuario():
    if not login_requerido():
        return redirect(url_for("auth.index"))

    nueva_password = request.form.get("nueva_password", "").strip()
    confirmar_password = request.form.get("confirmar_password", "").strip()

    tipo_usuario = session.get("tipo")

    if nueva_password == "" or confirmar_password == "":
        if tipo_usuario in ["tutor", "maestro"]:
            return redirect(url_for("maestro.menu_maestro", r="empty_request"))
        if tipo_usuario == "laboratorista":
            return redirect(
                url_for("laboratorista.menu_laboratorista", r="empty_request")
            )
        if tipo_usuario == "admin":
            return redirect(url_for("admin.menu_admin", r="empty_request"))
        return redirect(url_for("alumno.menu_alumno", r="empty_request"))

    if nueva_password != confirmar_password:
        if tipo_usuario in ["tutor", "maestro"]:
            return redirect(url_for("maestro.menu_maestro", r="password_no_match"))
        if tipo_usuario == "laboratorista":
            return redirect(
                url_for("laboratorista.menu_laboratorista", r="password_no_match")
            )
        if tipo_usuario == "admin":
            return redirect(url_for("admin.menu_admin", r="password_no_match"))
        return redirect(url_for("alumno.menu_alumno", r="password_no_match"))

    resultado = usuario.cambiar_password_usuario(
        session["matricula"], session["tipo"], nueva_password
    )

    if resultado["status"] == "ok":
        session.clear()
        return redirect(url_for("auth.index", r="password_changed"))

    if tipo_usuario in ["tutor", "maestro"]:
        return redirect(url_for("maestro.menu_maestro", r="error"))
    if tipo_usuario == "laboratorista":
        return redirect(url_for("laboratorista.menu_laboratorista", r="error"))
    if tipo_usuario == "admin":
        return redirect(url_for("admin.menu_admin", r="error"))
    return redirect(url_for("alumno.menu_alumno", r="error"))
