# -*- coding: utf-8 -*-
"""Cargas y valores de control (a mano) del modelo lanza–colgador para SOLIDWORKS, en el marco SW: (X, Y, Z)_SW = (−x, z, y)_CAD.

Estudios:
  CHORROS              reacción R = −ṁ·v·e de las 6 boquillas de la lanza (boquillas_O7_C2.json de Jean), en su copla.
  GIRO                 rotor a 1,7 rpm (0,178 rad/s; R03) con aceleración angular de 0,178 rad/s² (rampa de 1 s, HIPÓTESIS).
  PESO                 gravedad (peso propio del acero; el agua no se incluye).
  SERVICIO             CHORROS + GIRO + PESO.
  GOLPE_LANZA_RADIAL   200 N en el pie de la lanza hacia el eje del rotor (interfaz de la guía de R03, línea 163 de su memoria).
  GOLPE_LANZA_TANG     200 N en el pie, en dirección tangencial (de giro).
  MANGUERA_100N        100 N hacia abajo en el racor de la manguera (arrastre supuesto de R03, línea 152): carga del «cuello».
  U_GOLPE_FUERA_PLANO  1 000 N en el brazo A a Z1400, fuera del plano de la U (hipótesis de R03 usada en el estudio de la U),
                       aplicado como carga remota en la cara de la brida central A (la brida del brazo va abulonada a ella).
  U_GOLPE_EN_PLANO     el mismo golpe en el plano de la U, hacia el centro.
Controles estáticamente determinados (sondas): lanza a Z1450 (entre el carro y la boquilla más alta) y transversal a x = 240.
Escribe geometria/cuerpos.csv, geometria/cargas.csv y geometria/controles.json."""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
B = Path(__file__).resolve().parents[1]
HO = B.parents[2]
BOQ = HO / "01_DISENO_VIGENTE/cfd/CFD_ANSYS/02_ANALISIS/cara_inferior/alternativas_2026-10-07/PAQUETE_JEAN_O7_C2/boquillas_O7_C2.json"
geo = json.load(open(B / "geometria/geometria_lanza.json", encoding="utf-8"))


def sw(v):
    """Vector o punto del CAD (x, y, z) al marco SW (−x, z, y)."""
    return np.array([-v[0], v[2], v[1]], dtype=float)


with open(B / "geometria/cuerpos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["nombre", "vol_mm3", "cx", "cy", "cz"])
    for c in geo["cuerpos"]:
        w.writerow([c["nombre"], c["vol_mm3"]] + c["centro_sw_mm"])

bq = json.load(open(BOQ, encoding="utf-8"))["boquillas"]
copla = {"INT_1": "COPLA_INT_1", "INT_2": "COPLA_INT_2", "INT_3": "COPLA_INT_3", "INT_4": "COPLA_INT_4", "INT_5": "COPLA_INT_5",
         "INF_INT": "COPLA_INF_INT"}
cargas, chorros = [], []
for k, cop in copla.items():
    b = bq[k]
    p = np.array(b["vertice_m"]) * 1000.0
    e = np.array(b["eje"]) / np.linalg.norm(b["eje"])
    R = -b["mdot_kg_s"] * b["v_m_s"] * e
    chorros.append((p, R))
    cargas.append(["CHORRO_" + k, "CHORROS|SERVICIO", cop] + list(sw(p)) + list(sw(R)))
P_PIE = np.array([0.0, 250.0, 838.0])                  # pie de la lanza (centro del codo inferior, CAD)
cargas.append(["GOLPE_LANZA_RADIAL", "GOLPE_LANZA_RADIAL", "PIE_CODO_90"] + list(sw(P_PIE)) + list(sw([0, -200.0, 0])))
cargas.append(["GOLPE_LANZA_TANG", "GOLPE_LANZA_TANG", "PIE_CODO_90"] + list(sw(P_PIE)) + list(sw([200.0, 0, 0])))
P_RAC = np.array([150.0, 500.0, 1558.5])              # centro del racor de la manguera (CAD)
cargas.append(["MANGUERA_100N", "MANGUERA_100N", "RACOR"] + list(sw(P_RAC)) + list(sw([0, 0, -100.0])))
P_U = np.array([900.0, 0.0, 1400.0])                  # golpe del brazo A (CAD)
cargas.append(["U_GOLPE_FUERA_PLANO", "U_GOLPE_FUERA_PLANO", "BRIDA_A"] + list(sw(P_U)) + list(sw([0, -1000.0, 0])))
cargas.append(["U_GOLPE_EN_PLANO", "U_GOLPE_EN_PLANO", "BRIDA_A"] + list(sw(P_U)) + list(sw([-1000.0, 0, 0])))
with open(B / "geometria/cargas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["nombre", "estudios", "cuerpo", "x", "y", "z", "fx", "fy", "fz"])
    for c in cargas:
        w.writerow(c[:3] + ["%.4f" % v for v in c[3:]])

# ---------------- controles a mano (secciones estáticamente determinadas)
def tubo(D, t):
    di = D - 2 * t
    A = math.pi / 4 * (D ** 2 - di ** 2); I = math.pi / 64 * (D ** 4 - di ** 4)
    return A, I / (D / 2)


A25, W25 = tubo(33.4, 2.77)
A50, W50 = tubo(60.3, 2.77)


def vm_seccion(cargas_pf, c, eje):
    """Von Mises máx de flexión + axial + torsión en la sección de centro c y eje 'eje' (0 = x, 2 = z), cargas al lado libre."""
    F, M = np.zeros(3), np.zeros(3)
    for p, f in cargas_pf:
        F += f; M += np.cross(p - c, f)
    ax = [0, 1, 2]; ax.remove(eje)
    Mb = math.hypot(M[ax[0]], M[ax[1]]); T = abs(M[eje]); N = F[eje]
    return Mb, T, N


ctrl = {}
c_l = np.array([0.0, 250.0, 1450.0])
for nom, cp in (("CHORROS", chorros), ("GOLPE_LANZA_RADIAL", [(P_PIE, np.array([0, -200.0, 0]))]),
                ("GOLPE_LANZA_TANG", [(P_PIE, np.array([200.0, 0, 0]))])):
    Mb, T, N = vm_seccion(cp, c_l, 2)
    s = Mb / W25 + abs(N) / A25; tau = T / (2 * W25)
    ctrl["lanza_Z1450_" + nom] = {"M_flexion_Nm": round(Mb / 1000, 3), "sigma_MPa": round(s, 3), "von_Mises_MPa": round(math.sqrt(s ** 2 + 3 * tau ** 2), 3)}
c_t = np.array([240.0, 0.0, 1740.0])
for nom, f in (("U_GOLPE_FUERA_PLANO", np.array([0, -1000.0, 0])), ("U_GOLPE_EN_PLANO", np.array([-1000.0, 0, 0]))):
    Mb, T, N = vm_seccion([(P_U, f)], c_t, 0)
    s = Mb / W50 + abs(N) / A50; tau = T / (2 * W50)
    ctrl["transversal_x240_" + nom] = {"M_flexion_Nm": round(Mb / 1000, 1), "T_Nm": round(T / 1000, 1), "N_N": round(N, 0),
                                       "von_Mises_MPa": round(math.sqrt(s ** 2 + 3 * tau ** 2), 2)}
ctrl["nota"] = ("Von Mises de viga (M/W, N/A, T/2W) en la fibra extrema; la sonda de SOLIDWORKS toma el máximo de los nodos de la "
                "sección ±6 mm, que en flexión pura debería coincidir dentro de pocos %.")
json.dump(ctrl, open(B / "geometria/controles.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(ctrl, ensure_ascii=False, indent=1))
for c in cargas:
    print(c[0], c[2], [round(v, 2) for v in c[3:]])
