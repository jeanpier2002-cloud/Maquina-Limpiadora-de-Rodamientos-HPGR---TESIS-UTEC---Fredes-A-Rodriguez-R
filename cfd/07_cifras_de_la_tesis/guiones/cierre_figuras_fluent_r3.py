"""CIERRE (12/11/2026): copia de CFD03 05_SCRIPTS/visual/figuras_fluent_cfd03.py con el caso r3_od (diseno final O7+C2 + Caso 2,
R3_02 ramal A). Solo lee el .cas.h5/.dat.h5 de la Corrida 3; escribe en CIERRE_CFD_TESIS/video_final.
"""
"""CFD03: figuras y cuadros de video desde Fluent 2026 R1 (PyFluent 0.42.1) de los casos de D:/CFD03_visual
(Caso Base, Caso 2, Caso 3, INF_INT y verificacion del PAD). Adaptado de CFD02 (figuras_fluent.py, API verificada).
Solo lee los .cas.h5/.dat.h5 (copias). No escribe case/data.
Uso: python figuras_fluent.py <caso> [--solo-figuras] [--solo-video]
     caso = cb_od | c2_od | pad | cb_int | cb_sup | c3_sup | f5
Salida: D:/CFD03_visual/figuras_fluent/<caso>/*.png y .../frames_<video>/f_####.png
"""
import os, sys, json, math, time
from pathlib import Path
aqui = Path(__file__).resolve().parent
os.environ["MPLCONFIGDIR"] = str(aqui / ".mplconfig")
import ansys.fluent.core as pyfluent

LAT = ["lat_1_a", "lat_2_a", "lat_3_a", "lat_4_a", "lat_5_a", "inf_ext_a"]
CASOS = {
    # OD + cara inferior (sector en 0 grados): abanicos en el plano y = 0
    "cb_od": dict(archivo="1_CasoBase_OD_y_cara_inferior", pared="od", otras=["cara_inf"], pw=["od", "cara_inf"], inj=LAT,
                  plano=("zx-plane", "y", 0.0), target=(0.76, 0.0, 1.10),
                  iso=(1.9, -1.5, 0.8), lateral=(0.0, -2.2, 0.0), frontal=(2.2, 0.0, 0.0),
                  campo_lat=0.80, campo_iso=0.80, campo_front=0.78,
                  pw_abajo=dict(sup=["cara_inf"], target=(0.60, 0.0, 0.89), vec=(0.0, 0.0, -1.6), campo=0.62, up=(1, 0, 0),
                                rango=(0.0, 150.0))),
    "c2_od": dict(archivo="4_Caso2_OD_LAT1_inclinada", pared="od", otras=["cara_inf"], pw=["od", "cara_inf"], inj=LAT,
                  plano=("zx-plane", "y", 0.0), target=(0.76, 0.0, 1.10),
                  iso=(1.9, -1.5, 0.8), lateral=(0.0, -2.2, 0.0), frontal=(2.2, 0.0, 0.0),
                  campo_lat=0.80, campo_iso=0.80, campo_front=0.78),
    # verificacion PAD: la cara inferior y el PAD se ven desde abajo
    "pad": dict(archivo="6_Verificacion_PAD", pared="od", otras=["cara_inf", "pad"], pw=["cara_inf"], pw_malla=["pad"], pw_rango=(0.0, 150.0),
                inj=LAT, plano=("zx-plane", "y", 0.0), target=(0.70, 0.0, 0.92),
                iso=(1.4, -1.2, -0.6), lateral=(0.0, -2.2, 0.0), frontal=(2.2, 0.0, 0.0),
                campo_lat=0.62, campo_iso=0.70, campo_front=0.70,
                vista_pw=dict(target=(0.60, 0.0, 0.89), vec=(0.0, 0.0, -1.6), campo=0.62, up=(1, 0, 0))),
    # INF_INT de la lanza (sector en 90 grados): abanico en el plano x = 0
    "cb_int": dict(archivo="2_CasoBase_lanza_INF_INT_cara_inferior", pared="cara_inf", otras=["agujero", "od"],
                   pw=["cara_inf", "agujero"], inj=["inf_int"], plano=("yz-plane", "x", 0.0), target=(0.0, 0.62, 0.88),
                   iso=(-1.3, 1.1, -0.8), lateral=(2.2, 0.0, 0.0), frontal=(0.0, 0.0, -2.0),
                   campo_lat=0.66, campo_iso=0.75, campo_front=0.62,
                   vista_pw=dict(target=(0.0, 0.58, 0.89), vec=(0.0, 0.0, -1.6), campo=0.62, up=(0, 1, 0))),
    # agujero: lanza completa (INT_1-5 + INF_INT) con la red de 22 (F5_red22); configuracion de CFD02 (figuras_fluent.py)
    "f5": dict(archivo="7_CasoBase_agujero_lanza", pared="pared_agujero", otras=["lanza"], pw=["pared_agujero"],
               inj=["int_1", "int_2", "int_3", "int_4", "int_5", "inf_int"],
               plano=("yz-plane", "x", 0.0), target=(0.0, 0.25, 1.12),
               iso=(-1.4, -1.2, 1.6), lateral=(-2.4, 0.0, 0.0), frontal=(0.0, 0.0, 2.6),
               campo_lat=1.0, campo_iso=1.35, campo_front=1.1,
               pared_lat=["lanza"],
               # presion vista desde FUERA del agujero (lado de las boquillas, y > 0): el fondo queda blanco y la leyenda
               # se lee (desde dentro, la pared ocupaba toda la imagen); la franja se ve en espejo
               vista_pw=dict(target=(0.0, 0.45, 1.15), vec=(0.0, 1.0, 0.0), campo=0.70, up=(0, 0, 1))),
    # cara superior (sector en 0 grados)
    "cb_sup": dict(archivo="3_CasoBase_cara_superior", pared="sup", otras=[], pw=["sup"], inj=["sup_1_a", "sup_2_a"],
                   plano=("zx-plane", "y", 0.0), target=(0.60, 0.0, 1.50),
                   iso=(1.3, -1.4, 1.1), lateral=(0.0, -2.2, 0.0), frontal=(0.0, 0.0, 2.2),
                   campo_lat=0.55, campo_iso=0.50, campo_front=0.45),
    "c3_sup": dict(archivo="5_Caso3_cara_superior_SUP2_afuera", pared="sup", otras=[], pw=["sup"], inj=["sup_1_a", "sup_2_a"],
                   plano=("zx-plane", "y", 0.0), target=(0.60, 0.0, 1.50),
                   iso=(1.3, -1.4, 1.1), lateral=(0.0, -2.2, 0.0), frontal=(0.0, 0.0, 2.2),
                   campo_lat=0.55, campo_iso=0.50, campo_front=0.45),
}

CASOS["r3_od"] = dict(archivo="D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT/casos/R3_02_caso2/R3_02_caso2_fin", pared="od",
    otras=["cara_inf"], pw=["od", "cara_inf"], inj=LAT + ["c2_a"],
    plano=("zx-plane", "y", 0.0), target=(0.76, 0.0, 1.10),
    iso=(1.9, -1.5, 0.8), lateral=(0.0, -2.2, 0.0), frontal=(2.2, 0.0, 0.0),
    campo_lat=0.80, campo_iso=0.80, campo_front=0.78,
    pw_abajo=dict(sup=["cara_inf"], target=(0.60, 0.0, 0.89), vec=(0.0, 0.0, -1.6), campo=0.62, up=(1, 0, 0), rango=(0.0, 150.0)))

caso = sys.argv[1]; cfg = CASOS[caso]
solo_fig = "--solo-figuras" in sys.argv; solo_vid = "--solo-video" in sys.argv
solo_orb = "--solo-orbita" in sys.argv
if solo_orb: solo_vid = True
OUT = Path("D:/CFD_Redosado/CIERRE_CFD_TESIS/video_final/figuras_fluent") / caso; OUT.mkdir(parents=True, exist_ok=True)
log = open(OUT / "log.txt", "a", encoding="utf-8")
def p(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()

solver = pyfluent.launch_fluent(precision="double", processor_count=4, mode="solver",
                                ui_mode="hidden_gui", start_timeout=240, cwd="D:/CFD_Redosado/CIERRE_CFD_TESIS/video_final")
# Fluent 2026 dibuja por defecto una rejilla de suelo, reflejos y sombras (preferences.Graphics.GraphicsEffects,
# nombres leidos del arbol de la sesion). Se apagan solo durante esta sesion y se restauran al salir.
EFECTOS = ("GridPlaneEnabled", "ReflectionsEnabled", "SimpleShadowsEnabled")
ge = solver.preferences.Graphics.GraphicsEffects
efectos_orig = {k: getattr(ge, k)() for k in EFECTOS}
try:
    for k in EFECTOS:
        getattr(ge, k).set_state(False)
    p("Fluent", solver.get_fluent_version(), "caso", caso)
    solver.settings.file.read_case_data(file_name=(cfg["archivo"] if ":" in cfg["archivo"] else f"D:/CFD03_visual/{cfg['archivo']}") + ".cas.h5")
    g = solver.settings.results.graphics
    pic = g.picture
    pic.driver_options.hardcopy_format = "png"
    pic.use_window_resolution = False
    pic.x_resolution = 1920; pic.y_resolution = 1080
    for nombre_attr in ["graphics_color_theme"]:
        try: p(nombre_attr, "allowed:", getattr(g.colors, nombre_attr).allowed_values(), "actual:", getattr(g.colors, nombre_attr)())
        except Exception as e: p(nombre_attr, e)
    try:
        ro = g.views.rendering_options
        p("rendering_options:", {k: (getattr(ro, k)() if not hasattr(getattr(ro,k),'child_names') else '...') for k in ro.child_names})
    except Exception as e: p("ro:", e)
    try: p("windows children:", g.windows.child_names, "main:", g.windows.main.child_names)
    except Exception as e: p("win:", e)
    cam = g.views.camera
    tx, ty, tz = cfg["target"]

    def camara(vec, campo, up=(0, 0, 1), tgt=None):
        # el vector "arriba" va antes que la posicion: si no, una vista cenital (paralela al "arriba" previo) se rechaza
        ax_, ay_, az_ = tgt if tgt else (tx, ty, tz)
        L = math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
        cam.target = [ax_, ay_, az_]
        # paso intermedio oblicuo: Fluent rechaza una posicion cuya direccion es paralela al "arriba" vigente
        cam.position = [ax_ + 0.577 * L, ay_ - 0.577 * L, az_ + 0.577 * L]
        cam.up_vector = list(up)
        cam.position = [ax_ + vec[0], ay_ + vec[1], az_ + vec[2]]
        cam.up_vector = list(up)
        cam.field = [campo, campo]

    def guardar(nombre):
        f = str(OUT / nombre).replace("\\", "/")
        pic.save_picture(file_name=f)
        p("  ->", nombre, os.path.exists(f))

    superficies_pared = [cfg["pared"]] + cfg["otras"]
    g.mesh["m_pared"] = {"surfaces_list": superficies_pared, "options": {"edges": False, "faces": True}}
    g.mesh["m_pared_aristas"] = {"surfaces_list": superficies_pared, "options": {"edges": True, "faces": True}}
    g.mesh["m_lat"] = {"surfaces_list": cfg.get("pared_lat", superficies_pared), "options": {"edges": False, "faces": True}}
    todas = list(g.mesh["m_pared"].surfaces_list.allowed_values())
    g.mesh["m_todo"] = {"surfaces_list": todas, "options": {"edges": True, "faces": False}}

    s = solver.settings.results.surfaces
    met, eje, val = cfg["plano"]
    s.plane_surface["plano_abanicos"] = {"method": met, eje: val}

    def tracks(nombre, campo, filtro=None, estilo="point"):
        pt = g.particle_track
        if nombre not in pt.get_object_names():
            pt[nombre] = {}
        o = pt[nombre]
        o.field = campo
        o.injections_list = cfg["inj"]
        o.style_attribute.style = estilo
        if filtro is not None:
            o.filter_settings.enabled = True
            o.filter_settings.field = "particle-resid-time"
            o.filter_settings.options.option = "inside"
            o.filter_settings.filter_minimum = 0.0
            o.filter_settings.filter_maximum = filtro
        return o

    def contorno(nombre, campo, superficies):
        c = g.contour
        if nombre not in c.get_object_names():
            c[nombre] = {}
        o = c[nombre]
        o.field = campo
        o.surfaces_list = superficies
        return o

    def mostrar(coleccion, nombre, con_pared=True, malla="m_pared"):
        if con_pared:
            g.mesh[malla].display()
            try:
                coleccion.add_to_graphics(object_name=nombre)
                return
            except Exception as e:
                p("  add_to_graphics fallo:", e, "args:", getattr(coleccion.add_to_graphics, "argument_names", "?"))
        coleccion[nombre].display()

    if not solo_vid:
        # 01 malla
        g.mesh["m_pared_aristas"].display(); camara(cfg["iso"], cfg["campo_iso"]); guardar("01_malla_pared_iso.png")
        g.mesh["m_todo"].display(); camara(cfg["iso"], cfg["campo_iso"]); guardar("02_malla_dominio_iso.png")
        # 03-06 gotas
        o = tracks("pt_d", "particle-diameter")
        mostrar(g.particle_track, "pt_d"); camara(cfg["iso"], cfg["campo_iso"]); guardar("03_gotas_diametro_iso.png")
        mostrar(g.particle_track, "pt_d", malla="m_lat"); camara(cfg["lateral"], cfg["campo_lat"]); guardar("04_gotas_diametro_lateral.png")
        mostrar(g.particle_track, "pt_d")
        camara(cfg["frontal"], cfg["campo_front"], up=(0, 0, 1) if cfg["frontal"][2] == 0 else (0, 1, 0)); guardar("05_gotas_diametro_frontal.png")
        o = tracks("pt_v", "particle-velocity-mag")
        mostrar(g.particle_track, "pt_v", malla="m_lat"); camara(cfg["lateral"], cfg["campo_lat"]); guardar("06_gotas_velocidad_lateral.png")
        mostrar(g.particle_track, "pt_v"); camara(cfg["iso"], cfg["campo_iso"]); guardar("07_gotas_velocidad_iso.png")
        # 08-09 aire y concentracion en el plano de los abanicos
        o = contorno("c_vel", "velocity-magnitude", ["plano_abanicos"])
        mostrar(g.contour, "c_vel", malla="m_lat"); camara(cfg["lateral"], cfg["campo_lat"]); guardar("08_aire_velocidad_plano.png")
        o = contorno("c_conc", "dpm-concentration", ["plano_abanicos"])
        mostrar(g.contour, "c_conc", malla="m_lat"); camara(cfg["lateral"], cfg["campo_lat"]); guardar("09_concentracion_gotas_plano.png")
        # 10 presion de gotas en pared (si Fluent la acumula con trap)
        try:
            o = contorno("c_pw", "dpm-wall-normal-pressure", cfg.get("pw", [cfg["pared"]]))
            try:   # escala sobre las superficies dibujadas, no sobre todo el dominio (range_options, sonda 5)
                o.range_options.global_range = False
                if "pw_rango" in cfg:   # escala manual (valores por encima del maximo con el color del maximo)
                    o.range_options.auto_range = False
                    o.range_options.minimum, o.range_options.maximum = cfg["pw_rango"]
            except Exception as e: p("  range_options:", e)
            if "pw_malla" in cfg:
                g.mesh["m_pw"] = {"surfaces_list": cfg["pw_malla"], "options": {"edges": False, "faces": True}}
                mostrar(g.contour, "c_pw", malla="m_pw")
            else:
                mostrar(g.contour, "c_pw", con_pared=False)
            if "vista_pw" in cfg:
                vp = cfg["vista_pw"]; camara(vp["vec"], vp["campo"], up=vp["up"], tgt=vp["target"])
            else:
                camara(cfg["frontal"], cfg["campo_front"], up=(0, 0, 1) if cfg["frontal"][2] == 0 else (0, 1, 0))
            guardar("10_presion_gotas_pared.png")
            try:
                rng = o.range_options
                rng.compute(); p("  rango dpm-wall-normal-pressure:", rng.minimum(), rng.maximum())
            except Exception as e: p("  rango pw:", e)
        except Exception as e:
            p("10 omitida:", e)
        # 10b presion de gotas en la cara inferior vista desde abajo, escala manual (par con la verificacion del PAD)
        if "pw_abajo" in cfg:
            try:
                vb = cfg["pw_abajo"]
                o = contorno("c_pw2", "dpm-wall-normal-pressure", vb["sup"])
                o.range_options.global_range = False
                o.range_options.auto_range = False
                o.range_options.minimum, o.range_options.maximum = vb["rango"]
                mostrar(g.contour, "c_pw2", con_pared=False)
                camara(vb["vec"], vb["campo"], up=vb["up"], tgt=vb["target"])
                guardar("10b_presion_gotas_cara_inferior_desde_abajo.png")
            except Exception as e:
                p("10b omitida:", e)

    if not solo_fig and not solo_orb:
        # video A: crecimiento del spray (filtro por tiempo de residencia)
        fa = OUT / "frames_spray"; fa.mkdir(exist_ok=True)
        n = 48; tmax = 0.024
        o = tracks("pt_anim", "particle-velocity-mag", filtro=1e-4)
        try:   # misma escala en todos los cuadros (0-30 m/s; las gotas salen a 27-28 m/s)
            o.range_options.auto_range = False
            o.range_options.minimum = 0.0
            o.range_options.maximum = 30.0
        except Exception as e: p("range_options:", e)
        for i in range(n):
            t = tmax * (i + 1) / n
            o.filter_settings.filter_maximum = t
            mostrar(g.particle_track, "pt_anim", malla="m_lat")
            camara(cfg["lateral"], cfg["campo_lat"])
            pic.save_picture(file_name=str(fa / f"f_{i:04d}.png").replace("\\", "/"))
        p("frames spray:", n)
    if not solo_fig:
        # video B: orbita alrededor del sector con los abanicos
        fb = OUT / "frames_orbita"; fb.mkdir(exist_ok=True)
        o = tracks("pt_d", "particle-diameter")
        o.filter_settings.enabled = False
        mostrar(g.particle_track, "pt_d"); camara(cfg["iso"], cfg["campo_iso"])
        m = 90
        vx, vy, vz = cfg["iso"]
        for i in range(m):
            ang = 2 * math.pi * i / m   # giro de la camara alrededor del eje Z del rodamiento
            c_, s_ = math.cos(ang), math.sin(ang)
            camara((vx * c_ - vy * s_, vx * s_ + vy * c_, vz), cfg["campo_iso"])
            pic.save_picture(file_name=str(fb / f"f_{i:04d}.png").replace("\\", "/"))
        p("frames orbita:", m)
finally:
    try:
        for k, v in efectos_orig.items():
            getattr(ge, k).set_state(v)
        p("efectos graficos restaurados:", {k: getattr(ge, k)() for k in EFECTOS})
    except Exception as e:
        p("no se pudieron restaurar los efectos graficos:", e)
    solver.exit(); p("fin")
