# -*- coding: utf-8 -*-
"""Soporte superior K32 (HPGR D-080): placas base, anclajes y soldadura poste-placa de los 4 postes SHS80x4 (03/11/2026).
Demandas: reacciones simultaneas por base y combinacion de las tablas ORIGINALES de SAP2000 del modelo K34 (K32 con sismo E.030-2018,
V/P = 0,295; anexo_sap/tablas_sap/K34_K32_SISMO_E030_api/Joint_Reactions.csv, rigidez 0,8 EI del Metodo de Analisis Directo).
  - no sismicas: U2 y U3 (accidental de 1 kN), tal como estan en SAP;
  - sismicas para los anclajes (ACI 318-19 17.10.5.3 d): (1,2 + 0,197) D + BELT + TORQ +- Om0 E y (0,9 - 0,197) D +- Om0 E, con Om0 = 3
    [HIPOTESIS: la E.030 no define Om0; 3 es el de porticos ordinarios de acero en ASCE 7] y resistencias de concreto x 0,75 (17.10.5.4).
Capacidades: ACI 318-19 cap. 17 con las mismas hipotesis que D-073 (r07_anclajes_riel_calculos.py, que no se importa para no reescribir
sus salidas): losa de 200 mm y f'c 21 MPa fisurada sin bordes cercanos [HIPOTESIS], adhesivo con la adherencia minima de la tabla
17.6.5.2.5 (tau_cr 1,4 MPa), phi 0,55 (condicion B, categoria 2), varilla A4-70 tratada como fragil (phi 0,65 / 0,60).
Placa rigida: la compresion se ubica a 0,9 de la media placa (como D-073). Espesor de placa por flexion del voladizo de la placa en la
fila traccionada (AISC Design Guide 1, 2.a ed.; Fy 250 MPa). Soldadura poste-placa: filete en todo el contorno, metodo elastico de lineas.
Salidas: resultados_cabina/CALCULO_PLACAS_BASE_K32.json."""
import csv
import json
import math
import os

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(B, "anexo_sap", "tablas_sap", "K34_K32_SISMO_E030_api")
num = lambda v: float(v.replace(",", ".")) if v not in ("", None) else 0.0

# ------------------------------------------------------------------ reacciones de SAP
bases = [r["Joint"] for r in csv.DictReader(open(os.path.join(T, "Joint_Restraint_Assignments.csv"), encoding="utf-8-sig"), delimiter=";")]
R = {}
for r in csv.DictReader(open(os.path.join(T, "Joint_Reactions.csv"), encoding="utf-8-sig"), delimiter=";"):
    if r["Joint"] in bases and r.get("StepType", "") in ("", "Max", "Min") and r["OutputCase"] != "MODAL":
        R.setdefault(r["Joint"], {})[r["OutputCase"] + ("_" + r["StepType"] if r.get("StepType") else "")] = [num(r[k]) for k in ("F1", "F2", "F3", "M1", "M2", "M3")]
v = 2.0 / 3.0 * 0.2953
OM0 = 3.0
comb = {}
for j in bases:
    rj = R[j]
    lin = lambda **f: [sum(f[c] * rj[c][i] for c in f) for i in range(6)]
    c = {k: rj[k] for k in rj if k.startswith(("U2", "U3_"))}
    for e in ("SX", "SY"):
        for sg in (1, -1):
            c["U4O_%s%s" % (e, "P" if sg > 0 else "N")] = lin(DEAD=1.2 + v, BELT=1.0, TORQ=1.0, **{e: sg * OM0})
            c["U5O_%s%s" % (e, "P" if sg > 0 else "N")] = lin(DEAD=0.9 - v, **{e: sg * OM0})
    comb[j] = c

# ------------------------------------------------------------------ capacidades ACI 318-19 cap. 17 (como D-073)
fc, kc, tau_cr, tau_uncr = 21.0, 7.0, 1.4, 4.5
phi_c, phi_st, phi_sv, phi_cp = 0.55, 0.65, 0.60, 0.65
f_ya, f_uta = 450.0, 700.0
A_se = {12: 84.3, 16: 157.0}


def capacidades(d, hef, s):
    f_ut = min(f_uta, 1.9 * f_ya, 860.0)
    Nsa = A_se[d] * f_ut / 1000; Vsa = 0.6 * A_se[d] * f_ut / 1000 * 0.80
    Nb = kc * math.sqrt(fc) * hef ** 1.5 / 1000; ANco = 9 * hef ** 2
    cNa = 10 * d * math.sqrt(tau_uncr / 7.6); ANao = (2 * cNa) ** 2; Nba = tau_cr * math.pi * d * hef / 1000
    cono = lambda n: min((s * (n - 1) + 3 * hef) * 3 * hef, n * ANco) / ANco * Nb            # fila de n anclajes
    adh = lambda n: min((min(s, 2 * cNa) * (n - 1) + 2 * cNa) * 2 * cNa, n * ANao) / ANao * Nba
    grupo_c = min((s + 3 * hef) ** 2, 4 * ANco) / ANco * Nb
    grupo_a = min((min(s, 2 * cNa) + 2 * cNa) ** 2, 4 * ANao) / ANao * Nba
    return {"Nsa": Nsa, "Vsa": Vsa, "fila": min(cono(2), adh(2)), "uno": min(cono(1), adh(1)), "grupo": min(grupo_c, grupo_a),
            "Vcp": 2.0 * min(grupo_c, grupo_a), "cNa": cNa}


def verificar(d, hef, bp, s, tp):
    cap = capacidades(d, hef, s)
    z = (s / 2 + 0.9 * bp / 2) / 1000.0
    peor = {"DC": 0}
    for j, cs in comb.items():
        for k, (F1, F2, F3, M1, M2, M3) in cs.items():
            sis = k.startswith(("U4O", "U5O"))
            f075 = 0.75 if sis else 1.0
            Mx, My = abs(M1) / 1e6, abs(M2) / 1e6          # kN m
            N = -F3 / 1000.0                                  # traccion positiva (levantamiento)
            T_esq = max(0.0, N / 4 + My / z / 2 + Mx / z / 2)
            T_fila = max(0.0, N / 2 + max(My, Mx) / z)
            T_grupo = max(0.0, N)
            V = math.hypot(F1, F2) / 1000.0
            dcN = max(T_esq / (phi_st * cap["Nsa"]), T_fila / (f075 * phi_c * cap["fila"]), T_grupo / (f075 * phi_c * cap["grupo"]),
                      T_esq / (f075 * phi_c * cap["uno"]))
            dcV = max(V / 2 / (phi_sv * cap["Vsa"]), V / (f075 * phi_cp * cap["Vcp"]))
            inter = dcN + dcV if (dcN > 0.2 and dcV > 0.2) else max(dcN, dcV)
            dc = max(dcN, dcV, inter / 1.2)
            if dc > peor["DC"]:
                peor = {"DC": round(dc, 3), "DC_N": round(dcN, 3), "DC_V": round(dcV, 3), "interaccion": round(inter, 3), "base": j, "combo": k,
                        "N_kN": round(N, 2), "Mx_kNm": round(Mx, 3), "My_kNm": round(My, 3), "V_kN": round(V, 2), "T_esquina_kN": round(T_esq, 2)}
    # placa: voladizo desde la cara del poste a la fila de anclajes, ancho efectivo 2 x distancia (45 grados) por anclaje
    m_pl = (s / 2 - 40.0)                                      # mm, cara del SHS80 a la linea de anclajes
    T_max = max(max(0.0, -cc[2] / 4000 + abs(cc[4]) / 1e6 / ((s / 2 + 0.9 * bp / 2) / 1000) / 2 + abs(cc[3]) / 1e6 / ((s / 2 + 0.9 * bp / 2) / 1000) / 2)
                for cs in comb.values() for cc in cs.values())
    b_ef = min(2 * m_pl + 2 * 0, bp / 2)
    M_pl = T_max * 1000 * m_pl                                  # N mm por anclaje
    t_req = math.sqrt(4 * M_pl / (0.9 * 250.0 * max(b_ef, 1)))
    return {"d": d, "hef": hef, "placa_mm": bp, "s_mm": s, "t_placa_mm": tp, "cap_kN": {k: round(v_, 2) for k, v_ in cap.items()},
            "peor": peor, "placa": {"T_max_anclaje_kN": round(T_max, 2), "voladizo_mm": m_pl, "b_ef_mm": round(b_ef, 1), "t_req_mm": round(t_req, 1),
                                     "cumple": t_req <= tp}}


opciones = [verificar(d, h, bp, s, tp) for (d, h, bp, s, tp) in ((12, 100, 200, 130, 12), (12, 110, 220, 150, 12), (12, 110, 250, 170, 12),
                                                               (16, 125, 250, 170, 12), (16, 150, 250, 170, 12))]
# adherencia caracteristica en concreto fisurado (con calificacion sismica) que el producto debe garantizar para D/C <= 1
tau_base = tau_cr
for o in opciones:
    lo, hi = tau_base, 20.0
    for _ in range(40):
        tau_cr = (lo + hi) / 2
        if verificar(o["d"], o["hef"], o["placa_mm"], o["s_mm"], o["t_placa_mm"])["peor"]["DC"] <= 1.0:
            hi = tau_cr
        else:
            lo = tau_cr
    tau_cr = hi
    oo = verificar(o["d"], o["hef"], o["placa_mm"], o["s_mm"], o["t_placa_mm"])
    o["tau_cr_requerido_MPa"] = round(hi, 2)
    o["con_tau_requerido"] = {"DC": oo["peor"]["DC"], "gobierna": oo["peor"]["combo"], "DC_N": oo["peor"]["DC_N"]}
    tau_cr = tau_base
for o in opciones:
    print("M%d hef %d placa %dx%d s %d: DC %.3f (N %.3f V %.3f, %s %s) | t_req placa %.1f mm (t %d) | T esquina %.2f kN" % (
        o["d"], o["hef"], o["placa_mm"], o["t_placa_mm"], o["s_mm"], o["peor"]["DC"], o["peor"]["DC_N"], o["peor"]["DC_V"], o["peor"]["base"],
        o["peor"]["combo"], o["placa"]["t_req_mm"], o["t_placa_mm"], o["peor"]["T_esquina_kN"]))

# ------------------------------------------------------------------ soldadura poste-placa (filete en todo el contorno del SHS80)
a, L = 3.0, 80.0
Aw = 4 * L * a * 0.707                                          # mm2 (garganta efectiva)
Sw = (L ** 2 + L ** 2 / 3) * a * 0.707                          # modulo de linea de un cuadrado (b d + d^2/3) x garganta
peor_w = 0
for cs in comb.values():
    for k, (F1, F2, F3, M1, M2, M3) in cs.items():
        if k.startswith(("U4O", "U5O")):
            continue                                               # la soldadura se verifica con las combinaciones sin Om0
        f = abs(F3) / Aw + (abs(M1) + abs(M2)) / Sw + math.hypot(F1, F2) / Aw
        peor_w = max(peor_w, f)
for e in ("SX", "SY"):
    for j in bases:
        rj = R[j]
        for sg in (1, -1):
            for dfac in (1.2 + v, 0.9 - v):
                cc = [dfac * rj["DEAD"][i] + (rj["BELT"][i] + rj["TORQ"][i] if dfac > 1 else 0) + sg * rj[e][i] for i in range(6)]
                peor_w = max(peor_w, abs(cc[2]) / Aw + (abs(cc[3]) + abs(cc[4])) / Sw + math.hypot(cc[0], cc[1]) / Aw)
phiRn = 0.75 * 0.6 * 482.0                                     # AISC J2.4, E70XX, MPa sobre la garganta
res = {"fuente_reacciones": "anexo_sap/tablas_sap/K34_K32_SISMO_E030_api/Joint_Reactions.csv", "bases": bases, "Om0": OM0,
       "vertical_sismico": round(v, 3), "opciones_anclaje": opciones,
       "soldadura": {"filete_mm": a, "esfuerzo_max_MPa": round(peor_w, 1), "phiRn_MPa": round(phiRn, 1), "DC": round(peor_w / phiRn, 3)}}
json.dump(res, open(os.path.join(B, "resultados_cabina", "CALCULO_PLACAS_BASE_K32.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("soldadura a3 en todo el contorno: %.1f MPa frente a %.1f (D/C %.3f)" % (peor_w, phiRn, peor_w / phiRn))
print("bases", bases, "| peor sin sismo/sismo por base: ", {j: sorted(comb[j])[:2] for j in bases})
