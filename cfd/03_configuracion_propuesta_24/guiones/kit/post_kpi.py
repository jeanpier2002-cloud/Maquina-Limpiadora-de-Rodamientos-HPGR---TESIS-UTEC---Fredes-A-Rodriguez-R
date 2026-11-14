#!/usr/bin/env python3
"""
Post-proceso comun de KPIs K2-K6 para ANSYS Fluent y OpenFOAM (rama B).

Entrada: una tabla de IMPACTOS sobre una superficie objetivo (una fila por
parcela que toca la pared y queda depositada: condicion 'trap' en Fluent,
'escape' en OpenFOAM). Misma aritmetica que ../02_ENTRADAS/de_rama_B/post_F4.py:

  D(banda)  = mdot_banda * T_vuelta / A_banda            [kg/m2 por vuelta]   K2
  CV        = std(D)/mean(D) sobre bandas con masa (no ponderado)            K3
  seca      = sum A_banda(D <= 1e-9) / A_total                              K4
  C(Dmin)   = sum A_banda(D >= Dmin) / A_total                              K4
  eta       = mdot_depositado / mdot_inyectado                              K5
  J(banda)  = sum(mdot_i * vn_i) * T_vuelta / A_banda    [N s/m2 por vuelta]  K6
  p_huella  = sum(mdot_i * vn_i) / A_huella               [Pa]                 K6

Superficies (eje del rotor = eje Z global, centrado en x = y = 0, sistema R05):
  cilindro : pared exterior (OD) de radio R, bandas en z. Normal hacia afuera.
  anillo   : cara plana z = z0 entre r_int y r_ext, bandas en r. Normal +z.
  cono     : agujero conico 1:30 de la rama B (r = 0,450 + (z - 0,890)/60).

Modos de la columna de masa:
  estacionario : cada fila trae un CAUDAL de parcela (kg/s)  (seguimiento estacionario)
  transitorio  : cada fila trae una MASA de parcela (kg) y un tiempo t (s);
                 se usa la ventana [t_estable, t_fin) como en la rama B.

Las columnas del archivo de entrada se mapean con --col NOMBRE=columna_del_csv.
Nombres internos: x y z u v w d mdot masa t boquilla. Unidades SI.
El formato exacto del archivo de muestreo DPM de Fluent esta [VERIFICAR]: se
convierte a CSV con cabecera y se mapea aqui, sin tocar la aritmetica.

Exclusion de zonas ocluidas en E1 (no cuentan en KPI-1):
  --excluir z1_m,z2_m,theta_centro_deg,semiancho_deg   (repetible)
  Quita esa fraccion acimutal del area de las bandas afectadas.
  theta se mide en el marco FIJO del rodamiento con el mismo origen que la
  geometria R05 [VERIFICAR origen con INTERFAZ ISMAEL].

Uso (ejemplo):
  python post_kpi.py --entrada impactos_OD.csv --caso F7_EOD_base \
      --superficie cilindro --R 0.710 --lim 0.890 1.405 \
      --modo estacionario --mdot-inyectado 1.4913 \
      --col x=x_m --col y=y_m --col z=z_m --col u=u_m_s --col v=v_m_s --col w=w_m_s \
      --col d=d_m --col mdot=mdot_kg_s --col boquilla=injection \
      --salida ../06_RESULTADOS/F7
"""
import argparse
import csv
import math
import os

import numpy as np

P = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
P.add_argument("--entrada", required=True)
P.add_argument("--caso", required=True)
P.add_argument("--salida", required=True)
P.add_argument("--superficie", choices=["cilindro", "anillo", "anillo_inf", "cono"], required=True,
               help="anillo = cara superior (normal +z); anillo_inf = cara inferior (normal -z, CFD03)")
P.add_argument("--boquillas", default=None,
               help="CFD03: solo impactos de estas boquillas (nombres separados por coma, sin distinguir mayusculas)")
P.add_argument("--factor", type=float, default=1.0,
               help="CFD03: multiplica la masa/caudal de cada impacto (p. ej. 2 = ramal A + B por S9)")
P.add_argument("--R", type=float, help="radio del cilindro (m)")
P.add_argument("--z0", type=float, help="cota de la cara plana (m)")
P.add_argument("--lim", nargs=2, type=float, required=True,
               help="limites de la coordenada de banda: z (cilindro, cono) o r (anillo), m")
P.add_argument("--modo", choices=["estacionario", "transitorio"], required=True)
P.add_argument("--t-estable", type=float, default=0.020)
P.add_argument("--t-fin", type=float, default=0.035)
P.add_argument("--banda-mm", type=float, default=10.0, help="ancho de banda (10 mm = rama B)")
P.add_argument("--celda-huella-mm", type=float, default=5.0, help="celda (banda x arco) para A_huella")
P.add_argument("--omega", type=float, default=0.1780235837034216, help="rad/s (1,7 rpm, HIPOTESIS)")
P.add_argument("--mdot-inyectado", type=float, default=None, help="kg/s inyectados (para eta)")
P.add_argument("--excluir", action="append", default=[])
P.add_argument("--col", action="append", default=[], help="NOMBRE=columna")
P.add_argument("--sep", default=",")
A = P.parse_args()

T_VUELTA = 2 * math.pi / A.omega
SECO = 1e-9
col = {k: k for k in "x y z u v w d mdot masa t boquilla".split()}
for c in A.col:
    k, v = c.split("=", 1)
    col[k] = v


# ------------------------------------------------------------------ lectura
def leer():
    if A.sep == ",":
        # CFD03: lectura por columnas, eficiente en memoria para archivos de varios GB (lector_impactos.py).
        # En transitorio se descartan al leer las filas fuera de [t_estable, t_fin): son las mismas que la
        # seleccion 'sel' de abajo descarta, asi que los KPIs no cambian.
        import sys as _s, os as _o
        _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
        from lector_impactos import leer as _leer
        nec = ["x", "y", "z", "u", "v", "w", "d"] + (["mdot"] if A.modo == "estacionario" else ["masa", "t"])
        R = _leer(A.entrada, [col[k] for k in nec], texto=(col["boquilla"],),
                  filtro_t=(A.t_estable, A.t_fin) if A.modo == "transitorio" else None)
        for k in nec:
            if col[k] not in R and k != "d":
                raise SystemExit("falta la columna '%s' (mapear con --col %s=...)" % (col[k], k))
        D = {k: R.get(col[k]) for k in nec}
        if D["x"].size == 0:
            raise SystemExit("archivo sin filas en la ventana: %s" % A.entrada)
        D["boquilla"] = R[col["boquilla"]] if col["boquilla"] in R else np.array(["s/id"] * D["x"].size, dtype=object)
        return D
    with open(A.entrada, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f, delimiter=A.sep))
    if not filas:
        raise SystemExit("archivo sin filas: %s" % A.entrada)

    def arr(k, obligatorio=True):
        if col[k] not in filas[0]:
            if obligatorio:
                raise SystemExit("falta la columna '%s' (mapear con --col %s=...)" % (col[k], k))
            return None
        return np.array([float(r[col[k]]) for r in filas])

    D = {k: arr(k) for k in "x y z u v w".split()}
    D["d"] = arr("d", False)
    if A.modo == "estacionario":
        D["mdot"] = arr("mdot")
    else:
        D["masa"], D["t"] = arr("masa"), arr("t")
    D["boquilla"] = ([r[col["boquilla"]] for r in filas] if col["boquilla"] in filas[0]
                     else ["s/id"] * len(filas))
    return D


D = leer()
if A.modo == "transitorio":
    sel = (D["t"] >= A.t_estable) & (D["t"] < A.t_fin)
    dtv = A.t_fin - A.t_estable
    mdot_i = D["masa"] / dtv          # cada parcela aporta masa/duracion a la tasa media
else:
    sel = np.ones(D["x"].size, bool)
    mdot_i = D["mdot"]
if A.boquillas:                       # CFD03: filtro por boquilla (no cambia la aritmetica)
    quiero = {b.strip().lower() for b in A.boquillas.split(",")}
    sel &= np.array([str(b).lower() in quiero for b in D["boquilla"]])
mdot_raw = mdot_i.copy()             # CFD03: p_huella (presion instantanea en la huella de UN ramal) sin factor
mdot_i = mdot_i * A.factor           # CFD03: factor de contribuciones identicas (S9: 2); 1 = sin cambio
x, y, z = D["x"][sel], D["y"][sel], D["z"][sel]
U = np.column_stack([D["u"][sel], D["v"][sel], D["w"][sel]])
mdot_i = mdot_i[sel]
mdot_raw = mdot_raw[sel]
boq = np.array(D["boquilla"])[sel]
r = np.hypot(x, y)
th = np.degrees(np.arctan2(x, y))     # mismo origen que post_F4 (+Y), positivo hacia +X

# ------------------------------------------------ geometria de la superficie
if A.superficie == "cilindro":
    if A.R is None:
        raise SystemExit("--R es obligatorio para cilindro")
    s = z
    n_hat = np.column_stack([x / r, y / r, np.zeros_like(r)])   # normal exterior
    vn = -(U * n_hat).sum(axis=1)                                 # positiva si la gota va hacia la pared
    radio_arco = lambda sc: np.full_like(sc, A.R)
    area_banda = lambda b0, b1: 2 * math.pi * A.R * (b1 - b0)
elif A.superficie in ("anillo", "anillo_inf"):
    s = r
    vn = -U[:, 2] if A.superficie == "anillo" else U[:, 2]       # cara superior normal +z; inferior normal -z
    radio_arco = lambda sc: sc
    area_banda = lambda b0, b1: math.pi * (b1 ** 2 - b0 ** 2)
else:  # cono de la rama B
    R_INF, Z_INF, CONIC = 0.450, 0.890, 1.0 / 60.0
    COS_A = math.cos(math.atan(CONIC))
    s = z
    n_hat = np.column_stack([-x / r, -y / r, np.zeros_like(r)])  # pared del agujero: normal hacia el eje
    vn = -(U * n_hat).sum(axis=1)
    rz = lambda zz: R_INF + (zz - Z_INF) * CONIC
    radio_arco = rz
    area_banda = lambda b0, b1: 2 * math.pi * rz(0.5 * (b0 + b1)) * (b1 - b0) / COS_A
vn = np.clip(vn, 0.0, None)

# ------------------------------------------------------------------ bandas
lo, hi = A.lim
db = A.banda_mm * 1e-3
nb = int(math.ceil((hi - lo) / db - 1e-9))
bordes = np.minimum(lo + db * np.arange(nb + 1), hi)       # ultimo borde recortado (como la rama B)
fuera = (s < lo) | (s > hi)
idx = np.clip(np.digitize(s, bordes) - 1, 0, nb - 1)
A_b = np.array([area_banda(bordes[k], bordes[k + 1]) for k in range(nb)])
sc = 0.5 * (bordes[:-1] + bordes[1:])

# fraccion acimutal excluida por banda (E1: topes, PAD)
frac_excl = np.zeros(nb)
zonas = []
for e in A.excluir:
    s1, s2, thc, hw = [float(v) for v in e.split(",")]
    zonas.append((s1, s2, thc, hw))
    for k in range(nb):
        solape = max(0.0, min(bordes[k + 1], s2) - max(bordes[k], s1)) / (bordes[k + 1] - bordes[k])
        frac_excl[k] = min(1.0, frac_excl[k] + solape * (2 * hw) / 360.0)
A_ef = A_b * (1 - frac_excl)


def en_zona_excluida(si, ti):
    for s1, s2, thc, hw in zonas:
        dth = (ti - thc + 180.0) % 360.0 - 180.0
        if s1 <= si <= s2 and abs(dth) <= hw:
            return True
    return False


# NOTA: con rotor congelado la dosis por vuelta es axisimetrica; la exclusion
# solo reduce el area que cuenta. La masa se reparte por banda en la vuelta y
# se asigna a la parte NO ocluida en proporcion a su area.
dentro = ~fuera
m_b = np.zeros(nb); np.add.at(m_b, idx[dentro], mdot_i[dentro])
j_b = np.zeros(nb); np.add.at(j_b, idx[dentro], (mdot_i * vn)[dentro])
with np.errstate(divide="ignore", invalid="ignore"):
    Dz = np.where(A_b > 0, m_b * T_VUELTA / A_b, 0.0)       # D por vuelta (identico a la rama B)
    Jz = np.where(A_b > 0, j_b * T_VUELTA / A_b, 0.0)
cuenta = A_ef > 0
A_tot = A_ef[cuenta].sum()

# ------------------------------------------------------------------ KPIs
conmasa = (Dz > 0) & cuenta
cv = float(np.std(Dz[conmasa]) / np.mean(Dz[conmasa])) if conmasa.sum() > 1 else float("nan")
D_media = float((Dz * A_ef)[cuenta].sum() / A_tot)
seca = float(A_ef[cuenta & (Dz <= SECO)].sum() / A_tot)
J_media = float((Jz * A_ef)[cuenta].sum() / A_tot)
mdot_dep = float(mdot_i[dentro].sum())
eta = (100 * mdot_dep / A.mdot_inyectado) if A.mdot_inyectado else float("nan")

# huella en el rotor congelado: celdas (banda fina x arco) con deposito
dc = A.celda_huella_mm * 1e-3
nbc = int(math.ceil((hi - lo) / dc - 1e-9))
bc = np.minimum(lo + dc * np.arange(nbc + 1), hi)
ic = np.clip(np.digitize(s, bc) - 1, 0, nbc - 1)
arco = radio_arco(0.5 * (bc[ic] + bc[np.minimum(ic + 1, nbc)])) * np.radians(th)
jc = np.floor(arco / dc).astype(int)
celdas = {}
for a, b, mv in zip(ic[dentro], jc[dentro], (mdot_raw * vn)[dentro]):   # CFD03: sin --factor (una huella)
    celdas[(a, b)] = celdas.get((a, b), 0.0) + mv
A_huella = 0.0
for (a, b) in celdas:
    s0, s1 = bc[a], bc[min(a + 1, nbc)]
    if A.superficie == "anillo":
        A_huella += 0.5 * (s0 + s1) * (s1 - s0) * (dc / (0.5 * (s0 + s1)))   # = (s1-s0)*dc
    else:
        A_huella += (s1 - s0) * dc
p_huella = sum(celdas.values()) / A_huella if A_huella > 0 else float("nan")
# AVISO: con pocas parcelas por celda quedan celdas vacias dentro de la huella y
# p_huella se SOBRESTIMA (prueba sintetica: ~2 parcelas/celda -> +15 %).
# Exigir >= 10 parcelas/celda o aumentar --celda-huella-mm (ver P10: sesgo por parcelas).
vn_med = float((mdot_i * vn)[dentro].sum() / mdot_dep) if mdot_dep > 0 else float("nan")

# ------------------------------------------------------------------ salidas
os.makedirs(A.salida, exist_ok=True)
pre = os.path.join(A.salida, A.caso + "_")


def esc(nombre, cab, filas):
    with open(pre + nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(filas)
    print("escrito %s (%d filas)" % (pre + nombre, len(filas)))


esc("dosis_por_banda.csv",
    ["s_centro_mm", "mdot_banda_kg_s", "D_kg_m2_vuelta", "J_N_s_m2_vuelta", "area_banda_m2",
     "fraccion_excluida"],
    [["%.2f" % (sc[k] * 1e3), "%.6e" % m_b[k], "%.6f" % Dz[k], "%.6e" % Jz[k], "%.6f" % A_b[k],
      "%.4f" % frac_excl[k]] for k in range(nb)])

umbrales = np.unique(np.concatenate([np.logspace(-2, 1.4, 60), [0.1, 1.0, 5.0, 7.61, 10.0]]))
esc("cobertura.csv", ["D_min_kg_m2_vuelta", "cobertura_pct"],
    [["%.4f" % u, "%.4f" % (100 * A_ef[cuenta & (Dz >= u)].sum() / A_tot)] for u in umbrales])

filas_b = []
for b_ in sorted(set(boq[dentro].tolist())):
    k = (boq == b_) & dentro
    filas_b.append([b_, int(k.sum()), "%.6e" % mdot_i[k].sum(),
                    "%.2f" % (100 * mdot_i[k].sum() / mdot_dep),
                    "%.2f" % (s[k].min() * 1e3), "%.2f" % (s[k].max() * 1e3)])
esc("por_boquilla.csv", ["boquilla", "impactos", "mdot_kg_s", "pct_masa", "s_min_mm", "s_max_mm"], filas_b)

ind = dict(
    caso=A.caso, superficie=A.superficie, modo=A.modo, banda_mm=A.banda_mm,
    T_vuelta_s="%.3f" % T_VUELTA,
    n_impactos=int(dentro.sum()), n_fuera_de_limites=int(fuera.sum()),
    mdot_depositado_kg_s="%.6f" % mdot_dep,
    K5_eta_pct="%.2f" % eta,
    K2_D_media_kg_m2_vuelta="%.4f" % D_media,
    K2_D_min="%.4f" % Dz[cuenta].min(), K2_D_max="%.4f" % Dz[cuenta].max(),
    K3_CV="%.4f" % cv,
    K4_zona_seca_pct="%.3f" % (100 * seca),
    K4_cob_Dmin_1_pct="%.2f" % (100 * A_ef[cuenta & (Dz >= 1.0)].sum() / A_tot),
    K4_cob_Dmin_5_pct="%.2f" % (100 * A_ef[cuenta & (Dz >= 5.0)].sum() / A_tot),
    K6_J_media_N_s_m2_vuelta="%.5f" % J_media,
    K6_p_huella_Pa="%.2f" % p_huella,
    K6_vn_medio_m_s="%.3f" % vn_med,
    A_huella_m2="%.6f" % A_huella,
    parcelas_por_celda_huella="%.2f" % (dentro.sum() / max(len(celdas), 1)),
    area_que_cuenta_m2="%.6f" % A_tot,
)
esc("indicadores.csv", list(ind.keys()), [list(ind.values())])
print("  D media = %s | CV = %s | seca = %s %% | eta = %s %% | p_huella = %s Pa"
      % (ind["K2_D_media_kg_m2_vuelta"], ind["K3_CV"], ind["K4_zona_seca_pct"],
         ind["K5_eta_pct"], ind["K6_p_huella_Pa"]))
