#!/usr/bin/env python3
"""
Red hidraulica de la configuracion propuesta (24 boquillas: R05 de 22 + dos boquillas nuevas C2,
una por lado exterior, en una T al final del pie DN15 de INF_EXT).

Misma metodologia y mismas constantes que calculo_red_22.py (copiadas sin cambios):
  q = Kq*sqrt(p); Darcy-Weisbach + Swamee-Jain; Km = n*fT; p_C se ajusta hasta que la toma
  mas desfavorable tenga 4 bar; altura de bomba por Bernoulli deposito -> C; NPSH disponible.

Diferencia: el solucionador admite ramificaciones (arbol), necesario para la T del pie.
Control: el mismo solucionador reproduce la red de 22 (resultados_22.json).

HIPOTESIS C2 (las mismas que la nota C8 del 07/10/2026):
  C2-1 las dos boquillas nuevas tienen la misma Kq que la VeeJet 5020;
  C2-2 los 0,13 m de DN15 del pie son comunes hasta la T (con la reduccion y el codo de 45 grados);
  C2-3 cada salida de la T conserva el 30 fT terminal;
  C2-4 la derivacion nueva anade 0,05 m de DN15 con K_T = 1; el paso recto de la T, K_T = 0;
  C2-5 la boquilla nueva queda a la misma cota que INF_EXT (Z855).

Uso: python calculo_red_24.py   ->  resultados_24.json
"""
import json
import math

g = 9.81
rho = 982.1203530851709
mu = 4.5227e-4
nu = mu / rho
z_site = 2335.0
patm = 101325 * (1 - 2.25577e-5 * z_site) ** 5.25588
gpm = 3.785411784e-3 / 60
Kq = 2.0 * gpm / math.sqrt(40 * 6894.757)
p_n = 4.0e5
q_n = Kq * math.sqrt(p_n)
eps = 0.045e-3
ID = {"DN15": 17.08e-3, "DN25": 27.86e-3, "DN40": 42.76e-3, "DN50": 54.76e-3}
fT = {"DN15": 0.027, "DN25": 0.023, "DN40": 0.020, "DN50": 0.019}


def seg(Q, DN, L, K):
    D = ID[DN]
    A = math.pi * D ** 2 / 4
    v = Q / A
    Re = v * D / nu
    f = 0.25 / (math.log10(eps / (3.7 * D) + 5.74 / Re ** 0.9)) ** 2 if Re > 0 else 0.0
    return dict(v=v, Re=Re, f=f, hL=(f * L / D + K) * v ** 2 / (2 * g))


def bomba(Q, pC, zC=1.770, dp_union=0.30e5, dp_filtro=0.20e5):
    est = seg(Q, "DN40", 14.0, 6 * 0.60 + 2.00 + 0.06)
    rot = seg(Q, "DN40", 1.75, 30 * fT["DN40"])
    suc = seg(Q, "DN50", 1.5, 0.50 + 30 * fT["DN50"] + 3 * fT["DN50"])
    zS = 1.00
    vC = est["v"]
    partes = {
        "presion_en_C_m": pC / (rho * g),
        "desnivel_zC_menos_zS_m": zC - zS,
        "linea_estacionaria_m": est["hL"],
        "alimentacion_distribuidor_m": rot["hL"],
        "succion_m": suc["hL"],
        "union_rotativa_y_filtro_m": (dp_union + dp_filtro) / (rho * g),
        "carga_cinetica_C_m": vC ** 2 / (2 * g),
    }
    H = sum(partes.values())
    Ph = rho * g * Q * H
    return dict(partes=partes, H_m=H, Q_Lmin=Q * 60000, v_DN40=vC, P_h_W=Ph, P_eje_W=Ph / 0.55,
                P_el_W=Ph / 0.55 / 0.85, h_suc_m=suc["hL"])


def resolver_arbol(tramos, zC=1.770, iters=200):
    """tramos: lista de (nombre, nodo_padre, nodo_hijo, DN, L, K, z_hijo, [(tag, multiplicidad)]).
    El nodo raiz es "C". El caudal de un tramo es la suma de las boquillas del subarbol del hijo
    (un solo lado exterior; la multiplicidad solo entra en el caudal total)."""
    hijos = {}
    for t in tramos:
        hijos.setdefault(t[1], []).append(t)

    def boquillas_debajo(nodo):
        out = []
        for t in hijos.get(nodo, []):
            out += [tag for tag, _ in t[7]] + boquillas_debajo(t[2])
        return out

    abajo = {t[2]: [tag for tag, _ in t[7]] + boquillas_debajo(t[2]) for t in tramos}
    q = {tag: q_n for t in tramos for tag, _ in t[7]}
    pC = p_n
    hist = []
    for it in range(iters):
        P = {"C": pC}
        Z = {"C": zC}
        p, info = {}, []
        pendientes = list(hijos.get("C", []))
        while pendientes:
            t = pendientes.pop(0)
            nombre, pad, hij, DN, L, K, zf, noz = t
            Qt = sum(q[tag] for tag in abajo[hij])
            s = seg(Qt, DN, L, K)
            P[hij] = P[pad] - rho * g * (s["hL"] + (zf - Z[pad]))
            Z[hij] = zf
            info.append(dict(tramo=nombre, DN=DN, L_m=L, sumK=K, Q_Lmin=Qt * 60000, v_m_s=s["v"],
                             Re=s["Re"], f=s["f"], hL_m=s["hL"], z_fin_m=zf))
            for tag, _ in noz:
                p[tag] = P[hij]
            pendientes += hijos.get(hij, [])
        pmin = min(p.values())
        Qtot = sum(q[tag] * m for t in tramos for tag, m in t[7])
        hist.append((it, pC / 1e5, pmin / 1e5, Qtot * 60000))
        if abs(pmin - p_n) < 1e-3 and it > 2:
            break
        pC += p_n - pmin
        q = {tag: Kq * math.sqrt(p[tag]) for tag in p}
    mult = {tag: m for t in tramos for tag, m in t[7]}
    return dict(pC=pC, p=p, q=q, mult=mult, Qtot=Qtot, tramos=info, hist=hist)


fTd = lambda DN: fT[DN]
v_R04 = (54.70599032700168 / 60000) / (math.pi * ID["DN25"] ** 2 / 4)
K_lanza_eq = 0.9877540905619169 / (v_R04 ** 2 / (2 * g))
Kv = 3 * fT["DN40"]

exterior_comun = [
    ("C-S1", "C", "S1", "DN50", 0.5360, 60 * fTd("DN50"), 1.7400, [("S1_SUP_1", 2)]),
    ("S1-S2", "S1", "S2", "DN50", 0.0880, 20 * fTd("DN50"), 1.7400, [("S2_SUP_2", 2)]),
    ("S2-E0", "S2", "E0", "DN50", 0.2760, 50 * fTd("DN50"), 1.7400, []),
    ("E0-E1 (con valvula de ramal)", "E0", "E1", "DN40", 0.3940, 20 * fTd("DN40") + Kv, 1.3463, [("E1_LAT_4", 2)]),
    ("E1-E2", "E1", "E2", "DN40", 0.0821, 20 * fTd("DN40"), 1.2642, [("E2_LAT_3", 2)]),
    ("E2-E3", "E2", "E3", "DN40", 0.0821, 20 * fTd("DN40"), 1.1821, [("E3_LAT_2", 2)]),
    ("E3-E4", "E3", "E4", "DN40", 0.0821, 20 * fTd("DN40"), 1.1000, [("E4_LAT_1", 2)]),
    ("E4-E5", "E4", "E5", "DN40", 0.0600, 20 * fTd("DN40"), 1.0400, [("E5_LAT_5", 2)]),
    ("E5-extension", "E5", "E5x", "DN40", 0.0960, 0.0, 0.9440, []),
]
lanza = [
    ("C-I0 (red fija, V-AIS, flexible, cuello)", "C", "I0", "DN25", 0.0, K_lanza_eq, 1.7000, []),
    ("I0-I1", "I0", "I1", "DN25", 0.3618, 20 * fTd("DN25"), 1.3382, [("I1_INT_5", 1)]),
    ("I1-I2", "I1", "I2", "DN25", 0.0954, 20 * fTd("DN25"), 1.2428, [("I2_INT_4", 1)]),
    ("I2-I3", "I2", "I3", "DN25", 0.0953, 20 * fTd("DN25"), 1.1475, [("I3_INT_3", 1)]),
    ("I3-I4", "I3", "I4", "DN25", 0.0953, 20 * fTd("DN25"), 1.0522, [("I4_INT_2", 1)]),
    ("I4-I5", "I4", "I5", "DN25", 0.0954, 20 * fTd("DN25"), 0.9568, [("I5_INT_1", 1)]),
    ("I5-I6 (pie 25 grados)", "I5", "I6", "DN25", 0.2500, 60 * fTd("DN25"), 0.8500, [("I6_INF_INT", 1)]),
]
# Control: red de 22 con el solucionador de arbol (pie sin T, igual que calculo_red_22.py)
red22 = exterior_comun + [
    ("reduccion + pie DN15", "E5x", "E6", "DN15", 0.1300, 0.5 + 16 * fTd("DN15") + 30 * fTd("DN15"), 0.8550,
     [("E6_INF_EXT", 2)]),
] + lanza
# Red de 24: pie comun hasta la T (sin el 30 fT terminal), paso recto a INF_EXT y derivacion a C2
red24 = exterior_comun + [
    ("reduccion + pie DN15 comun hasta la T", "E5x", "T", "DN15", 0.1300, 0.5 + 16 * fTd("DN15"), 0.8550, []),
    ("T paso recto -> INF_EXT", "T", "E6", "DN15", 0.0, 0.0 + 30 * fTd("DN15"), 0.8550, [("E6_INF_EXT", 2)]),
    ("T derivacion -> C2", "T", "E7", "DN15", 0.0500, 1.0 + 30 * fTd("DN15"), 0.8550, [("E7_C2_nueva", 2)]),
] + lanza

# NPSH: misma pv implicita que calculo_red_22.py (deducida del caso de 19)
ramas19_Q = None
pv_back = None


def npsh(b):
    return (patm - pv_back) / (rho * g) + 0.5 - b["h_suc_m"]


if __name__ == "__main__":
    # pv implicita: se recalcula como en calculo_red_22.py a partir del caso de 19
    ramas19 = [
        ("C-S1", "C", "S1", "DN50", 0.5360, 1.140, 1.7400, [("S1", 2)]),
        ("S1-S2", "S1", "S2", "DN50", 0.0880, 0.380, 1.7400, [("S2", 2)]),
        ("S2-E0", "S2", "E0", "DN50", 0.2760, 0.950, 1.7400, []),
        ("E0-E1", "E0", "E1", "DN40", 0.3940, 0.400, 1.3460, [("E1", 2)]),
        ("E1-E2", "E1", "E2", "DN40", 0.0820, 0.400, 1.2640, [("E2", 2)]),
        ("E2-E3", "E2", "E3", "DN40", 0.0820, 0.400, 1.1820, [("E3", 2)]),
        ("E3-E4", "E3", "E4", "DN40", 0.0820, 0.400, 1.1000, [("E4", 2)]),
        ("E4-E5", "E4", "E5", "DN40", 0.0300, 0.400, 1.0700, [("E5", 2)]),
        ("C-I0", "C", "I0", "DN25", 0.2800, 2.070, 1.7400, []),
        ("I0-I1", "I0", "I1", "DN25", 0.4018, 0.460, 1.3382, [("I1", 1)]),
        ("I1-I2", "I1", "I2", "DN25", 0.0954, 0.460, 1.2428, [("I2", 1)]),
        ("I2-I3", "I2", "I3", "DN25", 0.0953, 0.460, 1.1475, [("I3", 1)]),
        ("I3-I4", "I3", "I4", "DN25", 0.0953, 0.460, 1.0522, [("I4", 1)]),
        ("I4-I5", "I4", "I5", "DN25", 0.0954, 0.460, 0.9568, [("I5", 1)]),
    ]
    r19 = resolver_arbol(ramas19)
    b19 = bomba(r19["Qtot"], r19["pC"])
    pv_back = patm - rho * g * (5.51249 + b19["h_suc_m"])

    salida = {}
    for nombre, red in (("22", red22), ("24", red24)):
        r = resolver_arbol(red)
        b = bomba(r["Qtot"], r["pC"])
        qs = {k: v * 60000 for k, v in r["q"].items()}
        salida[nombre] = dict(
            Q_total_Lmin=r["Qtot"] * 60000, pC_bar=r["pC"] / 1e5, H_m=b["H_m"],
            P_h_kW=b["P_h_W"] / 1e3, P_eje_kW=b["P_eje_W"] / 1e3, P_el_kW=b["P_el_W"] / 1e3,
            NPSHa_m=npsh(b), v_DN40_m_s=b["v_DN40"],
            boquillas=[dict(toma=k, multiplicidad=r["mult"][k], p_bar=r["p"][k] / 1e5, q_Lmin=qs[k]) for k in r["p"]],
            tramos=r["tramos"], partes_altura_m=b["partes"], iteraciones=r["hist"])
        print("%s boquillas: Q = %.3f L/min, pC = %.5f bar, H = %.3f m, P_h = %.3f kW, P_eje = %.3f kW, "
              "P_el = %.3f kW, NPSHa = %.3f m"
              % (nombre, r["Qtot"] * 60000, r["pC"] / 1e5, b["H_m"], b["P_h_W"] / 1e3, b["P_eje_W"] / 1e3,
                 b["P_el_W"] / 1e3, npsh(b)))
    for bq in salida["24"]["boquillas"]:
        print("  %-13s x%d  p = %.5f bar  q = %.3f L/min" % (bq["toma"], bq["multiplicidad"], bq["p_bar"], bq["q_Lmin"]))
    for t in salida["24"]["tramos"]:
        if t["DN"] == "DN15":
            print("  %-40s Q = %.3f L/min  v = %.3f m/s" % (t["tramo"], t["Q_Lmin"], t["v_m_s"]))
    salida["hipotesis_C2"] = [l.strip() for l in __doc__.splitlines() if l.strip().startswith("C2-")]
    json.dump(salida, open("resultados_24.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
