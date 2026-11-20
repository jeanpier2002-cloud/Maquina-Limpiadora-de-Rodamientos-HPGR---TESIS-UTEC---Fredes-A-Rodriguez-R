# -*- coding: utf-8 -*-
"""B2 (obs. 3.2 del asesor): diseno de las 10 uniones soldadas a momento del bastidor N3 (W6X9 A36), 02/11/2026.

Uniones (HPGR D-040: soldadas a momento con continuidad de alas):
  - 6 en T: M05/M06 contra M01/M02 (nudos 3, 4, 14, 15) y M07 contra M05/M06 (nudos 9, 11);
  - 4 esquinas: M03/M04 contra M01/M02 (nudos 1, 6, 12, 17); M01/M02 se prolongan hasta el borde exterior con tapa.
Detalle propuesto: la barra que llega se recorta (destaje de alas) y sus alas van A TOPE CON PENETRACION COMPLETA contra el
canto del ala de la barra continua; su alma, con filete a3 por ambos lados contra el alma de la continua; en la continua, un
rigidizador de alma de 6 mm en el lado opuesto (impide la distorsion que exige la continuidad de alabeo).

Esfuerzos: parrilla de Vlasov de p23 en modo CONTINUO (continuidad de alas), rigidez reducida (D-048), con todos los
estados que pasan por los nudos:
  - centrado (RG, LOCK): 1,2(G + K2M) + 1,6H (NOM, DISP, ASIM) y 1,0 + 1,0 (ENV208, FALLO); ASIM_D03 aparte (algebraico);
  - lavado (RP, LOCK): RET = 1,4(G + K2M + rodamiento) + 1,6 chorro; BASE = 1,4(G + rodamiento);
  - traslado con el rodamiento (nuevo en el anexo): desvio lateral de rueda S = 6,51 kN (D-068, ya con 1,35) con su par
    al contacto (Z290) y tiro de cadenas 1,35 x 1,95 kN por cadena en M04 (D-071), con 1,35(G + K2M + rodamiento).
Comprobaciones (AISC 360-16):
  - alas a tope CJP: tension en el extremo de la barra que llega, P/A + M33/S33 + M22/S22 + B*omega/Cw <= 0,9 Fy (J2.4,
    tabla J2.5: con aporte compatible gobierna el metal base);
  - alma: filete a3 por ambos lados (J2.4) y fluencia por corte del alma (J4.2);
  - esquinas: la barra continua termina en la tapa; su fuerza de ala pasa por la linea de la CJP (corte + flexion en el plano);
  - rigidizador: b/t <= 0,56 sqrt(E/Fy) (J10.8).
Salida: resultados/CALCULO_UNIONES_B2.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parents[1]
SAP_SCRIPTS = AQUI.parent / "SAP_ANEXO_N3_V573" / "scripts"
sys.path.insert(0, str(SAP_SCRIPTS))
import p23_vlasov_continuidad_alas as P23  # noqa: E402

SALIDA = AQUI / "resultados" / "CALCULO_UNIONES_B2.json"
CAR = P23.CAR

# --- Seccion W6X9 (AISC v16; SAP) y material A36 ---
D, BF, TF, TW, K_DET = 149.86, 100.076, 5.461, 4.318, 6.35
A = 1729.03
S33 = 6826195.38 / (D / 2)
S22 = 915709.14 / (BF / 2)
H0 = D - TF
OMEGA = H0 * BF / 4.0
CW = P23.CW_W6X9
AF = BF * TF
AW = (D - 2 * TF) * TW
FY, E = 248.0, 200000.0
FEXX = 482.0                  # E70XX
A_W = 3.0                     # garganta del filete del alma (mm)
L_W = D - 2 * TF - 2 * K_DET - 6.0   # largo util del filete por lado, descontando el destaje (mm)

Z_CONTACTO = 290.0 - 730.07   # contacto rueda-riel en coordenadas del modelo (Z fisica - 730,07)
Z_CADENA = 195.0 - 730.07
S_GUIA = 6510.0               # N, D-068 (1,35 x 4,82 kN)
F_CADENA = 1.35 * 1950.0      # N por cadena, D-071

# Uniones: nudo -> (tipo, barra que llega [s2k], barras continuas [s2k])
UNIONES = {
    1: ("esquina", 11, [1]), 6: ("esquina", 18, [5]), 12: ("esquina", 24, [6]), 17: ("esquina", 18, [10]),
    3: ("T", 12, [2, 3]), 4: ("T", 15, [23, 4]), 14: ("T", 14, [7, 8]), 15: ("T", 17, [8, 9]),
    9: ("T", 19, [21, 14]), 11: ("T", 20, [22, 17]),
}
NOMBRE = {1: "M01", 2: "M01", 3: "M01", 23: "M01", 4: "M01", 5: "M01", 6: "M02", 7: "M02", 8: "M02", 9: "M02", 10: "M02",
          11: "M03", 24: "M03", 18: "M04", 12: "M05", 13: "M05", 21: "M05", 14: "M05", 15: "M06", 16: "M06", 22: "M06",
          17: "M06", 19: "M07", 20: "M07"}


def cargas_base():
    pat = {p: [(int(q["nudo"]), [q["F1"], q["F2"], q["F3"], q["M1"], q["M2"], q["M3"]]) for q in CAR["patrones"][p]]
           for p in CAR["patrones"] if p.startswith(("H_", "JET_", "G_K2M"))}
    w3 = -3032.0 * 9.81 / 3.0         # rodamiento en los 3 PAD (nudos 7, 8 y 10; equilibrio simetrico, N_PAD SAP 9915 N)
    pat["G_RODAMIENTO"] = [(n, [0, 0, w3, 0, 0, 0]) for n in (7, 8, 10)]
    for j in (2, 5, 13, 16):
        for sg, s in (("P", 1.0), ("M", -1.0)):
            F = s * S_GUIA
            pat["SKEW_%d_%s" % (j, sg)] = [(j, [F, 0, 0, 0, Z_CONTACTO * F, 0])]   # M2 = rz*Fx (r = (0,0,z))
    for sg, s in (("P", 1.0), ("M", -1.0)):
        F = s * F_CADENA
        pat["TIRO_%s" % sg] = [(6, [0, F, 0, -Z_CADENA * F, 0, 330.0 * F]), (17, [0, F, 0, -Z_CADENA * F, 0, -330.0 * F])]
    return pat


def modelo(apoyos=None, mpc="lock"):
    mod, dam = P23.modelo_lock()
    m = dict(dam)
    m["apoyos"] = dict(dam["apoyos"]) if apoyos is None else apoyos
    if mpc != "lock":
        m["mpc"] = []
    pat = cargas_base()
    m["cargas"] = pat
    m["patrones"] = {p: 0.0 for p in pat}
    m["patrones"]["G_FRAME"] = 1.0
    return m


def combos():
    c = {}
    for nombre, v in CAR["casos"].items():
        fam = v["familia"]
        acc = fam in ("ENV208", "FALLO_EMP", "FALLO_DAT")
        g = 1.0 if acc else 1.2
        q = 1.0 if acc else 1.6
        lst = [("G_FRAME", g), ("G_K2M_ACT", g)] + [(p, q * f) for p, f in v["patrones"]]
        c["CENTRADO_" + nombre] = ("LOCK", lst, fam == "ASIM_D03")
    for j in ("JET_XP", "JET_XN", "JET_YP", "JET_YN"):
        c["RET_" + j] = ("LOCK", [("G_FRAME", 1.4), ("G_K2M_RET", 1.4), ("G_RODAMIENTO", 1.4), (j, 1.6)], False)
    c["BASE_R05"] = ("LOCK", [("G_FRAME", 1.4), ("G_RODAMIENTO", 1.4)], False)
    gt = [("G_FRAME", 1.35), ("G_K2M_RET", 1.35), ("G_RODAMIENTO", 1.35)]
    for j in (2, 5, 13, 16):
        for sg in ("P", "M"):
            c["DESVIO_%d_%s" % (j, sg)] = ("SKEW_%d" % j, gt + [("SKEW_%d_%s" % (j, sg), 1.0)], False)
    for sg in ("P", "M"):
        c["TIRO_" + sg] = ("TIRO", gt + [("TIRO_" + sg, 1.0)], False)
    return c


def apoyos_modelos():
    rueda_opuesta = {2: 13, 13: 2, 5: 16, 16: 5}
    mods = {"LOCK": modelo()}
    for j, o in rueda_opuesta.items():
        ap = {w: [3] for w in (2, 5, 13, 16)}
        ap[o] = [1, 3]                # la rueda del otro riel reacciona el desvio
        ap[6] = [2]; ap[17] = [2]      # las cadenas retienen Y en M04
        mods["SKEW_%d" % j] = modelo(ap, mpc=None)
    ap = {w: [1, 3] for w in (2, 5, 13, 16)}
    ap[2] = [1, 2, 3]; ap[13] = [1, 2, 3]   # Y en las ruedas del extremo opuesto: el tiro recorre todo el bastidor
    mods["TIRO"] = modelo(ap, mpc=None)
    return mods


def fuerzas_extremo(s, u, nudo, barra):
    """(P, Vy, Vz, T, M33, M22, B) en el extremo de 'barra' que toca 'nudo' (ejes locales; valores absolutos)."""
    nn, n_j = s["nn"], s["nid"][("J", nudo)]
    for b, d, a, c, wa, wc, le, p in s["elems"]:
        if b != barra or n_j not in (a, c):
            continue
        R = P23.rot(d)
        T = np.zeros((14, 14))
        for blk in range(4):
            T[3 * blk:3 * blk + 3, 3 * blk:3 * blk + 3] = R
        T[12, 12] = T[13, 13] = 1.0
        g = list(range(6 * a, 6 * a + 6)) + list(range(6 * c, 6 * c + 6)) + [6 * nn + wa, 6 * nn + wc]
        f = P23.k_local(p, le, s["cw"]) @ (T @ u[g])
        o = 0 if n_j == a else 6
        return {"P": abs(f[o]), "Vy": abs(f[o + 1]), "Vz": abs(f[o + 2]), "T": abs(f[o + 3]),
                "M33": abs(f[o + 4]), "M22": abs(f[o + 5]), "B": abs(f[12 if n_j == a else 13])}
    raise KeyError((nudo, barra))


def sig_ala(F):
    return F["P"] / A + F["M33"] / S33 + F["M22"] / S22 + F["B"] * OMEGA / CW


def main():
    mods = apoyos_modelos()
    sols = {k: P23.resolver(m, "CONTINUO") for k, m in mods.items()}
    C = combos()
    phiFy = 0.9 * FY
    filete = 0.75 * 0.6 * FEXX * A_W * L_W * 2            # N, dos filetes
    corte_alma = 1.0 * 0.6 * FY * TW * L_W                  # N, J4.2 fluencia por corte del alma recortada
    res = {}
    for nudo, (tipo, entra, sigue) in UNIONES.items():
        peor = {"ala": (0, "", {}), "alma": (0, "", {}), "linea": (0, "", {}), "ala_algebraico": (0, "", {})}
        for nombre, (mk, lst, algebraico) in C.items():
            s = sols[mk]
            u = sum(f * s["pats"][p][0] for p, f in lst)
            Fe = fuerzas_extremo(s, u, nudo, entra)
            sa = sig_ala(Fe)
            clave = "ala_algebraico" if algebraico else "ala"
            if sa > peor[clave][0]:
                peor[clave] = (sa, nombre, Fe)
            if algebraico:
                continue
            V = math.hypot(Fe["Vz"], Fe["P"] * AW / A)
            if V > peor["alma"][0]:
                peor["alma"] = (V, nombre, Fe)
            if tipo == "esquina":   # la continua termina: su fuerza de ala pasa por la linea de la CJP (largo BF, espesor TF)
                Fc = fuerzas_extremo(s, u, nudo, sigue[0])
                Ff = Fc["M33"] / H0 + Fc["P"] * AF / A
                Mf = Fc["M22"] / 2 + Fc["B"] / H0
                tau = Ff / (TF * BF)
                sig = Mf / (TF * BF ** 2 / 6)
                vm = math.sqrt(sig ** 2 + 3 * tau ** 2)
                if vm > peor["linea"][0]:
                    peor["linea"] = (vm, nombre, Fc)
        r = {"tipo": tipo, "barra_que_llega": NOMBRE[entra], "barra_continua": NOMBRE[sigue[0]],
             "ala_CJP": {"sigma_MPa": round(peor["ala"][0], 1), "DC": round(peor["ala"][0] / phiFy, 3), "caso": peor["ala"][1],
                         "esfuerzos": {k: round(v, 0) for k, v in peor["ala"][2].items()}},
             "ala_CJP_ASIM_D03_algebraico": {"sigma_MPa": round(peor["ala_algebraico"][0], 1),
                                             "DC": round(peor["ala_algebraico"][0] / phiFy, 3), "caso": peor["ala_algebraico"][1]},
             "alma_filete": {"V_kN": round(peor["alma"][0] / 1000, 2), "phiRn_filete_kN": round(filete / 1000, 1),
                             "phiVn_alma_kN": round(corte_alma / 1000, 1),
                             "DC": round(peor["alma"][0] / min(filete, corte_alma), 3), "caso": peor["alma"][1]}}
        if tipo == "esquina":
            r["linea_CJP_continua_termina"] = {"sigma_vm_MPa": round(peor["linea"][0], 1), "DC": round(peor["linea"][0] / phiFy, 3),
                                               "caso": peor["linea"][1]}
        res[str(nudo)] = r
    # Barras completas (no solo los nudos): tension maxima de ala en todos los extremos de elemento, por barra y grupo de casos.
    # Los casos de traslado (desvio y tiro) son nuevos en el anexo: el SAP de v5.7.3 no los tenia.
    barras_env = {}
    for nombre, (mk, lst, algebraico) in C.items():
        if algebraico:
            continue
        grupo = nombre.split("_")[0]
        s = sols[mk]
        u = sum(f * s["pats"][p][0] for p, f in lst)
        nn = s["nn"]
        for b, d, a, c, wa, wc, le, p in s["elems"]:
            # corte de Saint-Venant en el ala: tau = G * t * theta' (DG9 4.7), con theta' del GDL de alabeo
            tsv = p["G"] * TF * max(abs(u[6 * nn + wa]), abs(u[6 * nn + wc]))
            kt = (NOMBRE[b], grupo, "tau")
            if tsv > barras_env.get(kt, (0, ""))[0]:
                barras_env[kt] = (tsv, nombre)
            R = P23.rot(d)
            T = np.zeros((14, 14))
            for blk in range(4):
                T[3 * blk:3 * blk + 3, 3 * blk:3 * blk + 3] = R
            T[12, 12] = T[13, 13] = 1.0
            g = list(range(6 * a, 6 * a + 6)) + list(range(6 * c, 6 * c + 6)) + [6 * nn + wa, 6 * nn + wc]
            f = P23.k_local(p, le, s["cw"]) @ (T @ u[g])
            for o, ib in ((0, 12), (6, 13)):
                sg = abs(f[o]) / A + abs(f[o + 4]) / S33 + abs(f[o + 5]) / S22 + abs(f[ib]) * OMEGA / CW
                k = (NOMBRE[b], grupo)
                if sg > barras_env.get(k, (0, ""))[0]:
                    barras_env[k] = (sg, nombre)
    barras_out = {}
    for k, (val, nombre) in sorted(barras_env.items()):
        if len(k) == 3:
            mb, gr, _ = k
            barras_out.setdefault(mb, {}).setdefault(gr, {})["tau_sv_MPa"] = round(val, 1)
            barras_out[mb][gr]["DC_corte_DG9"] = round(val / (0.9 * 0.6 * FY), 3)
        else:
            mb, gr = k
            barras_out.setdefault(mb, {}).setdefault(gr, {}).update(
                {"sigma_MPa": round(val, 1), "DC_fluencia": round(val / phiFy, 3), "caso": nombre})

    # Validacion: modo SV (sin alabeo) frente a SAP RP_RIG_LOCK, ULS_BASE_R05: |M33| maximo de M07 (barras 19 y 20).
    # El SAP tiene el aro rigido sobre los PAD (acopla los PAD en planta); aqui el rodamiento entra como 3 cargas verticales.
    sv = P23.resolver(mods["LOCK"], "SV", cw=0.0)
    u = sum(f * sv["pats"][p][0] for p, f in C["BASE_R05"][1])
    m_v = max(fuerzas_extremo(sv, u, n, b)["M33"] for n, b in ((9, 19), (10, 19), (10, 20), (11, 20)))
    import csv as _csv
    m_s = 0.0
    f_sap = AQUI.parent / "SAP_ANEXO_N3_V573" / "resultados" / "v573" / "V573_RP_RIG_LOCK" / "fuerzas_barra.csv"
    for r in _csv.DictReader(f_sap.open(encoding="utf-8"), delimiter=";"):
        if r["barra"] in ("19", "20") and r["caso"] == "ULS_BASE_R05":
            m_s = max(m_s, abs(float(r["M3_Nmm"])))
    validacion = {"M33_max_M07_vlasov_SV_kNm": round(m_v / 1e6, 3), "M33_max_M07_SAP_kNm": round(m_s / 1e6, 3),
                  "dif_pct": round(100 * (m_v - m_s) / m_s, 1)}

    b_rig, t_rig = (BF - TW) / 2 - 2.0, 6.0
    salida = {
        "estado": "EJECUTADO (calculo); diseno CANDIDATO; uniones con continuidad de alas (modo CONTINUO de p23)",
        "seccion": {"A": A, "S33": round(S33, 0), "S22": round(S22, 0), "omega_mm2": round(OMEGA, 1), "Cw_mm6": CW,
                    "Fy_MPa": FY, "FEXX_MPa": FEXX, "a_filete_mm": A_W, "L_filete_mm": round(L_W, 1)},
        "rigidizador": {"b_mm": round(b_rig, 1), "t_mm": t_rig, "b_t": round(b_rig / t_rig, 1),
                        "limite_J10_8": round(0.56 * math.sqrt(E / FY), 1)},
        "fatiga": "AISC 360-16 Apendice 3, 3.1: no se evalua con menos de 20 000 ciclos de la carga variable "
                  "[HIPOTESIS: ~2 rodamientos por semana x 50 semanas x 20 anos = 2 000 ciclos de centrado y traslado]",
        "uniones": res,
        "barras_envolvente": barras_out,
        "validacion_BASE_R05_nudo3_barra12": validacion,
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print("%-5s %-8s %-4s<-%-4s  ala CJP: sigma  D/C  caso                 | alma V kN  D/C | linea esquina D/C | ASIM_D03" % ("nudo", "tipo", "cont", "lleg"))
    for n, r in res.items():
        print("%-5s %-8s %-4s<-%-4s  %6.1f  %.2f  %-22s | %5.2f  %.2f | %s | %.2f" % (
            n, r["tipo"], r["barra_continua"], r["barra_que_llega"], r["ala_CJP"]["sigma_MPa"], r["ala_CJP"]["DC"],
            r["ala_CJP"]["caso"], r["alma_filete"]["V_kN"], r["alma_filete"]["DC"],
            ("%.2f %s" % (r["linea_CJP_continua_termina"]["DC"], r["linea_CJP_continua_termina"]["caso"])) if "linea_CJP_continua_termina" in r else "   -    ",
            r["ala_CJP_ASIM_D03_algebraico"]["DC"]))
    print("rigidizador", salida["rigidizador"])
    print("validacion", validacion)
    for mb, gs in barras_out.items():
        print(mb, "  ".join("%s %.0f MPa (%.2f) tau %.0f (%.2f) %s" % (g, v["sigma_MPa"], v["DC_fluencia"], v["tau_sv_MPa"],
                                                                        v["DC_corte_DG9"], v["caso"]) for g, v in gs.items()))


if __name__ == "__main__":
    main()
