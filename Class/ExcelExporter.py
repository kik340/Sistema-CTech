# Class/ExcelExporter.py  —  versión mejorada
"""
Genera el reporte de Seguimiento Académico / Asistencia a Tutoría
imitando fielmente la plantilla oficial R01-26.
Utiliza todos los datos disponibles en la BD (asistencias QR por sesión,
seguimiento_detalle, actividades, etc.)
"""

import io
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, numbers
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from db.Conection import obtener_cursor

# Ruta al logo institucional
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "resources", "logo.png")
LOGO_PATH = os.path.normpath(LOGO_PATH)


def _insertar_encabezado_institucional(ws, fila_logo=1, col_max="BZ"):
    """
    Encabezado institucional con logo a la izquierda y nombre grande a la derecha.
    Filas 1-3, columna A = logo flotante, B en adelante = título + subtítulo.
    """
    # Logo en columna A, filas 1-3
    if os.path.exists(LOGO_PATH):
        try:
            logo = XLImage(LOGO_PATH)
            logo.width  = 100
            logo.height = 69
            ws.add_image(logo, "A1")
        except Exception:
            pass

    # Fila 1: nombre GRANDE del instituto (tamaño 20, negrita)
    ws.merge_cells(f"B1:{col_max}1")
    c1 = ws["B1"]
    c1.value     = "Instituto Tecnológico Superior de Atlixco"
    c1.font      = Font(name="Arial", bold=True, size=20, color="B30000")
    c1.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 34

    # Fila 2: subtítulo de la hoja (se rellena en cada _crear_hoja_*)
    ws.merge_cells(f"B2:{col_max}2")
    ws.row_dimensions[2].height = 16

    # Fila 3: línea divisoria vacía
    ws.merge_cells(f"B3:{col_max}3")
    c3 = ws["B3"]
    c3.fill = PatternFill("solid", fgColor="B30000")
    ws.row_dimensions[3].height = 3

    ws.column_dimensions["A"].width = 15   # espacio para el logo

    return 4   # primera fila disponible después del encabezado

def _configurar_impresion(ws, orientacion="landscape", escala=None, ajustar_ancho=True):
    """
    Configura la hoja para impresión/PDF:
    - Orientación horizontal (landscape) o vertical
    - Escalar para que todo el contenido quepa en el ancho de una página
    - Márgenes reducidos
    - Encabezado/pie de página vacíos
    """
    from openpyxl.worksheet.page import PageMargins
    ws.page_setup.orientation     = ws.ORIENTATION_LANDSCAPE if orientacion == "landscape" else ws.ORIENTATION_PORTRAIT
    ws.page_setup.paperSize        = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage        = True
    if ajustar_ancho:
        ws.page_setup.fitToWidth   = 1   # todo en 1 página de ancho
        ws.page_setup.fitToHeight  = 0   # páginas de alto las que necesite
    if escala:
        ws.page_setup.scale        = escala
        ws.page_setup.fitToPage    = False
    ws.page_margins = PageMargins(
        left=0.4, right=0.4, top=0.5, bottom=0.5,
        header=0.2, footer=0.2
    )
    ws.print_options.horizontalCentered = True



# ──────────────────────────────────────────────────────────────
# Helpers de estilo
# ──────────────────────────────────────────────────────────────

ROJO       = "B30000"
ROJO_CLARO = "D32F2F"
ROSA       = "FCE4EC"
VERDE      = "E8F5E9"
GRIS_CLARO = "F5F5F5"
BLANCO     = "FFFFFF"
GRIS_BORDE = "BDBDBD"
AMARILLO   = "FFF9C4"

def _borde(estilo="thin", color=GRIS_BORDE):
    s = Side(style=estilo, color=color)
    return Border(left=s, right=s, top=s, bottom=s)

BORDE_FINO    = _borde("thin")
BORDE_GRUESO  = _borde("medium", "9E9E9E")

def _font(bold=False, size=10, color="000000", italic=False):
    return Font(name="Arial", bold=bold, size=size, color=color, italic=italic)

def _fill(color):
    return PatternFill("solid", fgColor=color)

def _alin(h="center", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

def _enc(ws, fila, col, valor, color_fondo=ROJO, color_texto=BLANCO,
         negrita=True, wrap=True, alin_h="center"):
    c = ws.cell(row=fila, column=col, value=valor)
    c.font  = _font(bold=negrita, color=color_texto)
    c.fill  = _fill(color_fondo)
    c.alignment = _alin(h=alin_h, wrap=wrap)
    c.border = BORDE_FINO
    return c

def _dato(ws, fila, col, valor, bg=None, negrita=False, alin_h="left", fmt=None):
    c = ws.cell(row=fila, column=col, value=valor)
    c.font   = _font(bold=negrita)
    c.border = BORDE_FINO
    c.alignment = _alin(h=alin_h, v="center", wrap=True)
    if bg:
        c.fill = _fill(bg)
    if fmt:
        c.number_format = fmt
    return c


# ──────────────────────────────────────────────────────────────
# Clase principal
# ──────────────────────────────────────────────────────────────

class ExcelSeguimientoExporter:
    """
    Parámetros
    ----------
    seguimiento : dict  — datos del registro seguimiento_academico + info del grupo
    alumnos     : list  — dicts de alumnos_grupo JOIN alumnos
    detalle_map : dict  — {matricula: dict} de seguimiento_detalle
    sesiones_asistencia : list — registros de asistencias_tutoria con sesion_id,
                                 alumno_matricula, fecha_asistencia
    grupo_info  : dict  — info completa del grupo (periodo, carrera, semestre…)
    parcial     : str   — "1","2","3","4" o "S" (semestral)
    sesiones_detalle : list — registros de sesiones_tutoria (id, parcial, fecha_inicio…)
    actividades      : list — registros de actividades_tutoria
    """

    def __init__(self, seguimiento, alumnos, detalle_map,
                 sesiones_asistencia=None, grupo_info=None, parcial="1",
                 sesiones_detalle=None, actividades=None):
        self.seguimiento        = seguimiento
        self.alumnos            = alumnos
        self.detalle_map        = detalle_map
        self.sesiones_asistencia = sesiones_asistencia or []
        self.grupo_info         = grupo_info or {}
        self.parcial            = parcial
        self.sesiones_detalle   = sesiones_detalle or []
        self.actividades        = actividades or []

        # Índice rápido: {sesion_id: {alumno_matricula: fecha}}
        self._asis_idx = {}
        for reg in self.sesiones_asistencia:
            sid = reg.get("sesion_id")
            mat = reg.get("alumno_matricula") or reg.get("matricula", "")
            fecha = reg.get("fecha_asistencia")
            if sid not in self._asis_idx:
                self._asis_idx[sid] = {}
            self._asis_idx[sid][mat] = fecha

        # Sesiones ordenadas por parcial y número de sesión
        self._sesiones_por_parcial = {}   # {parcial_str: [sesion_dict, ...]}
        for s in self.sesiones_detalle:
            p = str(s.get("parcial", "1"))
            self._sesiones_por_parcial.setdefault(p, []).append(s)
        for p in self._sesiones_por_parcial:
            self._sesiones_por_parcial[p].sort(key=lambda x: x.get("fecha_inicio") or "")

        # Actividades indexadas: {(parcial, sesion_num): dict}
        self._act_idx = {}
        for a in self.actividades:
            key = (str(a.get("parcial", "")), int(a.get("sesion_num", 0)))
            self._act_idx[key] = a

    # ── utilidades ───────────────────────────────────────────

    def _generos(self):
        h = sum(1 for a in self.alumnos if str(a.get("genero","")).upper().startswith("H"))
        return h, len(self.alumnos) - h

    def _genero_alumno(self, alumno):
        g = str(alumno.get("genero","")).upper()
        return g[0] if g else "M"

    def _asistio(self, sesion_id, matricula):
        """Devuelve True si el alumno asistió a esa sesión QR."""
        return matricula in self._asis_idx.get(sesion_id, {})

    def _fecha_sesion(self, sesion_id):
        for s in self.sesiones_detalle:
            if s.get("id") == sesion_id:
                f = s.get("fecha_inicio")
                if f and hasattr(f, "date"):
                    return f.date()
                return f
        return None

    def _parciales_a_generar(self):
        if self.parcial == "S":
            return ["1","2","3","4"]
        return [self.parcial]

    def _info_comun(self):
        gi = self.grupo_info
        h, m = self._generos()
        return {
            "periodo"      : self.seguimiento.get("periodo", gi.get("periodo","Enero - Junio 2026")),
            "division"     : self.seguimiento.get("division", gi.get("carrera_nombre","Ingeniería Industrial")),
            "tutora"       : self.seguimiento.get("persona_tutora",""),
            "semestre_grupo": self.seguimiento.get("grupo_letra",
                               f"{gi.get('semestre','?')}° {gi.get('grupo','?')}" if gi else ""),
            "total"        : len(self.alumnos),
            "hombres"      : h,
            "mujeres"      : m,
        }

    # ── bloque de info general reutilizable ──────────────────

    def _bloque_info(self, ws, fila_ini, info, ancho_label=28, ancho_valor=40):
        campos = [
            ("Periodo:",              info["periodo"]),
            ("División:",             info["division"]),
            ("Persona tutora:",       info["tutora"]),
            ("Semestre y grupo:",     info["semestre_grupo"]),
            ("No. Total de estudiantes:", info["total"]),
            ("Hombres:",              info["hombres"]),
            ("Mujeres:",              info["mujeres"]),
        ]
        for i,(lbl,val) in enumerate(campos):
            f = fila_ini + i
            c_lbl = ws.cell(row=f, column=1, value=lbl)
            c_lbl.font = _font(bold=True)
            c_lbl.alignment = _alin(h="right")
            c_val = ws.cell(row=f, column=2, value=val)
            c_val.font = _font()
            c_val.border = BORDE_FINO
        ws.column_dimensions["A"].width = ancho_label
        ws.column_dimensions["B"].width = ancho_valor

    # ══════════════════════════════════════════════════════════
    # HOJA 1 — ASISTENCIA GRUPAL-INDIVIDUAL
    # ══════════════════════════════════════════════════════════

    def _crear_hoja_asistencia_grupal(self, wb):
        ws = wb.create_sheet("ASISTENCIA GRUPAL-INDIVIDUAL")
        info = self._info_comun()

        # ── encabezado institucional con logo ─────────────────
        _insertar_encabezado_institucional(ws, col_max="BZ")

        ws["B2"].value = "ASISTENCIA GRUPAL-INDIVIDUAL — Tutoría"
        ws["B2"].font  = _font(bold=True, size=11)
        ws["B2"].alignment = _alin()

        # ── sección informativa ───────────────────────────────
        self._bloque_info(ws, 4, info)

        # ── construcción de columnas dinámicas por parcial/sesión ──
        # Estructura por parcial: 4 sesiones × (Fecha, L,M,X,J,V,S, Asist.Indiv, Razón, Acción, Obs)
        # Columnas fijas: A=Nº, B=Matrícula, C=Nombre, D=Género  → col 1..4
        # Luego bloques de sesiones agrupados por parcial

        DIAS = ["L","M","X","J","V","S"]
        COLS_POR_SESION = 1 + 6 + 1 + 1 + 1 + 1   # Fecha + días + H + M + Asist.Ind + Razón
        # = 12 columnas por sesión  (simplificado; ajusta si necesitas Acciones y Obs)

        parciales = self._parciales_a_generar()

        # Primera fila de encabezados fija (fila 13)
        FILA_ENC1 = 13
        FILA_ENC2 = 14
        FILA_DATOS = 15
        ws.row_dimensions[FILA_ENC1].height = 30
        ws.row_dimensions[FILA_ENC2].height = 22

        # Columnas fijas
        _enc(ws, FILA_ENC1, 1, "Nº")
        _enc(ws, FILA_ENC1, 2, "MATRÍCULA")
        _enc(ws, FILA_ENC1, 3, "NOMBRE DEL ALUMNO", alin_h="left")
        _enc(ws, FILA_ENC1, 4, "SEXO\nH-M")
        for col in [1,2,3,4]:
            ws.merge_cells(start_row=FILA_ENC1, start_column=col,
                           end_row=FILA_ENC2,   end_column=col)

        col_ini = 5
        # Mapeo parcial → lista de (sesion_id, col_base)
        sesion_cols = {}   # {parcial: [(sesion_id, col_fecha, col_dias_start), ...]}

        for p in parciales:
            sesiones_p = self._sesiones_por_parcial.get(p, [])
            # Siempre 4 sesiones, rellenar con None si no hay datos
            while len(sesiones_p) < 4:
                sesiones_p.append(None)
            sesiones_p = sesiones_p[:4]

            sesion_cols[p] = []
            num_sesion_global = (int(p)-1)*4 + 1 if p.isdigit() else 1

            # ── encabezado de parcial (fusionar sobre las 4 sesiones) ──
            cols_total_parcial = 4 * COLS_POR_SESION
            ws.merge_cells(start_row=FILA_ENC1-1 if FILA_ENC1 > 1 else FILA_ENC1,
                           start_column=col_ini, end_row=FILA_ENC1-1 if FILA_ENC1 > 1 else FILA_ENC1,
                           end_column=col_ini + cols_total_parcial - 1)
            # Solo ponemos el rótulo en fila encabezado 1
            lbl_parcial = f"PARCIAL {p}" if p.isdigit() else "SEMESTRAL"
            _enc(ws, FILA_ENC1, col_ini, lbl_parcial, color_fondo="1A237E")

            for s_idx, sesion in enumerate(sesiones_p):
                sid = sesion["id"] if sesion else None
                col_fecha = col_ini
                col_dias  = col_ini + 1
                col_H     = col_ini + 7
                col_M     = col_ini + 8
                col_ai    = col_ini + 9
                col_razon = col_ini + 10
                col_next  = col_ini + COLS_POR_SESION

                sesion_cols[p].append({
                    "id": sid, "col_fecha": col_fecha,
                    "col_dias": col_dias, "col_H": col_H, "col_M": col_M,
                    "col_ai": col_ai, "col_razon": col_razon
                })

                # Encabezado sesión en fila FILA_ENC1
                num_ses = num_sesion_global + s_idx
                ws.merge_cells(start_row=FILA_ENC1, start_column=col_fecha,
                               end_row=FILA_ENC1,   end_column=col_next - 1)
                _enc(ws, FILA_ENC1, col_fecha, f"SESIÓN {num_ses}", color_fondo="283593")

                # Encabezados columnas en fila FILA_ENC2
                fecha_str = ""
                if sesion and sesion.get("fecha_inicio"):
                    fi = sesion["fecha_inicio"]
                    if hasattr(fi,"strftime"):
                        fecha_str = fi.strftime("%d/%m/%Y")
                    else:
                        fecha_str = str(fi)[:10]
                _enc(ws, FILA_ENC2, col_fecha, f"Fecha\n{fecha_str}", color_fondo="3949AB")
                for d_i, dia in enumerate(DIAS):
                    _enc(ws, FILA_ENC2, col_dias + d_i, dia, color_fondo="3949AB")
                _enc(ws, FILA_ENC2, col_H,    "H", color_fondo="3949AB")
                _enc(ws, FILA_ENC2, col_M,    "M", color_fondo="3949AB")
                _enc(ws, FILA_ENC2, col_ai,   "Asist.\nIndiv.", color_fondo="3949AB")
                _enc(ws, FILA_ENC2, col_razon,"Razón\nInasist.", color_fondo="3949AB")

                col_ini = col_next

        # Columnas de seguimiento académico al final
        col_seg = col_ini
        COLS_SEG = [
            "Posible\ndeserción","Beca JCF","Beca\nManut.","Beca JMF","Otra\nbeca",
            "Apoyo\nPsicol.","Apoyo\nMédico","Otro\napoyo",
            "Promedio","Mat.\nReprobadas","Aprobado","Observaciones"
        ]
        for i,t in enumerate(COLS_SEG):
            _enc(ws, FILA_ENC1, col_seg+i, t, color_fondo="4A148C")
            ws.merge_cells(start_row=FILA_ENC1, start_column=col_seg+i,
                           end_row=FILA_ENC2,   end_column=col_seg+i)

        # ── datos de alumnos ─────────────────────────────────
        for idx, alumno in enumerate(self.alumnos):
            fila = FILA_DATOS + idx
            mat  = alumno.get("matricula","")
            gen  = self._genero_alumno(alumno)
            bg   = GRIS_CLARO if idx % 2 == 0 else BLANCO

            _dato(ws, fila, 1, idx+1,  bg=bg, alin_h="center")
            _dato(ws, fila, 2, mat,    bg=bg, alin_h="center")
            _dato(ws, fila, 3, alumno.get("nombre_completo",""), bg=bg)
            _dato(ws, fila, 4, gen,    bg=bg, alin_h="center")

            for p, scols in sesion_cols.items():
                for sc in scols:
                    sid = sc["id"]
                    asistio = self._asistio(sid, mat) if sid else False
                    cf = sc["col_fecha"]
                    # Fecha de la sesión ya está en encabezado; celdas de días
                    if asistio:
                        # Determinar día de semana de la asistencia
                        fecha_asis = self._asis_idx.get(sid,{}).get(mat)
                        if fecha_asis and hasattr(fecha_asis,"weekday"):
                            dw = fecha_asis.weekday()  # 0=lunes
                        else:
                            dw = 0
                        col_marcado = sc["col_dias"] + min(dw, 5)
                        _dato(ws, fila, col_marcado, 1, bg=VERDE, alin_h="center")
                    # Celdas vacías para los días no marcados
                    for d_i in range(6):
                        c_col = sc["col_dias"] + d_i
                        cell = ws.cell(row=fila, column=c_col)
                        if not cell.value:
                            cell.border = BORDE_FINO
                            cell.fill   = _fill(bg)
                    # H / M automático
                    ws.cell(row=fila, column=sc["col_H"]).value = gen if gen=="H" and asistio else ""
                    ws.cell(row=fila, column=sc["col_M"]).value = gen if gen=="M" and asistio else ""
                    ws.cell(row=fila, column=sc["col_H"]).border = BORDE_FINO
                    ws.cell(row=fila, column=sc["col_M"]).border = BORDE_FINO
                    # Asistencia individual (vacío para llenado manual)
                    ws.cell(row=fila, column=sc["col_ai"]).border = BORDE_FINO
                    ws.cell(row=fila, column=sc["col_razon"]).border = BORDE_FINO

            # Datos de seguimiento académico
            det = self.detalle_map.get(mat, {})
            def _v(k): return det.get(k, 0)
            vals_seg = [
                _v("posible_desercion"), _v("beca_jcf"), _v("beca_manutencion"),
                _v("beca_jmf"), _v("beca_otro"), _v("apoyo_psicologico"),
                _v("apoyo_medico"), _v("apoyo_otro"),
                det.get("promedio",""), _v("materias_reprobadas"),
                "Sí" if _v("estatus_aprobado") else "No",
                det.get("comentario",""),
            ]
            for i,v in enumerate(vals_seg):
                c = _dato(ws, fila, col_seg+i, v, bg=bg, alin_h="center")
                # Resaltar posible deserción
                if i == 0 and v:
                    c.fill = _fill("FFCDD2")

        # ── fila de totales ───────────────────────────────────
        fila_tot = FILA_DATOS + len(self.alumnos)
        ws.cell(row=fila_tot, column=3, value="TOTALES").font = _font(bold=True)

        # ── anchos de columnas fijas ──────────────────────────
        ws.column_dimensions["A"].width = 5
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 34
        ws.column_dimensions["D"].width = 7
        # Columnas de sesiones: días angostos, razón ancha
        c = 5
        for p in parciales:
            for _ in range(4):
                ws.column_dimensions[get_column_letter(c)].width = 11   # fecha
                for dd in range(6):
                    ws.column_dimensions[get_column_letter(c+1+dd)].width = 4
                ws.column_dimensions[get_column_letter(c+7)].width = 4  # H
                ws.column_dimensions[get_column_letter(c+8)].width = 4  # M
                ws.column_dimensions[get_column_letter(c+9)].width = 8  # asist indiv
                ws.column_dimensions[get_column_letter(c+10)].width = 18  # razón
                c += COLS_POR_SESION
        # Columnas seguimiento
        anchos_seg = [12,9,9,9,9,10,10,10,10,12,10,30]
        for i,aw in enumerate(anchos_seg):
            ws.column_dimensions[get_column_letter(col_seg+i)].width = aw

        # Fijar filas/columnas para facilitar navegación
        ws.freeze_panes = "E15"
        _configurar_impresion(ws, orientacion="landscape", ajustar_ancho=True)
        return ws

    # ══════════════════════════════════════════════════════════
    # HOJA 2 — REPORTE GRUPAL
    # ══════════════════════════════════════════════════════════

    def _crear_hoja_reporte_grupal(self, wb):
        ws = wb.create_sheet("REPORTE GRUPAL")
        info = self._info_comun()

        _insertar_encabezado_institucional(ws, col_max="F")
        ws["B2"].value = "R09-ProA-SDA-28  Reporte de asistencia a tutoría grupal"
        ws["B2"].font  = _font(italic=True, size=10)
        ws["B2"].alignment = _alin()

        self._bloque_info(ws, 4, info)

        fila_act = 13
        parciales = self._parciales_a_generar()

        for p in parciales:
            label_p = f"{p}° Parcial" if p.isdigit() else "Semestral"
            ws.merge_cells(start_row=fila_act, start_column=1,
                           end_row=fila_act, end_column=6)
            c = ws.cell(row=fila_act, column=1, value=f"RESULTADOS — {label_p}")
            c.font  = _font(bold=True, color=BLANCO)
            c.fill  = _fill(ROJO)
            c.alignment = _alin()
            ws.row_dimensions[fila_act].height = 20
            fila_act += 1

            for ses_num in range(1, 5):
                num_global = (int(p)-1)*4 + ses_num if p.isdigit() else ses_num
                act = self._act_idx.get((p, ses_num))

                # Fila encabezado de sesión
                _enc(ws, fila_act, 1, f"SESIÓN {num_global}", color_fondo="3949AB")
                _enc(ws, fila_act, 2, "NOMBRE DE LA ACTIVIDAD", color_fondo="3949AB")
                _enc(ws, fila_act, 3, "DESCRIPCIÓN DE LA ACTIVIDAD",
                     color_fondo="3949AB", alin_h="left")
                ws.merge_cells(start_row=fila_act, start_column=3,
                               end_row=fila_act, end_column=5)
                _enc(ws, fila_act, 6, "EVIDENCIA", color_fondo="3949AB")
                fila_act += 1

                nombre_act  = act["nombre_actividad"] if act else ""
                desc_act    = act["descripcion"]      if act else ""
                ev_path     = act["evidencia_path"]   if act else None

                _dato(ws, fila_act, 1, "")
                _dato(ws, fila_act, 2, nombre_act)
                c_desc = _dato(ws, fila_act, 3, desc_act, alin_h="left")
                ws.merge_cells(start_row=fila_act, start_column=3,
                               end_row=fila_act+2, end_column=5)
                ws.row_dimensions[fila_act].height = 60

                # Imagen de evidencia
                if ev_path:
                    local = ev_path.replace("/static/","static/") if ev_path.startswith("/static/") else ev_path
                    if os.path.exists(local):
                        try:
                            img = XLImage(local)
                            img.width, img.height = 160, 120
                            ws.add_image(img, f"F{fila_act}")
                        except Exception:
                            pass
                fila_act += 4

        # Firma
        fila_act += 1
        ws.cell(row=fila_act, column=5, value="Firma del tutor:").font = _font(bold=True)
        ws.cell(row=fila_act+2, column=5, value=info["tutora"]).font = _font()

        # Anchos
        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 32
        ws.column_dimensions["C"].width = 28
        ws.column_dimensions["D"].width = 28
        ws.column_dimensions["E"].width = 22
        ws.column_dimensions["F"].width = 26
        _configurar_impresion(ws, orientacion="landscape", ajustar_ancho=True)
        return ws

    # ══════════════════════════════════════════════════════════
    # HOJA 3 — LISTA ASISTENCIA GRUPAL (para firmas)
    # ══════════════════════════════════════════════════════════

    def _crear_hoja_lista_asistencia_grupal(self, wb):
        ws = wb.create_sheet("LISTA ASISTENCIA GRUPAL")
        info = self._info_comun()

        _insertar_encabezado_institucional(ws, col_max="H")
        ws["B2"].value = "R07-ProA-SDA-28  Lista de asistencia a tutoría grupal"
        ws["B2"].font  = _font(italic=True, size=10)
        ws["B2"].alignment = _alin()

        self._bloque_info(ws, 4, info)

        parciales = self._parciales_a_generar()
        fila_enc_base = 13

        for p in parciales:
            label_p = f"{p}° Parcial" if p.isdigit() else "Semestral"
            ws.merge_cells(start_row=fila_enc_base, start_column=1,
                           end_row=fila_enc_base, end_column=8)
            c = ws.cell(row=fila_enc_base, column=1, value=f"PARCIAL {label_p}")
            c.font  = _font(bold=True, color=BLANCO)
            c.fill  = _fill(ROJO)
            c.alignment = _alin()
            fila_enc_base += 1

            sesiones_p = self._sesiones_por_parcial.get(p, [])[:4]
            while len(sesiones_p) < 4:
                sesiones_p.append(None)

            # Encabezado de columnas
            encabezados = ["MATRÍCULA","NOMBRE DEL ALUMNO","SEXO\nH-M"]
            for si, ses in enumerate(sesiones_p):
                num_global = (int(p)-1)*4 + (si+1) if p.isdigit() else si+1
                fecha_str = ""
                if ses and ses.get("fecha_inicio"):
                    fi = ses["fecha_inicio"]
                    if hasattr(fi,"strftime"):
                        fecha_str = fi.strftime("%d/%m/%Y")
                    else:
                        fecha_str = str(fi)[:10]
                encabezados.append(f"FIRMA\nSESIÓN {num_global}\n{fecha_str}")

            for col,tit in enumerate(encabezados, 1):
                _enc(ws, fila_enc_base, col, tit, color_fondo="283593")
            ws.row_dimensions[fila_enc_base].height = 36
            fila_enc_base += 1

            for idx, alumno in enumerate(self.alumnos):
                fila = fila_enc_base + idx
                mat  = alumno.get("matricula","")
                gen  = self._genero_alumno(alumno)
                bg   = GRIS_CLARO if idx % 2 == 0 else BLANCO

                _dato(ws, fila, 1, mat, bg=bg, alin_h="center")
                _dato(ws, fila, 2, alumno.get("nombre_completo",""), bg=bg)
                _dato(ws, fila, 3, gen, bg=bg, alin_h="center")

                for si, ses in enumerate(sesiones_p):
                    sid = ses["id"] if ses else None
                    asistio = self._asistio(sid, mat) if sid else False
                    # Celda en blanco si asistió (para firma), puntitos si faltó
                    valor = "" if asistio else "· · ·"
                    c = _dato(ws, fila, 4+si, valor, bg=bg, alin_h="center")
                    if not asistio:
                        c.font = _font(color="BDBDBD")

                ws.row_dimensions[fila].height = 20

            fila_enc_base += len(self.alumnos) + 2

        # Anchos
        ws.column_dimensions["A"].width = 14
        ws.column_dimensions["B"].width = 36
        ws.column_dimensions["C"].width = 9
        for ci in range(4, 9):
            ws.column_dimensions[get_column_letter(ci)].width = 20
        _configurar_impresion(ws, orientacion="landscape", ajustar_ancho=True)
        return ws

    # ══════════════════════════════════════════════════════════
    # HOJA 4 — REPORTE INDIVIDUAL
    # ══════════════════════════════════════════════════════════

    def _crear_hoja_reporte_individual(self, wb):
        ws = wb.create_sheet("REPORTE INDIVIDUAL")
        info = self._info_comun()

        _insertar_encabezado_institucional(ws, col_max="G")
        ws["B2"].value = "R08-ProA-SDA-28  Reporte de asistencia a tutoría individual"
        ws["B2"].font  = _font(italic=True, size=10)
        ws["B2"].alignment = _alin()

        self._bloque_info(ws, 4, info)

        parciales = self._parciales_a_generar()
        fila_cur  = 13

        for p in parciales:
            label_p = f"{p}° Parcial" if p.isdigit() else "Semestral"
            ws.merge_cells(start_row=fila_cur, start_column=1,
                           end_row=fila_cur, end_column=7)
            c = ws.cell(row=fila_cur, column=1, value=f"TUTORÍA INDIVIDUAL — {label_p}")
            c.font  = _font(bold=True, color=BLANCO)
            c.fill  = _fill(ROJO)
            c.alignment = _alin()
            fila_cur += 1

            sesiones_p = self._sesiones_por_parcial.get(p, [])[:4]
            while len(sesiones_p) < 4:
                sesiones_p.append(None)

            for si, ses in enumerate(sesiones_p):
                sid = ses["id"] if ses else None
                num_global = (int(p)-1)*4 + (si+1) if p.isdigit() else si+1
                fecha_str  = ""
                if ses and ses.get("fecha_inicio"):
                    fi = ses["fecha_inicio"]
                    fecha_str = fi.strftime("%d/%m/%Y") if hasattr(fi,"strftime") else str(fi)[:10]

                # Sub-encabezado de sesión
                ws.merge_cells(start_row=fila_cur, start_column=1,
                               end_row=fila_cur, end_column=7)
                sc = ws.cell(row=fila_cur, column=1,
                             value=f"SESIÓN {num_global}  —  {fecha_str}")
                sc.font  = _font(bold=True, color=BLANCO)
                sc.fill  = _fill("3949AB")
                sc.alignment = _alin()
                fila_cur += 1

                # Encabezados de tabla
                enc_cols = ["FECHA","SEXO","NOMBRE DEL ALUMNO",
                            "MOTIVOS DE TUTORÍA","ACCIONES IMPLEMENTADAS","FIRMA DEL TUTORADO"]
                for ci, tit in enumerate(enc_cols, 1):
                    _enc(ws, fila_cur, ci, tit, color_fondo="283593")
                ws.merge_cells(start_row=fila_cur, start_column=6,
                               end_row=fila_cur, end_column=7)
                fila_cur += 1

                # Solo alumnos que asistieron a tutoría individual
                alumnos_sesion = [
                    a for a in self.alumnos
                    if self._asistio(sid, a.get("matricula",""))
                ] if sid else []

                if not alumnos_sesion:
                    # Fila de "sin asistentes" para no dejar vacío
                    for ci in range(1,8):
                        ws.cell(row=fila_cur, column=ci).border = BORDE_FINO
                    fila_cur += 1
                else:
                    for idx, alumno in enumerate(alumnos_sesion):
                        bg  = GRIS_CLARO if idx % 2 == 0 else BLANCO
                        gen = self._genero_alumno(alumno)
                        _dato(ws, fila_cur, 1, fecha_str, bg=bg, alin_h="center")
                        _dato(ws, fila_cur, 2, gen, bg=bg, alin_h="center")
                        _dato(ws, fila_cur, 3, alumno.get("nombre_completo",""), bg=bg)
                        _dato(ws, fila_cur, 4, "", bg=bg)
                        _dato(ws, fila_cur, 5, "", bg=bg)
                        ws.merge_cells(start_row=fila_cur, start_column=6,
                                       end_row=fila_cur, end_column=7)
                        _dato(ws, fila_cur, 6, "", bg=bg)
                        ws.row_dimensions[fila_cur].height = 22
                        fila_cur += 1

                # Totales de sesión
                tot = len(alumnos_sesion)
                h_cnt = sum(1 for a in alumnos_sesion if self._genero_alumno(a)=="H")
                m_cnt = tot - h_cnt
                ws.cell(row=fila_cur, column=3,
                        value=f"Total: {tot}  |  H: {h_cnt}  |  M: {m_cnt}  |  "
                              f"% asistencia: {round(tot/info['total']*100,1) if info['total'] else 0}%"
                       ).font = _font(bold=True)
                fila_cur += 2

        # Firma
        ws.cell(row=fila_cur, column=5, value="Firma del tutor:").font = _font(bold=True)
        ws.cell(row=fila_cur+2, column=5, value=info["tutora"]).font   = _font()

        ws.column_dimensions["A"].width = 13
        ws.column_dimensions["B"].width = 8
        ws.column_dimensions["C"].width = 34
        ws.column_dimensions["D"].width = 28
        ws.column_dimensions["E"].width = 28
        ws.column_dimensions["F"].width = 20
        ws.column_dimensions["G"].width = 20
        _configurar_impresion(ws, orientacion="landscape", ajustar_ancho=True)
        return ws

    # ══════════════════════════════════════════════════════════
    # HOJA 5+ — PARCIAL (Seguimiento académico detallado)
    # ══════════════════════════════════════════════════════════

    def _crear_hoja_parcial(self, wb, nombre_hoja, parcial_str):
        ws  = wb.create_sheet(nombre_hoja)
        info = self._info_comun()

        _insertar_encabezado_institucional(ws, col_max="R")
        label_p = f"{parcial_str}° Parcial" if parcial_str.isdigit() else "Semestral"
        ws["B2"].value = f"Seguimiento Académico — {label_p}"
        ws["B2"].font  = _font(bold=True, size=11)
        ws["B2"].alignment = _alin()

        # Información general
        self._bloque_info(ws, 4, info)

        # ── Encabezados de tabla ──────────────────────────────
        FILA_ENC = 12
        ENC = [
            "No.","Matrícula","Nombre del Estudiante","Género",
            "Asistencia\n(sesiones)","Canalización\nTut. Indiv.",
            "Prob.\nEconómicos","Prob.\nSalud","Prob.\nEmocionales",
            "Prob.\nFamiliares","Prob.\nAcadémicos",
            "Beca JCF","Beca\nManut.","Beca JMF","Otra\nBeca",
            "Apoyo\nPsicol.","Apoyo\nMédico","Otro\nApoyo",
            "Promedio","Mat.\nReprobadas","Aprobado",
            "Posible\nDeserción","Entregó\nActividad","Observaciones",
        ]
        for ci, tit in enumerate(ENC, 1):
            _enc(ws, FILA_ENC, ci, tit, color_fondo=ROJO)
        ws.row_dimensions[FILA_ENC].height = 40

        # Calcular asistencias por alumno para este parcial
        sesiones_p = self._sesiones_por_parcial.get(parcial_str, [])
        sids_p     = [s["id"] for s in sesiones_p if s]

        for idx, alumno in enumerate(self.alumnos):
            fila = FILA_ENC + 1 + idx
            mat  = alumno.get("matricula","")
            gen  = self._genero_alumno(alumno)
            det  = self.detalle_map.get(mat, {})
            bg   = GRIS_CLARO if idx % 2 == 0 else BLANCO

            # Contar asistencias QR en este parcial
            asistencias_cnt = sum(1 for sid in sids_p if self._asistio(sid, mat))

            def _d(k, default=0): return det.get(k, default)

            vals = [
                idx+1, mat, alumno.get("nombre_completo",""), gen,
                asistencias_cnt, _d("canalizacion_tutoria_individual"),
                _d("problemas_economicos"), _d("problemas_salud"),
                _d("problemas_emocionales"), _d("problemas_familiares"),
                _d("problemas_academicos"),
                _d("beca_jcf"), _d("beca_manutencion"), _d("beca_jmf"), _d("beca_otro"),
                _d("apoyo_psicologico"), _d("apoyo_medico"), _d("apoyo_otro"),
                det.get("promedio",""), _d("materias_reprobadas"),
                "Sí" if _d("estatus_aprobado") else "No",
                "Sí" if _d("posible_desercion") else "No",
                "Sí" if _d("entrego_actividad") else "No",
                det.get("comentario",""),
            ]
            for ci, v in enumerate(vals, 1):
                c = _dato(ws, fila, ci, v, bg=bg,
                          alin_h="left" if ci in [3,23] else "center")
                # Resaltes especiales
                if ci == 22 and _d("posible_desercion"):   # posible deserción
                    c.fill = _fill("FFCDD2")
                if ci == 21 and not _d("estatus_aprobado") and _d("materias_reprobadas"):
                    c.fill = _fill("FFF9C4")

        # ── Fila de totales / resumen ─────────────────────────
        FILA_TOT = FILA_ENC + 1 + len(self.alumnos)
        ws.cell(row=FILA_TOT, column=3, value="TOTALES").font = _font(bold=True)
        ws.cell(row=FILA_TOT, column=4,
                value=f'=COUNTIF(D{FILA_ENC+1}:D{FILA_TOT-1},"H")').number_format = "0"
        ws.cell(row=FILA_TOT+1, column=3, value="% Aprobación").font = _font(bold=True)
        ws.cell(row=FILA_TOT+1, column=21,
                value=f'=COUNTIF(U{FILA_ENC+1}:U{FILA_TOT-1},"Sí")/{len(self.alumnos)}'
               ).number_format = "0.0%"

        # Anchos
        anchos = [5,14,34,7, 10,10, 10,10,10,10,10, 9,9,9,9, 10,10,10, 10,12,10,12,10,30]
        for ci, aw in enumerate(anchos, 1):
            ws.column_dimensions[get_column_letter(ci)].width = aw

        ws.freeze_panes = "E13"
        _configurar_impresion(ws, orientacion="landscape", ajustar_ancho=True)
        return ws

    # ══════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL
    # ══════════════════════════════════════════════════════════

    def exportar(self):
        wb = Workbook()
        wb.remove(wb.active)

        self._crear_hoja_asistencia_grupal(wb)
        self._crear_hoja_reporte_grupal(wb)
        self._crear_hoja_lista_asistencia_grupal(wb)
        self._crear_hoja_reporte_individual(wb)

        if self.parcial == "S":
            for num in ["1","2","3","4"]:
                nombre = f"{num}er parcial" if num == "1" else f"{num}° parcial"
                self._crear_hoja_parcial(wb, nombre, num)
            self._crear_hoja_parcial(wb, "Semestral", "S")
        else:
            nombre = f"{self.parcial}er parcial" if self.parcial == "1" else f"{self.parcial}° parcial"
            self._crear_hoja_parcial(wb, nombre, self.parcial)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output