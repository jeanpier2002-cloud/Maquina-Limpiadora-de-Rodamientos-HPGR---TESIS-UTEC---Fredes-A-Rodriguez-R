#!/usr/bin/env python3
"""
CORRIDA 3 · PDF de resultados para Jean (RESULTADOS_R3_para_Jean.pdf, 3-5 paginas; PROMPT_CORRIDA_3 §0 bis regla 5).
HTML -> PDF con Edge headless (mismo mecanismo que r3_pdf_jean.py / v3_pdf_comun.py).
Las tablas se leen de los CSV de 03_FLUENT/resultados (r3_comparar.py, r3_rigor.py, r3_tiempo_lavado.py, run_log.csv,
*_aceptacion.txt, destino_*.csv); lo que no existe se marca «pendiente». El texto interpretativo esta en TEXTO (abajo)
y se redacta a mano con las cifras de esos CSV: borrador de trabajo para que Jean lo audite.
Uso: python -I -B r3_pdf_resultados.py
"""
import csv
import html
import os
import subprocess
import time

B = "D:/CFD_Redosado/CORRIDA_3_O7C2"
R = B + "/04_REDACCION"
BUILD = R + "/build"
FL = B + "/03_FLUENT"
RES = FL + "/resultados"
FIG = FL + "/figuras"
EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
os.makedirs(BUILD, exist_ok=True)

# ------------------------------------------------------------------ texto interpretativo (se completa a mano)
TEXTO = {
    "corta": [],          # vinetas de la respuesta corta (HTML)
    "od": "",             # parrafo bajo la tabla del OD
    "inf": "",            # parrafo bajo la tabla de la cara inferior
    "n1": "",             # lectura de la tabla N1 / CFD
    "ab": "",             # lectura A<->B y destino por boquilla
    "rigor": "",          # lectura de malla y particulas
    "lavado": "",         # lectura del tiempo de lavado
    "falta": [],          # que fallo o falta
    "ismael": [],         # que alinear con Ismael
    "kevin": [],          # preguntas para Kevin
}
_t = os.path.join(R, "r3_texto_pdf.py")
if os.path.exists(_t):
    exec(open(_t, encoding="utf-8").read())      # define TEXTO con la redaccion actual (archivo aparte, editable)


def e(t):
    return html.escape(str(t), quote=False)


def coma(v, nd=2):
    try:
        return ("%.*f" % (nd, float(v))).replace(".", ",")
    except (TypeError, ValueError):
        return e(v) if v not in (None, "") else "—"


def a_pdf(html_ruta, pdf_ruta):
    if os.path.exists(pdf_ruta):
        os.remove(pdf_ruta)
    perfil = BUILD + "/perfil_edge"
    os.makedirs(perfil, exist_ok=True)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=" + perfil, "--no-pdf-header-footer",
           "--allow-file-access-from-files", "--virtual-time-budget=20000",
           "--print-to-pdf=" + pdf_ruta.replace("/", "\\"), "file:///" + html_ruta]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    ult, estable = -1, 0
    for _ in range(120):
        tam = os.path.getsize(pdf_ruta) if os.path.exists(pdf_ruta) else -1
        estable = estable + 1 if (tam == ult and tam > 0) else 0
        ult = tam
        if estable >= 3:
            break
        time.sleep(1)
    assert os.path.exists(pdf_ruta), "no se genero el PDF (rc %s %s)" % (r.returncode, r.stderr[-300:])
    print("PDF", pdf_ruta, os.path.getsize(pdf_ruta) // 1024, "KB")


def img(nombre, ancho="100%"):
    p = "%s/%s.png" % (FIG, nombre)
    if not os.path.exists(p):
        return "<div class='pie'>[figura %s pendiente]</div>" % e(nombre)
    return '<img src="file:///%s" style="width:%s">' % (p, ancho)


def tabla(cab, filas, anchos=None):
    h = "<table><tr>" + "".join("<th>%s</th>" % c for c in cab) + "</tr>"
    for f in filas:
        h += "<tr>" + "".join("<td>%s</td>" % c for c in f) + "</tr>"
    return h + "</table>"


def leer(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


CSS = """
@page { size: A4; margin: 10mm 12mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 8.9pt; line-height: 1.28; color: #1b1b1b; }
h1 { font-size: 16.5pt; margin: 0 0 2px 0; } h2 { font-size: 12pt; margin: 12px 0 4px 0; border-bottom: 1.5px solid #1f4e79; color: #1f4e79; padding-bottom: 1px; }
.sub { color: #555; font-size: 8.8pt; margin-bottom: 7px; }
.caja { background: #eef4fb; border-left: 4px solid #1f4e79; padding: 6px 10px; margin: 6px 0; }
.aviso { background: #fff6e0; border-left: 4px solid #d99000; padding: 6px 10px; margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 3px 0; font-size: 7.9pt; }
th { background: #1f4e79; color: #fff; text-align: left; padding: 1px 4px; } td { border-bottom: 1px solid #ccc; padding: 1px 4px; vertical-align: top; }
.pie { color: #666; font-size: 7.8pt; margin-top: 2px; } .pb { page-break-before: always; }
ul { margin: 3px 0 3px 18px; padding: 0; } li { margin-bottom: 2px; }
.dos { display: flex; gap: 8px; } .dos > div { flex: 1; }
"""
h = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><style>%s</style></head><body>" % CSS]
h.append("<h1>Corrida 3 (diseño O7+C2): resultados de Fluent</h1>")
h.append("<div class='sub'>Para Jean · generado %s · borrador de trabajo (auditar antes de usar). "
         "Estados: lo de Fluent es <b>EJECUTADO</b> (verificado numéricamente, <b>no validado</b>); N1 = rayos rectos = "
         "<b>predicción</b>. El CFD mide mojado y dosis, <b>no limpieza</b>.</div>" % time.strftime("%d/%m/%Y %H:%M"))
h.append("<div class='caja'><b>Respuesta corta.</b><ul>%s</ul></div>" % "".join("<li>%s</li>" % x for x in TEXTO["corta"]))

# ------------------------------------------------------------------ corridas
h.append("<h2>1. Qué se corrió (Fluent 2026 R1 Student, 4 procesos)</h2>")
runlog = [r for r in leer(B + "/00_ADMIN/run_log.csv") if r["etapa"] == "fluent_R3" and not
          (r["caso"].endswith("_humo") and r["id"] != "R3_00")]
DESC = {"R3_00": "humo del kit (100 pasos)", "R3_02": "Caso 2: kit + LAT_1 a −4° (ramal A)", "R3_01": "kit tal cual (LAT_1 horizontal)",
        "R3_03": "Caso 2, ramal B explícito", "R3_04": "malla gruesa, Courant const.", "R3_05": "malla fina, Courant const.",
        "R3_06": "½ de parcelas", "R3_07": "2× parcelas"}
filas = []
for r in runlog:
    ac = RES + "/%s_aceptacion.txt" % r["caso"]
    acep = open(ac, encoding="utf-8").read().strip() if os.path.exists(ac) else ""
    bal = acep.split("balance")[1].split("%")[0].strip() if "balance" in acep else ""
    est = [float(x["salida_sobre_inyectado"]) for x in leer(RES + "/R3/%s_estacionariedad.csv" % r["caso"])
           if 0.0249 <= float(x["t_ini_s"]) < 0.0499]
    filas.append([r["id"], e(DESC.get(r["id"], "")), "%s · %s s · %s" % (r["malla"], coma(float(r["dt_medio_s"]) * 1e5, 3) + "·10⁻⁵", r["pasos"]),
                  coma(r["costo_estimado_h"], 1), coma(r["costo_real_h"], 2) if r["costo_real_h"] else "—",
                  (coma(bal, 3) + " %") if bal else "—",
                  ("%s – %s" % (coma(min(est), 4), coma(max(est), 4))) if est else "—",
                  e(acep.split()[0]) if acep else e(r["estado"])])
h.append(tabla(["ID", "Qué", "Malla · Δt · pasos", "Costo est. (h)", "Costo real (h)", "Balance 25–50 ms",
                "Salida/inyectado, ventanas de 5 ms", "Aceptación"], filas))
h.append("<div class='pie'>Aceptación (§5 del prompt): pasos completos, sin Error/FATAL, 8 muestras DPM y |balance| &lt; 1 % "
         "(en el humo no se exige el balance). Estacionariedad: mínimo y máximo de la salida total / inyectado en las ventanas "
         "de 5 ms entre 25 y 50 ms. Fuente: 00_ADMIN/run_log.csv y 03_FLUENT/resultados/.</div>")

# ------------------------------------------------------------------ KPI
comp = leer(RES + "/T7_comparacion.csv")
casos = []
for r in comp:
    if r["caso"] not in casos:
        casos.append(r["caso"])
CORTO = {"Base (G3_A_base_v3, S9)": "Base", "Caso 2 diseño anterior (G8_C2_OD, S9)": "Caso 2 ant.",
         "R3_01 kit, LAT_1 horizontal (S9)": "R3_01 kit", "R3_02 Caso 2, ramal A (S9)": "R3_02 A",
         "R3_03 Caso 2, ramal B (S9)": "R3_03 B", "Caso 2 A+B explícito (R3_02 + R3_03)": "Caso 2 A+B"}


def bloque(prefijos, titulo, texto):
    filas = []
    for sup in prefijos:
        for r0 in [r for r in comp if r["superficie"] == sup and r["caso"] == casos[0]]:
            k = r0["kpi"]
            fila = [e(sup) + " · " + e(k)]
            for c in casos:
                v = next((x["valor"] for x in comp if x["superficie"] == sup and x["kpi"] == k and x["caso"] == c), "")
                nd = 3 if "CV" in k else (1 if "η" in k else 2)
                fila.append(coma(v, nd) if v != "" else "—")
            filas.append(fila)
    h.append("<h2>%s</h2>" % titulo)
    h.append(tabla(["KPI (kg·m⁻²·vuelta⁻¹ salvo indicación)"] + [e(CORTO.get(c, c)) for c in casos], filas))
    h.append("<div class='pie'>Con obstáculos de R05 (máscaras N1), bandas de 10 mm salvo indicación; ventana 25–50 ms; "
             "«S9» = el ramal B se toma como espejo del A. Base y Caso 2 anterior: CFD03/06_RESULTADOS/G8/comparacion.</div>")
    if texto:
        h.append("<p>%s</p>" % texto)


if comp:
    bloque(["OD", "OD bajo z 890-1000", "OD alto z 1000-1405"], "2. OD", TEXTO["od"])
    h.append("<div class='dos'><div>%s<div class='pie'>D por banda de 10 mm en el OD (escala log).</div></div><div>%s"
             "<div class='pie'>Franja z 1000–1070 mm, bandas de 2 mm, sin obstáculos.</div></div></div>" % (
                 img("R3F1_OD_dosis_z"), img("R3F2_OD_franja_2mm")))
    bloque(["Cara inferior", "Z1 r 450-521", "Z2 r 521-617 (pared proyectada)", "Z3 r 617-710"], "3. Cara inferior", TEXTO["inf"])
    h.append("<div class='dos'><div>%s<div class='pie'>D por banda de 10 mm (con obstáculos). Z2 es la pared proyectada "
             "de la malla, no los rodillos.</div></div><div>%s<div class='pie'>Aporte de cada boquilla, sin obstáculos.</div>"
             "</div></div>" % (img("R3F3_cara_inf_dosis_r"), img("R3F4_cara_inf_aportes")))
else:
    h.append("<div class='aviso'>Sin KPI todavía (ninguna corrida de 1000 pasos terminada y procesada).</div>")

# ------------------------------------------------------------------ N1
n1 = leer(RES + "/T7_N1_vs_CFD.csv")
if n1:
    h.append("<h2>4. Predicción N1 (25/10, antes de correr) frente al CFD</h2>")
    h.append(tabla(["Superficie", "Magnitud", "N1", "Estimado calibrado", "CFD R3_01 (S9)", "CFD R3_02 (S9)", "CFD Caso 2 A+B"],
                   [[e(r["superficie"]), e(r["magnitud"])] +
                    [coma(r[c], 3 if r["magnitud"] == "CV" else 2) if c != "estimado_CFD_calibrado" else
                     e(r[c]).replace(".", ",") for c in ("N1", "estimado_CFD_calibrado", "CFD_R3_01_S9", "CFD_R3_02_S9",
                                                         "CFD_Caso2_AB")] for r in n1]))
    h.append("<div class='pie'>N1 de 05_VERIF_PREVIA/PREDICCION_N1_O7C2.csv (cara inferior: «O7+C2 kit»; OD: «O7+C2 + Caso 2»). "
             "CV y zona seca: valores absolutos.</div>")
    if TEXTO["n1"]:
        h.append("<p>%s</p>" % TEXTO["n1"])

# ------------------------------------------------------------------ A<->B y destino
ab = leer(RES + "/T9_ruido_AB.csv")
dest = leer(RES + "/destino_R3_02_caso2.csv")
if ab or dest:
    h.append("<h2>5. Ramal A frente a ramal B, y adónde va el caudal de cada boquilla</h2>")
    if ab:
        h.append(tabla(["KPI", "A (R3_02, S9)", "B (R3_03, S9)", "B − A"],
                       [[e(r["kpi"]), coma(r["A_S9 (R3_02)"], 3), coma(r["B_S9 (R3_03)"], 3),
                         (coma(r["B_menos_A"], 2) + " %") if r["unidad"] == "%" else coma(r["B_menos_A"], 3)] for r in ab]))
    if dest:
        destb = leer(RES + "/destino_R3_03_B_caso2.csv")
        cols = [c for c in dest[0] if c.startswith("pct_") and any(float(r[c]) > 0.05 for r in dest)]
        sel = [r for r in dest + destb if float(r.get("pct_od", 100)) < 99.5]      # LAT_1-4: 100 % al OD
        h.append(tabla(["Boquilla"] + [e(c[4:].replace("abierto_", "sale por ")) for c in cols],
                       [[e(r["boquilla"])] + [coma(r[c], 1) for c in cols] for r in sel]))
        h.append("<div class='pie'>% del caudal inyectado de cada boquilla que sale por cada frontera del sector en 25–50 ms "
                 "(r3_destino.py; R3_02 para _a, R3_03 para _b). LAT_1 a LAT_4 mandan el 99,6–100 % al OD (no se listan). "
                 "«sale por agujero» = pasa bajo el aro hacia el agujero; por exterior, lateral y superior no sale nada.</div>")
    if TEXTO["ab"]:
        h.append("<p>%s</p>" % TEXTO["ab"])

# ------------------------------------------------------------------ rigor
for nombre, tit in (("malla", "6. Malla con Courant constante (lo que pidió Kevin)"), ("particulas", "7. Número de parcelas")):
    T9 = leer(RES + "/T9_%s.csv" % nombre)
    if not T9:
        continue
    cab = list(T9[0])
    h.append("<h2>%s</h2>" % tit)
    if any(r[c] in ("nan", "") for r in T9[:1] for c in cab[2:5]):
        h.append("<div class='aviso'>Pendiente: faltan corridas de este estudio al generar el PDF (tabla 1).</div>")
        if nombre == "particulas" and TEXTO.get("particulas_pend"):
            h.append("<p>%s</p>" % TEXTO["particulas_pend"])
        continue
    filas = []
    for r in T9:
        if r["kpi"] == "costo_real_h":
            filas.append(["<i>costo real (h)</i>"] + [coma(r[c], 2) for c in cab[2:5]] + [""] * 4)
            continue
        nd = 3 if "CV" in r["kpi"] or "seca" in r["kpi"] else 2
        u = " %" if r["modo"] == "rel" else ""
        filas.append([e(r["kpi"])] + [coma(r[c], nd) for c in cab[2:5]] +
                     [coma(r[cab[5]], 2 if u else 4) + u, coma(r[cab[7]], 2 if u else 4) + u, e(r["menor_2pct"] or "—"),
                      e(r["convergencia"].replace(" (diverge: |e21| > |e32|)", "*")), coma(r["p_observado"], 1),
                      (coma(r["GCI_fino_pct"], 2) + " %") if r["GCI_fino_pct"] else "—"])
    niveles = {"malla": ["gruesa (202 616)", "base (430 560)", "fina (846 960)"], "particulas": ["×0,5", "×1", "×2"]}[nombre]
    h.append(tabla(["KPI"] + niveles + ["1.º frente al 3.º", "3.º frente al 2.º", "&lt; 2 %", "tipo", "p obs.", "GCI"], filas))
    h.append("<div class='pie'>Cambios relativos (%) para D̄ y D_min; diferencia absoluta para CV y zona seca. «3.º frente al 2.º» = "
             "cambio entre los dos niveles más finos. Tipo, p y GCI: Celik et al. (2008), r3_gci.py (copia de CFD03/gci.py); "
             "* = el cambio entre los dos más finos es mayor que entre los dos más gruesos (cambios del orden del ruido: p no "
             "es fiable). D_min no es criterio (ruidoso).</div>")
    if nombre == "malla":
        h.append("<div class='dos'><div>%s</div><div>%s</div></div>" % (
            img("T9_malla_cara_inf_obst_10mm_D_media", "78%"),
            img("T9_malla_cara_inf_Z3_aro_exterior_sin_PAD_obst_2mm_D_media", "78%")))
        if TEXTO["rigor"]:
            h.append("<p>%s</p>" % TEXTO["rigor"])
    else:
        h.append("<div class='dos'><div>%s</div><div>%s</div></div>" % (
            img("T9_particulas_cara_inf_obst_10mm_D_media", "78%"),
            img("T9_particulas_cara_inf_Z3_aro_exterior_sin_PAD_obst_2mm_D_media", "78%")))
        if TEXTO.get("particulas"):
            h.append("<p>%s</p>" % TEXTO["particulas"])

# ------------------------------------------------------------------ lavado
lav = leer(RES + "/T10_tiempo_lavado.csv")
if lav:
    h.append("<h2>8. Tiempo de lavado (CANDIDATO; D_req = DATO EXTERNO PENDIENTE)</h2>")
    sup = []
    for r in lav:
        if (r["superficie"], r["caso"]) not in sup:
            sup.append((r["superficie"], r["caso"]))
    filas = []
    for s, c in sup:
        rr = [r for r in lav if r["superficie"] == s and r["caso"] == c]
        filas.append([e(s), e(c), coma(rr[0]["D_min_10mm"])] + [coma(r["min_peor_celda"], 1) for r in rr])
    h.append("<div class='dos'><div>%s</div><div>%s</div></div>" % (
        tabla(["Superficie", "Fuente", "D_min 10 mm", "65", "183", "305"], filas), img("T10_tiempo_lavado_O7C2")))
    h.append("<div class='pie'>Minutos para que la peor celda acumule D_req (kg·m⁻²): T = D_req·T_vuelta/D_min, T_vuelta = 35,294 s "
             "(1,7 rpm, HIPÓTESIS). Cara superior y agujero no cambian (G7).</div>")
    if TEXTO["lavado"]:
        h.append("<p>%s</p>" % TEXTO["lavado"])

# ------------------------------------------------------------------ pendientes
h.append("<h2>9. Qué falló o falta, qué alinear con Ismael y qué preguntar a Kevin</h2>")
for tit, k in (("Falló o falta", "falta"), ("Alinear con Ismael", "ismael"), ("Para Kevin", "kevin")):
    if TEXTO[k]:
        h.append("<b>%s</b><ul>%s</ul>" % (tit, "".join("<li>%s</li>" % x for x in TEXTO[k])))
h.append("<div class='pie'>Fuentes: 00_ADMIN/ESTADO_CORRIDA_3.md, run_log.csv, CAMBIOS_R3.md, 03_FLUENT/resultados y figuras "
         "(cada figura con su CSV). Scripts en 03_FLUENT/scripts.</div>")
h.append("</body></html>")
ruta = BUILD + "/resultados_r3.html"
open(ruta, "w", encoding="utf-8").write("\n".join(h))
a_pdf(ruta, R + "/RESULTADOS_R3_para_Jean.pdf")
