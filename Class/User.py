"""Gestor principal de usuarios del sistema.

Aquí se concentra la lógica de acceso, solicitudes, alumnos, externos, personal
y operaciones comunes relacionadas con cuentas.
"""

from db.Conection import obtener_cursor
from datetime import datetime, timedelta
import random
import re
from Class.EmailManager import EmailSender
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    """Concentra la lógica principal de autenticación, altas y consultas de usuarios."""

    def existe_matricula_global(self, matricula):
        conexion, cursor = obtener_cursor()

        cursor.execute("SELECT id FROM alumnos WHERE matricula=%s", (matricula,))
        if cursor.fetchone():
            conexion.close()
            return True

        cursor.execute("SELECT id FROM externos WHERE matricula=%s", (matricula,))
        if cursor.fetchone():
            conexion.close()
            return True

        cursor.execute("SELECT id FROM personal WHERE matricula=%s", (matricula,))
        existe = cursor.fetchone() is not None

        conexion.close()
        return existe

    def existe_email_global(self, email):
        conexion, cursor = obtener_cursor()

        cursor.execute("SELECT id FROM alumnos WHERE email=%s", (email,))
        if cursor.fetchone():
            conexion.close()
            return True

        cursor.execute("SELECT id FROM externos WHERE email=%s", (email,))
        if cursor.fetchone():
            conexion.close()
            return True

        cursor.execute("SELECT id FROM personal WHERE email=%s", (email,))
        existe = cursor.fetchone() is not None

        conexion.close()
        return existe

    def generar_matricula(self, codigo_tipo):
        while True:
            anio = datetime.now().year
            consecutivo = str(random.randint(1000, 9999))
            matricula = f"{anio}{codigo_tipo}{consecutivo}"

            if not self.existe_matricula_global(matricula):
                return matricula

    def limpiar_texto(self, texto):
        texto = texto.lower().strip()
        reemplazos = {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "ñ": "n"
        }

        for a, b in reemplazos.items():
            texto = texto.replace(a, b)

        texto = re.sub(r"[^a-z0-9 ]", "", texto)
        return texto
    def obtener_datos_carrera(self, carrera_id):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT id, nombre
            FROM carreras
            WHERE id = %s
            LIMIT 1
        """, (carrera_id,))

        carrera = cursor.fetchone()
        conexion.close()
        return carrera


    def generar_base_matricula_alumno(self, carrera_id, anio_ingreso):
        carrera = self.obtener_datos_carrera(carrera_id)

        if not carrera:
            return None

        siglas = self.generar_siglas_carrera(carrera["nombre"])
        anio_2 = str(anio_ingreso)[-2:]
        carrera_2 = str(carrera["id"]).zfill(2)

        return f"{siglas}{anio_2}{carrera_2}"
    def generar_matricula_personal(self, tipo):
        tipo = str(tipo).strip().lower()

        if tipo == "tutor":
            prefijo = "TT"
        elif tipo == "laboratorista":
            prefijo = "LB"
        else:
            prefijo = "PS"

        anio_2 = datetime.now().strftime("%y")

        intentos = 0
        max_intentos = 500

        while intentos < max_intentos:
            sufijo = str(random.randint(0, 9999)).zfill(4)
            matricula = f"{prefijo}{anio_2}{sufijo}"

            if not self.existe_matricula_global(matricula):
                return matricula

            intentos += 1

        return None


    def generar_email_personal(self, matricula):
        return f"{matricula}@itsatlixco.edu.mx"

    def generar_matricula_alumno(self, carrera_id, anio_ingreso):
        base = self.generar_base_matricula_alumno(carrera_id, anio_ingreso)

        if not base:
            return None

        intentos = 0
        max_intentos = 300

        while intentos < max_intentos:
            sufijo = str(random.randint(0, 99)).zfill(2)
            matricula = f"{base}{sufijo}"

            if not self.existe_matricula_global(matricula):
                return matricula

            intentos += 1

        return None

    def generar_siglas_carrera(self, nombre_carrera):
        nombre_carrera = (nombre_carrera or "").strip()

        if nombre_carrera == "":
            return "XX"

        palabras_originales = [p for p in nombre_carrera.split() if p]

        iniciales_mayusculas = ""
        for palabra in palabras_originales:
            primera = palabra[:1]
            if primera.isalpha() and primera.isupper():
                iniciales_mayusculas += primera

        if len(iniciales_mayusculas) >= 2:
            return iniciales_mayusculas[:2]

        texto = self.limpiar_texto(nombre_carrera)
        palabras = [p for p in texto.split() if p]

        if len(palabras) >= 2:
            return (palabras[0][0] + palabras[1][0]).upper()

        limpio = texto.replace(" ", "")
        if len(limpio) >= 2:
            return limpio[:2].upper()

        return "XX"

    def generar_base_matricula_alumno(self, carrera_id, anio_ingreso):
        carrera = self.obtener_datos_carrera(carrera_id)

        if not carrera:
            return None

        siglas = self.generar_siglas_carrera(carrera["nombre"])
        anio_2 = str(anio_ingreso)[-2:]
        carrera_2 = str(carrera["id"]).zfill(2)

        return f"{siglas}{anio_2}{carrera_2}"


    def generar_matricula_alumno(self, carrera_id, anio_ingreso):
        base = self.generar_base_matricula_alumno(carrera_id, anio_ingreso)

        if not base:
            return None

        intentos = 0
        max_intentos = 300

        while intentos < max_intentos:
            sufijo = str(random.randint(0, 99)).zfill(2)
            matricula = f"{base}{sufijo}"

            if not self.existe_matricula_global(matricula):
                return matricula

            intentos += 1

        return None

    def generar_email_institucional(self, ap_paterno, ap_materno, matricula):
        return f"{matricula}@itsatlixco.edu.mx"
    def generar_email_externo(self, matricula):
        return f"EE{matricula}@itsatlixco.edu.mx"

    def crear_solicitud(self, datos):
        tipo_solicitud = str(datos["tipo_solicitud"]).strip().lower()

        if tipo_solicitud == "alumno":
            resultado = self.registrar_alumno_directo(datos, guardar_en_solicitudes=True)
            if resultado["status"] == "ok":
                return {"status": "request_ok"}
            return resultado

        if tipo_solicitud == "tutor":
            resultado = self.registrar_personal_directo({
                "nombre": datos["nombre"],
                "ap_paterno": datos["ap_paterno"],
                "ap_materno": datos["ap_materno"],
                "correo_temporal": datos["correo_temporal"],
                "password": datos["password"],
                "tipo": "tutor"
            })
            if resultado["status"] == "ok":
                return {"status": "request_ok"}
            return resultado

        conexion, cursor = obtener_cursor()

        try:
            nombre_completo = f'{datos["nombre"]} {datos["ap_paterno"]} {datos["ap_materno"]}'
            password_hash = generate_password_hash(datos["password"])

            cursor.execute("""
                INSERT INTO solicitudes_registro
                (
                    nombre,
                    ap_paterno,
                    ap_materno,
                    nombre_completo,
                    correo_temporal,
                    password,
                    tipo_solicitud,
                    carrera_id,
                    anio_ingreso,
                    motivo,
                    estado
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pendiente')
            """, (
                datos["nombre"],
                datos["ap_paterno"],
                datos["ap_materno"],
                nombre_completo,
                datos["correo_temporal"],
                password_hash,
                datos["tipo_solicitud"],
                datos.get("carrera_id"),
                datos.get("anio_ingreso"),
                datos.get("motivo")
            ))

            conexion.commit()
            conexion.close()
            return {"status": "request_ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error crear_solicitud:", e)
            return {"status": "error"}



    def obtener_solicitudes_pendientes(self, limit=None, offset=0):
        conexion, cursor = obtener_cursor()

        sql = """
            SELECT 
                s.id,
                s.nombre,
                s.ap_paterno,
                s.ap_materno,
                s.nombre_completo,
                s.correo_temporal,
                s.tipo_solicitud,
                s.motivo,
                s.estado,
                s.fecha_creacion,
                c.nombre AS carrera
            FROM solicitudes_registro s
            LEFT JOIN carreras c ON c.id = s.carrera_id
            WHERE s.tipo_solicitud IN ('alumno','externo')
              AND s.estado IN ('pendiente','aprobada')
            ORDER BY 
                CASE WHEN s.estado = 'pendiente' THEN 0 ELSE 1 END,
                s.fecha_creacion DESC
        """

        if limit is not None:
            sql += " LIMIT %s OFFSET %s"
            cursor.execute(sql, (limit, offset))
        else:
            cursor.execute(sql)

        solicitudes = cursor.fetchall()
        conexion.close()
        return solicitudes

    def contar_solicitudes_visibles(self):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM solicitudes_registro
            WHERE tipo_solicitud IN ('alumno','externo')
              AND estado IN ('pendiente','aprobada')
        """)

        total = cursor.fetchone()["total"]
        conexion.close()
        return total


    def aprobar_solicitud(self, solicitud_id):
        """Aprueba una solicitud de registro pendiente desde el módulo de tutor."""
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                SELECT 
                    s.*
                FROM solicitudes_registro s
                WHERE s.id=%s AND s.estado='pendiente'
            """, (solicitud_id,))
            solicitud = cursor.fetchone()

            if not solicitud:
                conexion.close()
                return {"status": "not_found"}

            if solicitud["tipo_solicitud"] == "alumno":
                if not solicitud["carrera_id"] or not solicitud["anio_ingreso"]:
                    conexion.close()
                    return {"status": "empty_request"}

                matricula = self.generar_matricula_alumno(
                    solicitud["carrera_id"],
                    int(solicitud["anio_ingreso"])
                )

                if not matricula:
                    conexion.close()
                    return {"status": "error_matricula"}

                email = self.generar_email_institucional(
                    solicitud["ap_paterno"],
                    solicitud["ap_materno"],
                    matricula
                )

                reintentos_email = 0
                while self.existe_email_global(email) and reintentos_email < 300:
                    matricula = self.generar_matricula_alumno(
                        solicitud["carrera_id"],
                        int(solicitud["anio_ingreso"])
                    )

                    if not matricula:
                        conexion.close()
                        return {"status": "error_matricula"}

                    email = self.generar_email_institucional(
                        solicitud["ap_paterno"],
                        solicitud["ap_materno"],
                        matricula
                    )
                    reintentos_email += 1

                if self.existe_email_global(email):
                    conexion.close()
                    return {"status": "email_exists"}

                cursor.execute("""
                    INSERT INTO alumnos
                    (
                        matricula,
                        nombre,
                        ap_paterno,
                        ap_materno,
                        nombre_completo,
                        email,
                        password,
                        carrera_id,
                        anio_ingreso
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    matricula,
                    solicitud["nombre"],
                    solicitud["ap_paterno"],
                    solicitud["ap_materno"],
                    solicitud["nombre_completo"],
                    email,
                    solicitud["password"],
                    solicitud["carrera_id"],
                    solicitud["anio_ingreso"]
                ))

            elif solicitud["tipo_solicitud"] == "externo":
                matricula = "EX" + datetime.now().strftime("%y") + str(random.randint(1000, 9999))
                email = self.generar_email_externo(matricula)

                if self.existe_email_global(email):
                    conexion.close()
                    return {"status": "email_exists"}

                fecha_expiracion = datetime.now() + timedelta(days=1)

                cursor.execute("""
                    INSERT INTO externos
                    (
                        matricula,
                        nombre,
                        ap_paterno,
                        ap_materno,
                        nombre_completo,
                        email,
                        password,
                        motivo,
                        qr_temporal,
                        fecha_expiracion
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    matricula,
                    solicitud["nombre"],
                    solicitud["ap_paterno"],
                    solicitud["ap_materno"],
                    solicitud["nombre_completo"],
                    email,
                    solicitud["password"],
                    solicitud["motivo"],
                    1,
                    fecha_expiracion
                ))

            else:
                conexion.close()
                return {"status": "tipo_wrong"}

            cursor.execute("""
                UPDATE solicitudes_registro
                SET estado='aprobada'
                WHERE id=%s
            """, (solicitud_id,))

            conexion.commit()

            email_sender = EmailSender()
            email_sender.enviar_datos_acceso(
                destino=solicitud["correo_temporal"],
                nombre=solicitud["nombre_completo"],
                matricula=matricula,
                email_institucional=email
            )

            conexion.close()

            return {
                "status": "ok",
                "matricula": matricula,
                "email": email,
                "correo_temporal": solicitud["correo_temporal"]
            }

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error aprobar_solicitud:", e)
            return {"status": "error"}

    def rechazar_solicitud(self, solicitud_id):
        """Rechaza una solicitud de registro pendiente desde el módulo de tutor."""
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                UPDATE solicitudes_registro
                SET estado='rechazada'
                WHERE id=%s AND estado='pendiente'
            """, (solicitud_id,))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error rechazar_solicitud:", e)
            return {"status": "error"}
    def login_por_matricula(self, matricula, password):
        conexion, cursor = obtener_cursor()

        try:
            matricula = str(matricula).strip()

            if matricula == "":
                conexion.close()
                return {"status": "empty_login"}

            cursor.execute("""
                SELECT
                    matricula,
                    nombre_completo,
                    email,
                    password,
                    'alumno' AS tipo,
                    carrera_id,
                    activo
                FROM alumnos
                WHERE matricula = %s
                LIMIT 1
            """, (matricula,))
            usuario = cursor.fetchone()

            if not usuario:
                cursor.execute("""
                    SELECT
                        matricula,
                        nombre_completo,
                        email,
                        password,
                        'externo' AS tipo,
                        NULL AS carrera_id,
                        activo
                    FROM externos
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                usuario = cursor.fetchone()

            if not usuario:
                cursor.execute("""
                    SELECT
                        matricula,
                        nombre_completo,
                        email,
                        password,
                        tipo,
                        carrera_id,
                        activo
                    FROM personal
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                usuario = cursor.fetchone()

            conexion.close()

            if not usuario:
                return {"status": "user_wrong"}

            if int(usuario["activo"]) != 1:
                return {"status": "inactive_user"}

            if not check_password_hash(usuario["password"], password):
                return {"status": "password_wrong"}

            return {
                "status": "ok",
                "matricula": usuario["matricula"],
                "nombre": usuario["nombre_completo"],
                "email": usuario["email"],
                "tipo": usuario["tipo"],
                "carrera": usuario.get("carrera_id")
            }

        except Exception as e:
            conexion.close()
            print("Error login_por_matricula:", e)
            return {"status": "error"}

    def buscar_alumno_por_matricula(self, matricula):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT 
                a.matricula,
                a.nombre_completo,
                a.email,
                c.nombre AS carrera
            FROM alumnos a
            INNER JOIN carreras c ON c.id = a.carrera_id
            WHERE a.matricula=%s AND a.activo=1
            LIMIT 1
        """, (matricula,))

        alumno = cursor.fetchone()
        conexion.close()
        return alumno

    def buscar_externo_por_matricula(self, matricula):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT matricula, nombre_completo, email, motivo, fecha_expiracion
            FROM externos
            WHERE matricula=%s AND activo=1
            LIMIT 1
        """, (matricula,))

        externo = cursor.fetchone()
        conexion.close()
        return externo

    def limpiar_externos_expirados(self):
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                DELETE FROM externos
                WHERE qr_temporal=1
                  AND fecha_expiracion IS NOT NULL
                  AND fecha_expiracion < NOW()
            """)
            conexion.commit()
            conexion.close()
            return True

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error limpiar_externos_expirados:", e)
            return False

    def obtener_mis_datos(self, matricula, tipo):
        conexion, cursor = obtener_cursor()

        try:
            matricula = str(matricula).strip()
            tipo = str(tipo).strip().lower()

            if tipo in ["tutor", "laboratorista"]:
                cursor.execute("""
                    SELECT
                        matricula,
                        nombre,
                        ap_paterno,
                        ap_materno,
                        email,
                        correo_temporal,
                        tipo,
                        activo
                    FROM personal
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                datos = cursor.fetchone()
                conexion.close()
                return datos

            if tipo == "alumno":
                cursor.execute("""
                    SELECT
                        matricula,
                        nombre,
                        ap_paterno,
                        ap_materno,
                        email,
                        NULL AS correo_temporal,
                        'alumno' AS tipo,
                        activo
                    FROM alumnos
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                datos = cursor.fetchone()
                conexion.close()
                return datos

            if tipo == "externo":
                cursor.execute("""
                    SELECT
                        matricula,
                        nombre,
                        ap_paterno,
                        ap_materno,
                        email,
                        email AS correo_temporal,
                        'externo' AS tipo,
                        activo
                    FROM externos
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                datos = cursor.fetchone()
                conexion.close()
                return datos

            conexion.close()
            return None

        except Exception as e:
            conexion.close()
            print("Error obtener_mis_datos:", e)
            return None

    def registrar_alumno_directo(self, datos, guardar_en_solicitudes=True):
        conexion, cursor = obtener_cursor()

        try:
            nombre = str(datos["nombre"]).strip()
            ap_paterno = str(datos["ap_paterno"]).strip()
            ap_materno = str(datos["ap_materno"]).strip()
            nombre_completo = f"{nombre} {ap_paterno} {ap_materno}"
            correo_temporal = str(datos["correo_temporal"]).strip()
            carrera_id = datos.get("carrera_id")
            anio_ingreso = datos.get("anio_ingreso")

            if not carrera_id or not anio_ingreso:
                conexion.close()
                return {"status": "empty_request"}

            anio_ingreso = int(anio_ingreso)

            password_hash = datos.get("password_hash")
            if not password_hash:
                password_hash = generate_password_hash(datos["password"])

            matricula = self.generar_matricula_alumno(carrera_id, anio_ingreso)

            if not matricula:
                conexion.close()
                return {"status": "error_matricula"}

            email_institucional = self.generar_email_institucional(
                ap_paterno,
                ap_materno,
                matricula
            )

            reintentos_email = 0
            while self.existe_email_global(email_institucional) and reintentos_email < 300:
                matricula = self.generar_matricula_alumno(carrera_id, anio_ingreso)

                if not matricula:
                    conexion.close()
                    return {"status": "error_matricula"}

                email_institucional = self.generar_email_institucional(
                    ap_paterno,
                    ap_materno,
                    matricula
                )
                reintentos_email += 1

            if self.existe_email_global(email_institucional):
                conexion.close()
                return {"status": "email_exists"}

            cursor.execute("""
                INSERT INTO alumnos
                (
                    matricula,
                    nombre,
                    ap_paterno,
                    ap_materno,
                    nombre_completo,
                    email,
                    password,
                    carrera_id,
                    anio_ingreso
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                matricula,
                nombre,
                ap_paterno,
                ap_materno,
                nombre_completo,
                email_institucional,
                password_hash,
                carrera_id,
                anio_ingreso
            ))

            if guardar_en_solicitudes:
                cursor.execute("""
                    INSERT INTO solicitudes_registro
                    (
                        nombre,
                        ap_paterno,
                        ap_materno,
                        nombre_completo,
                        correo_temporal,
                        password,
                        tipo_solicitud,
                        carrera_id,
                        anio_ingreso,
                        motivo,
                        estado
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    nombre,
                    ap_paterno,
                    ap_materno,
                    nombre_completo,
                    correo_temporal,
                    password_hash,
                    "alumno",
                    carrera_id,
                    anio_ingreso,
                    None,
                    "aprobada"
                ))

            conexion.commit()
            conexion.close()

            try:
                EmailSender().enviar_datos_acceso(
                    destino=correo_temporal,
                    nombre=nombre_completo,
                    matricula=matricula,
                    email_institucional=email_institucional
                )
            except Exception as e:
                print("Error enviando correo alumno:", e)

            return {
                "status": "ok",
                "matricula": matricula,
                "email": email_institucional,
                "correo_temporal": correo_temporal
            }

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error registrar_alumno_directo:", e)
            return {"status": "error"}
    def registrar_personal_directo(self, datos):
        conexion, cursor = obtener_cursor()

        try:
            nombre = str(datos["nombre"]).strip()
            ap_paterno = str(datos["ap_paterno"]).strip()
            ap_materno = str(datos["ap_materno"]).strip()
            nombre_completo = f"{nombre} {ap_paterno} {ap_materno}"
            correo_temporal = str(datos["correo_temporal"]).strip()
            password_hash = generate_password_hash(datos["password"])
            tipo = str(datos["tipo"]).strip().lower()

            if tipo not in ["tutor", "laboratorista"]:
                conexion.close()
                return {"status": "tipo_wrong"}

            matricula = self.generar_matricula_personal(tipo)

            if not matricula:
                conexion.close()
                return {"status": "error_matricula"}

            email_institucional = self.generar_email_personal(matricula)

            reintentos = 0
            while self.existe_email_global(email_institucional) and reintentos < 500:
                matricula = self.generar_matricula_personal(tipo)

                if not matricula:
                    conexion.close()
                    return {"status": "error_matricula"}

                email_institucional = self.generar_email_personal(matricula)
                reintentos += 1

            if self.existe_email_global(email_institucional):
                conexion.close()
                return {"status": "email_exists"}

            cursor.execute("""
                INSERT INTO personal
                (
                    matricula,
                    nombre,
                    ap_paterno,
                    ap_materno,
                    nombre_completo,
                    email,
                    correo_temporal,
                    password,
                    tipo,
                    activo
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            """, (
                matricula,
                nombre,
                ap_paterno,
                ap_materno,
                nombre_completo,
                email_institucional,
                correo_temporal,
                password_hash,
                tipo
            ))

            conexion.commit()
            conexion.close()

            try:
                EmailSender().enviar_datos_acceso(
                    destino=correo_temporal,
                    nombre=nombre_completo,
                    matricula=matricula,
                    email_institucional=email_institucional
                )
            except Exception as e:
                print("Error enviando correo personal:", e)

            return {
                "status": "ok",
                "matricula": matricula,
                "email": email_institucional,
                "correo_temporal": correo_temporal
            }

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error registrar_personal_directo:", e)
            return {"status": "error"}
    def cambiar_password_personal(self, matricula, nueva_password):
        conexion, cursor = obtener_cursor()

        try:
            password_hash = generate_password_hash(nueva_password)

            cursor.execute("""
                UPDATE personal
                SET password = %s
                WHERE matricula = %s AND activo = 1
            """, (password_hash, matricula))

            if cursor.rowcount == 0:
                conexion.close()
                return {"status": "not_found"}

            cursor.execute("SHOW COLUMNS FROM personal LIKE 'correo_temporal'")
            tiene_correo_temporal = cursor.fetchone() is not None

            if tiene_correo_temporal:
                cursor.execute("""
                    SELECT nombre_completo, correo_temporal, email
                    FROM personal
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
            else:
                cursor.execute("""
                    SELECT nombre_completo, email AS correo_temporal, email
                    FROM personal
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))

            personal = cursor.fetchone()

            conexion.commit()
            conexion.close()

            if personal:
                destino = personal["correo_temporal"] or personal["email"]
                try:
                    EmailSender().enviar_correo_confirmacion_password(
                        destino=destino,
                        nombre=personal["nombre_completo"],
                        matricula=matricula,
                        email_institucional=personal["email"]
                    )
                except Exception as e:
                    print("Error enviando correo de confirmación:", e)

            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error cambiar_password_personal:", e)
            return {"status": "error"}


    def obtener_grupos_disponibles_para_alumno(self, matricula):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT carrera_id
            FROM alumnos
            WHERE matricula = %s AND activo = 1
            LIMIT 1
        """, (matricula,))
        alumno = cursor.fetchone()

        if not alumno:
            conexion.close()
            return []

        carrera_id = alumno["carrera_id"]

        cursor.execute("""
            SELECT
                g.id,
                m.nombre AS materia,
                m.id AS materia_id,
                g.semestre,
                g.grupo,
                g.turno,
                g.periodo,
                c.nombre AS carrera,
                CASE
                    WHEN ag.id IS NULL THEN 0
                    ELSE 1
                END AS inscrito
            FROM grupos g
            INNER JOIN materias m ON m.id = g.materia_id
            INNER JOIN carreras c ON c.id = g.carrera_id
            LEFT JOIN alumnos_grupo ag
                ON ag.grupo_id = g.id
               AND ag.alumno_matricula = %s
               AND ag.activo = 1
            WHERE g.carrera_id = %s
              AND g.activo = 1
              AND m.activa = 1
            ORDER BY CAST(g.semestre AS UNSIGNED), m.nombre, g.grupo
        """, (matricula, carrera_id))

        grupos = cursor.fetchall()
        conexion.close()
        return grupos

    def inscribir_alumno_a_grupo(self, matricula, grupo_id):
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                SELECT matricula, carrera_id
                FROM alumnos
                WHERE matricula = %s AND activo = 1
                LIMIT 1
            """, (matricula,))
            alumno = cursor.fetchone()

            if not alumno:
                conexion.close()
                return {"status": "student_not_found"}

            cursor.execute("""
                SELECT id, carrera_id
                FROM grupos
                WHERE id = %s AND activo = 1
                LIMIT 1
            """, (grupo_id,))
            grupo = cursor.fetchone()

            if not grupo:
                conexion.close()
                return {"status": "group_not_found"}

            if int(alumno["carrera_id"]) != int(grupo["carrera_id"]):
                conexion.close()
                return {"status": "wrong_career"}

            cursor.execute("""
                SELECT id, activo
                FROM alumnos_grupo
                WHERE alumno_matricula = %s AND grupo_id = %s
                LIMIT 1
            """, (matricula, grupo_id))
            existe = cursor.fetchone()

            if existe and int(existe["activo"]) == 1:
                conexion.close()
                return {"status": "exists"}

            if existe and int(existe["activo"]) == 0:
                cursor.execute("""
                    UPDATE alumnos_grupo
                    SET activo = 1
                    WHERE id = %s
                """, (existe["id"],))
            else:
                cursor.execute("""
                    INSERT INTO alumnos_grupo (alumno_matricula, grupo_id, activo)
                    VALUES (%s, %s, 1)
                """, (matricula, grupo_id))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error inscribir_alumno_a_grupo:", e)
            return {"status": "error"}
    def cambiar_password_usuario(self, matricula, tipo, nueva_password):
        conexion, cursor = obtener_cursor()

        try:
            matricula = str(matricula).strip()
            tipo = str(tipo).strip().lower()
            password_hash = generate_password_hash(nueva_password)

            if tipo in ["tutor", "laboratorista"]:
                cursor.execute("""
                    UPDATE personal
                    SET password = %s
                    WHERE matricula = %s
                    LIMIT 1
                """, (password_hash, matricula))

                cursor.execute("""
                    SELECT nombre_completo, correo_temporal, email
                    FROM personal
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                usuario = cursor.fetchone()

            elif tipo == "alumno":
                cursor.execute("""
                    UPDATE alumnos
                    SET password = %s
                    WHERE matricula = %s
                    LIMIT 1
                """, (password_hash, matricula))

                cursor.execute("""
                    SELECT nombre_completo, NULL AS correo_temporal, email
                    FROM alumnos
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                usuario = cursor.fetchone()

            elif tipo == "externo":
                cursor.execute("""
                    UPDATE externos
                    SET password = %s
                    WHERE matricula = %s
                    LIMIT 1
                """, (password_hash, matricula))

                cursor.execute("""
                    SELECT nombre_completo, email AS correo_temporal, email
                    FROM externos
                    WHERE matricula = %s
                    LIMIT 1
                """, (matricula,))
                usuario = cursor.fetchone()

            else:
                conexion.close()
                return {"status": "tipo_wrong"}

            conexion.commit()
            conexion.close()

            try:
                if usuario:
                    destino = usuario["correo_temporal"] if usuario["correo_temporal"] else usuario["email"]

                    if destino:
                        EmailSender().enviar_cambio_password(
                            destino=destino,
                            nombre=usuario["nombre_completo"],
                            matricula=matricula
                        )
            except Exception as e:
                print("Error enviando correo por cambio de contraseña:", e)

            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error cambiar_password_usuario:", e)
            return {"status": "error"}
