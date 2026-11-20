# -*- coding: utf-8 -*-
"""Resumen de las variantes de refuerzo de la unión W5 (s07 + s08), 12/11/2026.
Lee resultados/union_variantes/nodos_<VAR>_<EST>.csv (nodos de la superficie del tubo fino, x = 170–272 del CAD; marco SW
(X, Y, Z) = (-x, z, y) del CAD; MPa) y geometria/variantes_w5/geometria_variantes.json.
Métricas (von Mises en la superficie exterior del tubo; máximo dentro de la tolerancia de búsqueda tol = máx(0,3; 0,5·h) mm):
  FIN   a lo largo del tubo, a d = 0,4t, 1,0t, 5, 10 y 20 mm más allá del fin de la unión (x_e = 200 en BASE/S40/S80; punta del
        refuerzo en LENG/CART), máximo sobre la circunferencia.
  PIE   sobre la línea de pie del cordón, dentro de la unión (x de 172 a x_e − 1): a 0,4t y 1,0t del pie medido en arco sobre el
        tubo (θ_pie = 20,0° en W5 y en la lengüeta; 24,4° en los cordones de la cartela, x > 200); punto caliente IIW con von Mises
        σ_hs = 1,67·σ(0,4t) − 0,67·σ(1,0t).
  MEMB  estimación de dos puntos de la tensión de membrana de la pared: promedio de los tensores en la cara exterior y en la
        interior para el mismo (x, θ), y su von Mises; se excluyen los nodos exteriores a menos de 1,0t de las líneas singulares.
La comparación entre variantes (figura) usa la malla de 1 mm; la de 0,6 mm (BASE y S40) solo comprueba la convergencia.
  CART  el W5 sigue terminando en x = 200: además se mide FIN allí (fuera de la franja de la cartela y de 1,0t alrededor del pie
        de sus cordones), se excluye esa esquina de la membrana, y la barra «fin de la unión» toma el peor de los dos extremos.
  VIGA  sonda en x = 240 (todos los nodos del tubo en ±3 mm) frente a la viga a mano (M = 1 000 N·(900 − 240) mm, T = 340 N·m).
Escribe resultados/union_variantes/RESUMEN_VARIANTES_W5.json, RESUMEN_VARIANTES_W5.md y fig_union_variantes.png."""
import json
import math
import os
import numpy as np
from scipy.spatial import cKDTree

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE_DIR, "resultados", "union_variantes")
GEO = json.load(open(os.path.join(BASE_DIR, "geometria", "variantes_w5", "geometria_variantes.json"), encoding="utf-8"))
R = 30.15
FY = 153.0
VARS = ["BASE", "S40", "S80", "LENG", "CART"]
NOMBRE = {"BASE": "Actual: Sch 10S (t 2,77)", "S40": "Sch 40S (t 3,91)", "S80": "Sch 80S (t 5,54)",
          "LENG": "Sch 10S + lengüeta horizontal 8 mm", "CART": "Sch 10S + cartela vertical 8 mm"}
X_FIN = {"BASE": 200.0, "S40": 200.0, "S80": 200.0, "LENG": 255.0, "CART": 266.0}
TH_PIE = {"BASE": 20.03, "S40": 20.03, "S80": 20.03, "LENG": 20.03, "CART": 24.35}   # CART: 24,35 solo en x > 200 (cordones WR)


def th_pie(var, x):
    """Ángulo del pie del cordón (grados) en x (escalar o arreglo): W5 hasta x = 200, cordones de la cartela después."""
    return np.where((var == "CART") & (np.asarray(x) > 200.0), TH_PIE[var], 20.03)
ESTUDIOS = [("FUERA_h1", 1.0), ("FUERA_h0p6", 0.6), ("EN_h1", 1.0)]


def vm(sx, sy, sz, txy, txz, tyz):
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (txy ** 2 + txz ** 2 + tyz ** 2))


def leer(var, est):
    p = os.path.join(RES, "nodos_%s_%s.csv" % (var, est))
    if not os.path.exists(p):
        return None
    d = np.genfromtxt(p, delimiter=";", names=True)
    x = -d["X"]; v = d["Y"] - 1740.0; w = d["Z"]
    return {"x": x, "r": np.hypot(v, w), "th": np.degrees(np.arctan2(w, v)), "von": d["VON"],
            "S": np.vstack([d[k] for k in ("SX", "SY", "SZ", "TXY", "TXZ", "TYZ")]).T}


def metr(var, est, h):
    d = leer(var, est)
    if d is None:
        return None
    t = GEO["variantes"][var]["t_mm"]; r_in = R - t
    tol = max(0.3, 0.5 * h)
    ext = d["r"] >= 29.9
    inn = np.abs(d["r"] - r_in) <= 0.15
    x, th, von = d["x"], d["th"], d["von"]
    xe = X_FIN[var]
    out = {"t_mm": t, "tol_mm": tol, "nodos_ext": int(ext.sum()), "nodos_int": int(inn.sum())}
    # FIN: más allá del fin de la unión
    fin = {}
    for nom, dd in (("0,4t", 0.4 * t), ("1,0t", 1.0 * t), ("5", 5.0), ("10", 10.0), ("20", 20.0)):
        m = ext & (np.abs(x - (xe + dd)) <= tol)
        fin[nom] = round(float(von[m].max()), 1) if m.any() else None
    out["fin"] = fin
    # CART: el W5 sigue terminando en x = 200 (la cartela solo cubre la franja de arriba); medir también ahí,
    # fuera de la franja de la cartela y de 1,0t alrededor del pie de sus cordones (|θ| < 24,35° + 1,0t/R)
    if var == "CART":
        lib = ext & (np.abs(th) > TH_PIE["CART"] + math.degrees(1.0 * t / R))
        fw = {}
        for nom, dd in (("1,0t", 1.0 * t), ("5", 5.0), ("10", 10.0), ("20", 20.0)):
            m = lib & (np.abs(x - (200.0 + dd)) <= tol)
            fw[nom] = round(float(von[m].max()), 1) if m.any() else None
        out["fin_w5_x200"] = fw
    # perfil: máximo sobre la circunferencia por x (cada 0,5 mm)
    xs = np.arange(171.0, 272.0, 0.5)
    out["perfil_x"] = xs.tolist()
    out["perfil_max"] = [round(float(von[ext & (np.abs(x - xx) <= tol)].max()), 1) if (ext & (np.abs(x - xx) <= tol)).any() else None for xx in xs]
    # PIE: línea de pie del cordón dentro de la unión
    dth = math.degrees(tol / R)
    pie = []
    for xx in np.arange(172.0, xe - 1.0 * t + 1e-9, 1.0):      # sin la esquina del fin del cordón (va en FIN)
        for lado in (1, -1):
            s = []
            for dd in (0.4 * t, 1.0 * t):
                tht = lado * (float(th_pie(var, xx)) + math.degrees(dd / R))
                m = ext & (np.abs(x - xx) <= tol) & (np.abs(th - tht) <= dth)
                s.append(float(von[m].max()) if m.any() else float("nan"))
            pie.append((xx, lado, s[0], s[1], 1.67 * s[0] - 0.67 * s[1]))
    pie = np.array(pie)
    ok = ~np.isnan(pie[:, 3])
    if ok.any():
        i1 = np.nanargmax(np.where(ok, pie[:, 3], -1)); ih = np.nanargmax(np.where(ok, pie[:, 4], -1))
        out["pie"] = {"max_1,0t": round(float(pie[i1, 3]), 1), "x_1,0t": float(pie[i1, 0]),
                      "max_0,4t": round(float(np.nanmax(pie[:, 2])), 1),
                      "max_hs": round(float(pie[ih, 4]), 1), "x_hs": float(pie[ih, 0])}
    # MEMB: dos puntos (exterior + interior), fuera de las zonas singulares
    th_p = th_pie(var, x)
    sing = (np.abs(np.abs(th) - th_p) < math.degrees(1.0 * t / R)) & (x < xe + 1.0 * t)
    sing |= (np.abs(x - xe) < 1.0 * t) & (np.abs(th) < th_p + math.degrees(1.0 * t / R))
    sing |= (np.abs(th) < 6.0) & (x < xe + 1.0 * t)          # franja aplanada pegada a la placa
    if var == "CART":                                        # esquina del fin del W5 (x = 200), donde arrancan los cordones de la cartela
        sing |= (np.abs(x - 200.0) < 1.0 * t) & (np.abs(th) < TH_PIE["CART"] + math.degrees(1.0 * t / R))
    # cara interior: no tiene aristas singulares; si no fluye, la fluencia no atraviesa la pared
    out["interior"] = {}
    for k, mk in (("union", inn & (x <= xe)), ("libre", inn & (x > xe))):
        if mk.any():
            q = np.argmax(np.where(mk, von, -1))
            out["interior"][k] = {"max": round(float(von[q]), 1), "x": round(float(x[q]), 1), "th": round(float(th[q]), 1)}
    e_idx = np.where(ext & ~sing)[0]; i_idx = np.where(inn)[0]
    if len(i_idx) and len(e_idx):
        arc_i = np.radians(th[i_idx]) * R; arc_e = np.radians(th[e_idx]) * R
        kd = cKDTree(np.c_[x[i_idx], arc_i])
        dist, j = kd.query(np.c_[x[e_idx], arc_e], distance_upper_bound=1.5 * tol + 1.0)
        val = dist < np.inf
        Sm = 0.5 * (d["S"][e_idx[val]] + d["S"][i_idx[j[val]]])
        mvm = vm(*Sm.T)
        xe_v = x[e_idx[val]]
        reg = {"union": (xe_v <= xe), "libre": (xe_v > xe)}
        out["memb"] = {}
        for k, mk in reg.items():
            if mk.any():
                q = np.argmax(np.where(mk, mvm, -1))
                out["memb"][k] = {"max": round(float(mvm[q]), 1), "x": round(float(xe_v[q]), 1),
                                  "th": round(float(th[e_idx[val]][q]), 1)}
    # VIGA: sonda x = 240
    m = np.abs(x - 240.0) <= 3.0
    out["sonda_240"] = round(float(von[m].max()), 1) if m.any() else None
    W = math.pi * (60.3 ** 4 - (60.3 - 2 * t) ** 4) / (32 * 60.3)
    Mb, T = 1000.0 * (900 - 240), 340e3
    out["viga_240_mano"] = round(math.sqrt((Mb / W) ** 2 + 3 * (T / (2 * W)) ** 2), 1) if est.startswith("FUERA") else None
    return out


def main():
    res = {}
    for var in VARS:
        res[var] = {"nombre": NOMBRE[var], "x_fin_union": X_FIN[var], "th_pie_deg": TH_PIE[var],
                    "masa_tubo_central_kg": GEO["variantes"][var]["masa_tubo_central_kg"],
                    "masa_refuerzo_kg": GEO["variantes"][var]["masa_refuerzo_kg"]}
        for est, h in ESTUDIOS:
            mm = metr(var, est, h)
            if mm is not None:
                res[var][est] = mm
    json.dump(res, open(os.path.join(RES, "RESUMEN_VARIANTES_W5.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # tabla Markdown
    L = ["| Variante | Estudio | Fin: 0,4t | Fin: 1,0t | Fin: 5 mm | Fin: 10 mm | Pie: 1,0t (x) | Pie: punto caliente | Interior (unión / libre) | Membrana (unión / libre) | Sonda x=240 (mano) |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for var in VARS:
        for est, h in ESTUDIOS:
            m = res[var].get(est)
            if not m:
                continue
            f = m["fin"]; p = m.get("pie", {}); mb = m.get("memb", {}); it = m.get("interior", {})
            L.append("| %s | %s | %s | %s | %s | %s | %s (%s) | %s | %s / %s | %s / %s | %s (%s) |" % (
                var, est, f["0,4t"], f["1,0t"], f["5"], f["10"], p.get("max_1,0t"), p.get("x_1,0t"), p.get("max_hs"),
                it.get("union", {}).get("max"), it.get("libre", {}).get("max"),
                mb.get("union", {}).get("max"), mb.get("libre", {}).get("max"), m["sonda_240"], m["viga_240_mano"]))
    for est, h in ESTUDIOS:
        m = res["CART"].get(est)
        if m and m.get("fin_w5_x200"):
            L.append("")
            L.append("CART %s, fin del W5 en x = 200 (fuera de la franja de la cartela): %s" % (est, m["fin_w5_x200"]))
    open(os.path.join(RES, "RESUMEN_VARIANTES_W5.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    figura(res)


def figura(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    CORTO = {"BASE": "Sch 10S actual (t 2,77)", "S40": "Sch 40S (t 3,91)", "S80": "Sch 80S (t 5,54)",
             "LENG": "10S + lengüeta 8 mm", "CART": "10S + cartela 8 mm"}
    col = {"BASE": "#1f1f1f", "S40": "#1f77b4", "S80": "#2ca02c", "LENG": "#d62728", "CART": "#9467bd"}
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.9), gridspec_kw={"width_ratios": [1.5, 1]})
    for var in VARS:
        m = res[var].get("FUERA_h1")
        if not m:
            continue
        xs = np.array(m["perfil_x"]); ys = np.array([np.nan if v is None else v for v in m["perfil_max"]], dtype=float)
        ax[0].plot(xs, ys, color=col[var], lw=1.3, label=CORTO[var])
    ax[0].axhline(FY, color="0.4", ls="--", lw=0.9); ax[0].text(268, FY + 4, "fluencia supuesta 153 MPa", ha="right", va="bottom", fontsize=8, color="0.3")
    ax[0].axvline(200, color="0.6", ls=":", lw=0.9); ax[0].text(201, 8, "fin del W5", fontsize=7.5, color="0.4", rotation=90, va="bottom")
    for xv, txt, cv in ((255, "punta lengüeta", col["LENG"]), (266, "punta cartela", col["CART"])):
        ax[0].axvline(xv, color=cv, ls=":", lw=0.8); ax[0].text(xv + 0.8, 8, txt, fontsize=7.5, color=cv, rotation=90, va="bottom")
    ax[0].text(172, 445, "Dentro de la unión el\nmáximo es el pie del\ncordón (singular).", fontsize=7.0, color="0.3", va="top")
    ax[0].set_xlim(171, 272); ax[0].set_ylim(0, 450)
    ax[0].set_xlabel("Distancia al eje del rotor x (mm)"); ax[0].set_ylabel("von Mises máx. en la circunferencia (MPa)")
    ax[0].set_title("(a) Tubo transversal, golpe de 1 000 N fuera del plano (malla 1 mm)", fontsize=9, loc="left")
    ax[0].legend(fontsize=7.3, frameon=False, loc="upper left", bbox_to_anchor=(0.41, 1.0))
    # (b) barras: métricas convergidas
    met = [("Fin de la unión\na 1,0t", lambda m: max(m["fin"]["1,0t"], (m.get("fin_w5_x200") or {}).get("1,0t") or 0)),("Pie del cordón\na 1,0t", lambda m: m.get("pie", {}).get("max_1,0t")),
           ("Cara interior\n(máx.)", lambda m: max(v["max"] for v in m.get("interior", {}).values()) if m.get("interior") else None),
           ("Membrana\n(dos puntos)", lambda m: max(v["max"] for v in m.get("memb", {}).values()) if m.get("memb") else None)]
    wbar = 0.15
    for k, var in enumerate(VARS):
        m = res[var].get("FUERA_h1")
        if not m:
            continue
        vals = [f(m) or 0 for _, f in met]
        ax[1].bar(np.arange(len(met)) + (k - 2) * wbar, vals, wbar, color=col[var], label=var)
    ax[1].axhline(FY, color="0.4", ls="--", lw=0.9)
    ax[1].set_xticks(range(len(met))); ax[1].set_xticklabels([n for n, _ in met], fontsize=8)
    ax[1].set_ylabel("von Mises (MPa)"); ax[1].set_title("(b) Métricas por variante (malla 1 mm)", fontsize=9, loc="left")
    ax[1].set_ylim(0, 300)
    ax[1].legend(fontsize=7.5, frameon=False, ncol=5, loc="upper center", columnspacing=0.8, handlelength=1.2)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig_union_variantes.png"), dpi=200)


if __name__ == "__main__":
    main()
