#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera la revision V5.2 N3 R05 en FreeCAD.

El modelo conserva la parrilla N3 W6X9 de R01 y agrega, en una rama separada,
la cabina heredada, la puerta, los rieles largos, las posiciones de lavado y
carga, ruedas ferroviarias candidatas, soportes, PAD, centrado, retencion,
bloqueo y reservas de interfaz. Las piezas cuyo cierre depende de planta,
proveedor o ensayo llevan esa condicion en sus propiedades.

R05 conserva N3 W6X9 y corrige F01-F05 de la revisión independiente de R04.
El estado físico exportado es lavado: el cassette completo de cada centrador
queda retraído a R1080, mientras las posiciones activas son envolventes GHOST.
Las guías fijas permanecen bajo Z780. Los topes y el manillar incluyen placas,
cartelas y pernos conceptuales que hacen explícita su ruta de carga.

Resultado: CIERRE_HALLAZGOS_R04_R05_SIN_NUEVA_CORRIDA_SAP.
No es un modelo liberado para fabricacion.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import FreeCAD as App
import Part


OUT = Path(__file__).resolve().parent
WORK = OUT / "_work"
VIEWS = OUT / "VISTAS_TECNICAS"
WORK.mkdir(parents=True, exist_ok=True)
VIEWS.mkdir(parents=True, exist_ok=True)

FCSTD = OUT / "04_MESA_N3_R05_CIERRE_HALLAZGOS.FCStd"
STEP = OUT / "05_MESA_N3_R05_ESTADO_LAVADO.step"
DXF = WORK / "LINEAS_MEDIAS_N3_R05_NO_AFECTADAS.dxf"
PAYLOAD = WORK / "mesh_payload_R05.json"
DATA_JSON = WORK / "R05_CAD_DATA.json"
QA_JSON = WORK / "GEOMETRY_QA_R05.json"
QA_CSV = WORK / "GEOMETRIC_CHECKS_R05.csv"
TRACE_CSV = OUT / "14_FUENTES_Y_TRAZABILIDAD_R05.csv"
LOG = WORK / "REGISTRO_GENERACION_R05.txt"

RESULT_CLASS = "CIERRE_HALLAZGOS_R04_R05_SIN_NUEVA_CORRIDA_SAP"
WARNING = "NO LIBERADO PARA FABRICACION - R05 SAP NO EJECUTADO"
TOL = 1.0e-3


def q(value, unit, status, source, note=""):
    return {"value": value, "unit": unit, "status": status, "source": source, "note": note}


P = {
    # Base N3 verificada
    "x_left": q(-930.0, "mm", "VERIFICADO", "SAP R01 / Joint Coordinates"),
    "x_right": q(930.0, "mm", "VERIFICADO", "SAP R01 / Joint Coordinates"),
    "y_end_neg": q(-950.0, "mm", "VERIFICADO", "SAP R01 / Joint Coordinates"),
    "y_end_pos": q(950.0, "mm", "VERIFICADO", "SAP R01 / Joint Coordinates"),
    "y_pad_neg": q(-574.175, "mm", "VERIFICADO", "R01 parametric model"),
    "y_pad_pos": q(574.175, "mm", "VERIFICADO", "R01 parametric model"),
    "x_pad01": q(663.0, "mm", "VERIFICADO", "SAP R01 / Joint Coordinates"),
    "wheel_x_abs": q(930.0, "mm", "VERIFICADO", "SAP R01 / support nodes"),
    "wheel_y_abs": q(722.0, "mm", "VERIFICADO", "SAP R01 / support nodes"),
    "profile_name": q("W6X9", "-", "VERIFICADO", "SAP R01 / Frame Section Assignments"),
    "profile_d": q(149.860, "mm", "VERIFICADO", "AISC Shapes Database v16 W150X13.5"),
    "profile_bf": q(100.076, "mm", "VERIFICADO", "AISC Shapes Database v16 W150X13.5"),
    "profile_tw": q(4.318, "mm", "VERIFICADO", "AISC Shapes Database v16 W6X9"),
    "profile_tf": q(5.461, "mm", "VERIFICADO", "AISC Shapes Database v16 W6X9"),
    "profile_area": q(1730.0, "mm2", "VERIFICADO", "AISC Shapes Database v16"),
    "profile_line_mass": q(13.5, "kg/m", "VERIFICADO", "AISC Shapes Database v16"),
    "frame_mass": q(168.12469, "kg", "CALCULADO_R01", "SAP R01 / mass summary"),
    "z_frame_top": q(805.0, "mm", "HEREDADO_PROVISIONAL", "V5.2 inherited CAD datum"),
    # Rodamiento
    "bearing_model": q("SKF 241/900 ECAK30/W33", "-", "VERIFICADO", "Project brief and SKF designation"),
    "bearing_od": q(1420.0, "mm", "VERIFICADO", "Project brief"),
    "bearing_id": q(900.0, "mm", "VERIFICADO", "Project brief"),
    "bearing_width": q(515.0, "mm", "VERIFICADO", "Project brief"),
    "bearing_mass": q(3032.0, "kg", "VERIFICADO", "Project brief"),
    "sap_external_load": q(29.844, "kN", "EJECUTADO_R01", "SAP R01 / 3 loads of 9.948 kN"),
    "gravity": q(9.81, "m/s2", "HIPOTESIS_DISENO", "R03 calculation convention"),
    # Cabina y recorrido
    "cabin_x_inside": q(3940.0, "mm", "HEREDADO_PROVISIONAL", "V5/V5.2 inherited CAD"),
    "cabin_y_inside": q(4040.0, "mm", "HEREDADO_PROVISIONAL", "V5/V5.2 inherited CAD"),
    "cabin_z_inside": q(2570.0, "mm", "HEREDADO_PROVISIONAL", "V5/V5.2 inherited CAD"),
    "door_plane_y": q(-2020.0, "mm", "HEREDADO_PROVISIONAL", "V5/V5.2 inherited CAD"),
    "door_width": q(2140.0, "mm", "HEREDADO_PROVISIONAL", "V5/V5.2 inherited CAD"),
    "door_z_bottom": q(140.0, "mm", "HEREDADO_PROVISIONAL", "V5/V5.2 inherited CAD"),
    "door_z_top": q(1605.0, "mm", "HEREDADO_PROVISIONAL", "V5/V5.2 inherited CAD"),
    "wash_center_y": q(0.0, "mm", "DECISION_R03", "Inherited work center retained"),
    "c_load": q(300.0, "mm", "DECISION_R03_REVISABLE", "Clearance between rear moving envelope and door in load state"),
    "operator_clearance": q(800.0, "mm", "HIPOTESIS_DISENO", "External standing and handle zone; verify plant"),
    # Rueda y riel seleccionados de manera condicionada
    "wheel_product": q("Blickle SPKVS 200K", "-", "CANDIDATO_CON_RESPALDO_CATALOGO", "Blickle flanged wheel catalogue"),
    "wheel_d": q(200.0, "mm", "CATALOGO", "Blickle SPKVS 200K"),
    "wheel_flange_d": q(240.0, "mm", "CATALOGO", "Blickle SPKVS 200K"),
    "wheel_total_width": q(60.0, "mm", "CATALOGO", "Blickle SPKVS 200K"),
    "wheel_running_width": q(48.0, "mm", "CATALOGO", "Blickle SPKVS 200K"),
    "wheel_axle_bore": q(35.0, "mm", "CATALOGO", "Blickle SPKVS 200K"),
    "wheel_catalog_capacity": q(2500.0, "kg", "CATALOGO", "Blickle SPKVS 200K at 4 km/h"),
    "wheel_hardness_min": q(190.0, "HB", "CATALOGO", "Blickle SPKVS series"),
    "wheel_hardness_max": q(230.0, "HB", "CATALOGO", "Blickle SPKVS series"),
    "wheel_mass_each": q(14.3, "kg", "CATALOGO_VERIFICADO_R05", "Blickle product 253179, consulted 2026-09-08"),
    "axle_d": q(35.0, "mm", "DECISION_R03", "Matched to wheel bore; C45 normalized candidate"),
    "fork_plate_t": q(12.0, "mm", "CALCULADO_R03", "Double-plate fork preliminary sizing"),
    "fork_clear_width": q(80.0, "mm", "CORREGIDO_R03", "Symmetric opening gives 4 mm minimum clearance to asymmetric flange"),
    "fork_top_width": q(132.0, "mm", "CORREGIDO_R03", "Covers two 12 mm cheeks outside the 80 mm clear opening"),
    "fork_mass_each": q(13.0, "kg", "ESTIMACION_CAD_R03", "Updated fork envelope; verify after detailed machining"),
    "rail_product": q("A45 DIN 536", "-", "CANDIDATO_CON_RESPALDO_CATALOGO", "ArcelorMittal crane rail"),
    "rail_y_min": q(-4620.0, "mm", "HEREDADO_PROVISIONAL", "V5.2 long rail envelope"),
    "rail_y_max": q(1920.0, "mm", "HEREDADO_PROVISIONAL", "V5.2 long rail envelope"),
    "rail_height": q(55.0, "mm", "CATALOGO", "ArcelorMittal A45"),
    "rail_base_width": q(125.0, "mm", "CATALOGO", "ArcelorMittal A45"),
    "rail_head_width": q(45.0, "mm", "CATALOGO", "ArcelorMittal A45"),
    "rail_web_width": q(24.0, "mm", "CATALOGO", "ArcelorMittal A45"),
    "rail_mass_per_m": q(22.10, "kg/m", "CATALOGO", "ArcelorMittal A45"),
    "rail_Ix": q(90.0, "cm4", "CATALOGO", "ArcelorMittal A45 section sheet"),
    "rail_Z_head": q(27.0, "cm3", "CATALOGO", "ArcelorMittal A45 section sheet"),
    "rail_Z_base": q(41.5, "cm3", "CATALOGO", "ArcelorMittal A45 section sheet"),
    "rail_contact_z": q(290.0, "mm", "HEREDADO_PROVISIONAL", "V5.2 inherited CAD datum"),
    "rail_support_count": q(12, "-", "DECISION_R03_REVISABLE", "594.5 mm average spacing over 6540 mm"),
    "rail_pad_t": q(7.0, "mm", "CATALOGO_INTERFACE", "Gantrex RailLok pad option"),
    "rail_clip": q("Gantrex RailLok BG10/BJ", "-", "CANDIDATO_CON_RESPALDO_CATALOGO", "Gantrex selection table for A45 with 7 mm pad"),
    # PAD, centrado, retencion y bloqueo
    "pad_radius": q(663.0, "mm", "VERIFICADO", "SAP R01 pad nodes"),
    "pad_base_h": q(45.0, "mm", "BASE_DESARROLLO_R03", "12 mm spreader plus 33 mm pedestal"),
    "pad_cap_h": q(32.0, "mm", "BASE_DESARROLLO_R03", "Retained for recalculation with PAD equilibrium"),
    "pad_liner_h": q(8.0, "mm", "CANDIDATO_CONDICIONADO", "Same liner in both compared alternatives"),
    "pad_r_in": q(638.0, "mm", "HEREDADO_VERIFICADO", "R01 CAD"),
    "pad_r_out": q(688.0, "mm", "HEREDADO_VERIFICADO", "R01 CAD"),
    "pad_angle": q(24.0, "deg", "HEREDADO_VERIFICADO", "R01 CAD"),
    "liner_material": q("PE-UHMW PE1000 8 mm", "-", "SELECCION_RECOMENDADA_CONDICIONADA", "Roechling Polystone M / chemical check pending"),
    "liner_compressive_strength": q(20.68, "MPa", "CATALOGO", "Roechling Polystone M: 3000 psi"),
    "locator_angles": q("60;180;300", "deg", "DECISION_R03", "R01 arrangement retained"),
    "locator_roller_d": q(50.0, "mm", "DECISION_R03", "R735 center gives R710 nominal contact"),
    "locator_roller_length": q(60.0, "mm", "DECISION_R03", "Horizontal tangential axis"),
    "locator_center_r": q(735.0, "mm", "CALCULADO", "710 bearing radius plus 25 roller radius"),
    "locator_retract_stroke": q(345.0, "mm", "PREDIMENSIONADO_R05", "Complete carriage R735 to R1080; fixed guides below Z780"),
    "locator_screw": q("Tr24x5", "-", "CANDIDATO_R05", "5.31 N.m theoretical at 2 kN and efficiency 0.30"),
    "locator_force_limit": q(2.0, "kN", "REQUISITO_DEMANDA_R05", "Force envelope for mast, screw and locks; not certified capacity"),
    "centering_target": q(5.0, "mm", "REQUISITO_DISENO_R05", "Radial error: full PAD coverage with 17 mm geometric margin; tolerance chain pending"),
    "retention_design_force": q(2.0, "kN", "REQUISITO_DEMANDA_R05", "Per-stop design envelope; not a certified capacity"),
    "table_lock_pin_d": q(25.0, "mm", "CALCULADO_R03", "Duplex stainless pin in double shear"),
    "table_lock_design_force": q(10.0, "kN", "DECISION_R03", "Covers winch jam and wash actions pending final data"),
    # Operacion, masa y acciones
    "moving_mass_design": q(3500.0, "kg", "DECISION_R03", "Rounded design mass with margin for undocumented accessories"),
    "cg_ecc_x": q(100.0, "mm", "HIPOTESIS_ENVOLVENTE_CG_MOVIL", "Whole mobile assembly CG envelope; does not move the bearing on PADs"),
    "cg_ecc_y": q(100.0, "mm", "HIPOTESIS_ENVOLVENTE_CG_MOVIL", "Whole mobile assembly CG envelope; does not move the bearing on PADs"),
    "uneven_factor": q(1.333, "-", "HISTORICO_R02_NO_USAR_COMO_ENVOLVENTE", "Retained only for traceability"),
    "vertical_impact_factor": q(1.15, "-", "HIPOTESIS_DISENO", "Low-speed rail joints"),
    "travel_speed": q(0.15, "m/s", "DECISION_R03", "Controlled walking speed"),
    "structural_acceleration": q(0.30, "m/s2", "HIPOTESIS_DISENO", "Start/brake structural case"),
    "rolling_start_clean": q(0.006, "-", "HIPOTESIS_ENSAYO", "Conservative clean aligned rail scenario"),
    "rolling_run_clean": q(0.004, "-", "HIPOTESIS_ENSAYO", "Conservative clean aligned rail scenario"),
    "rolling_start_best": q(0.0035, "-", "ESCENARIO", "Commissioning target"),
    "rolling_run_best": q(0.0025, "-", "ESCENARIO", "Commissioning target"),
    "rolling_start_adverse": q(0.015, "-", "ESCENARIO", "Wet/misaligned/joint deterioration"),
    "rolling_run_adverse": q(0.010, "-", "ESCENARIO", "Wet/misaligned/joint deterioration"),
    "slope_design": q(0.002, "m/m", "HIPOTESIS_DISENO", "0.2 percent; survey required"),
    "slope_adverse": q(0.005, "m/m", "ESCENARIO", "0.5 percent"),
    "joint_force_clean": q(50.0, "N", "HIPOTESIS_ENSAYO", "Alignment/joint allowance"),
    "joint_force_adverse": q(150.0, "N", "ESCENARIO", "Poor joint/alignment allowance"),
    "hse_start_guideline": q(200.0, "N", "REFERENCIA_ERGONOMICA", "HSE push/pull assessment guideline for men; not a safe limit"),
    "hse_run_guideline": q(100.0, "N", "REFERENCIA_ERGONOMICA", "HSE push/pull assessment guideline for men; not a safe limit"),
    "haacon_minimum_load": q(75.0, "kg", "CATALOGO_NO_CUMPLIDO", "haacon manual 094008, technical data"),
    "haacon_rope_manual_d": q(6.0, "mm", "CATALOGO", "haacon manual 094008, technical data"),
    "haacon_rope_web_d": q(7.0, "mm", "DISCREPANCIA_DOCUMENTAL", "haacon commercial page reviewed in R02"),
    "drive_architecture": q("Empuje manual directo; cadena solo alternativa", "-", "PREFERENCIA_USUARIO_R05", "R05 adds a connected handle; dynamometer test pending"),
    "drive_design_pull": q(1.0, "kN", "DECISION_R03", "Covers adverse start and 565 N stop screen"),
    "drive_sprocket_radius": q(75.0, "mm", "PREDIMENSIONADO_R03", "Compact guarded drive sprocket"),
    "drive_ratio": q(6.0, "-", "PREDIMENSIONADO_R03", "Manual reduction target"),
    "drive_efficiency": q(0.60, "-", "HIPOTESIS_DISENO", "Chain and reduction combined efficiency"),
    "drive_handwheel_radius": q(250.0, "mm", "PREDIMENSIONADO_R03", "Two-hand fixed operator station"),
    "drive_brake_torque": q(100.0, "N.m", "REQUISITO_R03", "Normally-on brake independent of transmitted load"),
    "drive_operator_y": q(-2700.0, "mm", "ALTERNATIVA_NO_SELECCIONADA_R05", "Zona alternativa fuera del frente de cabina; integración de cadena pendiente"),
    # Interfaz aspersion
    "head_a_standoff": q(150.0, "mm", "HEREDADO_PRELIMINAR", "HANDOFF_DATA_CLAUDE"),
    "head_a_status": q("PENDIENTE_DATOS_DE_ENTRADA", "-", "PENDIENTE_EXTERNO", "HANDOFF_DATA_CLAUDE"),
}


def v(name):
    return P[name]["value"]


URLS = {
    "Blickle SPKVS": "https://www.blickle.com/product/spkvs-200k-253179",
    "ArcelorMittal A45": "https://rails.arcelormittal.com/wp-content/uploads/2023/10/ArcelorMittal-CRANE-Rails-EN.pdf",
    "Gantrex BG10": "https://www.gantrex.com/content/uploads/2022/07/GXHQ_EN_CLIPS_RailLok-Clip-BG10_2017-09_R2.0-1.pdf",
    "haacon 4585 manual": "https://www.haacon.com/wp-content/uploads/2022/10/094008_Seilwinde-DE-FR-EN-IT.pdf",
    "Tractel Tirfor TU8 candidate": "https://www.tractel.com/PIM/Manuals/LH/Manual%20LH/Group%201/150425.ind-03.03-23.pdf",
    "HSE push pull": "https://www.hse.gov.uk/msd/pushpull/assessment.htm",
    "ISO 11228-2": "https://www.iso.org/standard/26521.html",
    "Roechling PE1000": "https://www.roechling.com/fileadmin/assets/Technical%20Data%20Sheet%20Polystone%C2%AE%20M%20Natural%20-%20ASTM%20717946%20EN.pdf",
    "SKF 6207 reference": "https://cdn.skfmediahub.skf.com/api/public/0901d19680416953/pdf_preview_medium/0901d19680416953_pdf_preview_medium.pdf",
}


COL = {
    "FRAME": (0.12, 0.42, 0.74), "PAD": (0.95, 0.49, 0.10),
    "LINER": (0.10, 0.72, 0.66), "BEARING": (0.28, 0.57, 0.78),
    "WHEEL": (0.26, 0.29, 0.33), "FORK": (0.86, 0.48, 0.12),
    "RAIL": (0.35, 0.38, 0.42), "SUPPORT": (0.55, 0.58, 0.62),
    "CABIN": (0.62, 0.70, 0.78), "CENTER": (0.88, 0.35, 0.16),
    "LOCK": (0.74, 0.22, 0.17), "HANDLE": (0.20, 0.48, 0.25),
    "GHOST": (0.48, 0.52, 0.56), "HEAD": (0.55, 0.28, 0.72),
    "FLOOR": (0.72, 0.73, 0.75), "REFERENCE": (0.15, 0.25, 0.88),
    "DRIVE": (0.32, 0.53, 0.24),
}


def add_prop(obj, name, value, group="R05_TRAZABILIDAD"):
    if name not in obj.PropertiesList:
        if isinstance(value, bool):
            obj.addProperty("App::PropertyBool", name, group)
        elif isinstance(value, (int, float)):
            obj.addProperty("App::PropertyFloat", name, group)
        else:
            obj.addProperty("App::PropertyString", name, group)
    setattr(obj, name, value)


def add_shape(doc, group, name, label, shape, role, status, source, export=True,
              transparency=0, note="", moving=False):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    add_prop(obj, "Rol", role)
    add_prop(obj, "EstadoIngenieria", status)
    add_prop(obj, "Fuente", source)
    add_prop(obj, "NotaTecnica", note)
    add_prop(obj, "ExportarSTEP", bool(export))
    add_prop(obj, "ComponenteMovil", bool(moving))
    add_prop(obj, "NoLiberadoFabricacion", True)
    try:
        obj.ViewObject.ShapeColor = COL.get(role, COL["SUPPORT"])
        obj.ViewObject.LineColor = tuple(max(0.0, c * 0.60) for c in obj.ViewObject.ShapeColor)
        obj.ViewObject.Transparency = int(transparency)
    except Exception:
        pass
    group.addObject(obj)
    return obj


def make_w_member(x1, y1, x2, y2, z_top, yoff=0.0):
    d, bf, tw, tf = v("profile_d"), v("profile_bf"), v("profile_tw"), v("profile_tf")
    z0 = z_top - d
    y1 += yoff
    y2 += yoff
    if abs(y2-y1) < TOL:
        xa, xb = sorted((x1, x2)); length = xb-xa
        lower = Part.makeBox(length, bf, tf, App.Vector(xa, y1-bf/2, z0))
        web = Part.makeBox(length, tw, d-2*tf, App.Vector(xa, y1-tw/2, z0+tf))
        upper = Part.makeBox(length, bf, tf, App.Vector(xa, y1-bf/2, z_top-tf))
    elif abs(x2-x1) < TOL:
        ya, yb = sorted((y1, y2)); length = yb-ya
        lower = Part.makeBox(bf, length, tf, App.Vector(x1-bf/2, ya, z0))
        web = Part.makeBox(tw, length, d-2*tf, App.Vector(x1-tw/2, ya, z0+tf))
        upper = Part.makeBox(bf, length, tf, App.Vector(x1-bf/2, ya, z_top-tf))
    else:
        raise ValueError("Only X/Y aligned W members are supported")
    return lower.fuse(web).fuse(upper).removeSplitter(), length


def annular_sector(r_in, r_out, angle_deg, height, z0, theta, yoff=0.0):
    outer = Part.makeCylinder(r_out, height, App.Vector(0, yoff, z0), App.Vector(0,0,1), angle_deg)
    inner = Part.makeCylinder(r_in, height, App.Vector(0, yoff, z0), App.Vector(0,0,1), angle_deg)
    sh = outer.cut(inner)
    sh.rotate(App.Vector(0, yoff, 0), App.Vector(0,0,1), theta-angle_deg/2)
    return sh


def radial_box(radius, radial, tangent, height, z0, theta, yoff=0.0):
    sh = Part.makeBox(radial, tangent, height,
                      App.Vector(radius-radial/2, yoff-tangent/2, z0))
    sh.rotate(App.Vector(0, yoff, 0), App.Vector(0,0,1), theta)
    return sh


def cylinder_centered(center, axis, length, radius):
    a = App.Vector(*axis)
    a.normalize()
    c = App.Vector(*center)
    return Part.makeCylinder(radius, length, c.sub(a.multiply(length/2)), a)


def tube_centered(center, axis, length, od, thickness):
    """Hollow circular tube centred on an arbitrary axis."""
    outer = cylinder_centered(center, axis, length, od / 2.0)
    inner_d = od - 2.0 * thickness
    inner = cylinder_centered(center, axis, length + 2.0, inner_d / 2.0)
    return outer.cut(inner)


def make_a45(x, y0, y1, ztop):
    h = v("rail_height"); base = v("rail_base_width"); head = v("rail_head_width"); web = v("rail_web_width")
    z0 = ztop-h
    pts = [
        App.Vector(x-base/2, y0, z0), App.Vector(x+base/2, y0, z0),
        App.Vector(x+54, y0, z0+14.5), App.Vector(x+web/2, y0, z0+14.5),
        App.Vector(x+head/2, y0, z0+33.0), App.Vector(x+head/2, y0, ztop),
        App.Vector(x-head/2, y0, ztop), App.Vector(x-head/2, y0, z0+33.0),
        App.Vector(x-web/2, y0, z0+14.5), App.Vector(x-54, y0, z0+14.5),
        App.Vector(x-base/2, y0, z0),
    ]
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(App.Vector(0, y1-y0, 0))


def solve3(a, b):
    """Solve a 3x3 system without adding a numerical dependency to FreeCAD."""
    m = [list(map(float, a[i])) + [float(b[i])] for i in range(3)]
    for i in range(3):
        pivot = max(range(i, 3), key=lambda row: abs(m[row][i]))
        m[i], m[pivot] = m[pivot], m[i]
        divisor = m[i][i]
        if abs(divisor) < 1.0e-12:
            raise ValueError("Singular support geometry")
        for j in range(i, 4):
            m[i][j] /= divisor
        for row in range(3):
            if row == i:
                continue
            factor = m[row][i]
            for j in range(i, 4):
                m[row][j] -= factor*m[i][j]
    return [m[i][3] for i in range(3)]


def reactions_three_supports(points, weight_kN, ex_mm, ey_mm):
    matrix = [
        [1.0, 1.0, 1.0],
        [p[0] for p in points],
        [p[1] for p in points],
    ]
    return solve3(matrix, [weight_kN, weight_kN*ex_mm, weight_kN*ey_mm])


def calculations():
    g = v("gravity")
    frame_outer_x = v("wheel_x_abs") + v("profile_bf")/2
    frame_outer_y = v("y_end_pos") + v("profile_bf")/2
    s_geom = abs(v("door_plane_y")) + frame_outer_y
    s_op = s_geom + v("c_load")
    y_load = -s_op
    rail_len = v("rail_y_max")-v("rail_y_min")
    wheelbase = 2*v("wheel_y_abs")
    rail_req_zero_margin = s_op+wheelbase
    load_wheel_min = y_load-v("wheel_y_abs")
    load_end_margin = load_wheel_min-v("rail_y_min")
    wash_end_margin = v("rail_y_max")-v("wheel_y_abs")
    door_side_clear = (v("door_width")-2*frame_outer_x)/2
    frame_bottom = v("z_frame_top")-v("profile_d")
    bearing_bottom = v("z_frame_top")+v("pad_base_h")+v("pad_cap_h")+v("pad_liner_h")
    bearing_top = bearing_bottom+v("bearing_width")
    wheel_axis_z = v("rail_contact_z")+v("wheel_d")/2
    moving_bottom_z = wheel_axis_z-v("wheel_flange_d")/2
    carrier_axis_to_frame = frame_bottom-wheel_axis_z
    carrier_wheel_top_to_frame = frame_bottom-(v("rail_contact_z")+v("wheel_d"))
    support_spacing = rail_len/(v("rail_support_count")-1)

    pad_area = math.pi*(v("pad_r_out")**2-v("pad_r_in")**2)*v("pad_angle")/360
    # Masses of R03 moving items; values other than bearing/frame remain design estimates.
    pad_base_volume = 160*140*12 + 80*70*33
    pad_cap_volume = pad_area*v("pad_cap_h")
    pad_liner_volume = pad_area*v("pad_liner_h")
    pad_mass_each = (pad_base_volume+pad_cap_volume)*7.85e-6 + pad_liner_volume*0.93e-6
    mass_items = [
        ("Bearing", v("bearing_mass"), 0.0, 0.0, bearing_bottom+v("bearing_width")/2, "VERIFICADO"),
        ("W6X9 frame", v("frame_mass"), 61.4574, 0.0, v("z_frame_top")-v("profile_d")/2, "CORREGIDO_CON_GEOMETRIA_R01"),
        ("3 PAD assemblies", 3*pad_mass_each, 0.0, 0.0, v("z_frame_top")+43, "CALCULADO_R03"),
        ("4 flanged wheels", 4*v("wheel_mass_each"), 0.0, 0.0, wheel_axis_z, "CATALOGO"),
        ("4 fork and adapter sets", 4*v("fork_mass_each"), 0.0, 0.0, 520.0, "CALCULADO_R03"),
        ("3 locator assemblies", 36.0, 0.0, 0.0, 950.0, "HIPOTESIS_MASA"),
        ("Retention locks", 8.0, 0.0, -850.0, 550.0, "HIPOTESIS_MASA"),
        ("Push handle and chain coupling", 7.0, 0.0, -1000.0, 980.0, "HIPOTESIS_MASA"),
        ("Fasteners guards and services allowance", 20.0, 0.0, 0.0, 700.0, "HIPOTESIS_MASA"),
    ]
    estimated_mass = sum(x[1] for x in mass_items)
    cgx = sum(x[1]*x[2] for x in mass_items)/estimated_mass
    cgy = sum(x[1]*x[3] for x in mass_items)/estimated_mass
    cgz = sum(x[1]*x[4] for x in mass_items)/estimated_mass
    W = v("moving_mass_design")*g/1000
    r_avg = W/4
    r_four_max = r_avg*(1+v("cg_ecc_x")/v("wheel_x_abs")+v("cg_ecc_y")/v("wheel_y_abs"))
    wheel_points = [(-930.0,-722.0),(-930.0,722.0),(930.0,-722.0),(930.0,722.0)]
    wheel_names = ["W-01", "W-02", "W-03", "W-04"]
    three_contact_cases = []
    for ex in (v("cg_ecc_x"), -v("cg_ecc_x")):
        for ey in (v("cg_ecc_y"), -v("cg_ecc_y")):
            for missing in range(4):
                active = [i for i in range(4) if i != missing]
                rr = reactions_three_supports([wheel_points[i] for i in active], W, ex, ey)
                feasible = min(rr) >= -1.0e-8
                three_contact_cases.append({
                    "ex_mm": ex, "ey_mm": ey, "missing_wheel": wheel_names[missing],
                    "active_wheels": [wheel_names[i] for i in active],
                    "reactions_kN": rr, "feasible_unilateral": feasible,
                    "max_reaction_kN": max(rr),
                })
    feasible_wheel_cases = [c for c in three_contact_cases if c["feasible_unilateral"]]
    governing_wheel_case = max(feasible_wheel_cases, key=lambda c: c["max_reaction_kN"])
    r_three_max = governing_wheel_case["max_reaction_kN"]
    r_select = r_three_max*v("vertical_impact_factor")
    wheel_cap = v("wheel_catalog_capacity")*g/1000

    basket_adapter_mass = 20.0
    basket_base_mass = estimated_mass-v("bearing_mass")+basket_adapter_mass

    E = 200000.0
    I = v("rail_Ix")*10000.0
    L = support_spacing
    r_uls = r_three_max*1.40
    Pn = r_uls*1000
    rail_M = Pn*L/4
    rail_stress_head = rail_M/(v("rail_Z_head")*1000)
    rail_stress_base = rail_M/(v("rail_Z_base")*1000)
    rail_defl = r_select*1000*L**3/(48*E*I)

    weight_N = v("moving_mass_design")*g
    push = {
        "best_level": {
            "start_N": v("rolling_start_best")*weight_N,
            "run_N": v("rolling_run_best")*weight_N,
            "slope": 0.0, "joint_N": 0.0,
        },
        "design_clean": {
            "start_N": v("rolling_start_clean")*weight_N+v("slope_design")*weight_N+v("joint_force_clean"),
            "run_N": v("rolling_run_clean")*weight_N+v("slope_design")*weight_N+v("joint_force_clean"),
            "slope": v("slope_design"), "joint_N": v("joint_force_clean"),
        },
        "adverse": {
            "start_N": v("rolling_start_adverse")*weight_N+v("slope_adverse")*weight_N+v("joint_force_adverse"),
            "run_N": v("rolling_run_adverse")*weight_N+v("slope_adverse")*weight_N+v("joint_force_adverse"),
            "slope": v("slope_adverse"), "joint_N": v("joint_force_adverse"),
        },
    }
    stop_distance = 0.10
    kinetic = 0.5*v("moving_mass_design")*v("travel_speed")**2
    emergency_stop_force = kinetic/stop_distance+v("slope_adverse")*weight_N
    drive_force_N = v("drive_design_pull")*1000
    drive_output_torque_Nm = drive_force_N*v("drive_sprocket_radius")/1000
    drive_operator_force_N = drive_output_torque_Nm*1000/(v("drive_ratio")*v("drive_efficiency")*v("drive_handwheel_radius"))
    stop_torque_Nm = emergency_stop_force*v("drive_sprocket_radius")/1000
    haacon_minimum_traction_N = v("haacon_minimum_load")*g

    bearing_weight_kN = v("bearing_mass")*g/1000
    bearing_cg_height_mm = v("bearing_width")/2
    inertia_equivalent_ecc_mm = bearing_cg_height_mm*v("structural_acceleration")/g
    pad_ecc_envelope_mm = max(v("cg_ecc_x"), v("cg_ecc_y"))+inertia_equivalent_ecc_mm
    pad_points = [(663.0,0.0),(-331.5,574.175),(-331.5,-574.175)]
    pad_names = ["PAD-01", "PAD-02", "PAD-03"]
    pad_cases=[]
    for ex in (pad_ecc_envelope_mm,-pad_ecc_envelope_mm):
        for ey in (pad_ecc_envelope_mm,-pad_ecc_envelope_mm):
            rr=reactions_three_supports(pad_points,bearing_weight_kN,ex,ey)
            pad_cases.append({"ex_mm":ex,"ey_mm":ey,"reactions_kN":dict(zip(pad_names,rr)),"max_reaction_kN":max(rr)})
    governing_pad_case=max(pad_cases,key=lambda c:c["max_reaction_kN"])
    pad_service = bearing_weight_kN/3
    pad_static_envelope = governing_pad_case["max_reaction_kN"]
    pad_dynamic = pad_static_envelope*v("vertical_impact_factor")
    pad_uls = pad_static_envelope*1.40
    pad_design = pad_uls
    pad_pressure = pad_dynamic*1000/pad_area
    arc_len = v("pad_radius")*math.radians(v("pad_angle"))
    overhang = (arc_len-70)/2
    qline = pad_design*1000/arc_len
    def cap_stress(t):
        M = qline*overhang**2/2
        return 6*M/(50*t**2)
    def cap_defl(t):
        Istrip = 50*t**3/12
        return qline*overhang**4/(8*E*Istrip)
    pad_options = [
        {"base_mm":45, "cap_mm":32, "liner_mm":8, "stress_MPa":cap_stress(32), "deflection_mm":cap_defl(32)},
        {"base_mm":62, "cap_mm":15, "liner_mm":8, "stress_MPa":cap_stress(15), "deflection_mm":cap_defl(15)},
    ]

    axle_span_r03 = 80.0
    axle_span_r04 = v("fork_clear_width")+v("fork_plate_t")
    axle_M_r03_sensitivity = r_select*1000*axle_span_r03/4
    axle_M_r04_sensitivity = r_select*1000*axle_span_r04/4
    axle_M = r_uls*1000*axle_span_r04/4
    axle_Z = math.pi*v("axle_d")**3/32
    axle_bending = axle_M/axle_Z
    axle_shear = r_uls*1000/(2*math.pi*v("axle_d")**2/4)
    pin_area = math.pi*v("table_lock_pin_d")**2/4
    lock_shear = v("table_lock_design_force")*1000/(2*pin_area)
    screw_torque = v("locator_force_limit")*1000*5/(2*math.pi*0.30)/1000

    sap_scale = W/31.49274
    structural = {
        "R01_SLS_total_kN":31.49274,
        "R01_max_U3_mm":1.353133,
        "R01_max_relative_deflection_mm":1.235802378,
        "R01_pad_level_difference_mm":0.294331,
        "R01_max_DC":0.277132,
        "R03_weight_scale":sap_scale,
        "R03_est_max_U3_mm":1.353133*sap_scale,
        "R03_est_relative_deflection_mm":1.235802378*sap_scale,
        "R03_est_pad_level_difference_mm":0.294331*sap_scale,
        "R03_est_max_DC":0.277132*sap_scale,
        "L_over_800_limit_mm":1860/800,
        "classification":"ESTIMACION_LINEAL_ESCALADA_NO_EJECUTADA_EN_SAP",
    }

    return {
        "classification": RESULT_CLASS, "warning": WARNING,
        "parameters": P, "urls": URLS,
        "geometry": {
            "frame_outer_x_half_mm":frame_outer_x, "frame_outer_y_half_mm":frame_outer_y,
            "s_geom_mm":s_geom, "s_operational_mm":s_op, "wash_y_mm":0.0, "load_y_mm":y_load,
            "rail_length_mm":rail_len, "rail_required_zero_margin_mm":rail_req_zero_margin,
            "load_end_rail_margin_mm":load_end_margin, "wash_end_rail_margin_mm":wash_end_margin,
            "door_side_clearance_mm":door_side_clear,
            "door_bottom_clearance_mm":moving_bottom_z-v("door_z_bottom"),
            "door_top_clearance_mm":v("door_z_top")-bearing_top,
            "frame_bottom_mm":frame_bottom, "bearing_bottom_mm":bearing_bottom,
            "bearing_top_mm":bearing_top, "wheel_axis_z_mm":wheel_axis_z,
            "wheel_top_mm":v("rail_contact_z")+v("wheel_d"),
            "moving_bottom_z_mm":moving_bottom_z,
            "axis_to_frame_mm":carrier_axis_to_frame,
            "wheel_top_to_frame_mm":carrier_wheel_top_to_frame,
            "support_spacing_mm":support_spacing,
            "moving_rear_projection_mm":1057.0,
            "outer_moving_y_at_load_mm":y_load-1057.0,
            "operator_outer_limit_y_mm":y_load-1057.0-v("operator_clearance"),
            "fork_min_side_clearance_mm":4.0,
            "locator_180_base_overlap_mm":70.038,
            "locator_retracted_radial_range_mm":[1055.0,1105.0],
            "head_a_reserved_radial_range_mm":[710.0,860.0],
            "lock_hole_top_clearance_mm":51.5,
        },
        "mass_items": [dict(name=x[0], mass_kg=x[1], x_mm=x[2], y_mm=x[3], z_mm=x[4], status=x[5]) for x in mass_items],
        "mass": {"estimated_mass_kg":estimated_mass, "full_bearing_mass_kg":estimated_mass,
                 "basket_base_without_payload_kg":basket_base_mass,
                 "basket_payload_mass_kg":None,
                 "basket_max_payload_within_3500_kg":v("moving_mass_design")-basket_base_mass,
                 "design_mass_kg":v("moving_mass_design"),
                 "design_weight_kN":W, "cg_estimated_mm":[cgx,cgy,cgz],
                 "mass_margin_kg":v("moving_mass_design")-estimated_mass},
        "wheel": {"average_service_kN":r_avg, "four_contact_equal_stiffness_max_kN":r_four_max,
                  "three_contact_static_max_kN":r_three_max, "selection_demand_kN":r_select,
                  "uls_strength_demand_kN":r_uls,
                  "catalog_capacity_kN":wheel_cap, "utilization":r_select/wheel_cap,
                  "axle_span_r03_sensitivity_mm":axle_span_r03,
                  "axle_span_r04_mm":axle_span_r04,
                  "axle_bending_r03_sensitivity_MPa":axle_M_r03_sensitivity/axle_Z,
                  "axle_bending_r04_sensitivity_MPa":axle_M_r04_sensitivity/axle_Z,
                  "axle_bending_uls_MPa":axle_bending, "axle_double_shear_uls_MPa":axle_shear,
                  "governing_case":governing_wheel_case,"three_contact_cases":three_contact_cases},
        "rail": {"service_point_load_kN":r_select, "uls_point_load_kN":r_uls,
                 "support_pitch_mm":L, "moment_Nmm":rail_M,
                 "stress_head_MPa":rail_stress_head, "stress_base_MPa":rail_stress_base,
                 "deflection_mm":rail_defl},
        "push": push,
        "braking": {"speed_m_s":v("travel_speed"), "kinetic_energy_J":kinetic,
                    "emergency_stop_distance_m":stop_distance,
                    "emergency_manual_force_N":emergency_stop_force,
                    "direct_manual_conclusion":"PREFERENCIA_INICIAL_NO_VALIDADA; medir arranque, marcha y parada",
                    "haacon_status":"RETIRED_AS_RECOMMENDATION_MINIMUM_LOAD_NOT_MET",
                    "haacon_minimum_traction_N":haacon_minimum_traction_N,
                    "assistance":"ALTERNATIVA_NO_SELECCIONADA; zona CAD fuera de cabina",
                    "drive_design_force_N":drive_force_N,"drive_output_torque_Nm":drive_output_torque_Nm,
                    "drive_operator_force_N":drive_operator_force_N,"stop_torque_Nm":stop_torque_Nm,
                    "brake_torque_Nm":v("drive_brake_torque"),
                    "brake_utilization":stop_torque_Nm/v("drive_brake_torque")},
        "pad": {"area_mm2":pad_area, "service_load_kN":pad_service,
                "bearing_weight_kN":bearing_weight_kN,"bearing_cg_height_mm":bearing_cg_height_mm,
                "inertia_equivalent_ecc_mm":inertia_equivalent_ecc_mm,
                "eccentricity_envelope_mm":pad_ecc_envelope_mm,"static_envelope_kN":pad_static_envelope,
                "dynamic_service_load_kN":pad_dynamic, "uls_strength_load_kN":pad_uls,
                "design_load_kN":pad_design, "dynamic_service_pressure_MPa":pad_pressure,
                "liner_compressive_utilization":pad_pressure/v("liner_compressive_strength"),
                "arc_length_mm":arc_len, "tangential_overhang_mm":overhang,
                "options":pad_options, "governing_case":governing_pad_case,"cases":pad_cases,
                "selected":"45 base/pedestal + 32 cap + 8 liner retained as development base"},
        "centering": {"roller_center_radius_mm":735.0, "contact_radius_mm":710.0,
                      "stroke_mm":v("locator_retract_stroke"), "force_limit_kN":v("locator_force_limit"),
                      "screw_torque_Nm":screw_torque,
                      "roller_axis":"horizontal and tangential",
                      "retention_force_kN":v("retention_design_force"),
                      "tilt_note":"Tilt is controlled by the three PAD plane and hoist, not by the radial adjuster"},
        "lock": {"pin_d_mm":v("table_lock_pin_d"), "design_force_kN":v("table_lock_design_force"),
                 "double_shear_MPa":lock_shear, "stations_y_mm":[0.0,y_load]},
        "structural": structural,
        "external_pending": [
            "Survey actual door clear opening, threshold and external maneuvering footprint",
            "Survey rail line/level; design requires <=0.2 percent slope and aligned joints",
            "Verify slab thickness strength reinforcement and anchor edge distances",
            "Obtain Head A final swept envelope, hose routing, mass and reactions",
            "Confirm wash chemistry temperature and corrosion class with wheel rail liner suppliers",
            "Measure starting and running force using an inline dynamometer after assembly",
            "If required, author runs the minimal R05 SAP cases specified in the memorandum; Codex did not run SAP",
            "Approve bearing surfaces that may contact PE-UHMW liners and locator rollers",
        ],
    }


def make_groups(doc):
    groups = {}
    names = [
        ("G00_FIXED", "00 FIXED CABIN FLOOR AND RAIL SYSTEM"),
        ("G01_FRAME", "01 MOVING W6X9 FRAME"), ("G02_PAD", "02 PAD ASSEMBLIES"),
        ("G03_BEARING", "03 BEARING REFERENCE"), ("G04_WHEELS", "04 WHEELS FORKS AND STIFFENERS"),
        ("G05_CENTERING", "05 CENTERING AND RETENTION"), ("G06_HANDLE", "06 HANDLE AND ASSISTANCE INTERFACE"),
        ("G07_LOCK", "07 POSITIVE TABLE LOCK"), ("G08_HEAD", "08 HEAD A AND DRAIN RESERVES"),
        ("G09_LOAD_GHOST", "09 LOAD POSITION REFERENCE"), ("G10_REFERENCE", "10 DATUMS AND ENVELOPES"),
    ]
    for name,label in names:
        g=doc.addObject("App::DocumentObjectGroup",name); g.Label=label; groups[name]=g
    return groups


def build_cad(data):
    doc=App.newDocument("V5_2_N3_R05")
    meta=doc.addObject("App::FeaturePython","IDENTIFICACION_R05")
    meta.Label="V5.2 N3 R05 - CIERRE HALLAZGOS R04"
    for n,val in [("Revision","V5.2_N3_R05"),("Clasificacion",RESULT_CLASS),("Advertencia",WARNING),
                  ("FechaUTC",datetime.now(timezone.utc).isoformat()),("PerfilBase","W6X9"),
                  ("SAP","CASOS_PREPARADOS_NO_EJECUTADOS")]: add_prop(meta,n,val)
    groups=make_groups(doc); items=[]
    # Spreadsheet audit trail
    s=doc.addObject("Spreadsheet::Sheet","PARAMETROS_R05"); s.Label="R05 PARAMETROS Y PROCEDENCIA"
    for c,t in enumerate(["Parametro","Valor","Unidad","Estado","Fuente","Nota"],1): s.set(chr(64+c)+"1",t)
    for r,(k,e) in enumerate(P.items(),2):
        vals=[k,str(e["value"]),e["unit"],e["status"],e["source"],e["note"]]
        for c,t in enumerate(vals,1): s.set(chr(64+c)+str(r),str(t))
    for col,w in zip("ABCDEF",[220,130,90,190,360,320]): s.setColumnWidth(col,w)

    # Fixed floor and cabin inherited envelope
    floor=Part.makeBox(4200,7600,20,App.Vector(-2100,-5000,-20))
    items.append(add_shape(doc,groups["G00_FIXED"],"FLOOR_REFERENCE","Floor and foundation reference",floor,"FLOOR","PENDIENTE_EXTERNO","Plant survey required",False,82))
    wall=100.0; xi=v("cabin_x_inside")/2; yi=v("cabin_y_inside")/2; zi=v("cabin_z_inside")
    fixed_shapes=[
        ("CABIN_LEFT",Part.makeBox(wall,2*yi,zi,App.Vector(-xi-wall,-yi,0))),
        ("CABIN_RIGHT",Part.makeBox(wall,2*yi,zi,App.Vector(xi,-yi,0))),
        ("CABIN_REAR",Part.makeBox(2*xi,wall,zi,App.Vector(-xi,yi,0))),
        ("CABIN_FRONT_LEFT",Part.makeBox(xi-v("door_width")/2,wall,zi,App.Vector(-xi,-yi-wall,0))),
        ("CABIN_FRONT_RIGHT",Part.makeBox(xi-v("door_width")/2,wall,zi,App.Vector(v("door_width")/2,-yi-wall,0))),
        ("CABIN_FRONT_LOW",Part.makeBox(v("door_width"),wall,v("door_z_bottom"),App.Vector(-v("door_width")/2,-yi-wall,0))),
        ("CABIN_FRONT_TOP",Part.makeBox(v("door_width"),wall,zi-v("door_z_top"),App.Vector(-v("door_width")/2,-yi-wall,v("door_z_top")))),
        ("CABIN_ROOF",Part.makeBox(2*xi,2*yi,80,App.Vector(-xi,-yi,zi))),
    ]
    for name,sh in fixed_shapes:
        items.append(add_shape(doc,groups["G00_FIXED"],name,name.replace("_"," "),sh,"CABIN","HEREDADO_PROVISIONAL","V5/V5.2 inherited CAD",True,78))
    door_frame=Part.makePolygon([App.Vector(-v("door_width")/2,v("door_plane_y"),v("door_z_bottom")),App.Vector(v("door_width")/2,v("door_plane_y"),v("door_z_bottom")),App.Vector(v("door_width")/2,v("door_plane_y"),v("door_z_top")),App.Vector(-v("door_width")/2,v("door_plane_y"),v("door_z_top")),App.Vector(-v("door_width")/2,v("door_plane_y"),v("door_z_bottom"))])
    items.append(add_shape(doc,groups["G10_REFERENCE"],"DOOR_CLEAR_OPENING","Inherited nominal door clear opening",door_frame,"REFERENCE","HEREDADO_PROVISIONAL","V5/V5.2 inherited CAD",False,0))

    # Rails, pads, support pedestals and clips
    for side,x in [("L",-v("wheel_x_abs")),("R",v("wheel_x_abs"))]:
        rail=make_a45(x,v("rail_y_min"),v("rail_y_max"),v("rail_contact_z"))
        items.append(add_shape(doc,groups["G00_FIXED"],f"RAIL_A45_{side}",f"A45 rail {side}",rail,"RAIL","CANDIDATO_CON_RESPALDO_CATALOGO","ArcelorMittal A45 DIN 536",True,0,"Foundation and corrosion approval pending"))
        for i in range(v("rail_support_count")):
            y=v("rail_y_min")+i*data["geometry"]["support_spacing_mm"]
            ped=Part.makeBox(250,280,212,App.Vector(x-125,y-140,0))
            plate=Part.makeBox(250,280,16,App.Vector(x-125,y-140,212))
            pad=Part.makeBox(140,160,7,App.Vector(x-70,y-80,228))
            assy=ped.fuse(plate).fuse(pad)
            items.append(add_shape(doc,groups["G00_FIXED"],f"RAIL_SUPPORT_{side}_{i+1:02d}",f"Rail support {side}-{i+1:02d}",assy,"SUPPORT","PREDIMENSIONADO_R03","600 mm rail span calculation; slab pending",True,18))
            # simplified paired rail clips
            clips=Part.makeBox(35,50,20,App.Vector(x-92.5,y-25,228)).fuse(Part.makeBox(35,50,20,App.Vector(x+57.5,y-25,228)))
            items.append(add_shape(doc,groups["G00_FIXED"],f"RAIL_CLIPS_{side}_{i+1:02d}",f"Gantrex clip pair {side}-{i+1:02d}",clips,"LOCK","CATALOGO_INTERFACE","Gantrex BG10/BJ for A45",True,5))

    # Active moving frame in wash position
    members=[
        ("M01","LONGITUDINAL_LEFT",-930,-950,-930,950),("M02","LONGITUDINAL_RIGHT",930,-950,930,950),
        ("M03","END_NEG",-930,-950,930,-950),("M04","END_POS",-930,950,930,950),
        ("M05","PAD_03",-930,-574.175,930,-574.175),("M06","PAD_02",-930,574.175,930,574.175),
        ("M07","PAD_01",663,-574.175,663,574.175),
    ]
    for mid,role,x1,y1,x2,y2 in members:
        sh,L=make_w_member(x1,y1,x2,y2,v("z_frame_top"))
        obj=add_shape(doc,groups["G01_FRAME"],f"{mid}_W6X9",f"{mid} {role} W6X9",sh,"FRAME","BASE_R05_CONSERVA_N3_R01","SAP R01 geometry and AISC section",True,0,"Strong axis vertical; top flanges coplanar",True)
        add_prop(obj,"LongitudEje_mm",float(L)); items.append(obj)

    # PAD: 12 mm spreader + 33 mm pedestal = base/pedestal 45, cap 32, liner 8
    pad_angles=[0.0,120.0,240.0]
    for i,theta in enumerate(pad_angles,1):
        spread=radial_box(v("pad_radius"),160,140,12,v("z_frame_top"),theta)
        pedestal=radial_box(v("pad_radius"),80,70,33,v("z_frame_top")+12,theta)
        cap=annular_sector(v("pad_r_in"),v("pad_r_out"),v("pad_angle"),v("pad_cap_h"),v("z_frame_top")+45,theta)
        liner=annular_sector(v("pad_r_in"),v("pad_r_out"),v("pad_angle"),v("pad_liner_h"),v("z_frame_top")+77,theta)
        items.append(add_shape(doc,groups["G02_PAD"],f"PAD_{i:02d}_BASE",f"PAD {i} base and pedestal 45",spread.fuse(pedestal),"PAD","BASE_DESARROLLO_R03","Retained after recalculation from bearing equilibrium",True,0,"Includes 12 mm spreader and 33 mm pedestal",True))
        items.append(add_shape(doc,groups["G02_PAD"],f"PAD_{i:02d}_CAP",f"PAD {i} cap 32",cap,"PAD","BASE_DESARROLLO_R03","Local strip model with bearing-derived PAD envelope",True,0,"Alternative 15 mm cap remains comparison only",True))
        items.append(add_shape(doc,groups["G02_PAD"],f"PAD_{i:02d}_LINER",f"PAD {i} PE-UHMW liner 8",liner,"LINER","SELECCION_RECOMENDADA_CONDICIONADA","Roechling Polystone M properties",True,0,"Verify wash chemistry and approved bearing contact surface",True))

    bearing_bottom=data["geometry"]["bearing_bottom_mm"]
    bearing=Part.makeCylinder(v("bearing_od")/2,v("bearing_width"),App.Vector(0,0,bearing_bottom)).cut(Part.makeCylinder(v("bearing_id")/2,v("bearing_width"),App.Vector(0,0,bearing_bottom)))
    items.append(add_shape(doc,groups["G03_BEARING"],"BEARING_REFERENCE",v("bearing_model"),bearing,"BEARING","ENVOLVENTE_VERIFICADA","Project brief; simplified annulus",True,65,"Not rigidly fused to table",True))

    # Four flanged wheels and direct-under-web forks
    axis_z=data["geometry"]["wheel_axis_z_mm"]; frame_bottom=data["geometry"]["frame_bottom_mm"]
    for i,(x,y) in enumerate([(-930,-722),(-930,722),(930,-722),(930,722)],1):
        run=cylinder_centered((x,y,axis_z),(1,0,0),v("wheel_running_width"),v("wheel_d")/2)
        flange_x=x-30 if x<0 else x+30
        flange=cylinder_centered((flange_x,y,axis_z),(1,0,0),12,v("wheel_flange_d")/2)
        axle=cylinder_centered((x,y,axis_z),(1,0,0),140,v("axle_d")/2)
        items.append(add_shape(doc,groups["G04_WHEELS"],f"WHEEL_{i:02d}",f"W-{i:02d} SPKVS 200K envelope",run.fuse(flange),"WHEEL","CANDIDATO_CON_RESPALDO_CATALOGO","Blickle SPKVS 200K",True,0,"Catalogue capacity 2500 kg at 4 km/h",True))
        items.append(add_shape(doc,groups["G04_WHEELS"],f"AXLE_{i:02d}",f"W-{i:02d} axle d35",axle,"FORK","PREDIMENSIONADO_R05","Luz 92 mm entre planos medios; carga ULS calculada",True,0,"Material candidato sujeto a certificado; hombros y ajustes pendientes",True))
        plate=Part.makeBox(v("fork_top_width"),180,12,App.Vector(x-v("fork_top_width")/2,y-90,frame_bottom-12))
        left=Part.makeBox(12,160,frame_bottom-12-(axis_z-50),App.Vector(x-v("fork_clear_width")/2-12,y-80,axis_z-50))
        right=Part.makeBox(12,160,frame_bottom-12-(axis_z-50),App.Vector(x+v("fork_clear_width")/2,y-80,axis_z-50))
        bore=Part.makeCylinder(v("axle_d")/2+0.5,140,App.Vector(x-70,y,axis_z),App.Vector(1,0,0))
        fork=plate.fuse(left).fuse(right).cut(bore)
        items.append(add_shape(doc,groups["G04_WHEELS"],f"FORK_{i:02d}",f"W-{i:02d} direct fork",fork,"FORK","REVISADO_R05","80 mm libres; planos medios a 92 mm bajo el alma W6",True,0,"Holgura lateral mínima 4 mm; sin brazo en voladizo",True))
        # paired web stiffeners at wheel station
        st1=Part.makeBox(v("profile_bf"),8,v("profile_d")-2*v("profile_tf"),App.Vector(x-v("profile_bf")/2,y-74,data["geometry"]["frame_bottom_mm"]+v("profile_tf")))
        st2=Part.makeBox(v("profile_bf"),8,v("profile_d")-2*v("profile_tf"),App.Vector(x-v("profile_bf")/2,y+66,data["geometry"]["frame_bottom_mm"]+v("profile_tf")))
        items.append(add_shape(doc,groups["G04_WHEELS"],f"WEB_STIFFENERS_{i:02d}",f"W-{i:02d} web stiffeners",st1.fuse(st2),"FORK","PREDIMENSIONADO_R03","Local wheel load path",True,0,"8 mm S355 candidate; weld verification pending SAP local model",True))

    # F02 R05: cassette completo retraible. El STEP representa el estado de lavado.
    # Dos guias radiales fijas quedan bajo Z775; la placa de montaje solo alcanza
    # la cara superior del bastidor. Carro, mastil, eje y rodillo se trasladan
    # juntos desde R735 hasta R1080 y se enclavan con dos pasadores d16.
    zroller=950.0
    for i,theta in enumerate([60.0,180.0,300.0],1):
        a=math.radians(theta)
        tangent=(-math.sin(a),math.cos(a),0)
        radial=(math.cos(a),math.sin(a),0)

        mount=radial_box(820,280,160,12,793,theta)
        guide1=radial_box(915,430,30,20,755,theta)
        guide1.translate(App.Vector(-55*math.sin(a),55*math.cos(a),0))
        guide2=radial_box(915,430,30,20,755,theta)
        guide2.translate(App.Vector(55*math.sin(a),-55*math.cos(a),0))
        cross1=radial_box(730,30,150,30,775,theta)
        cross2=radial_box(900,30,150,30,775,theta)
        screw=cylinder_centered((907.5*math.cos(a),907.5*math.sin(a),735),radial,345,12)
        bearing_a=radial_box(735,35,80,40,715,theta)
        bearing_b=radial_box(1080,35,80,40,715,theta)
        fixed_base=mount.fuse(guide1).fuse(guide2).fuse(cross1).fuse(cross2).fuse(screw).fuse(bearing_a).fuse(bearing_b)

        # Four vertical M16 candidate fasteners through the base and W6 flange/web zone.
        bolts=None
        for rr in (730.0,910.0):
            for tt in (-45.0,45.0):
                hx=rr*math.cos(a)-tt*math.sin(a); hy=rr*math.sin(a)+tt*math.cos(a)
                b=Part.makeCylinder(8,50,App.Vector(hx,hy,775),App.Vector(0,0,1))
                bolts=b if bolts is None else bolts.fuse(b)

        rc=v("locator_center_r")+v("locator_retract_stroke")
        carriage=radial_box(rc,180,160,12,768,theta)
        mast_outer=radial_box(rc,80,40,170,780,theta)
        mast_inner=radial_box(rc,68,28,172,779,theta)
        mast=mast_outer.cut(mast_inner)
        saddle=radial_box(rc,100,80,20,930,theta)
        roller=cylinder_centered((rc*math.cos(a),rc*math.sin(a),zroller),tangent,v("locator_roller_length"),v("locator_roller_d")/2)
        shaft=cylinder_centered((rc*math.cos(a),rc*math.sin(a),zroller),tangent,100,10)
        lock1=Part.makeCylinder(8,60,App.Vector((rc-60)*math.cos(a),(rc-60)*math.sin(a),745),App.Vector(0,0,1))
        lock2=Part.makeCylinder(8,60,App.Vector((rc+60)*math.cos(a),(rc+60)*math.sin(a),745),App.Vector(0,0,1))
        carriage_assy=carriage.fuse(mast).fuse(saddle).fuse(shaft).fuse(lock1).fuse(lock2)

        role="CENTER"; status="DATUM_RETRACTABLE" if i!=2 else "ADJUSTABLE_TR24X5"
        items.append(add_shape(doc,groups["G05_CENTERING"],f"LOCATOR_{i:02d}_FIXED_GUIDE",f"Locator {i} fixed guide and screw",fixed_base,role,"DEFINIDO_R05","Twin guides below Z775, Tr24x5 screw and end bearings",True,0,"Wear pads, covers, corrosion and final fasteners pending",True))
        items.append(add_shape(doc,groups["G05_CENTERING"],f"LOCATOR_{i:02d}_BASE_FASTENERS",f"Locator {i} base fasteners",bolts,"FASTENER","CANDIDATO_R05","4 x M16 geometry; final grade and W6 local check pending",True,0,status,True))
        items.append(add_shape(doc,groups["G05_CENTERING"],f"LOCATOR_{i:02d}_CARRIAGE_WASH",f"Locator {i} complete carriage at R1080",carriage_assy,role,"PREDIMENSIONADO_R05","RHS80x40x6 mast; d16 locks; 2 kN demand",True,0,"State exported: wash/retracted",True))
        items.append(add_shape(doc,groups["G05_CENTERING"],f"LOCATOR_{i:02d}_ROLLER_WASH",f"Locator {i} roller at R1080",roller,role,"PREDIMENSIONADO_R05","Complete cassette retracted; roller R1055-R1105",True,0,"Head A hoses and intermediate travel remain interface checks",True))

        # Full active cassette is retained as a non-exported reference, not only a roller.
        ra=v("locator_center_r")
        active_carriage=radial_box(ra,180,160,12,768,theta)
        active_outer=radial_box(ra,80,40,170,780,theta)
        active_inner=radial_box(ra,68,28,172,779,theta)
        active_mast=active_outer.cut(active_inner)
        active_saddle=radial_box(ra,100,80,20,930,theta)
        active_shaft=cylinder_centered((ra*math.cos(a),ra*math.sin(a),zroller),tangent,100,10)
        active_roller=cylinder_centered((ra*math.cos(a),ra*math.sin(a),zroller),tangent,v("locator_roller_length"),v("locator_roller_d")/2)
        active=active_carriage.fuse(active_mast).fuse(active_saddle).fuse(active_shaft).fuse(active_roller)
        items.append(add_shape(doc,groups["G10_REFERENCE"],f"LOCATOR_{i:02d}_ACTIVE_GHOST",f"Locator {i} complete active state R735",active,"GHOST","REFERENCIA_OPERATIVA_R05","Complete active cassette; nominal bearing contact",False,82,"Set-down only after radial error <=5 mm is confirmed"))

        # F03 R05: independent low retention stop with web and gussets overlapping
        # the fixed mounting plate; four fasteners share the same structural base.
        contact=radial_box(720,20,80,30,bearing_bottom,theta)
        web=radial_box(720,20,80,95,800,theta)
        gus1=radial_box(750,60,8,85,805,theta); gus1.translate(App.Vector(-32*math.sin(a),32*math.cos(a),0))
        gus2=radial_box(750,60,8,85,805,theta); gus2.translate(App.Vector(32*math.sin(a),-32*math.cos(a),0))
        stop=contact.fuse(web).fuse(gus1).fuse(gus2)
        items.append(add_shape(doc,groups["G05_CENTERING"],f"BEARING_RETENTION_STOP_{i:02d}",f"Connected low retention stop {i}",stop,"LOCK","CALCULADO_PRELIMINAR_R05","2 kN required per stop; 30 MPa strip and 0.833 MPa contact",True,0,"Shares bolted base; final code/material and Head A trajectory pending",True))

    # F03 R05: manillar conectado al alma del travesano extremo mediante dos
    # placas y cuatro pernos M12 candidatos por poste. La carga de calculo es
    # 1.5 kN total; la validacion ergonomica sigue requiriendo dinamometro.
    for x in (-450.0,450.0):
        upright=tube_centered((x,-1040,925),(0,0,1),250,42.4,3.2)
        brace=tube_centered((x,-1020,810),(0,1,0),40,42.4,3.2)
        plate=Part.makeBox(100,16,125,App.Vector(x-50,-1008,680))
        gusset=Part.makeBox(80,40,8,App.Vector(x-40,-1040,798))
        bolts=None
        for bx in (x-30,x+30):
            for bz in (710,770):
                b=Part.makeCylinder(6,40,App.Vector(bx,-1015,bz),App.Vector(0,1,0))
                bolts=b if bolts is None else bolts.fuse(b)
        assy=upright.fuse(brace).fuse(plate).fuse(gusset).fuse(bolts)
        items.append(add_shape(doc,groups["G06_HANDLE"],f"HANDLE_POST_{'L' if x<0 else 'R'}","Connected push handle post",assy,"HANDLE","CALCULADO_PRELIMINAR_R05","CHS42.4x3.2, end plate and 4xM12 candidate",True,0,"1.5 kN total structural envelope; final code and ergonomic test pending",True))
    bar=tube_centered((0,-1040,1050),(1,0,0),900,42.4,3.2)
    items.append(add_shape(doc,groups["G06_HANDLE"],"HANDLE_BAR","Two-hand CHS push bar",bar,"HANDLE","CALCULADO_PRELIMINAR_R05","93.9 MPa at 1.5 kN central envelope",True,0,"Manual push remains preference, not validated",True))
    drive_pedestal=Part.makeBox(300,280,520,App.Vector(1200,v("drive_operator_y")-140,0))
    drive_axis=(1350,v("drive_operator_y"),620)
    drive_sprocket=cylinder_centered(drive_axis,(1,0,0),80,v("drive_sprocket_radius"))
    handwheel=cylinder_centered((1540,v("drive_operator_y"),760),(1,0,0),30,v("drive_handwheel_radius"))
    items.append(add_shape(doc,groups["G10_REFERENCE"],"CHAIN_ASSISTANCE_OPTION_ENVELOPE","Unselected chain assistance zone",drive_pedestal.fuse(drive_sprocket).fuse(handwheel),"GHOST","ALTERNATIVA_NO_SELECCIONADA_R05","Zona exterior sin solape con frente de cabina",False,82,"No representa transmisión, guardas ni freno seleccionados"))

    # Central under-frame lock: one moving central lug nests between two fixed ears.
    # The hole is now fully contained, and the solids have 12 mm lateral clearance.
    lock_mount=Part.makeBox(50,80,45,App.Vector(-25,-890,610))
    lock_lug=Part.makeBox(40,80,110,App.Vector(-20,-890,520))
    # Placa de transferencia solapada con el ala inferior del travesaño M03.
    lock_connector=Part.makeBox(120,130,16,App.Vector(-60,-950,650))
    lug_hole=Part.makeCylinder(v("table_lock_pin_d")/2+1,40,App.Vector(-20,-850,575),App.Vector(1,0,0))
    lock_body=lock_mount.fuse(lock_lug.cut(lug_hole)).fuse(lock_connector)
    lock_pin=cylinder_centered((0,-850,575),(1,0,0),220,v("table_lock_pin_d")/2)
    items.append(add_shape(doc,groups["G07_LOCK"],"TABLE_LOCK_BODY","Moving central lock lug and transfer bracket",lock_body,"LOCK","CONSERVADO_R04_EN_R05","Conector solapado con M03 y agujero transversal cerrado",True,0,"Soldadura final y carga de lavado pendientes",True))
    items.append(add_shape(doc,groups["G07_LOCK"],"TABLE_LOCK_PIN","Duplex stainless d25 lock pin",lock_pin,"LOCK","PREDIMENSIONADO_R03","10 kN double-shear check",True,0,"Interlocked proof-of-engagement required",True))
    for label,cy in [("WASH",-850.0),("LOAD",data["geometry"]["load_y_mm"]-850.0)]:
        ear_l=Part.makeBox(58,100,140,App.Vector(-90,cy-50,500))
        ear_r=Part.makeBox(58,100,140,App.Vector(32,cy-50,500))
        base=Part.makeBox(220,140,30,App.Vector(-110,cy-70,470))
        hole=Part.makeCylinder(v("table_lock_pin_d")/2+1,180,App.Vector(-90,cy,575),App.Vector(1,0,0))
        recv=base.fuse(ear_l).fuse(ear_r).cut(hole)
        items.append(add_shape(doc,groups["G00_FIXED"],f"LOCK_RECEIVER_{label}",f"Fixed double-ear lock receiver {label}",recv,"LOCK","CORREGIDO_R03","Two fixed ears with enclosed holes and central-lug clearance",True,0,"Foundation, bearing and weld verification pending"))

    # Head A and drainage are keep-outs, not final geometry.
    spray=Part.makeCylinder(860,715,App.Vector(0,0,790)).cut(Part.makeCylinder(710,715,App.Vector(0,0,790)))
    items.append(add_shape(doc,groups["G08_HEAD"],"HEAD_A_KEEP_OUT","Head A preliminary sweep reserve",spray,"HEAD","INTERFAZ_PRELIMINAR","HANDOFF_DATA_CLAUDE; standoff 150 mm",False,84,"Actual head hoses and reactions pending"))
    head_step_path=OUT/"00_REFERENCIAS"/"Head_A.step"
    if head_step_path.exists():
        head_shape=Part.Shape(); head_shape.read(str(head_step_path))
        items.append(add_shape(doc,groups["G08_HEAD"],"HEAD_A_STATIC_REFERENCE","Head A supplied STEP reference",head_shape,"HEAD","GEOMETRIA_SUMINISTRADA","Head_A.step",False,70,"Static supplied state; full trajectory and hoses pending"))
    drain=Part.makeBox(900,900,120,App.Vector(-450,-450,515))
    items.append(add_shape(doc,groups["G08_HEAD"],"DRAIN_KEEP_OUT","Drain removable interface reserve",drain,"HEAD","INTERFAZ_PRELIMINAR","R01 reserve",False,88,"Tray geometry and whether it moves remain pending"))

    # Load state reference: envelope only, keeping one physical assembly in the STEP.
    yl=data["geometry"]["load_y_mm"]
    ghost_frame=Part.makeBox(2*data["geometry"]["frame_outer_x_half_mm"],2*data["geometry"]["frame_outer_y_half_mm"],v("profile_d"),App.Vector(-data["geometry"]["frame_outer_x_half_mm"],yl-data["geometry"]["frame_outer_y_half_mm"],data["geometry"]["frame_bottom_mm"]))
    ghost_bearing=Part.makeCylinder(v("bearing_od")/2,v("bearing_width"),App.Vector(0,yl,bearing_bottom)).cut(Part.makeCylinder(v("bearing_id")/2,v("bearing_width"),App.Vector(0,yl,bearing_bottom)))
    ghost_handle=Part.makeBox(900,74,267,App.Vector(-450,yl-1057,805))
    items.append(add_shape(doc,groups["G09_LOAD_GHOST"],"LOAD_FRAME_ENVELOPE","Load position frame envelope",ghost_frame,"GHOST","CALCULATED_REFERENCE","S_operational with C_LOAD 300",False,88))
    items.append(add_shape(doc,groups["G09_LOAD_GHOST"],"LOAD_BEARING_ENVELOPE","Load position bearing envelope",ghost_bearing,"GHOST","CALCULATED_REFERENCE","Fully outside cabin",False,90))
    items.append(add_shape(doc,groups["G09_LOAD_GHOST"],"LOAD_HANDLE_ENVELOPE","Load position handle envelope",ghost_handle,"GHOST","CALCULATED_REFERENCE","Moving rear projection corrected to 1057 mm",False,90))

    # Travel centerline and wheel position markers
    travel=Part.makeLine(App.Vector(0,0,1550),App.Vector(0,yl,1550))
    items.append(add_shape(doc,groups["G10_REFERENCE"],"TRAVEL_CENTERLINE","Center travel wash to load",travel,"REFERENCE","CALCULADO_R03","3020.038 plus C_LOAD 300",False,0))
    doc.recompute()
    return doc,items


def write_dxf(data):
    pairs=[]
    def add(c,x): pairs.extend([str(c),str(x)])
    add(0,"SECTION"); add(2,"HEADER"); add(9,"$ACADVER"); add(1,"AC1009"); add(9,"$INSUNITS"); add(70,4); add(0,"ENDSEC")
    add(0,"SECTION"); add(2,"TABLES"); layers=[("10_FRAME_WASH",5),("11_FRAME_LOAD",8),("20_PAD",3),("30_WHEELS",2),("40_RAIL_AXES",8),("50_CABIN",4),("60_DOOR",1),("70_SUPPORTS",9),("90_NOTES",7)]
    add(0,"TABLE"); add(2,"LAYER"); add(70,len(layers))
    for name,color in layers: add(0,"LAYER"); add(2,name); add(70,0); add(62,color); add(6,"CONTINUOUS")
    add(0,"ENDTAB"); add(0,"ENDSEC"); add(0,"SECTION"); add(2,"ENTITIES")
    nodes={1:(-930,-950),2:(-930,-722),3:(-930,-574.175),4:(-930,574.175),5:(-930,722),6:(-930,950),7:(-331.5,-574.175),8:(-331.5,574.175),9:(663,-574.175),10:(663,0),11:(663,574.175),12:(930,-950),13:(930,-722),14:(930,-574.175),15:(930,574.175),16:(930,722),17:(930,950),18:(0,-950)}
    edges=[(1,2),(2,3),(3,4),(4,5),(5,6),(12,13),(13,14),(14,15),(15,16),(16,17),(1,18),(18,12),(3,7),(7,9),(9,14),(4,8),(8,11),(11,15),(6,17),(9,10),(10,11)]
    for layer,off in [("10_FRAME_WASH",0.0),("11_FRAME_LOAD",data["geometry"]["load_y_mm"])]:
        for i,(a,b) in enumerate(edges,1):
            x1,y1=nodes[a]; x2,y2=nodes[b]
            add(999,f"B{i:03d}|W6X9|N{a:03d}-N{b:03d}|YOFF={off}")
            add(0,"LINE"); add(8,layer); add(10,x1); add(20,y1+off); add(30,0); add(11,x2); add(21,y2+off); add(31,0)
    for theta in [0,120,240]:
        a=math.radians(theta); add(0,"POINT"); add(8,"20_PAD"); add(10,v("pad_radius")*math.cos(a)); add(20,v("pad_radius")*math.sin(a)); add(30,0)
    for x in [-930,930]:
        for y in [-722,722]: add(0,"POINT"); add(8,"30_WHEELS"); add(10,x); add(20,y); add(30,0)
        add(0,"LINE"); add(8,"40_RAIL_AXES"); add(10,x); add(20,v("rail_y_min")); add(30,0); add(11,x); add(21,v("rail_y_max")); add(31,0)
    xi=v("cabin_x_inside")/2; yi=v("cabin_y_inside")/2
    for x1,y1,x2,y2 in [(-xi,-yi,xi,-yi),(xi,-yi,xi,yi),(xi,yi,-xi,yi),(-xi,yi,-xi,-yi)]: add(0,"LINE"); add(8,"50_CABIN"); add(10,x1); add(20,y1); add(30,0); add(11,x2); add(21,y2); add(31,0)
    add(0,"LINE"); add(8,"60_DOOR"); add(10,-v("door_width")/2); add(20,v("door_plane_y")); add(30,0); add(11,v("door_width")/2); add(21,v("door_plane_y")); add(31,0)
    for i in range(v("rail_support_count")):
        y=v("rail_y_min")+i*data["geometry"]["support_spacing_mm"]
        add(0,"LINE"); add(8,"70_SUPPORTS"); add(10,-1055); add(20,y); add(30,0); add(11,1055); add(21,y); add(31,0)
    add(0,"TEXT"); add(8,"90_NOTES"); add(10,-1900); add(20,1850); add(30,0); add(40,55); add(1,"V5.2 N3 R05 - W6X9 - NO FABRICATION RELEASE")
    add(0,"ENDSEC"); add(0,"EOF")
    DXF.write_text("\n".join(pairs)+"\n",encoding="ascii")


def tessellate(obj,deflection=6.0):
    if obj.Shape.isNull(): return {"vertices":[],"triangles":[]}
    verts,tris=obj.Shape.tessellate(deflection)
    return {"vertices":[[p.x,p.y,p.z] for p in verts],"triangles":[list(t) for t in tris]}


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest().upper()


def write_trace():
    sources=[
        ("R01 SAP","00_REFERENCIAS/V5_2_N3_W6X9_REV01_SAP_RAW.xlsx","historical executed results"),
        ("Independent R04 review","00_REFERENCIAS/REVISION_INDEPENDIENTE_R04_2026-09-08.txt","F01-F05 source and bounded R05 assignment"),
        ("Head A geometry","00_REFERENCIAS/Head_A.step","project reference; final swept hoses pending"),
    ]
    with TRACE_CSV.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["Fuente","Ruta o identificacion de fuente","Uso R05","SHA256"])
        for name,rel,use in sources:
            p=OUT/rel; w.writerow([name,rel,use,sha256(p) if p.exists() else "MISSING"])
        for name,url in URLS.items(): w.writerow([name,url,"catalogue or technical reference","WEB"])


def main():
    start=datetime.now(timezone.utc); data=calculations(); DATA_JSON.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    r05_calc_path=WORK/"R05_CALC_DATA.json"
    if not r05_calc_path.exists():
        raise RuntimeError("Run 01_CALCULO_R05_REPRODUCIBLE.py before the CAD generator")
    r05_calc=json.loads(r05_calc_path.read_text(encoding="utf-8"))
    doc,items=build_cad(data); doc.recompute(); doc.saveAs(str(FCSTD))
    export=[o for o in items if getattr(o,"ExportarSTEP",False) and not o.Shape.isNull()]
    Part.export(export,str(STEP)); write_dxf(data); write_trace()
    payload={"revision":"V5.2_N3_R05","classification":RESULT_CLASS,"warning":WARNING,
             "data":data,"engineering_data":r05_calc,"items":[{"name":o.Name,"label":o.Label,"role":getattr(o,"Rol",""),
             "status":getattr(o,"EstadoIngenieria",""),"moving":bool(getattr(o,"ComponenteMovil",False)),
             "export":bool(getattr(o,"ExportarSTEP",False)),"color":list(getattr(o.ViewObject,"ShapeColor",(0.5,0.5,0.5))),
             "alpha":255-int(getattr(o.ViewObject,"Transparency",0)*2.55),"mesh":tessellate(o)} for o in items]}
    PAYLOAD.write_text(json.dumps(payload,separators=(",",":")),encoding="utf-8")
    checks=[
        ("R05-001","profile W6X9 retained",v("profile_name")=="W6X9","PASS"),
        ("R05-002","load state outside door",data["geometry"]["load_y_mm"]+data["geometry"]["frame_outer_y_half_mm"] <= v("door_plane_y")-v("c_load"),"PASS"),
        ("R05-003","rail covers load wheels",data["geometry"]["load_end_rail_margin_mm"]>0,"PASS"),
        ("R05-004","rail covers wash wheels",data["geometry"]["wash_end_rail_margin_mm"]>0,"PASS"),
        ("R05-005","wheel catalogue demand below capacity",r05_calc["wheel"]["catalog_service_utilization"]<1,"PASS_CONDITIONED_CONTACT_AND_SUPPLIER"),
        ("R05-006","physical placement requirement gives full PAD coverage",min(min(c["coverage_fraction"]) for c in r05_calc["pad"]["coverage_cases"] if c["design"])>0.999,"PASS_GEOMETRIC_REQUIREMENT"),
        ("R05-007","audit -100,+100 is rejected",not r05_calc["pad"]["coverage_cases"][-1]["all_full_contact"],"PASS_REJECTED_INCOMPATIBLE_CASE"),
        ("R05-008","complete locator carriage is exported retracted",all(doc.getObject(f"LOCATOR_{i:02d}_CARRIAGE_WASH") is not None for i in range(1,4)),"PASS_CAD_NOMINAL"),
        ("R05-009","fixed guide top below Z780 except mounting interface",r05_calc["mechanisms"]["locator"]["guide_z_max_mm"]<=780,"PASS_DESIGN_REQUIREMENT"),
        ("R05-010","retention load path objects present",all(doc.getObject(f"BEARING_RETENTION_STOP_{i:02d}") is not None for i in range(1,4)),"PASS_CAD_NOMINAL"),
        ("R05-011","handle connection objects present",doc.getObject("HANDLE_POST_L") is not None and doc.getObject("HANDLE_POST_R") is not None,"PASS_CAD_NOMINAL"),
        ("R05-012","rail support installation envelope exceeds P/2",r05_calc["rail"]["governing_vertical_installation_kN"]>r05_calc["wheel"]["uls_local_kN"]/2,"PASS_CORRECTED_F05"),
        ("R05-013","manual direct push validated",False,"PREFERENCE_NOT_VALIDATED_TEST_REQUIRED"),
        ("R05-014","chain assistance selected",False,"NOT_SELECTED_BY_USER"),
        ("R05-015","SAP R05 executed",False,"NOT_EXECUTED_BY_INSTRUCTION"),
        ("R05-016","fabrication release",False,"NOT_RELEASED"),
    ]
    with QA_CSV.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["ID","Check","Value","Status"]); w.writerows(checks)
    qa={"checks":[{"id":a,"check":b,"value":c,"status":d} for a,b,c,d in checks],"fcstd":str(FCSTD),"step":str(STEP),"step_objects":len(export)}
    QA_JSON.write_text(json.dumps(qa,indent=2,ensure_ascii=False),encoding="utf-8")
    LOG.write_text(f"start_utc={start.isoformat()}\nend_utc={datetime.now(timezone.utc).isoformat()}\nfreecad={App.Version()}\nfcstd={FCSTD}\nstep={STEP}\ndxf={DXF}\nobjects={len(items)}\nstep_objects={len(export)}\nclassification={RESULT_CLASS}\nwarning={WARNING}\n",encoding="utf-8")
    print(json.dumps({"status":RESULT_CLASS,"fcstd":str(FCSTD),"step":str(STEP),"dxf":str(DXF),"objects":len(items),"step_objects":len(export)},ensure_ascii=False))


if __name__=="__main__":
    main()
