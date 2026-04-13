"""Gestor del módulo de tutor.

Este módulo agrupa operaciones de grupos, carreras, materias y seguimiento
académico de alumnos.
"""

from db.Conection import obtener_cursor


class TutorManager:
    """Agrupa la lógica de carreras, grupos y seguimiento académico."""

    def obtener_grupos_tutor(self, tutor_matricula):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT 
                g.id,
                g.semestre,
                g.grupo,
                g.turno,
                g.periodo,
                c.nombre AS carrera,
                m.nombre AS materia
            FROM grupos g
            INNER JOIN carreras c ON c.id = g.carrera_id
            INNER JOIN materias m ON m.id = g.materia_id
            WHERE g.tutor_matricula = %s AND g.activo = 1
            ORDER BY g.semestre, m.nombre, g.grupo
        """, (tutor_matricula,))

        grupos = cursor.fetchall()
        conexion.close()
        return grupos

    def obtener_alumnos_de_grupo(self, grupo_id):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT 
                a.matricula,
                a.nombre_completo,
                a.email,
                c.nombre AS carrera
            FROM alumnos_grupo ag
            INNER JOIN alumnos a ON a.matricula = ag.alumno_matricula
            INNER JOIN grupos g ON g.id = ag.grupo_id
            INNER JOIN carreras c ON c.id = a.carrera_id
            WHERE ag.grupo_id = %s
              AND ag.activo = 1
              AND a.activo = 1
            ORDER BY a.nombre_completo
        """, (grupo_id,))

        alumnos = cursor.fetchall()
        conexion.close()
        return alumnos

    def obtener_o_crear_seguimiento(self, grupo_id, tutor_matricula, parcial):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT id, grupo_id, tutor_matricula, parcial, total_estudiantes, observaciones
            FROM seguimiento_academico
            WHERE grupo_id = %s AND parcial = %s
            LIMIT 1
        """, (grupo_id, parcial))

        seguimiento = cursor.fetchone()

        if seguimiento:
            conexion.close()
            return seguimiento

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM alumnos_grupo ag
            INNER JOIN alumnos a ON a.matricula = ag.alumno_matricula
            WHERE ag.grupo_id = %s
              AND ag.activo = 1
              AND a.activo = 1
        """, (grupo_id,))
        total = cursor.fetchone()["total"]

        cursor.execute("""
            INSERT INTO seguimiento_academico
            (
                grupo_id,
                tutor_matricula,
                parcial,
                total_estudiantes
            )
            VALUES (%s, %s, %s, %s)
        """, (grupo_id, tutor_matricula, parcial, total))

        seguimiento_id = cursor.lastrowid
        conexion.commit()

        cursor.execute("""
            SELECT id, grupo_id, tutor_matricula, parcial, total_estudiantes, observaciones
            FROM seguimiento_academico
            WHERE id = %s
        """, (seguimiento_id,))
        seguimiento = cursor.fetchone()

        conexion.close()
        return seguimiento

    def obtener_detalle_seguimiento(self, seguimiento_id):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT 
                alumno_matricula,
                asistencia,
                canalizacion_tutoria_individual,
                problemas_economicos,
                problemas_salud,
                problemas_emocionales,
                problemas_familiares,
                problemas_academicos,
                beca_jcf,
                beca_manutencion,
                beca_jmf,
                beca_otro,
                apoyo_psicologico,
                apoyo_medico,
                apoyo_otro,
                promedio,
                materias_reprobadas,
                estatus_aprobado,
                posible_desercion,
                comentario
            FROM seguimiento_detalle
            WHERE seguimiento_id = %s
        """, (seguimiento_id,))

        detalle = cursor.fetchall()
        conexion.close()
        return detalle

    def guardar_detalle_seguimiento(self, seguimiento_id, alumnos, observaciones=None):
        conexion, cursor = obtener_cursor()

        try:
            for alumno in alumnos:
                cursor.execute("""
                    INSERT INTO seguimiento_detalle
                    (
                        seguimiento_id,
                        alumno_matricula,
                        asistencia,
                        canalizacion_tutoria_individual,
                        problemas_economicos,
                        problemas_salud,
                        problemas_emocionales,
                        problemas_familiares,
                        problemas_academicos,
                        beca_jcf,
                        beca_manutencion,
                        beca_jmf,
                        beca_otro,
                        apoyo_psicologico,
                        apoyo_medico,
                        apoyo_otro,
                        promedio,
                        materias_reprobadas,
                        estatus_aprobado,
                        posible_desercion,
                        comentario
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        asistencia = VALUES(asistencia),
                        canalizacion_tutoria_individual = VALUES(canalizacion_tutoria_individual),
                        problemas_economicos = VALUES(problemas_economicos),
                        problemas_salud = VALUES(problemas_salud),
                        problemas_emocionales = VALUES(problemas_emocionales),
                        problemas_familiares = VALUES(problemas_familiares),
                        problemas_academicos = VALUES(problemas_academicos),
                        beca_jcf = VALUES(beca_jcf),
                        beca_manutencion = VALUES(beca_manutencion),
                        beca_jmf = VALUES(beca_jmf),
                        beca_otro = VALUES(beca_otro),
                        apoyo_psicologico = VALUES(apoyo_psicologico),
                        apoyo_medico = VALUES(apoyo_medico),
                        apoyo_otro = VALUES(apoyo_otro),
                        promedio = VALUES(promedio),
                        materias_reprobadas = VALUES(materias_reprobadas),
                        estatus_aprobado = VALUES(estatus_aprobado),
                        posible_desercion = VALUES(posible_desercion),
                        comentario = VALUES(comentario)
                """, (
                    seguimiento_id,
                    alumno["alumno_matricula"],
                    alumno.get("asistencia", 0),
                    alumno.get("canalizacion_tutoria_individual", 0),
                    alumno.get("problemas_economicos", 0),
                    alumno.get("problemas_salud", 0),
                    alumno.get("problemas_emocionales", 0),
                    alumno.get("problemas_familiares", 0),
                    alumno.get("problemas_academicos", 0),
                    alumno.get("beca_jcf", 0),
                    alumno.get("beca_manutencion", 0),
                    alumno.get("beca_jmf", 0),
                    alumno.get("beca_otro", 0),
                    alumno.get("apoyo_psicologico", 0),
                    alumno.get("apoyo_medico", 0),
                    alumno.get("apoyo_otro", 0),
                    alumno.get("promedio"),
                    alumno.get("materias_reprobadas", 0),
                    alumno.get("estatus_aprobado", 0),
                    alumno.get("posible_desercion", 0),
                    alumno.get("comentario")
                ))

            cursor.execute("""
                UPDATE seguimiento_academico
                SET observaciones = %s
                WHERE id = %s
            """, (observaciones, seguimiento_id))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error guardar_detalle_seguimiento:", e)
            return {"status": "error"}



    def obtener_exportacion_seguimiento(self, seguimiento_id):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT *
            FROM seguimiento_academico
            WHERE id = %s
        """, (seguimiento_id,))
        seguimiento = cursor.fetchone()

        if not seguimiento:
            cursor.close()
            conexion.close()
            return None

        cursor.execute("""
            SELECT 
                sd.*,
                sd.alumno_matricula AS matricula,
                COALESCE(a.nombre_completo, sd.alumno_matricula) AS nombre_completo
            FROM seguimiento_detalle sd
            LEFT JOIN alumnos a ON a.matricula = sd.alumno_matricula
            WHERE sd.seguimiento_id = %s
            ORDER BY sd.alumno_matricula ASC
        """, (seguimiento_id,))
        registros = cursor.fetchall()

        alumnos = []
        detalle_map = {}

        for r in registros:
            matricula = r["matricula"]

            alumnos.append({
                "matricula": matricula,
                "nombre_completo": r["nombre_completo"]
            })

            detalle_map[matricula] = r

        seguimiento["total_estudiantes"] = len(alumnos)

        cursor.close()
        conexion.close()

        return {
            "seguimiento": seguimiento,
            "alumnos": alumnos,
            "detalles": registros,
            "detalle_map": detalle_map
        }
    def obtener_resumen_seguimiento(self, seguimiento_id):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(asistencia) AS total_asistencia,
                SUM(canalizacion_tutoria_individual) AS total_canalizados,
                SUM(problemas_economicos) AS total_prob_economicos,
                SUM(problemas_salud) AS total_prob_salud,
                SUM(problemas_emocionales) AS total_prob_emocionales,
                SUM(problemas_familiares) AS total_prob_familiares,
                SUM(problemas_academicos) AS total_prob_academicos,
                SUM(beca_jcf) AS total_beca_jcf,
                SUM(beca_manutencion) AS total_beca_manutencion,
                SUM(beca_jmf) AS total_beca_jmf,
                SUM(beca_otro) AS total_beca_otro,
                SUM(apoyo_psicologico) AS total_apoyo_psicologico,
                SUM(apoyo_medico) AS total_apoyo_medico,
                SUM(apoyo_otro) AS total_apoyo_otro,
                SUM(estatus_aprobado) AS total_aprobados,
                SUM(posible_desercion) AS total_desercion
            FROM seguimiento_detalle
            WHERE seguimiento_id = %s
        """, (seguimiento_id,))

        resumen = cursor.fetchone()
        conexion.close()
        return resumen
    
    def agregar_carrera(self, nombre):
        """Registra una nueva carrera disponible dentro del sistema."""
        conexion, cursor = obtener_cursor()

        try:
            nombre = str(nombre).strip()

            cursor.execute("""
                SELECT id
                FROM carreras
                WHERE nombre = %s
                LIMIT 1
            """, (nombre,))
            existe = cursor.fetchone()

            if existe:
                conexion.close()
                return {"status": "exists"}

            cursor.execute("""
                SELECT id
                FROM carreras
                ORDER BY id ASC
            """)
            filas = cursor.fetchall()

            ids_usados = set()
            for fila in filas:
                ids_usados.add(int(fila["id"]))

            nuevo_id = 1
            while nuevo_id in ids_usados or nuevo_id == 18:
                nuevo_id += 1

            cursor.execute("""
                INSERT INTO carreras (id, nombre, activa)
                VALUES (%s, %s, 1)
            """, (nuevo_id, nombre))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error agregar_carrera:", e)
            return {"status": "error"}
    def agregar_materia(self, carrera_id, nombre, semestre):
        """Crea una nueva materia vinculada a una carrera y semestre."""
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                SELECT id
                FROM carreras
                WHERE id = %s AND activa = 1
                LIMIT 1
            """, (carrera_id,))
            carrera = cursor.fetchone()

            if not carrera:
                conexion.close()
                return {"status": "career_not_found"}

            cursor.execute("""
                SELECT id
                FROM materias
                WHERE carrera_id = %s AND nombre = %s AND semestre = %s
                LIMIT 1
            """, (carrera_id, nombre, semestre))
            existe = cursor.fetchone()

            if existe:
                conexion.close()
                return {"status": "exists"}

            cursor.execute("""
                INSERT INTO materias (carrera_id, nombre, semestre, activa)
                VALUES (%s, %s, %s, 1)
            """, (carrera_id, nombre, semestre))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error agregar_materia:", e)
            return {"status": "error"}

    def obtener_materias_activas(self):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT
                m.id,
                m.nombre,
                m.semestre,
                m.carrera_id,
                m.activa,
                c.nombre AS carrera
            FROM materias m
            INNER JOIN carreras c ON c.id = m.carrera_id
            WHERE m.activa = 1
            ORDER BY c.nombre, m.semestre, m.nombre
        """)

        materias = cursor.fetchall()
        conexion.close()
        return materias

    def obtener_carreras_activas(self):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT id, nombre, activa
            FROM carreras
            WHERE activa = 1
            ORDER BY nombre
        """)

        carreras = cursor.fetchall()
        conexion.close()
        return carreras
    def crear_grupo(self, datos):
        """Crea un grupo académico con carrera, materia, turno y periodo."""
        conexion, cursor = obtener_cursor()

        try:
            materia_id = int(datos["materia_id"])
            semestre = str(datos["semestre"]).strip()
            grupo = str(datos["grupo"]).strip().upper()
            turno = str(datos["turno"]).strip()
            periodo = str(datos["periodo"]).strip().upper()
            tutor_matricula = str(datos.get("tutor_matricula", "")).strip() or None

            # Tomar la carrera directamente desde la materia para evitar errores
            cursor.execute("""
                SELECT
                    m.id,
                    m.carrera_id,
                    m.semestre,
                    m.activa,
                    c.activa AS carrera_activa
                FROM materias m
                INNER JOIN carreras c ON c.id = m.carrera_id
                WHERE m.id = %s
                LIMIT 1
            """, (materia_id,))
            materia = cursor.fetchone()

            if not materia or materia["activa"] != 1 or materia["carrera_activa"] != 1:
                conexion.close()
                return {"status": "subject_not_found"}

            carrera_id = materia["carrera_id"]

            # Si no mandan semestre, usar el de la materia
            if semestre == "":
                semestre = str(materia["semestre"]).strip()

            # Revisar si ya existe el grupo
            cursor.execute("""
                SELECT
                    id,
                    tutor_matricula,
                    activo
                FROM grupos
                WHERE carrera_id = %s
                AND materia_id = %s
                AND semestre = %s
                AND UPPER(TRIM(grupo)) = UPPER(TRIM(%s))
                AND UPPER(TRIM(COALESCE(turno, ''))) = UPPER(TRIM(%s))
                AND UPPER(TRIM(COALESCE(periodo, ''))) = UPPER(TRIM(%s))
                LIMIT 1
            """, (
                carrera_id,
                materia_id,
                semestre,
                grupo,
                turno,
                periodo
            ))
            existe = cursor.fetchone()

            if existe:
                # Si existía inactivo, lo reactivamos
                if existe["activo"] == 0:
                    cursor.execute("""
                        UPDATE grupos
                        SET activo = 1,
                            tutor_matricula = %s
                        WHERE id = %s
                    """, (tutor_matricula, existe["id"]))
                    conexion.commit()
                    conexion.close()
                    return {"status": "ok", "group_id": existe["id"]}

                # Si existe pero no tiene tutor, te lo asigna automáticamente
                if existe["tutor_matricula"] is None and tutor_matricula is not None:
                    cursor.execute("""
                        UPDATE grupos
                        SET tutor_matricula = %s
                        WHERE id = %s
                    """, (tutor_matricula, existe["id"]))
                    conexion.commit()
                    conexion.close()
                    return {"status": "ok", "group_id": existe["id"]}

                conexion.close()
                return {"status": "exists"}

            # Crear grupo ya asignado al tutor que lo creó
            cursor.execute("""
                INSERT INTO grupos
                (
                    carrera_id,
                    materia_id,
                    semestre,
                    grupo,
                    turno,
                    periodo,
                    tutor_matricula,
                    activo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """, (
                carrera_id,
                materia_id,
                semestre,
                grupo,
                turno,
                periodo,
                tutor_matricula
            ))

            group_id = cursor.lastrowid
            conexion.commit()
            conexion.close()
            return {"status": "ok", "group_id": group_id}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error crear_grupo:", e)
            return {"status": "error"}


    def obtener_grupos_sin_tutor(self):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT
                g.id,
                c.nombre AS carrera,
                m.nombre AS materia,
                g.semestre,
                g.grupo,
                g.turno,
                g.periodo
            FROM grupos g
            INNER JOIN carreras c ON c.id = g.carrera_id
            INNER JOIN materias m ON m.id = g.materia_id
            WHERE g.tutor_matricula IS NULL
            AND g.activo = 1
            ORDER BY c.nombre, m.nombre, g.semestre, g.grupo
        """)

        grupos = cursor.fetchall()
        conexion.close()
        return grupos


    def asignar_tutor_a_grupo(self, grupo_id, tutor_matricula):
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                SELECT id, tutor_matricula
                FROM grupos
                WHERE id = %s AND activo = 1
                LIMIT 1
            """, (grupo_id,))
            grupo = cursor.fetchone()

            if not grupo:
                conexion.close()
                return {"status": "not_found"}

            if grupo["tutor_matricula"] is not None:
                conexion.close()
                return {"status": "occupied"}

            cursor.execute("""
                UPDATE grupos
                SET tutor_matricula = %s
                WHERE id = %s
            """, (tutor_matricula, grupo_id))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error asignar_tutor_a_grupo:", e)
            return {"status": "error"}
    def agregar_alumno_a_grupo(self, alumno_matricula, grupo_id):
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                SELECT matricula
                FROM alumnos
                WHERE matricula = %s AND activo = 1
                LIMIT 1
            """, (alumno_matricula,))
            alumno = cursor.fetchone()

            if not alumno:
                conexion.close()
                return {"status": "student_not_found"}

            cursor.execute("""
                SELECT id
                FROM grupos
                WHERE id = %s AND activo = 1
                LIMIT 1
            """, (grupo_id,))
            grupo = cursor.fetchone()

            if not grupo:
                conexion.close()
                return {"status": "group_not_found"}

            cursor.execute("""
                SELECT id
                FROM alumnos_grupo
                WHERE alumno_matricula = %s AND grupo_id = %s
                LIMIT 1
            """, (alumno_matricula, grupo_id))
            existe = cursor.fetchone()

            if existe:
                conexion.close()
                return {"status": "exists"}

            cursor.execute("""
                INSERT INTO alumnos_grupo (alumno_matricula, grupo_id, activo)
                VALUES (%s, %s, 1)
            """, (alumno_matricula, grupo_id))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error agregar_alumno_a_grupo:", e)
            return {"status": "error"}


    def obtener_alumnos_por_grupo(self, grupo_id):
        conexion, cursor = obtener_cursor()

        cursor.execute("""
            SELECT
                a.matricula,
                a.nombre_completo,
                a.email
            FROM alumnos_grupo ag
            INNER JOIN alumnos a ON a.matricula = ag.alumno_matricula
            WHERE ag.grupo_id = %s
            AND ag.activo = 1
            AND a.activo = 1
            ORDER BY a.nombre_completo
        """, (grupo_id,))

        alumnos = cursor.fetchall()
        conexion.close()
        return alumnos


    def quitar_alumno_de_grupo(self, alumno_matricula, grupo_id):
        conexion, cursor = obtener_cursor()

        try:
            cursor.execute("""
                UPDATE alumnos_grupo
                SET activo = 0
                WHERE alumno_matricula = %s AND grupo_id = %s
            """, (alumno_matricula, grupo_id))

            conexion.commit()
            conexion.close()
            return {"status": "ok"}

        except Exception as e:
            conexion.rollback()
            conexion.close()
            print("Error quitar_alumno_de_grupo:", e)
            return {"status": "error"}
