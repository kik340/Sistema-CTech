import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_file,
)

from Class.Laboratorista import LaboratoristaManager
from Class.User import User
from utils.helpers import login_requerido

laboratorista_bp = Blueprint("laboratorista", __name__)

laboratorista_manager = LaboratoristaManager()
usuario = User()


@laboratorista_bp.route("/menu_laboratorista")
def menu_laboratorista():
    if not login_requerido("laboratorista"):
        return redirect(url_for("auth.index"))

    vencidos = laboratorista_manager.actualizar_estado_prestamos()

    pagina = request.args.get("page", 1, type=int)
    por_pagina = 25

    todos_los_equipos = laboratorista_manager.obtener_equipos()
    total_equipos = len(todos_los_equipos)
    total_paginas = max(1, (total_equipos + por_pagina - 1) // por_pagina)

    if pagina < 1:
        pagina = 1
    if pagina > total_paginas:
        pagina = total_paginas

    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina

    equipos = todos_los_equipos[inicio:fin]
    equipos_disponibles = laboratorista_manager.obtener_equipos_disponibles()
    datos_usuario = usuario.obtener_mis_datos(session["matricula"], session["tipo"])

    return render_template(
        "Laboratorista/menu.html",
        nombre=session["nombre"],
        equipos=equipos,
        equipos_disponibles=equipos_disponibles,
        pagina=pagina,
        total_paginas=total_paginas,
        dispositivos_vencidos=vencidos,
        datos_usuario=datos_usuario,
    )


@laboratorista_bp.route("/registrar_equipo", methods=["POST"])
def registrar_equipo():
    if not login_requerido("laboratorista"):
        return redirect(url_for("auth.index"))

    nombre_equipo = request.form.get("nombre_equipo", "").strip()
    categoria = request.form.get("categoria", "").strip()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    numero_serie = request.form.get("numero_serie", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    estado = request.form.get("estado", "disponible").strip()
    ubicacion = request.form.get("ubicacion", "").strip()

    if nombre_equipo == "" or categoria == "":
        return redirect(url_for("laboratorista.menu_laboratorista", r="empty_request"))

    datos = {
        "nombre_equipo": nombre_equipo,
        "categoria": categoria,
        "marca": marca if marca != "" else None,
        "modelo": modelo if modelo != "" else None,
        "numero_serie": numero_serie if numero_serie != "" else None,
        "descripcion": descripcion if descripcion != "" else None,
        "estado": estado if estado != "" else "disponible",
        "ubicacion": ubicacion if ubicacion != "" else None,
    }

    resultado = laboratorista_manager.registrar_equipo(datos)

    if resultado["status"] == "ok":
        return redirect(url_for("laboratorista.menu_laboratorista", r="ok"))

    if resultado["status"] == "exists":
        return redirect(
            url_for("laboratorista.menu_laboratorista", r="equipment_exists")
        )

    return redirect(url_for("laboratorista.menu_laboratorista", r="error"))


@laboratorista_bp.route("/buscar_usuario_qr", methods=["POST"])
def buscar_usuario_qr():
    if not login_requerido("laboratorista"):
        return jsonify({"status": "error", "message": "Acceso no autorizado"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No llegaron datos"}), 400

    contenido_qr = data.get("contenido_qr", "").strip()

    if contenido_qr == "" or "-" not in contenido_qr:
        return jsonify({"status": "error", "message": "Formato de QR inválido"}), 400

    matricula, correo = contenido_qr.split("-", 1)
    matricula = matricula.strip()

    usuario_qr = laboratorista_manager.buscar_usuario_por_matricula(matricula)

    if not usuario_qr:
        return jsonify({"status": "not_found", "message": "Usuario no encontrado"}), 404

    return jsonify({"status": "ok", "usuario": usuario_qr})


@laboratorista_bp.route("/registrar_prestamo", methods=["POST"])
def registrar_prestamo():
    if not login_requerido("laboratorista"):
        return redirect(url_for("auth.index"))

    equipo_id = request.form.get("equipo_id", "").strip()
    matricula_usuario = request.form.get("matricula_usuario", "").strip()
    tipo_usuario = request.form.get("tipo_usuario", "").strip()
    fecha_limite = request.form.get("fecha_limite", "").strip()
    observaciones = request.form.get("observaciones", "").strip()

    if equipo_id == "" or matricula_usuario == "" or tipo_usuario == "":
        return redirect(url_for("laboratorista.menu_laboratorista", r="empty_request"))

    resultado = laboratorista_manager.registrar_prestamo(
        int(equipo_id), matricula_usuario, tipo_usuario, fecha_limite, observaciones
    )

    if resultado["status"] == "ok":
        return redirect(url_for("laboratorista.menu_laboratorista", r="loan_ok"))

    if resultado["status"] == "team_not_found":
        return redirect(
            url_for("laboratorista.menu_laboratorista", r="group_not_found")
        )

    if resultado["status"] in ["not_available", "already_loaned"]:
        return redirect(url_for("laboratorista.menu_laboratorista", r="equipment_busy"))

    return redirect(url_for("laboratorista.menu_laboratorista", r="error"))


@laboratorista_bp.route("/equipos_estado")
def equipos_estado():
    if not login_requerido("laboratorista"):
        return jsonify({"status": "error"}), 403

    vencidos = laboratorista_manager.actualizar_estado_prestamos()
    equipos = laboratorista_manager.obtener_equipos()

    return jsonify({"status": "ok", "equipos": equipos, "vencidos": vencidos})


@laboratorista_bp.route("/generar_excel")
def generar_excel():
    if not login_requerido("laboratorista"):
        return jsonify({"status": "error", "message": "Acceso no autorizado"}), 403

    try:
        template_path = os.path.join(
            "static", "resources", "Bitácora de uso general (Blanco).xlsx"
        )
        nombre_archivo = f"bitacora_generada_{session['matricula']}.xlsx"
        output_path = os.path.join("static", "resources", nombre_archivo)

        laboratorista_manager.generar_excel_bitacora(
            nombre_laboratorio="Laboratorio de Cómputo",
            periodo=datetime.now().strftime("%Y"),
            responsable=session["nombre"],
            template_path=template_path,
            output_path=output_path,
        )

        url_descarga = url_for("static", filename=f"resources/{nombre_archivo}")
        return jsonify({"status": "ok", "download_url": url_descarga})

    except Exception as e:
        print("Error al generar Excel:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
