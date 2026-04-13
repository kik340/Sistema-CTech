"""Clases para construir PDFs del sistema.

Este archivo encapsula la plantilla visual del PDF y la variante usada para
exportar el código QR del alumno o externo.
"""

import io
import os
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors


class PdfManager:
    """Define la base visual para los PDFs generados por la aplicación."""
    def __init__(self, logo_path, nombre_escuela):
        self.logo_path = logo_path
        self.nombre_escuela = nombre_escuela
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.ancho, self.alto = A4

    def dibujar_texto_con_borde(self, x, y, texto, fuente="Helvetica-Bold", tamano=18):
        self.c.setFont(fuente, tamano)
        self.c.setFillColor(colors.black)

        desplazamientos = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]

        for dx, dy in desplazamientos:
            self.c.drawCentredString(x + dx, y + dy, texto)

        self.c.setFillColor(colors.white)
        self.c.drawCentredString(x, y, texto)

    def dibujar_encabezado(self):
        altura_franja = 95
        y_franja = self.alto - altura_franja

        self.c.setFillColor(colors.HexColor("#b30000"))
        self.c.rect(0, y_franja, self.ancho, altura_franja, fill=1, stroke=0)

        centro_logo_x = 72
        centro_logo_y = y_franja + 47

        self.c.setFillColor(colors.white)
        self.c.circle(centro_logo_x, centro_logo_y, 33, fill=1, stroke=0)

        if os.path.exists(self.logo_path):
            self.c.drawImage(
                self.logo_path,
                centro_logo_x - 25,
                centro_logo_y - 25,
                width=50,
                height=50,
                preserveAspectRatio=True,
                mask="auto"
            )

        self.dibujar_texto_con_borde(
            self.ancho / 2 + 35,
            y_franja + 40,
            self.nombre_escuela,
            "Helvetica-Bold",
            20
        )

        self.c.setLineWidth(1.4)
        self.c.setStrokeColor(colors.black)
        self.c.line(30, y_franja - 8, self.ancho - 30, y_franja - 8)

    def guardar_pdf(self):
        self.c.showPage()
        self.c.save()
        self.buffer.seek(0)
        return self.buffer


class PdfQrAlumno(PdfManager):
    """Especializa la plantilla PDF para exportar el QR del usuario."""
    def __init__(self, logo_path, nombre_escuela, nombre_alumno, matricula, email, carrera, qr_buffer):
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
            mask="auto"
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

        return self.guardar_pdf()


class PdfSeguimientoAcademico(PdfManager):
    """Genera un PDF en formato tabla con la información del seguimiento académico."""

    def __init__(self, logo_path, nombre_escuela, seguimiento, filas):
        super().__init__(logo_path, nombre_escuela)
        self.seguimiento = seguimiento
        self.filas = filas

    def _valor_si_no(self, valor):
        return "Sí" if int(valor or 0) == 1 else "No"

    def construir(self):
        self.buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=landscape(A3),
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=18 * mm,
            bottomMargin=14 * mm,
        )

        estilos = getSampleStyleSheet()
        elementos = []

        titulo = Paragraph("<b>Seguimiento académico</b>", estilos["Title"])
        subtitulo = Paragraph(
            (
                f"<b>Grupo ID:</b> {self.seguimiento.get('grupo_id', '')} &nbsp;&nbsp;&nbsp; "
                f"<b>Parcial:</b> {self.seguimiento.get('parcial', '')} &nbsp;&nbsp;&nbsp; "
                f"<b>Total estudiantes:</b> {self.seguimiento.get('total_estudiantes', '')}"
            ),
            estilos["Normal"],
        )
        observaciones = Paragraph(
            f"<b>Observaciones generales:</b> {self.seguimiento.get('observaciones') or 'Sin observaciones'}",
            estilos["Normal"],
        )

        elementos.extend([titulo, Spacer(1, 8), subtitulo, Spacer(1, 8), observaciones, Spacer(1, 10)])

        encabezados = [
            "Matrícula", "Nombre", "Asistencia", "Canalización", "Prob. económicos",
            "Prob. salud", "Prob. emocionales", "Prob. familiares", "Prob. académicos",
            "Beca JCF", "Beca manutención", "Beca JMF", "Otra beca", "Apoyo psicológico",
            "Apoyo médico", "Otro apoyo", "Promedio", "Reprobadas", "Aprobado",
            "Posible deserción", "Comentario"
        ]

        data = [encabezados]
        for fila in self.filas:
            data.append([
                str(fila.get("matricula", "")),
                str(fila.get("nombre_completo", "")),
                self._valor_si_no(fila.get("asistencia")),
                self._valor_si_no(fila.get("canalizacion_tutoria_individual")),
                self._valor_si_no(fila.get("problemas_economicos")),
                self._valor_si_no(fila.get("problemas_salud")),
                self._valor_si_no(fila.get("problemas_emocionales")),
                self._valor_si_no(fila.get("problemas_familiares")),
                self._valor_si_no(fila.get("problemas_academicos")),
                self._valor_si_no(fila.get("beca_jcf")),
                self._valor_si_no(fila.get("beca_manutencion")),
                self._valor_si_no(fila.get("beca_jmf")),
                self._valor_si_no(fila.get("beca_otro")),
                self._valor_si_no(fila.get("apoyo_psicologico")),
                self._valor_si_no(fila.get("apoyo_medico")),
                self._valor_si_no(fila.get("apoyo_otro")),
                "" if fila.get("promedio") is None else str(fila.get("promedio")),
                str(fila.get("materias_reprobadas") or 0),
                self._valor_si_no(fila.get("estatus_aprobado")),
                self._valor_si_no(fila.get("posible_desercion")),
                str(fila.get("comentario") or ""),
            ])

        col_widths = [
            26*mm, 55*mm, 18*mm, 20*mm, 20*mm, 18*mm, 20*mm, 20*mm, 20*mm,
            17*mm, 22*mm, 17*mm, 18*mm, 22*mm, 20*mm, 18*mm, 18*mm, 18*mm, 16*mm, 24*mm, 45*mm
        ]

        tabla = Table(data, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b30000")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("LEADING", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 1), (19, -1), "CENTER"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f7f7f7")]),
        ]))

        elementos.append(tabla)
        doc.build(elementos)
        self.buffer.seek(0)
        return self.buffer
class PdfSeguimientoAcademico(PdfManager):
    def __init__(self, logo_path, nombre_escuela, seguimiento, alumnos, detalle_map):
        super().__init__(logo_path, nombre_escuela)
        self.seguimiento = seguimiento
        self.alumnos = alumnos
        self.detalle_map = detalle_map

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

        if len(problemas) == 1:
            return problemas[0]

        if len(problemas) == 2:
            return f"{problemas[0]} y {problemas[1]}"

        return f"Varios ({len(problemas)}): " + ", ".join(problemas)

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

    def construir(self):
        from reportlab.lib import colors

        self.dibujar_encabezado()

        y = self.alto - 125

        self.c.setFillColor(colors.black)
        self.c.setFont("Helvetica-Bold", 16)
        self.c.drawString(40, y, "Seguimiento Académico")

        y -= 25
        self.c.setFont("Helvetica", 11)
        self.c.drawString(40, y, f"Grupo ID: {self.seguimiento.get('grupo_id', '')}")
        self.c.drawString(220, y, f"Parcial: {self.seguimiento.get('parcial', '')}")
        self.c.drawString(380, y, f"Total estudiantes: {self.seguimiento.get('total_estudiantes', len(self.alumnos))}")

        y -= 30

        columnas = [
            ("Matrícula", 55),
            ("Nombre", 115),
            ("Asis.", 32),
            ("Prom.", 35),
            ("Repr.", 32),
            ("Aprob.", 36),
            ("Deserc.", 40),
            ("Problemas", 110),
            ("Becas", 75),
            ("Apoyos", 75),
            ("Comentario", 110),
        ]

        x_inicial = 20
        altura_header = 22
        altura_fila = 38

        ancho_total = sum(ancho for _, ancho in columnas)

        self.c.setFillColor(colors.HexColor("#b30000"))
        self.c.rect(x_inicial, y - altura_header, ancho_total, altura_header, fill=1, stroke=0)

        x = x_inicial
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 7)
        for titulo, ancho in columnas:
            self.c.rect(x, y - altura_header, ancho, altura_header, fill=0, stroke=1)
            self.c.drawCentredString(x + ancho / 2, y - 14, titulo)
            x += ancho

        y -= altura_header

        self.c.setFont("Helvetica", 6.3)
        self.c.setFillColor(colors.black)

        for alumno in self.alumnos:
            d = self.detalle_map.get(alumno["matricula"], {})

            if y < 90:
                self.c.showPage()
                self.dibujar_encabezado()
                y = self.alto - 125

                self.c.setFillColor(colors.HexColor("#b30000"))
                self.c.rect(x_inicial, y - altura_header, ancho_total, altura_header, fill=1, stroke=0)

                x = x_inicial
                self.c.setFillColor(colors.white)
                self.c.setFont("Helvetica-Bold", 7)
                for titulo, ancho in columnas:
                    self.c.rect(x, y - altura_header, ancho, altura_header, fill=0, stroke=1)
                    self.c.drawCentredString(x + ancho / 2, y - 14, titulo)
                    x += ancho

                y -= altura_header
                self.c.setFont("Helvetica", 6.3)
                self.c.setFillColor(colors.black)

            problemas = self._compactar_problemas(d)
            becas = self._compactar_becas(d)
            apoyos = self._compactar_apoyos(d)
            comentario = (d.get("comentario") or "").strip()

            if len(comentario) > 55:
                comentario = comentario[:52] + "..."

            valores = [
                str(alumno["matricula"]),
                str(alumno["nombre_completo"])[:26],
                self._texto_si_no(d.get("asistencia", 0)),
                str(d.get("promedio", "")),
                str(d.get("materias_reprobadas", 0)),
                self._texto_si_no(d.get("estatus_aprobado", 0)),
                self._texto_si_no(d.get("posible_desercion", 0)),
                problemas,
                becas,
                apoyos,
                comentario if comentario else "-",
            ]

            x = x_inicial
            for i, (_, ancho) in enumerate(columnas):
                self.c.rect(x, y - altura_fila, ancho, altura_fila, fill=0, stroke=1)

                texto = valores[i]
                lineas = []
                while texto:
                    limite = max(1, int(ancho / 4.2))
                    parte = texto[:limite]
                    texto = texto[limite:]
                    lineas.append(parte)

                lineas = lineas[:4]
                yy = y - 10
                for linea in lineas:
                    self.c.drawString(x + 2, yy, linea)
                    yy -= 8

                x += ancho

            y -= altura_fila

        y -= 18
        observaciones = (self.seguimiento.get("observaciones") or "").strip()

        if observaciones:
            if y < 100:
                self.c.showPage()
                self.dibujar_encabezado()
                y = self.alto - 130

            self.c.setFont("Helvetica-Bold", 10)
            self.c.drawString(30, y, "Observaciones generales:")
            y -= 14

            self.c.setFont("Helvetica", 8)
            ancho_texto = 530
            palabras = observaciones.split()
            lineas = []
            actual = ""

            for palabra in palabras:
                prueba = actual + (" " if actual else "") + palabra
                if self.c.stringWidth(prueba, "Helvetica", 8) <= ancho_texto:
                    actual = prueba
                else:
                    if actual:
                        lineas.append(actual)
                    actual = palabra

            if actual:
                lineas.append(actual)

            for linea in lineas:
                if y < 60:
                    self.c.showPage()
                    self.dibujar_encabezado()
                    y = self.alto - 130
                    self.c.setFont("Helvetica", 8)

                self.c.drawString(30, y, linea)
                y -= 11

        return self.guardar_pdf()
