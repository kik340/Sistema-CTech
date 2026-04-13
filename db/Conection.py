"""Conexión base a MySQL para el proyecto.

Este módulo devuelve una conexión abierta y un cursor en formato diccionario
para que el resto de clases trabaje con la base de datos.
"""

import mysql.connector

def obtener_cursor():
    """Abre la conexión principal a MySQL y devuelve también un cursor tipo diccionario."""
    conexion = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="itsa_qr"
    )
    cursor = conexion.cursor(dictionary=True)
    return conexion, cursor
