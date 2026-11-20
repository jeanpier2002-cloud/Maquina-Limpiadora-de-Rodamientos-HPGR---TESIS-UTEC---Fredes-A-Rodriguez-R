# -*- coding: utf-8 -*-
"""Soporte superior (R07 V17B): resumen de los casos K de la cabina como estructura (SoporteCabinaSAP.cs) y chequeos a mano.
Entradas: resultados_cabina/K*.json. Salidas: resultados_cabina/RESUMEN_CABINA.csv y resultados_cabina/CHEQUEOS_MANO.json."""
import csv
import glob
import json
import math
import os

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(B, "resultados_cabina")
L_VIGA = 4040.0

filas = []
for f in sorted(glob.glob(os.path.join(R, "K*.json")), key=lambda p: int(os.path.basename(p).split("_")[0][1:])):
    d = json.load(open(f, encoding="utf-8"))
    hz = lambda u: math.hypot(u[0], u[1])
    s2 = [k for k in d["cojinetes"] if k.startswith("S2")]
    pand = [x for v in d["pandeo"].values() for x in v]
    pos = [x for x in pand if x > 0]
    neg = [x for x in pand if x < 0]
    vm = d.get("chapa_vm_MPa", {})
    vm_s = max((v for c, z in vm.items() if c.startswith("S") for v in z.values()), default=None)
    vm_u = max((v for c, z in vm.items() if c.startswith("U") for v in z.values()), default=None)
    flecha = d["flecha_apoyo_S1_mm"]
    filas.append({
        "caso": d["caso"], "opciones": d["opciones"],
        "masa_barras_kg": round(d["masa_barras_kg"], 1), "masa_chapa_kg": round(d["masa_chapa_kg"], 1),
        "DC_max": round(d.get("DC_max", float("nan")), 3), "DC_seccion": d.get("DC_seccion", ""), "DC_combo": d.get("DC_combo", ""),
        "f1_Hz": round(d["frecuencias_Hz"][0], 2), "f2_Hz": round(d["frecuencias_Hz"][1], 2),
        "cojinete_sup_S2_max_mm": round(max(hz(d["cojinetes"][k]["sup"]) for k in s2), 3),
        "cojinete_inf_S2_max_mm": round(max(hz(d["cojinetes"][k]["inf"]) for k in s2), 3),
        "flecha_apoyo_S1_mm": round(flecha, 3), "L_sobre_flecha": round(L_VIGA / flecha) if flecha > 0 else "",
        "flecha_apoyo_S1_NL_mm": round(d["flecha_apoyo_S1_NL_mm"], 1) if "flecha_apoyo_S1_NL_mm" in d else "",
        "techo_w_max_S1_mm": round(d.get("techo_w_max_S1_mm", float("nan")), 2),
        "muro_desplome_S1_mm": round(d.get("muro_desplome_max_S1_mm", float("nan")), 2),
        "pandeo_min_positivo": round(min(pos), 3) if pos else "", "pandeo_min_negativo": round(max(neg), 3) if neg else "",
        "chapa_vm_servicio_MPa": round(vm_s, 1) if vm_s is not None else "", "chapa_vm_ultimo_MPa": round(vm_u, 1) if vm_u is not None else "",
        "reac_Fz_max_S1_N": round(d["reacciones"]["S1"]["Fz_max"]), "reac_Fh_max_U3_N": round(max(d["reacciones"][c]["Fh_max"] for c in ("U3_AXP", "U3_AYP"))),
        "reac_M_max_U3_Nmm": round(max(d["reacciones"][c]["M_max"] for c in ("U3_AXP", "U3_AYP"))),
    })
with open(os.path.join(R, "RESUMEN_CABINA.csv"), "w", newline="", encoding="utf-8") as fo:
    w = csv.DictWriter(fo, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)

# ---- chequeos a mano (Timoshenko y Woinowsky-Krieger, placa apoyada; EN 1993-1-5 §6.4) ----
E, nu, rho, g = 193000.0, 0.29, 8000e-9, 9.81e-3   # inox 304: MPa, kg/mm3, N/kg en mm... g en N/kg = 9.81 -> q en N/mm2 abajo
a = 4040.0                                           # luz menor del techo (mm)
P = 1789 + 412 + 304 + 2266                          # cuerpo del cartucho en S1 (N), como en el modelo
D = lambda t: E * t ** 3 / (12 * (1 - nu ** 2))
alfa_P, alfa_q = 0.01160, 0.00406                    # placa cuadrada apoyada: carga central y carga uniforme
w_P = lambda t: alfa_P * P * a ** 2 / D(t)
w_q = lambda t: alfa_q * (t * rho * 9.81) * a ** 4 / D(t)
t_req = (alfa_P * P * a ** 2 / (a / 1000.0) * 12 * (1 - nu ** 2) / E) ** (1 / 3)
# abolladura por carga concentrada en el borde superior del muro, sin rigidizadores (k_F = 6 + 2 (h/a)^2 con a grande)
h_w = 2610.0
F_cr = lambda t, kF=6.0: 0.9 * kF * E * t ** 3 / h_w
# correas del techo de la cabina (la chapa plana no se sostiene sola): cubierta no transitable de categoria H de EN 1991-1-1
# (q_k 0,4 kN/m2 y Q_k 1,0 kN, valores recomendados), luz 4 040 entre muros, separacion 0,8 m, flecha <= L/200 [HIPOTESIS]
s_c, q_k, Q_k, g_chapa = 800.0, 0.4e-3, 1000.0, 1.5 * 8000e-9 * 9.81   # mm, N/mm2, N, N/mm2
q_lin = (q_k + g_chapa) * s_c                                          # N/mm por correa
I_req = max(5 * q_lin * a ** 4 / (384 * E * a / 200), Q_k * a ** 3 / (48 * E * a / 200))
M_Ed = 1.5 * max(q_k * s_c * a ** 2 / 8, Q_k * a / 4) + 1.35 * g_chapa * s_c * a ** 2 / 8
rhs = lambda h, b, t: ((b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12, (2 * (h + b) - 4 * t) * t * 7.93e-3)  # I (mm4), kg/m
I_8040_3, kg_8040_3 = rhs(80, 40, 3)
n_correas = math.ceil(4140 / s_c) - 1
correas = {"luz_mm": a, "separacion_mm": s_c, "q_lineal_N_mm": round(q_lin, 3), "I_requerido_mm4": round(I_req),
           "M_Ed_Nmm": round(M_Ed), "seccion": "RHS 80x40x3 inox 304", "I_mm4": round(I_8040_3),
           "sigma_MPa": round(M_Ed / (I_8040_3 / 40), 1), "D_C_flexion": round(M_Ed / (I_8040_3 / 40) / (205 / 1.1), 2),
           "cantidad": n_correas, "masa_kg": round(n_correas * a / 1000 * kg_8040_3, 1),
           "fuente": "EN 1991-1-1 tabla 6.10 (cubierta H, valores recomendados); EN 1993-1-4 (inox); flecha L/200 [HIPOTESIS]"}
mano = {
    "fuente": "Timoshenko y Woinowsky-Krieger, Theory of Plates and Shells, tablas 8 y 23 (placa cuadrada apoyada, nu 0,3); EN 1993-1-5 §6.4",
    "P_cartucho_N": P,
    "techo_plano": {str(t): {"w_carga_central_mm": round(w_P(t), 1), "w_peso_propio_mm": round(w_q(t), 1)} for t in (1.5, 3.0, 6.0)},
    "t_requerido_L1000_mm": round(t_req, 1),
    "masa_techo_con_t_requerido_kg": round(a * 4140 * t_req * rho, 0),
    "muro_Fcr_borde_N": {str(t): round(F_cr(t)) for t in (1.5, 2.0, 3.0)},
    "correas_techo": correas,
    "nota": "Lineal: con grandes desplazamientos la membrana reduce la flecha, pero el techo plano sigue sin servir de apoyo.",
}
json.dump(mano, open(os.path.join(R, "CHEQUEOS_MANO.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for r in filas:
    print(r["caso"], r["masa_barras_kg"], r["DC_max"], r["f1_Hz"], r["cojinete_sup_S2_max_mm"], r["flecha_apoyo_S1_mm"], r["techo_w_max_S1_mm"], r["pandeo_min_positivo"], r["chapa_vm_ultimo_MPa"])
print(json.dumps(mano, ensure_ascii=False))
