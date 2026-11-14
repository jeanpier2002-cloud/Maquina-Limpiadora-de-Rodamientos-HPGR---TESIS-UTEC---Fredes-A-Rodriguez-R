#!/usr/bin/env python3
"""
Generador de la tabla de inyeccion de un abanico plano para
KinematicLookupTableInjection de OpenFOAM v2606.

Formato que exige OpenFOAM (leido de kinematicParcelInjectionDataIO.C):
    (Px Py Pz) (Ux Uy Uz) d rho mDot

Geometria (decision del usuario, 19/09/2026):
  - el VERTICE del abanico esta en el orificio, h mm detras de la punta
  - los parcels NACEN en el plano de la punta, sobre el rayo que sale del vertice
  Asi el abanico es geometricamente exacto y ninguna gota aparece dentro del metal.

Notas de fisica declaradas (no hay dato de fabricante):
  - El reparto de masa a lo largo del abanico se controla con la DENSIDAD DE
    ENTRADAS, no con mDot: con parcelBasisType=mass todos los parcels llevan la
    misma masa (ver InjectionModel.C, setNumberOfParticles, caso pbMass).
  - El semiangulo fuera del plano (espesor del abanico) NO tiene dato. Es el
    parametro que el ensayo de huella debe fijar. Por defecto 2 grados.
  - El diametro se muestrea de una Rosin-Rammler EN MASA, porque los parcels
    llevan masa igual: asi la distribucion de masa por tamano es la pedida.

Uso:
    python gen_abanico.py --salida <archivo> [opciones]
    python gen_abanico.py --help
"""
import argparse
import csv
import math
import os
import sys

import numpy as np

# ---------------------------------------------------------------- parametros
P = argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
P.add_argument("--salida", required=True, help="archivo de tabla para OpenFOAM")
P.add_argument("--csv", default=None, help="copia de la tabla en CSV para el registro")
P.add_argument("--vertice", nargs=3, type=float, default=[0.0, 0.0, 0.0],
               metavar=("X", "Y", "Z"), help="vertice del abanico (orificio), en m")
P.add_argument("--eje", nargs=3, type=float, default=[0.0, 1.0, 0.0],
               metavar=("X", "Y", "Z"), help="eje de salida (direccion del chorro)")
P.add_argument("--plano-abanico", nargs=3, type=float, default=[0.0, 0.0, 1.0],
               metavar=("X", "Y", "Z"),
               help="normal del plano del abanico; el abanico se abre perpendicular a ella")
P.add_argument("--h-punta-mm", type=float, default=4.5,
               help="distancia vertice->punta medida sobre el eje (mm)")
P.add_argument("--angulo-deg", type=float, default=50.0, help="angulo total del abanico")
P.add_argument("--angulo-fuera-deg", type=float, default=2.0,
               help="angulo total fuera del plano (espesor del abanico). SIN DATO: lo fija el ensayo")
P.add_argument("--n-plano", type=int, default=60, help="muestras en el plano del abanico")
P.add_argument("--n-fuera", type=int, default=5, help="muestras fuera del plano")
P.add_argument("--reparto", choices=["angulo", "huella"], default="angulo",
               help="masa uniforme por unidad de angulo, o uniforme a lo largo de la huella plana")
P.add_argument("--muestreo", choices=["extremos", "centros"], default="extremos",
               help="extremos: los rayos extremos caen justo en +-angulo/2, asi la huella mide "
                    "exactamente lo nominal (a cambio, las dos entradas de borde pesan de mas "
                    "en ~1/n_plano). centros: masa estrictamente uniforme, pero el abanico "
                    "resulta algo mas estrecho que el nominal")
P.add_argument("--q-lmin", type=float, default=9.11766505450028, help="caudal de la boquilla, L/min")
P.add_argument("--rho-liq", type=float, default=982.1203530851709, help="densidad del agua a 62 C")
P.add_argument("--vel", type=float, default=27.11354121556065, help="modulo de la velocidad de salida, m/s")
P.add_argument("--duracion", type=float, default=0.05, help="duracion de la inyeccion, s (para informar massTotal)")
P.add_argument("--diam", choices=["fijo", "RR"], default="fijo", help="diametro fijo o Rosin-Rammler en masa")
P.add_argument("--d-fijo-um", type=float, default=300.0, help="diametro si --diam fijo, en micras")
P.add_argument("--rr-lambda-um", type=float, default=300.0, help="lambda de Rosin-Rammler, micras")
P.add_argument("--rr-n", type=float, default=2.5, help="exponente n de Rosin-Rammler")
P.add_argument("--rr-dmin-um", type=float, default=50.0, help="diametro minimo, micras")
P.add_argument("--rr-dmax-um", type=float, default=900.0, help="diametro maximo, micras")
P.add_argument("--omega-rad-s", type=float, default=0.0,
               help="giro del rotor: suma omega x r a la velocidad de emision (0 = no)")
P.add_argument("--eje-giro", nargs=3, type=float, default=[0.0, 0.0, 1.0],
               metavar=("X", "Y", "Z"), help="eje de rotacion para omega x r")
A = P.parse_args()


def unit(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < 1e-12:
        sys.exit("ERROR: vector nulo")
    return v / n


# ------------------------------------------------- base local del abanico
vertice = np.asarray(A.vertice, dtype=float)
eje = unit(A.eje)                      # a : direccion del chorro
n_plano = unit(A.plano_abanico)        # normal del plano del abanico
e_fuera = unit(n_plano - np.dot(n_plano, eje) * eje)   # perpendicular al abanico
e_ancho = unit(np.cross(e_fuera, eje))                 # dentro del abanico, transversal
# comprobacion de ortonormalidad (si esto falla, la geometria esta mal dada)
for nom, a_, b_ in (("eje-ancho", eje, e_ancho), ("eje-fuera", eje, e_fuera),
                    ("ancho-fuera", e_ancho, e_fuera)):
    if abs(float(np.dot(a_, b_))) > 1e-9:
        sys.exit("ERROR: base no ortogonal (%s)" % nom)

# ------------------------------------------------- muestreo angular
half_in = math.radians(A.angulo_deg) / 2.0
half_out = math.radians(A.angulo_fuera_deg) / 2.0

def muestras(n, semi):
    """n valores en [-semi, +semi]: en los extremos o en los centros de los intervalos."""
    if n == 1:
        return np.array([0.0])
    if A.muestreo == "extremos":
        return np.linspace(-semi, semi, n)
    return (np.arange(n) + 0.5) / n * 2 * semi - semi


if A.reparto == "angulo":
    # masa uniforme por unidad de angulo
    alfa = muestras(A.n_plano, half_in)
else:
    # masa uniforme a lo largo de la huella sobre un plano perpendicular:
    # se reparte tan(alfa) de forma uniforme
    alfa = np.arctan(muestras(A.n_plano, math.tan(half_in)))

beta = muestras(A.n_fuera, half_out)

AL, BE = np.meshgrid(alfa, beta, indexing="ij")
AL = AL.ravel()
BE = BE.ravel()
N = AL.size

# direcciones unitarias desde el vertice
dirs = (eje[None, :]
        + np.tan(AL)[:, None] * e_ancho[None, :]
        + np.tan(BE)[:, None] * e_fuera[None, :])
dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)

# ------------------------------------------------- posiciones en el plano de la punta
h = A.h_punta_mm * 1e-3
proy = dirs @ eje                      # cos del angulo respecto del eje
if proy.min() <= 1e-6:
    sys.exit("ERROR: alguna direccion no avanza sobre el eje")
pos = vertice[None, :] + (h / proy)[:, None] * dirs

# ------------------------------------------------- velocidades
vel = A.vel * dirs
if A.omega_rad_s != 0.0:
    w = A.omega_rad_s * unit(A.eje_giro)
    vel = vel + np.cross(w[None, :], pos)      # arrastre del rotor

# ------------------------------------------------- diametros
if A.diam == "fijo":
    diam = np.full(N, A.d_fijo_um * 1e-6)
    nota_diam = "fijo %.1f um" % A.d_fijo_um
else:
    # Rosin-Rammler EN MASA: F(d) = 1 - exp(-(d/lambda)^n), cuantiles deterministas
    u = (np.arange(N) + 0.5) / N
    d = A.rr_lambda_um * (-np.log(1.0 - u)) ** (1.0 / A.rr_n)
    d = np.clip(d, A.rr_dmin_um, A.rr_dmax_um) * 1e-6
    # barajado determinista para que el tamano no quede correlacionado con el angulo
    idx = np.argsort((np.arange(N) * 7919) % N)     # 7919 primo, permutacion fija
    diam = d[idx]
    nota_diam = ("RosinRammler en masa lambda=%.1f um n=%.2f acotada [%.0f, %.0f] um"
                 % (A.rr_lambda_um, A.rr_n, A.rr_dmin_um, A.rr_dmax_um))

# ------------------------------------------------- caudales
q_m3_s = A.q_lmin / 60000.0
mdot_total = q_m3_s * A.rho_liq          # kg/s de la boquilla
mdot = np.full(N, mdot_total / N)        # OpenFOAM suma los mDot de todas las entradas
masa_total = mdot_total * A.duracion     # lo que hay que poner en massTotal

# ------------------------------------------------- escritura del diccionario
cab = """/*--------------------------------*- C++ -*----------------------------------*\\
| Tabla de inyeccion de abanico plano, generada por scripts/gen_abanico.py     |
| NO editar a mano: regenerar con el mismo comando y los mismos argumentos.    |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      {obj};
}}
// formato por entrada: (Px Py Pz) (Ux Uy Uz) d rho mDot
// comando : {cmd}
// entradas: {n}  ({nin} en el plano x {nout} fuera del plano)
// abanico : {ang} grados en el plano, {angf} grados fuera del plano (SIN DATO: lo fija el ensayo de huella)
// reparto : masa uniforme por {rep}
// diametro: {nd}
// caudal  : {q} L/min = {md:.9g} kg/s  =>  massTotal = {mt:.9g} kg para duracion = {dur} s
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

""".format(obj=os.path.basename(A.salida), cmd=" ".join(sys.argv[1:]), n=N,
           nin=A.n_plano, nout=A.n_fuera, ang=A.angulo_deg, angf=A.angulo_fuera_deg,
           rep=("unidad de angulo" if A.reparto == "angulo" else "longitud de huella"),
           nd=nota_diam, q=A.q_lmin, md=mdot_total, mt=masa_total, dur=A.duracion)

os.makedirs(os.path.dirname(os.path.abspath(A.salida)), exist_ok=True)
with open(A.salida, "w", newline="\n") as f:
    f.write(cab)
    f.write("(\n")
    for i in range(N):
        f.write("    (%.9g %.9g %.9g) (%.9g %.9g %.9g) %.9g %.9g %.9g\n" % (
            pos[i, 0], pos[i, 1], pos[i, 2],
            vel[i, 0], vel[i, 1], vel[i, 2],
            diam[i], A.rho_liq, mdot[i]))
    f.write(");\n\n// ************************************************************************* //\n")

if A.csv:
    os.makedirs(os.path.dirname(os.path.abspath(A.csv)), exist_ok=True)
    with open(A.csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["i", "alfa_deg", "beta_deg", "Px_m", "Py_m", "Pz_m",
                    "Ux_m_s", "Uy_m_s", "Uz_m_s", "d_um", "rho_kg_m3", "mDot_kg_s"])
        for i in range(N):
            w.writerow([i, "%.6f" % math.degrees(AL[i]), "%.6f" % math.degrees(BE[i]),
                        "%.9g" % pos[i, 0], "%.9g" % pos[i, 1], "%.9g" % pos[i, 2],
                        "%.9g" % vel[i, 0], "%.9g" % vel[i, 1], "%.9g" % vel[i, 2],
                        "%.4f" % (diam[i] * 1e6), "%.6f" % A.rho_liq, "%.9g" % mdot[i]])

# ------------------------------------------------- autocomprobacion
ang_real = math.degrees(np.arccos(np.clip(
    np.dot(dirs[np.argmin(AL)], dirs[np.argmax(AL)]), -1, 1)))
d_media_masa = float((diam ** 3).sum() / (diam ** 2).sum())   # D32 de la tabla
print("tabla escrita          : %s" % A.salida)
print("entradas               : %d" % N)
print("angulo entre extremos  : %.4f grados  (pedido %.4f; la diferencia viene del muestreo y de la proyeccion fuera del plano)"
      % (ang_real, A.angulo_deg))
print("suma de mDot           : %.9g kg/s   (objetivo %.9g)" % (mdot.sum(), mdot_total))
print("massTotal a declarar   : %.9g kg  para duration = %g s" % (masa_total, A.duracion))
print("diametro               : %s   (D32 de la tabla = %.1f um)" % (nota_diam, d_media_masa * 1e6))
print("posiciones: plano de la punta a %.4f mm del vertice sobre el eje" % (A.h_punta_mm,))
print("  semiancho sembrado   : %.4f mm en el plano, %.4f mm fuera del plano"
      % (1e3 * np.abs((pos - vertice) @ e_ancho).max(),
         1e3 * np.abs((pos - vertice) @ e_fuera).max()))
print("velocidad: |U| min/max : %.6f / %.6f m/s" % (
    np.linalg.norm(vel, axis=1).min(), np.linalg.norm(vel, axis=1).max()))
