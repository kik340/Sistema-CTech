# PDFManager.py - Versión SIMPLIFICADA y CORREGIDA

import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm, cm


class PdfManager:
    """Define la base visual para los PDFs generados por la aplicación."""

    def __init__(self, logo_path, nombre_escuela):
        self.logo_path = logo_path
        self.nombre_escuela = nombre_escuela
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.ancho, self.alto = A4

    def dibujar_encabezado(self):
        altura_franja = 95
        y_franja = self.alto - altura_franja

        self.c.setFillColor(colors.HexColor("#b30000"))
        self.c.rect(0, y_franja, self.ancho, altura_franja, fill=1, stroke=0)

        # Buscar logo
        logo_encontrado = None
        rutas_posibles = [
            self.logo_path,
            "static/img/logo_itsa.png",
            "static/resources/logo.png",
            "static/logo.png",
            "static/img/logo.png",
        ]

        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                logo_encontrado = ruta
                break

        centro_logo_x = 72
        centro_logo_y = y_franja + 47

        self.c.setFillColor(colors.white)
        self.c.circle(centro_logo_x, centro_logo_y, 33, fill=1, stroke=0)

        if logo_encontrado and os.path.exists(logo_encontrado):
            try:
                self.c.drawImage(
                    logo_encontrado,
                    centro_logo_x - 25,
                    centro_logo_y - 25,
                    width=50,
                    height=50,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except:
                pass

        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(colors.white)
        self.c.drawCentredString(
            self.ancho / 2 + 35, y_franja + 40, self.nombre_escuela
        )

        self.c.setLineWidth(1.4)
        self.c.setStrokeColor(colors.black)
        self.c.line(30, y_franja - 8, self.ancho - 30, y_franja - 8)

    def guardar_pdf(self):
        self.c.save()
        self.buffer.seek(0)
        return self.buffer


class PdfQrAlumno(PdfManager):
    """Especializa la plantilla PDF para exportar el QR del usuario."""

    def __init__(
        self,
        logo_path,
        nombre_escuela,
        nombre_alumno,
        matricula,
        email,
        carrera,
        qr_buffer,
    ):
        super().__init__(logo_path, nombre_escuela)
        self.nombre_alumno = nombre_alumno
        self.matricula = matricula
        self.carrera = carrera
        self.email = email
        self.qr_buffer = qr_buffer

    def construir(self):
        self.dibujar_encabezado()

        qr_reader = ImageReader(self.qr_buffer)

        qr_size = 250
        qr_x = (self.ancho - qr_size) / 2
        qr_y = self.alto - 465

        self.c.setStrokeColor(colors.black)
        self.c.setLineWidth(0.8)
        self.c.rect(qr_x - 18, qr_y - 18, qr_size + 36, qr_size + 36, fill=0, stroke=1)

        self.c.drawImage(
            qr_reader,
            qr_x,
            qr_y,
            width=qr_size,
            height=qr_size,
            preserveAspectRatio=True,
            mask="auto",
        )

        y_info = qr_y - 65

        self.c.setFillColor(colors.black)

        self.c.setFont("Helvetica", 15)
        self.c.drawString(85, y_info, f"Matricula: {self.matricula}")

        self.c.setFont("Helvetica-Bold", 20)
        self.c.drawString(85, y_info - 40, self.nombre_alumno.upper())

        self.c.setFont("Helvetica", 20)
        self.c.drawString(85, y_info - 78, f"Carrera: {self.carrera}")

        self.c.setFont("Helvetica", 16)
        self.c.drawString(85, y_info - 108, self.email)

        self.c.showPage()
        self.c.save()
        self.buffer.seek(0)
        return self.buffer


class PdfSeguimientoAcademico:
    """Genera PDF de seguimiento académico - VERSIÓN SIMPLIFICADA Y ROBUSTA"""

    def __init__(self, logo_path, nombre_escuela, seguimiento, alumnos, detalle_map):
        self.logo_path = logo_path
        self.nombre_escuela = nombre_escuela
        self.seguimiento = seguimiento
        self.alumnos = alumnos
        self.detalle_map = detalle_map
        self.buffer = io.BytesIO()
        # Crear canvas en landscape
        self.ancho, self.alto = landscape(A4)
        self.c = canvas.Canvas(self.buffer, pagesize=landscape(A4))

    def _texto_si_no(self, valor):
        return "Sí" if str(valor) == "1" else "No"

    def _compactar_problemas(self, d):
        problemas = []
        if d.get("problemas_economicos") == 1:
            problemas.append("Económicos")
        if d.get("problemas_salud") == 1:
            problemas.append("Salud")
        if d.get("problemas_emocionales") == 1:
            problemas.append("Emocionales")
        if d.get("problemas_familiares") == 1:
            problemas.append("Familiares")
        if d.get("problemas_academicos") == 1:
            problemas.append("Académicos")
        if not problemas:
            return "Ninguno"
        return ", ".join(problemas)

    def _compactar_becas(self, d):
        becas = []
        if d.get("beca_jcf") == 1:
            becas.append("JCF")
        if d.get("beca_manutencion") == 1:
            becas.append("Manutención")
        if d.get("beca_jmf") == 1:
            becas.append("JMF")
        if d.get("beca_otro") == 1:
            becas.append("Otra")
        return ", ".join(becas) if becas else "Ninguna"

    def _compactar_apoyos(self, d):
        apoyos = []
        if d.get("apoyo_psicologico") == 1:
            apoyos.append("Psicológico")
        if d.get("apoyo_medico") == 1:
            apoyos.append("Médico")
        if d.get("apoyo_otro") == 1:
            apoyos.append("Otro")
        return ", ".join(apoyos) if apoyos else "Ninguno"

    def _buscar_logo(self):
        rutas = [
            self.logo_path,
            "static/img/logo_itsa.png",
            "static/resources/logo.png",
            "static/logo.png",
        ]
        for ruta in rutas:
            if os.path.exists(ruta):
                return ruta
        return None

    def _dibujar_encabezado(self):
        """Dibuja el encabezado sin usar rect con coordenadas problemáticas"""
        ancho = self.ancho
        alto = self.alto

        # Franja roja
        franja_alto = 80
        y_franja = alto - franja_alto

        self.c.setFillColor(colors.HexColor("#b30000"))
        self.c.rect(0, y_franja, ancho, franja_alto, fill=1, stroke=0)

        # Logo
        logo = self._buscar_logo()
        if logo:
            try:
                self.c.drawImage(
                    logo,
                    30,
                    y_franja + 15,
                    width=50,
                    height=50,
                    preserveAspectRatio=True,
                )
            except:
                pass

        # Textos
        self.c.setFont("Helvetica-Bold", 16)
        self.c.setFillColor(colors.white)
        self.c.drawString(100, y_franja + 50, self.nombre_escuela)

        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(100, y_franja + 30, "REPORTE DE SEGUIMIENTO ACADÉMICO")

        self.c.setFont("Helvetica", 8)
        periodo = self.seguimiento.get("periodo", "Enero - Junio 2026")
        self.c.drawString(100, y_franja + 15, f"Periodo: {periodo}")

        # Línea separadora
        self.c.setStrokeColor(colors.black)
        self.c.setLineWidth(1)
        self.c.line(30, y_franja - 10, ancho - 30, y_franja - 10)

        # Información del grupo
        y_info = y_franja - 30
        self.c.setFillColor(colors.black)
        self.c.setFont("Helvetica", 8)

        division = self.seguimiento.get("division", "Ingeniería Industrial")
        tutor = self.seguimiento.get("persona_tutora", "")
        parcial = self.seguimiento.get("parcial", "Primero")

        self.c.drawString(30, y_info, f"División: {division}")
        self.c.drawString(280, y_info, f"Persona tutora: {tutor}")
        self.c.drawString(550, y_info, f"Parcial: {parcial}")

        y_info -= 18
        grupo_letra = self.seguimiento.get("grupo_letra", "A")
        total = len(self.alumnos)
        hombres = sum(1 for a in self.alumnos if a.get("genero", "M") == "H")
        mujeres = total - hombres

        self.c.drawString(30, y_info, f"Grupo: {grupo_letra}")
        self.c.drawString(280, y_info, f"N° estudiantes: {total}")
        self.c.drawString(450, y_info, f"Hombres: {hombres}")
        self.c.drawString(550, y_info, f"Mujeres: {mujeres}")

        return y_info - 20

    def construir(self):
        """Construye el PDF completo"""
        try:
            ancho = self.ancho

            # Dibujar encabezado
            y = self._dibujar_encabezado()

            # Definir columnas
            columnas = [
                ("Matrícula", 55),
                ("Nombre", 110),
                ("S", 25),
                ("Asist", 35),
                ("Prom", 40),
                ("Rep", 38),
                ("Apr", 35),
                ("Becas", 60),
                ("Apoyos", 60),
                ("Problemas", 90),
                ("Des", 35),
                ("Comentario", 110),
            ]

            x_inicial = 20
            alto_header = 22

            # Calcular posiciones
            posiciones = []
            x_actual = x_inicial
            for nombre, ancho_col in columnas:
                posiciones.append((x_actual, ancho_col))
                x_actual += ancho_col

            # Dibujar header
            self.c.setFillColor(colors.HexColor("#b30000"))
            self.c.rect(
                x_inicial,
                y - alto_header,
                x_actual - x_inicial,
                alto_header,
                fill=1,
                stroke=0,
            )

            self.c.setFillColor(colors.white)
            self.c.setFont("Helvetica-Bold", 7)
            for i, (nombre, ancho_col) in enumerate(columnas):
                x, w = posiciones[i]
                self.c.rect(x, y - alto_header, w, alto_header, fill=0, stroke=1)
                self.c.drawCentredString(x + w / 2, y - alto_header + 8, nombre)

            y -= alto_header
            self.c.setFont("Helvetica", 6.5)
            self.c.setFillColor(colors.black)
            alto_fila = 28

            # Dibujar alumnos
            for alumno in self.alumnos:
                # Verificar espacio
                if y - alto_fila < 60:
                    self.c.showPage()
                    y = self._dibujar_encabezado()
                    # Redibujar header
                    self.c.setFillColor(colors.HexColor("#b30000"))
                    self.c.rect(
                        x_inicial,
                        y - alto_header,
                        x_actual - x_inicial,
                        alto_header,
                        fill=1,
                        stroke=0,
                    )
                    self.c.setFillColor(colors.white)
                    self.c.setFont("Helvetica-Bold", 7)
                    for i, (nombre, ancho_col) in enumerate(columnas):
                        x, w = posiciones[i]
                        self.c.rect(
                            x, y - alto_header, w, alto_header, fill=0, stroke=1
                        )
                        self.c.drawCentredString(x + w / 2, y - alto_header + 8, nombre)
                    y -= alto_header
                    self.c.setFont("Helvetica", 6.5)
                    self.c.setFillColor(colors.black)

                datos = self.detalle_map.get(alumno["matricula"], {})

                valores = [
                    alumno["matricula"],
                    alumno["nombre_completo"][:25],
                    alumno.get("genero", "M")[:1],
                    self._texto_si_no(datos.get("asistencia", 0)),
                    str(datos.get("promedio", "")) if datos.get("promedio") else "",
                    str(datos.get("materias_reprobadas", 0)),
                    self._texto_si_no(datos.get("estatus_aprobado", 0)),
                    self._compactar_becas(datos)[:12],
                    self._compactar_apoyos(datos)[:12],
                    self._compactar_problemas(datos)[:20],
                    self._texto_si_no(datos.get("posible_desercion", 0)),
                    (datos.get("comentario", "") or "-")[:35],
                ]

                for i, (x, w) in enumerate(posiciones):
                    self.c.rect(x, y - alto_fila, w, alto_fila, fill=0, stroke=0.5)
                    texto = str(valores[i]) if valores[i] else ""

                    if i == 1:  # Nombre
                        self.c.drawString(x + 2, y - alto_fila + 10, texto)
                    elif i in [0, 2, 3, 4, 5, 6, 10]:  # Centrados
                        self.c.drawCentredString(x + w / 2, y - alto_fila + 10, texto)
                    else:
                        self.c.drawString(x + 2, y - alto_fila + 10, texto)

                y -= alto_fila

            # Observaciones
            observaciones = self.seguimiento.get("observaciones", "").strip()
            if observaciones:
                y -= 15
                self.c.setFont("Helvetica-Bold", 7)
                self.c.drawString(20, y, "Observaciones generales:")
                y -= 10
                self.c.setFont("Helvetica", 6.5)

                # Texto multilínea simple
                if self.c.stringWidth(observaciones, "Helvetica", 6.5) > ancho - 60:
                    # Si es muy largo, truncar
                    observaciones = observaciones[:80] + "..."

                self.c.drawString(30, y, observaciones)
                y -= 15

            # Firmas
            y -= 20
            self.c.setFont("Helvetica", 7)
            self.c.drawString(60, y, "___________________________________")
            self.c.drawString(80, y - 10, "Firma del Tutor")

            self.c.drawString(ancho - 220, y, "___________________________________")
            self.c.drawString(ancho - 190, y - 10, "Firma del Alumno")

            # Pie
            self.c.setFont("Helvetica", 6)
            self.c.setFillColor(colors.gray)
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
            self.c.drawString(ancho - 150, 20, f"Generado: {fecha}")

            self.c.showPage()
            self.c.save()
            self.buffer.seek(0)

        except Exception as e:
            # Si hay error, crear un PDF de error
            self.buffer = io.BytesIO()
            c = canvas.Canvas(self.buffer, pagesize=landscape(A4))
            c.drawString(100, 400, f"Error generando PDF: {str(e)}")
            c.showPage()
            c.save()
            self.buffer.seek(0)

        return self.buffer
