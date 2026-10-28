# Class/TokenManager.py
"""Gestión de tokens de asistencia con rotación por escaneo"""

import secrets
import hashlib
from datetime import datetime, timedelta
from db.Conection import obtener_cursor


class TokenManager:
    """Genera y valida tokens que cambian con cada escaneo"""

    def __init__(self):
        pass

    def generar_token_unico(self, grupo_id, tutor_matricula, sesion_id=None):
        """
        Genera un token único para un uso.
        Si se proporciona sesion_id, se actualiza el token de esa sesión.
        """
        conexion, cursor = obtener_cursor()

        # Crear token único
        token_raw = secrets.token_urlsafe(16)
        token_hash = hashlib.sha256(token_raw.encode()).hexdigest()

        fecha_expiracion = datetime.now() + timedelta(minutes=2)  # 2 minutos de vida

        try:
            if sesion_id:
                # Actualizar token existente
                cursor.execute(
                    """
                    UPDATE sesiones_tutoria 
                    SET token_actual = %s, 
                        token_anterior = token_actual,
                        fecha_expiracion = %s,
                        usado = 0
                    WHERE id = %s
                """,
                    (token_hash, fecha_expiracion, sesion_id),
                )
                conexion.commit()
            else:
                # Crear nueva sesión de tutoría
                cursor.execute(
                    """
                    INSERT INTO sesiones_tutoria 
                    (token_actual, grupo_id, tutor_matricula, fecha_expiracion, fecha_inicio)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (
                        token_hash,
                        grupo_id,
                        tutor_matricula,
                        fecha_expiracion,
                        datetime.now(),
                    ),
                )
                conexion.commit()
                sesion_id = cursor.lastrowid

            return {
                "status": "ok",
                "contenido_qr": f"TUTORIA|{token_raw}|{grupo_id}|{sesion_id}",
                "token": token_raw,
                "sesion_id": sesion_id,
                "expira_en": 2,
            }

        except Exception as e:
            conexion.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            cursor.close()
            conexion.close()

    def escanear_y_rotar_token(self, contenido_qr, alumno_matricula):
        """
        Procesa el escaneo, registra asistencia y rota el token inmediatamente
        """
        conexion, cursor = obtener_cursor()

        # Parsear QR: TUTORIA|token_raw|grupo_id|sesion_id
        if not contenido_qr.startswith("TUTORIA|"):
            return {"status": "error", "message": "QR inválido"}

        partes = contenido_qr.split("|")
        if len(partes) != 4:
            return {"status": "error", "message": "Formato QR inválido"}

        _, token_raw, grupo_id_str, sesion_id_str = partes
        grupo_id = int(grupo_id_str)
        sesion_id = int(sesion_id_str)

        token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
        ahora = datetime.now()

        # Verificar token en la sesión activa
        cursor.execute(
            """
            SELECT st.*, g.grupo as grupo_letra 
            FROM sesiones_tutoria st
            JOIN grupos g ON st.grupo_id = g.id
            WHERE st.id = %s 
            AND st.token_actual = %s
            AND st.usado = 0
            AND st.fecha_expiracion > %s
        """,
            (sesion_id, token_hash, ahora),
        )

        sesion = cursor.fetchone()

        if not sesion:
            # Verificar si ya fue usado (token anterior)
            cursor.execute(
                """
                SELECT * FROM sesiones_tutoria 
                WHERE id = %s AND token_anterior = %s
            """,
                (sesion_id, token_hash),
            )

            token_anterior = cursor.fetchone()
            if token_anterior:
                return {
                    "status": "error",
                    "message": "⚠️ Este QR ya fue usado. ¡Solicita un QR nuevo al tutor!",
                }

            return {
                "status": "error",
                "message": "❌ QR expirado o inválido. Solicita un nuevo QR al tutor",
            }

        # Verificar que el alumno pertenezca al grupo
        cursor.execute(
            """
            SELECT * FROM alumnos_grupo 
            WHERE grupo_id = %s AND alumno_matricula = %s AND activo = 1
        """,
            (grupo_id, alumno_matricula),
        )

        if not cursor.fetchone():
            cursor.close()
            conexion.close()
            return {"status": "error", "message": "❌ No perteneces a este grupo"}

        # Registrar asistencia del alumno
        cursor.execute(
            """
            INSERT INTO asistencias_tutoria 
            (grupo_id, sesion_id, alumno_matricula, fecha_asistencia)
            VALUES (%s, %s, %s, %s)
        """,
            (grupo_id, sesion_id, alumno_matricula, ahora),
        )

        # ¡ROTAR TOKEN! Generar nuevo token para el siguiente alumno
        nuevo_token_raw = secrets.token_urlsafe(16)
        nuevo_token_hash = hashlib.sha256(nuevo_token_raw.encode()).hexdigest()
        nueva_expiracion = datetime.now() + timedelta(minutes=2)

        cursor.execute(
            """
            UPDATE sesiones_tutoria 
            SET token_actual = %s,
                token_anterior = token_actual,
                fecha_expiracion = %s,
                usado = 1
            WHERE id = %s
        """,
            (nuevo_token_hash, nueva_expiracion, sesion_id),
        )

        conexion.commit()

        # Cerrar conexión
        cursor.close()
        conexion.close()

        return {
            "status": "ok",
            "message": f"✅ Asistencia registrada para {alumno_matricula}",
            "nuevo_token": nuevo_token_raw,
            "nuevo_contenido_qr": f"TUTORIA|{nuevo_token_raw}|{grupo_id}|{sesion_id}",
            "alumno_registrado": alumno_matricula,
        }

    def obtener_estado_sesion(self, sesion_id):
        """Obtiene el estado actual de la sesión de tutoría"""
        conexion, cursor = obtener_cursor()

        cursor.execute(
            """
            SELECT st.*, 
                   COUNT(a.id) as total_asistencias
            FROM sesiones_tutoria st
            LEFT JOIN asistencias_tutoria a ON st.id = a.sesion_id
            WHERE st.id = %s
            GROUP BY st.id
        """,
            (sesion_id,),
        )

        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()

        return resultado
