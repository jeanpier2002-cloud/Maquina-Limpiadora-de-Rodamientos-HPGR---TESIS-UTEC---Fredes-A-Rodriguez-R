#!/usr/bin/env python3
"""
Recalculo hidraulico del subsistema de aspersion con la geometria oficial R05 (22 boquillas),
con la MISMA metodologia de "CALCULOS_DESARROLLO_ANALITICO_ASPERSION.pdf" (Calculos_aspersion.md):
  - q = Kq * sqrt(p) por boquilla (VeeJet H3/8U-5020, 2 gpm @ 40 psi)
  - Darcy-Weisbach + Swamee-Jain (eps = 0,045 mm), Km = n * fT (20 fT paso, 60 fT salida de
    derivacion, 30 fT codo), estaciones de calculo por tramo
  - aproximaciones sucesivas: p_C se ajusta hasta que la toma mas desfavorable tenga 4 bar
  - altura de bomba por Bernoulli deposito -> C; potencia; NPSH disponible

Paso 1 (validacion): reproduce el caso de 19 boquillas del documento (Tabla 4) -> 173,99 L/min, 50,75 m.
Paso 2: red R05 de 22 boquillas (ver HIPOTESIS_R05 abajo). Salida: resultados_22.json y tablas.

Uso: python calculo_red_22.py
"""
import json
import math

g = 9.81
# ---------------------------------------------------------------- fluido (documento §1.1, agua 62 C)
rho = 982.1203530851709          # kg/m3 (INPUTS_CALCULOS_ASPERSION.json / PARAMETROS_CFD.json)
mu = 4.5227e-4                   # Pa s  (CLAUDE.md)
nu = mu / rho
z_site = 2335.0
patm = 101325 * (1 - 2.25577e-5 * z_site) ** 5.25588      # ISO 2533 (documento §1.10)
# ---------------------------------------------------------------- boquilla (documento §1.2)
gpm = 3.785411784e-3 / 60
Kq = 2.0 * gpm / math.sqrt(40 * 6894.757)                  # m3/s/Pa^0.5
p_n = 4.0e5
q_n = Kq * math.sqrt(p_n)
# ---------------------------------------------------------------- tuberia (documento §1.5; R05 tubo)
eps = 0.045e-3
ID = {"DN15": 17.08e-3, "DN25": 27.86e-3, "DN40": 42.76e-3, "DN50": 54.76e-3}
fT = {"DN15": 0.027, "DN25": 0.023, "DN40": 0.020, "DN50": 0.019}   # DN15: Crane TP-410 [VERIFICAR]


def seg(Q, DN, L, K):
    D = ID[DN]
    A = math.pi * D ** 2 / 4
    v = Q / A
    Re = v * D / nu
    f = 0.25 / (math.log10(eps / (3.7 * D) + 5.74 / Re ** 0.9)) ** 2 if Re > 0 else 0.0
    return dict(v=v, Re=Re, f=f, hL=(f * L / D + K) * v ** 2 / (2 * g))


def resolver(ramas, zC=1.770, iters=200):
    """ramas: {nombre: [ (tramo, DN, L, K, z_fin, boquillas_en_z_fin [(tag, n_equivalentes)] ), ...] }
    Cada rama sale de C. El caudal de cada tramo es la suma de las boquillas aguas abajo en esa rama.
    n_equivalentes: numero de boquillas identicas en ese punto (2 lados exteriores simetricos se
    modelan con una rama y multiplicidad 2 en el caudal total)."""
    q = {}
    for r in ramas.values():
        for t in r:
            for tag, _ in t[5]:
                q[tag] = q_n
    pC = p_n
    hist = []
    for it in range(iters):
        p = {}
        tramos = []
        for nombre, r in ramas.items():
            P, z = pC, zC
            for k, (tr, DN, L, K, zf, noz) in enumerate(r):
                Qt = sum(q[tag] for t2 in r[k:] for tag, _ in t2[5])
                s = seg(Qt, DN, L, K)
                P = P - rho * g * (s["hL"] + (zf - z))
                z = zf
                tramos.append(dict(rama=nombre, tramo=tr, DN=DN, L_m=L, sumK=K, Q_Lmin=Qt * 60000,
                                   v_m_s=s["v"], Re=s["Re"], f=s["f"], hL_m=s["hL"], z_fin_m=zf))
                for tag, _ in noz:
                    p[tag] = P
        pmin = min(p.values())
        Qtot = sum(q[tag] * mult for r in ramas.values() for t in r for tag, mult in t[5])
        hist.append((it, pC / 1e5, pmin / 1e5, Qtot * 60000))
        if abs(pmin - p_n) < 1e-3 and it > 2:
            break
        pC += p_n - pmin
        q = {tag: Kq * math.sqrt(p[tag]) for tag in p}
    return dict(pC=pC, p=p, q=q, Qtot=Qtot, tramos=tramos, hist=hist)


def bomba(Q, pC, zC=1.770, dp_union=0.30e5, dp_filtro=0.20e5):
    """Documento §1.6-1.10."""
    est = seg(Q, "DN40", 14.0, 6 * 0.60 + 2.00 + 0.06)          # linea estacionaria, sum K = 5,66
    rot = seg(Q, "DN40", 1.75, 30 * fT["DN40"])                  # union rotativa -> C, un codo
    suc = seg(Q, "DN50", 1.5, 0.50 + 30 * fT["DN50"] + 3 * fT["DN50"])   # sum K = 1,127
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
                P_el_W=Ph / 0.55 / 0.85, h_suc_m=suc["hL"], est=est, suc=suc)


fTd = lambda DN: fT[DN]

# ============================================================ PASO 1: caso de 19 (Tabla 4 del documento)
ramas19 = {
    "exterior (x2)": [
        ("C-S1", "DN50", 0.5360, 1.140, 1.7400, [("S1", 2)]),
        ("S1-S2", "DN50", 0.0880, 0.380, 1.7400, [("S2", 2)]),
        ("S2-E0", "DN50", 0.2760, 0.950, 1.7400, []),
        ("E0-E1", "DN40", 0.3940, 0.400, 1.3460, [("E1", 2)]),
        ("E1-E2", "DN40", 0.0820, 0.400, 1.2640, [("E2", 2)]),
        ("E2-E3", "DN40", 0.0820, 0.400, 1.1820, [("E3", 2)]),
        ("E3-E4", "DN40", 0.0820, 0.400, 1.1000, [("E4", 2)]),
        ("E4-E5", "DN40", 0.0300, 0.400, 1.0700, [("E5", 2)]),
    ],
    "lanza": [
        ("C-I0", "DN25", 0.2800, 2.070, 1.7400, []),
        ("I0-I1", "DN25", 0.4018, 0.460, 1.3382, [("I1", 1)]),
        ("I1-I2", "DN25", 0.0954, 0.460, 1.2428, [("I2", 1)]),
        ("I2-I3", "DN25", 0.0953, 0.460, 1.1475, [("I3", 1)]),
        ("I3-I4", "DN25", 0.0953, 0.460, 1.0522, [("I4", 1)]),
        ("I4-I5", "DN25", 0.0954, 0.460, 0.9568, [("I5", 1)]),
    ],
}
# nota: la rama exterior se resuelve una vez; el caudal de sus tramos es el de UN lado.
r19 = resolver(ramas19)
b19 = bomba(r19["Qtot"], r19["pC"])
pv_back = patm - rho * g * (5.51249 + b19["h_suc_m"])   # pv implicita en el documento (NPSH sin hs)
val = dict(Q_Lmin=r19["Qtot"] * 60000, pC_bar=r19["pC"] / 1e5, H_m=b19["H_m"], P_eje_kW=b19["P_eje_W"] / 1e3,
           P_el_kW=b19["P_el_W"] / 1e3, documento=dict(Q_Lmin=173.99, pC_bar=3.998805, H_m=50.74881, P_eje_kW=2.58,
                                                        P_el_kW=3.03))
print("VALIDACION 19 boquillas:", json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in val.items()}))

# ============================================================ PASO 2: red R05, 22 boquillas
# HIPOTESIS_R05 (fuentes: R05_parametros_r05.json, 00_LEEME_R05.md, 02_REGISTRO_CAMBIOS.md,
#                RESULTADOS_CALCULOS_R04.json "hidraulica_ramal_lanza"):
# H1 Lado exterior: misma topologia del documento (transversal DN50 en Z1740 hasta X900, ramal DN40).
# H2 LAT_5 pasa de Z1070 a Z1040 (D-5): tramo E4-E5 = 0,060 m.
# H3 VALVULA_RAMAL (paso total D42,76) en el ramal (Z1525-1615): K = 3 fT(DN40) (bola de paso total, como Kbola del doc).
# H4 INF_EXT (E6, Z855): el ramal DN40 sigue hasta Z944 (0,096 m), reduccion 1-1/2 x 1/2 hasta Z880 y pie DN15
#    con codo de 45 grados hasta el portaboquillas. Tramo DN15 equivalente 0,13 m [VERIFICAR con el CAD],
#    K = 0,5 (reduccion) + 16 fT (45 RL) + 30 fT (codo/terminal) sobre la velocidad DN15.
# H5 Lanza: recorrido R04/R05 real desde el cubo (red fija + V-AIS Cv 38 + flexible 1,26 m + curva 180 +
#    cuello movil). Se usa la perdida de R04 (0,98775 m a 54,706 L/min) como K equivalente sobre la
#    velocidad DN25 (K_eq constante, supuesto turbulento rugoso). Tope del cuello: Z1700.
# H6 INF_INT (I6, Z850): pie DN25 bajo INT_1 con codo de 25 grados; L = 0,25 m, K = 2 x 30 fT [VERIFICAR].
# H7 Tomas superiores a Z1740 (como el documento: el descenso dentro de la boquilla no se modela).
v_R04 = (54.70599032700168 / 60000) / (math.pi * ID["DN25"] ** 2 / 4)
K_lanza_eq = 0.9877540905619169 / (v_R04 ** 2 / (2 * g))
Kv = 3 * fT["DN40"]
ramas22 = {
    "exterior (x2)": [
        ("C-S1", "DN50", 0.5360, 60 * fTd("DN50"), 1.7400, [("S1_SUP_1", 2)]),
        ("S1-S2", "DN50", 0.0880, 20 * fTd("DN50"), 1.7400, [("S2_SUP_2", 2)]),
        ("S2-E0", "DN50", 0.2760, 50 * fTd("DN50"), 1.7400, []),
        ("E0-E1 (con valvula de ramal)", "DN40", 0.3940, 20 * fTd("DN40") + Kv, 1.3463, [("E1_LAT_4", 2)]),
        ("E1-E2", "DN40", 0.0821, 20 * fTd("DN40"), 1.2642, [("E2_LAT_3", 2)]),
        ("E2-E3", "DN40", 0.0821, 20 * fTd("DN40"), 1.1821, [("E3_LAT_2", 2)]),
        ("E3-E4", "DN40", 0.0821, 20 * fTd("DN40"), 1.1000, [("E4_LAT_1", 2)]),
        ("E4-E5", "DN40", 0.0600, 20 * fTd("DN40"), 1.0400, [("E5_LAT_5", 2)]),
        ("E5-extension", "DN40", 0.0960, 0.0, 0.9440, []),
        ("reduccion + pie DN15", "DN15", 0.1300, 0.5 + 16 * fTd("DN15") + 30 * fTd("DN15"), 0.8550, [("E6_INF_EXT", 2)]),
    ],
    "lanza": [
        ("C-I0 (red fija, V-AIS, flexible, cuello)", "DN25", 0.0, K_lanza_eq, 1.7000, []),
        ("I0-I1", "DN25", 0.3618, 20 * fTd("DN25"), 1.3382, [("I1_INT_5", 1)]),
        ("I1-I2", "DN25", 0.0954, 20 * fTd("DN25"), 1.2428, [("I2_INT_4", 1)]),
        ("I2-I3", "DN25", 0.0953, 20 * fTd("DN25"), 1.1475, [("I3_INT_3", 1)]),
        ("I3-I4", "DN25", 0.0953, 20 * fTd("DN25"), 1.0522, [("I4_INT_2", 1)]),
        ("I4-I5", "DN25", 0.0954, 20 * fTd("DN25"), 0.9568, [("I5_INT_1", 1)]),
        ("I5-I6 (pie 25 grados)", "DN25", 0.2500, 60 * fTd("DN25"), 0.8500, [("I6_INF_INT", 1)]),
    ],
}
r22 = resolver(ramas22)
b22 = bomba(r22["Qtot"], r22["pC"])
NPSHa = (patm - pv_back) / (rho * g) + 0.5 - b22["h_suc_m"]
NPSHa19 = (patm - pv_back) / (rho * g) + 0.5 - b19["h_suc_m"]
qs = {k: v * 60000 for k, v in r22["q"].items()}
res = dict(
    validacion_19=val,
    hipotesis=["H1-H7 en el codigo"],
    constantes=dict(rho=rho, mu=mu, patm_Pa=patm, pv_Pa_implicita_doc=pv_back, Kq_Lmin_sqrtbar=Kq * 60000 / math.sqrt(1e5),
                    q_n_Lmin=q_n * 60000, K_lanza_eq=K_lanza_eq),
    iteraciones=r22["hist"],
    pC_bar=r22["pC"] / 1e5,
    boquillas=[dict(toma=k, p_bar=r22["p"][k] / 1e5, q_Lmin=qs[k]) for k in r22["p"]],
    Q_total_Lmin=r22["Qtot"] * 60000,
    Q_total_m3h=r22["Qtot"] * 3600,
    q_min_max_Lmin=[min(qs.values()), max(qs.values())],
    dispersion_q_pct=100 * (max(qs.values()) / min(qs.values()) - 1),
    Q_lado_exterior_Lmin=sum(qs[k] for k in qs if k[0] in "SE"),
    Q_lanza_Lmin=sum(qs[k] for k in qs if k[0] == "I"),
    tramos=r22["tramos"],
    bomba=dict(partes_m=b22["partes"], H_m=b22["H_m"], v_DN40_m_s=b22["v_DN40"], P_h_W=b22["P_h_W"],
               P_eje_W=b22["P_eje_W"], P_el_W=b22["P_el_W"], NPSHa_m=NPSHa, NPSHa_hs0_m=NPSHa - 0.5,
               eta_bomba=0.55, eta_motor=0.85),
    comparacion_19=dict(Q_Lmin=r19["Qtot"] * 60000, H_m=b19["H_m"], P_eje_W=b19["P_eje_W"], P_el_W=b19["P_el_W"],
                        NPSHa_m=NPSHa19),
    volumen_10min_L=r22["Qtot"] * 60000 * 10,
    barrido_presion_uniforme=[dict(p_bar=pb, q_Lmin=Kq * math.sqrt(pb * 1e5) * 60000, Q22_Lmin=22 * Kq * math.sqrt(pb * 1e5) * 60000,
                                   v_j=0.95 * math.sqrt(2 * pb * 1e5 / rho),
                                   F_N=rho * Kq * math.sqrt(pb * 1e5) * 0.95 * math.sqrt(2 * pb * 1e5 / rho)) for pb in (3, 4, 5, 6)],
)
json.dump(res, open("resultados_22.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("22 boquillas: Q = %.3f L/min, pC = %.5f bar, H = %.3f m, P_eje = %.3f kW, P_el = %.3f kW, NPSHa = %.3f m"
      % (res["Q_total_Lmin"], res["pC_bar"], b22["H_m"], b22["P_eje_W"] / 1e3, b22["P_el_W"] / 1e3, NPSHa))
for bq in res["boquillas"]:
    print("  %-12s p = %.5f bar  q = %.5f L/min" % (bq["toma"], bq["p_bar"], bq["q_Lmin"]))
