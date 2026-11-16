from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from utils.helpers import login_requerido
from Class.Tutor import TutorManager
from db.Conection import obtener_cursor
from Class.User import User

admin_bp = Blueprint("admin", __name__)
tutor_manager = TutorManager()

@admin_bp.route("/menu_admin")
def menu_admin():
    if not login_requerido("admin"):
        return redirect(url_for("auth.index"))
    
    carreras = tutor_manager.obtener_carreras_activas()
    materias = tutor_manager.obtener_materias_activas()
    grupos_sin_tutor = tutor_manager.obtener_grupos_sin_tutor()
    
    # Obtener lista de maestros activos
    conexion, cursor = obtener_cursor()
    cursor.execute("SELECT matricula, nombre_completo FROM personal WHERE tipo = 'tutor' AND activo = 1")
    tutores = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return render_template("Admin/menu.html", 
                           nombre=session.get("nombre"), 
                           carreras=carreras,
                           materias=materias,
                           tutores=tutores,
                           grupos_pendientes=grupos_sin_tutor)

@admin_bp.route("/agregar_carrera", methods=["POST"])
def agregar_carrera():
    if not login_requerido("admin"): return redirect(url_for("auth.index"))
    nombre = request.form.get("nombre")
    resultado = tutor_manager.agregar_carrera(nombre)
    return redirect(url_for("admin.menu_admin", r=resultado["status"]))

@admin_bp.route("/agregar_materia", methods=["POST"])
def agregar_materia():
    if not login_requerido("admin"): return redirect(url_for("auth.index"))
    carrera_id = request.form.get("carrera_id")
    nombre = request.form.get("nombre")
    semestre = request.form.get("semestre")
    resultado = tutor_manager.agregar_materia(carrera_id, nombre, semestre)
    return redirect(url_for("admin.menu_admin", r=resultado["status"]))

@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if not login_requerido("admin"): return redirect(url_for("auth.index"))
    datos = {
        "materia_id": request.form.get("materia_id"),
        "semestre": request.form.get("semestre"),
        "grupo": request.form.get("grupo"),
        "turno": request.form.get("turno"),
        "periodo": request.form.get("periodo"),
        "tutor_matricula": request.form.get("tutor_matricula") or None
    }
    resultado = tutor_manager.crear_grupo(datos)
    return redirect(url_for("admin.menu_admin", r=resultado["status"]))

@admin_bp.route("/asignar_tutor", methods=["POST"])
def asignar_tutor():
    if not login_requerido("admin"): return redirect(url_for("auth.index"))
    grupo_id = request.form.get("grupo_id")
    tutor_matricula = request.form.get("tutor_matricula")
    resultado = tutor_manager.asignar_tutor_a_grupo(grupo_id, tutor_matricula)
    return redirect(url_for("admin.menu_admin", r=resultado["status"]))

@admin_bp.route('/eliminar_materia/<int:materia_id>', methods=['POST'])
def admin_eliminar_materia(materia_id):
    if not login_requerido("admin"):
        return jsonify({"status": "error"})
    
    resultado = tutor_manager.eliminar_materia(materia_id)
    return jsonify(resultado)

@admin_bp.route('/reestablecer_password', methods=['POST'])
def admin_reestablecer_password():
    if not login_requerido("admin"):
        return jsonify({"status": "error", "message": "No autorizado"})
    
    matricula = request.form.get('matricula')
    tipo = request.form.get('tipo') 
    nueva_password = request.form.get('nueva_password')
    
    user_manager = User()
    resultado = user_manager.cambiar_password_usuario(matricula, tipo, nueva_password)
    return jsonify(resultado)