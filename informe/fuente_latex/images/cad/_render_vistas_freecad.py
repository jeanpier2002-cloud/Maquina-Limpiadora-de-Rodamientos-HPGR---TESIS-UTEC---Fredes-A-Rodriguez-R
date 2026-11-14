# Exporta vistas de la COPIA k2m573_copia.FCStd (R06 + K2-M v5.7.3). No guarda el documento.
import FreeCAD as App, FreeCADGui as Gui, os, traceback
out = r"C:/Users/enriq/AppData/Local/Temp/claude/C--Users-enriq-Downloads-PRISM/09310999-7eef-4036-beb1-2cdc6d720a50/scratchpad/cad"
log = open(os.path.join(out, "render2_log.txt"), "w")

C = {"naranja": (0.95, 0.55, 0.10), "amarillo": (1.00, 0.85, 0.10), "negro": (0.12, 0.12, 0.12),
     "verde": (0.20, 0.70, 0.30), "plata": (0.80, 0.80, 0.85), "rojo": (0.80, 0.15, 0.15),
     "azul": (0.20, 0.35, 0.65), "gris": (0.75, 0.75, 0.78), "gris_osc": (0.35, 0.35, 0.38),
     "celeste": (0.30, 0.70, 0.95), "oliva": (0.45, 0.55, 0.20), "beige": (0.85, 0.82, 0.72)}


def miembros(doc, g):
    g = doc.getObject(g)
    s, pila = set(), [g] if g else []
    while pila:
        x = pila.pop()
        for m in getattr(x, "Group", []) or []:
            s.add(m.Name)
            if hasattr(m, "Group"):
                pila.append(m)
    return s


def pintar(o, color, transp=0):
    vo = o.ViewObject
    try:
        vo.ShapeColor = color
    except Exception:
        try:
            m = App.Material(); m.DiffuseColor = color; vo.ShapeAppearance = [m]
        except Exception:
            pass
    try:
        vo.Transparency = int(transp)
    except Exception:
        pass


def color_k2m(n):
    if "RODILLO" in n and "PASADOR" not in n:
        return "negro"
    for k in ("PERNO", "TUERCA", "ARANDELA", "PASADOR", "EJE_PIVOTE", "CASQUILLO", "RETEN_"):
        if k in n:
            return "plata"
    for k in ("RESORTE", "CARTUCHO", "VARILLA", "GATILLO", "LEVA", "COLLAR_DISPARO", "LIMITADOR", "TOPE_FIN"):
        if k in n:
            return "verde"
    for k in ("BRAZO", "HORQUILLA"):
        if k in n:
            return "amarillo"
    for k in ("TOPE_RETENCION", "RECEPTOR_PASADOR", "SOPORTE_RETENCION"):
        if k in n:
            return "rojo"
    return "naranja"


ASP = ("TUBO", "CODO", "VALVULA", "UNION_ROTATIVA", "COPLA", "NIPLE", "PURGA", "BOQUILLA", "LANZA", "ROTOR",
       "CUBO", "PIE_", "RAMAL", "MANGUERA", "FLEXIBLE", "REDUCCION", "PORTABOQUILLA", "RACOR", "CADENA",
       "MANETA", "CARRO_LANZA", "MASTIL", "HUSILLO", "EMBOLO", "OREJETA", "POLEA", "RESALTE", "DEFLECTOR",
       "DISCO_EST", "TAPA_LANZA", "ABRAZADERA", "BRAZO_SERVICIO", "PLACA_BLOQUEO", "BARRA_RETENCION", "UNERA")


def clasificar(o, cab, sup, guard, sop_comp, accion, drenaje, rieles):
    n = o.Name
    if n in sup or n in guard or n.endswith("_ACTIVO") or n in ("MANETA_V_AIS_BARRIDO", "FLOOR_REFERENCE"):
        return None
    if n in cab:
        return "cabina"
    if n.startswith("R061_K2M_"):
        return "k2m"
    if n == "CTX_BEARING_REFERENCE":
        return "rodamiento"
    if n.startswith("CTX_") and "W6X9" in n:
        return "mesa"
    if n.startswith(("CTX_PAD", "CTX_WEB")):
        return "pad"
    if n.startswith(("CTX_WHEEL", "CTX_AXLE", "CTX_FORK", "CTX_HANDLE")) or n in rieles:
        return "rodadura"
    if n.startswith(("CTX_BEARING_RETENTION", "CTX_TABLE_LOCK", "LOCK_RECEIVER", "R061_RET_")):
        return "bloqueo"
    if n in drenaje:
        return "drenaje"
    if n in sop_comp or n in accion:
        return "soporte_aspersion"
    if any(s in n for s in ASP):
        return "aspersion"
    return "otro"


ESTILO = {"k2m": None, "rodamiento": ("gris", 55), "mesa": ("azul", 0), "pad": ("oliva", 0),
          "rodadura": ("gris_osc", 0), "bloqueo": ("rojo", 0), "drenaje": ("beige", 40),
          "soporte_aspersion": ("plata", 0), "aspersion": ("celeste", 0), "otro": ("plata", 0),
          "cabina": ("gris", 88)}

VISTAS = [
    ("A_conjunto_iso", {"k2m", "rodamiento", "mesa", "pad", "rodadura", "bloqueo", "drenaje", "soporte_aspersion",
                        "aspersion", "otro"}, "iso", None),
    ("B_soporte_iso", {"k2m", "rodamiento", "mesa", "pad", "rodadura", "bloqueo"}, "iso", "CTX_"),
    ("C_soporte_planta", {"k2m", "rodamiento", "mesa", "pad", "rodadura", "bloqueo"}, "top", "CTX_"),
    ("D_aspersion_frontal", {"rodamiento", "aspersion", "mesa", "pad"}, "front", None),
    ("E_aspersion_iso", {"rodamiento", "aspersion"}, "iso", None),
    ("F_k2m_u2", {"k2m", "mesa", "pad"}, "dir", "R061_K2M_2_"),
    ("G_k2m_u1", {"k2m", "mesa", "pad"}, "dir", "R061_K2M_1_"),
]

try:
    doc = App.openDocument(os.path.join(out, "k2m573_copia.FCStd"))
    Gui.updateGui()
    cab = miembros(doc, "G00_CONTEXTO_CABINA_R05")
    sup = miembros(doc, "G_R061_SUPERADOS_H9")
    guard = miembros(doc, "R06_LANZA_GUARDADA")
    sop_comp = miembros(doc, "G06_SOPORTE_COMPACTO")
    accion = miembros(doc, "G07_APOYOS_ACCIONAMIENTO_FIJOS")
    drenaje = miembros(doc, "R06_DRENAJE")
    rieles = miembros(doc, "R06_RIELES_Y_SOPORTES")
    clase = {}
    for o in doc.Objects:
        if o.ViewObject is None:
            continue
        if o.TypeId == "App::DocumentObjectGroup" or not hasattr(o, "Shape"):
            continue
        k = clasificar(o, cab, sup, guard, sop_comp, accion, drenaje, rieles)
        clase[o.Name] = k
        if k is None:
            continue
        if k == "k2m":
            pintar(o, C[color_k2m(o.Name)], 0)
        else:
            c, t = ESTILO[k]
            pintar(o, C[c], t)
    cuenta = {}
    for k in clase.values():
        cuenta[k] = cuenta.get(k, 0) + 1
    log.write("clases: %s\n" % cuenta)
    log.write("otros: %s\n" % [n for n, k in clase.items() if k == "otro"])
    v = Gui.ActiveDocument.ActiveView
    App.ParamGet("User parameter:BaseApp/Preferences/View").SetBool("UseNavigationAnimations", False)
    try:
        v.setAnimationEnabled(False)
    except Exception:
        pass
    for nombre, visibles, vista, foco in VISTAS:
        # primero los grupos (su visibilidad se propaga a los hijos), luego cada pieza
        for o in doc.Objects:
            if o.ViewObject is not None and o.TypeId == "App::DocumentObjectGroup":
                o.ViewObject.Visibility = True
        Gui.updateGui()
        for o in doc.Objects:
            if o.ViewObject is None or o.TypeId == "App::DocumentObjectGroup":
                continue
            o.ViewObject.Visibility = (o.Name in clase and clase[o.Name] in visibles)
        Gui.updateGui()
        if vista == "dir":
            # mirar la unidad desde el exterior de la mesa
            bbs = [o.Shape.BoundBox for o in doc.Objects if o.Name.startswith(foco) and hasattr(o, "Shape")]
            cx = sum((b.XMin + b.XMax) / 2 for b in bbs) / len(bbs)
            cy = sum((b.YMin + b.YMax) / 2 for b in bbs) / len(bbs)
            r = (cx * cx + cy * cy) ** 0.5
            v.setViewDirection((-cx / r, -cy / r, -0.75))
        else:
            {"iso": v.viewIsometric, "top": v.viewTop, "front": v.viewFront, "right": v.viewRight}[vista]()
        Gui.updateGui()
        if foco:
            Gui.Selection.clearSelection()
            for o in doc.Objects:
                if o.Name.startswith(foco) and o.ViewObject is not None and o.ViewObject.Visibility:
                    Gui.Selection.addSelection(o)
            Gui.SendMsgToActiveView("ViewSelection")
            Gui.Selection.clearSelection()
            if vista == "dir":
                import re as _re
                cs = v.getCamera()
                m = _re.search(r"height\s+([0-9.eE+-]+)", cs)
                if m:
                    cs = cs.replace(m.group(0), "height %g" % (float(m.group(1)) * 1.5))
                    v.setCamera(cs)
        else:
            v.fitAll()
            ZOOM = {"A_conjunto_iso": 0.55, "D_aspersion_frontal": 0.8, "E_aspersion_iso": 0.62}
            if nombre in ZOOM:
                import re as _re
                cs = v.getCamera()
                m = _re.search(r"height\s+([0-9.eE+-]+)", cs)
                if m:
                    v.setCamera(cs.replace(m.group(0), "height %g" % (float(m.group(1)) * ZOOM[nombre])))
        Gui.updateGui()
        v.saveImage(os.path.join(out, nombre + ".png"), 3000, 2000, "White")
        nv = sum(1 for o in doc.Objects if o.ViewObject is not None and o.TypeId != "App::DocumentObjectGroup" and o.ViewObject.Visibility)
        log.write("guardada %s (%d piezas visibles)\n" % (nombre, nv))
    App.closeDocument(doc.Name)
except Exception:
    log.write(traceback.format_exc())
    try:
        App.closeDocument(doc.Name)
    except Exception:
        pass
log.close()
Gui.getMainWindow().close()
