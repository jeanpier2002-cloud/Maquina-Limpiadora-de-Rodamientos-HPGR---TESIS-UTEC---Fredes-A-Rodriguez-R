#!/usr/bin/env python3
# v3 (CORRIDA 2, 24/10/2026): copia de CORRIDA_1_13a21oct/06_VOF/scripts/e1_generar.py con rutas cambiadas a 02_VOF_v3 y /home/piermoto/vof3 (sed); sin otros cambios.
"""
Etapa 1 - Lamina plana 2D que incide normal sobre una pared (interFoam, OpenFOAM v2606 ESI).

Genera un caso completo (malla Fluent .msh con msh_writer.py + diccionarios de OpenFOAM) en
D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/casos_e1/<nombre>/. El script de WSL e1_correr.sh lo copia a /home/piermoto/vof3/e1/,
convierte la malla con fluentMeshToFoam y corre interFoam.

Geometria (medio dominio, plano de simetria en el eje del chorro):
  x: a lo largo de la pared, 0 = eje del chorro (simetria) ... LX = 15 mm (salida a la atmosfera)
  y: normal a la pared, 0 = pared ... H = 20 mm (plano de entrada del chorro)
  z: una celda de espesor B (2D, 'empty').
Chorro: lamina de espesor E0 = 0,30 mm (semiancho 0,15 mm en el medio dominio), v = 27,4711 m/s,
agua a 62 C. Entrada en y = H, 0 <= x <= E0/2.

Malla: producto tensorial de dos distribuciones 1D por tramos (uniforme + crecimiento geometrico),
definidas en funcion de N = celdas a traves del espesor E0 (Delta = E0/N). Al duplicar N se
duplica el numero de celdas de cada tramo con la misma razon de expansion total del tramo
(refinamiento sistematico, como simpleGrading de blockMesh).

Uso: python e1_generar.py --N 20 --co 0.5 [--modelo laminar|kOmegaSST] [--tfin 1.2e-3] [--nombre X]
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from msh_writer import write_structured  # noqa: E402  (copia sin editar de CFD03, SHA-256 0841df58...)

# ---------------------------------------------------------------- datos fisicos (PROMPT §2 y §4)
E0 = 0.30e-3            # espesor de la lamina (m), PROMPT §5 etapa 1
V0 = 27.4711            # velocidad de salida LAT_3_A (m/s), tabla_maestra_22_boquillas.csv
RHO_W, MU_W = 982.12, 4.5227e-4      # agua 62 C (CLAUDE.md, PROMPT §2.1)
RHO_A, MU_A = 0.9061, 1.825e-5       # aire a 76 240 Pa (PROMPT §2.1, como Fluent)
SIGMA = 0.0662                       # N/m, agua 62 C (PROMPT §2.1)
H, LX, B = 20e-3, 15e-3, 1e-4        # dominio (m)
Y_COL = 2e-3                         # el chorro se inicializa lleno desde y = 2 mm hasta la entrada


def tramo_geom(L, n, E):
    """n celdas en longitud L con razon ultima/primera = E (E>1 crece). Devuelve los n tamanos."""
    if n == 1 or abs(E - 1) < 1e-12:
        return np.full(n, L / n)
    r = E ** (1.0 / (n - 1))
    a = L * (r - 1) / (r ** n - 1)
    return a * r ** np.arange(n)


def distribucion(tramos, N):
    """tramos: lista de (longitud, n_a_N5, E). E<1 decrece. n se escala con N/5."""
    s = []
    for L, n5, E in tramos:
        n = int(round(n5 * N / 5))
        s.append(tramo_geom(L, n, E))
    h = np.concatenate(s)
    return np.concatenate([[0.0], np.cumsum(h)])


def nodos(N):
    # x: [0, 0,84 mm] uniforme (14 celdas a N=5) + [0,84, 15 mm] crece x10 (60 celdas a N=5)
    x = distribucion([(0.84e-3, 14, 1.0), (LX - 0.84e-3, 60, 10.0)], N)
    # y: [0, 0,12 mm] crece x3 desde la pared (3 celdas a N=5) + [0,12, 0,84] uniforme (12)
    #    + [0,84, 20 mm] crece x20 (50 celdas a N=5)
    y = distribucion([(0.12e-3, 3, 3.0), (0.72e-3, 12, 1.0), (H - 0.84e-3, 50, 20.0)], N)
    x[-1], y[-1] = LX, H
    return x, y


def malla(path, N):
    x, y = nodos(N)
    z = np.array([0.0, B])
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    xc = 0.5 * (x[1:] + x[:-1])
    n_in = int(math.ceil(N / 2))             # caras de entrada (N impar: la ultima va al 50 %)

    def techo(i, k):
        if xc[i] < E0 / 2:
            return ("entrada", "velocity-inlet")
        if i < n_in:
            return ("entrada_media", "velocity-inlet")
        return ("atmosfera", "pressure-outlet")

    bc = {"imin": ("simetria", "symmetry"), "imax": ("salida", "pressure-outlet"),
          "jmin": ("pared", "wall"), "jmax": techo,
          "kmin": ("frenteYfondo", "symmetry"), "kmax": ("frenteYfondo", "symmetry")}
    info = write_structured(path, X, Y, Z, bc, title=f"lamina2D N{N}")
    hx, hy = np.diff(x), np.diff(y)
    info.update(dict(N=N, delta_m=E0 / N, nx=len(hx), ny=len(hy), dx_min=hx.min(), dx_max=hx.max(),
                     dy_min=hy.min(), dy_max=hy.max(), dy_pared=hy[0],
                     AR_max_xy=float(max((hx.max() / hy.min()), (hy.max() / hx.min()))),
                     x_entrada_max=float(x[n_in]), n_entrada=n_in))
    return info


# ---------------------------------------------------------------- diccionarios
CAB = """/*--------------------------------*- C++ -*----------------------------------*\\
  Generado por e1_generar.py (CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3). OpenFOAM v2606 (ESI).
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    object      {obj};
}}
"""


def escribir(caso, rel, cls, cuerpo):
    p = os.path.join(caso, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="\n") as f:
        f.write(CAB.format(cls=cls, obj=os.path.basename(rel)) + cuerpo.strip() + "\n")


def control(a):
    return f"""
application     interFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {a.tfin:g};
deltaT          1e-09;
writeControl    adjustable;
writeInterval   {a.tescr:g};
purgeWrite      0;
writeFormat     binary;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable yes;
adjustTimeStep  yes;
maxCo           {a.co:g};
maxAlphaCo      {a.co:g};
maxDeltaT       1e-05;

functions
{{
    wallShearStress
    {{
        type            wallShearStress;
        libs            (fieldFunctionObjects);
        writeFields     yes;
        patches         (pared);
        executeControl  timeStep;
        writeControl    writeTime;
    }}
    fuerzas
    {{
        type            forces;
        libs            (forces);
        patches         (pared);
        rho             rho;
        CofR            (0 0 0);
        log             off;
        writeControl    timeStep;
        writeInterval   1;
    }}
    paredSup
    {{
        type            surfaces;
        libs            (sampling);
        interpolationScheme cell;
        surfaceFormat   raw;
        writeControl    adjustableRunTime;
        writeInterval   {a.tsup:g};
        fields          (alpha.water p rho wallShearStress);
        surfaces
        {{
            pared
            {{
                type        patch;
                patches     (pared);
                interpolate false;
                triangulate false;
            }}
        }}
    }}
}}
"""


ESQ = """
ddtSchemes      { default Euler; }
gradSchemes     { default Gauss linear; }
divSchemes
{
    default         none;
    div(rhoPhi,U)   Gauss linearUpwind grad(U);
    div(phi,alpha)  Gauss vanLeer;
    div(phirb,alpha) Gauss linear;
    "div\\(phi,(k|omega)\\)" Gauss upwind;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes   { default corrected; }
wallDist        { method meshWave; }
"""

SOL = """
solvers
{
    "alpha.water.*"
    {
        nAlphaCorr      2;
        nAlphaSubCycles 1;
        cAlpha          1;
        MULESCorr       yes;
        nLimiterIter    5;
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0;
    }
    "pcorr.*"
    {
        solver          PCG;
        preconditioner  { preconditioner GAMG; tolerance 1e-5; relTol 0; smoother GaussSeidel; }
        tolerance       1e-5;
        relTol          0;
        maxIter         50;
    }
    p_rgh
    {
        // banco e1_banco_presion.sh (N40, 4 rangos): GAMG+GaussSeidel relTol 0.01 = 2,68 s/paso (104 it);
        // GAMG+DIC relTol 0.05 = 0,93 s/paso (16 it). Misma tolerancia absoluta 1e-7.
        solver          GAMG;
        smoother        DIC;
        tolerance       1e-7;
        relTol          0.05;
    }
    p_rghFinal
    {
        $p_rgh;
        relTol          0;
    }
    "(U|k|omega).*"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-7;
        relTol          0;
    }
}
PIMPLE
{
    momentumPredictor   no;
    nOuterCorrectors    1;
    nCorrectors         3;
    nNonOrthogonalCorrectors 0;
}
relaxationFactors { equations { ".*" 1; } }
"""


def campos(caso, a, N):
    ras = a.modelo != "laminar"
    media = (N % 2 == 1)
    ent_media_U = "    entrada_media { type fixedValue; value uniform (0 %.6g 0); }\n" % (-V0) if media else ""
    ent_media_a = "    entrada_media { type fixedValue; value uniform 0.5; }\n" if media else ""
    ent_media_p = "    entrada_media { type fixedFluxPressure; value uniform 0; }\n" if media else ""
    comunes = "    simetria { type symmetry; }\n    frenteYfondo { type empty; }\n"
    escribir(caso, "0/U", "volVectorField", f"""
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{{
    pared       {{ type noSlip; }}
    entrada     {{ type fixedValue; value uniform (0 {-V0:.6g} 0); }}
{ent_media_U}    atmosfera   {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
    salida      {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
{comunes}}}
""")
    escribir(caso, "0/p_rgh", "volScalarField", f"""
dimensions      [1 -1 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{{
    pared       {{ type fixedFluxPressure; value uniform 0; }}
    entrada     {{ type fixedFluxPressure; value uniform 0; }}
{ent_media_p}    atmosfera   {{ type totalPressure; p0 uniform 0; }}
    salida      {{ type totalPressure; p0 uniform 0; }}
{comunes}}}
""")
    escribir(caso, "0/alpha.water", "volScalarField", f"""
dimensions      [0 0 0 0 0 0 0];
internalField   uniform 0;
boundaryField
{{
    pared       {{ type zeroGradient; }}
    entrada     {{ type fixedValue; value uniform 1; }}
{ent_media_a}    atmosfera   {{ type inletOutlet; inletValue uniform 0; value uniform 0; }}
    salida      {{ type inletOutlet; inletValue uniform 0; value uniform 0; }}
{comunes}}}
""")
    if ras:
        I, Lm = 0.05, 0.07 * E0           # intensidad 5 % y escala 0,07*e0 (SUPUESTO, declarado)
        k_in = 1.5 * (I * V0) ** 2
        om_in = math.sqrt(k_in) / (0.09 ** 0.25 * Lm)
        k0, om0 = 1e-6, 10.0
        for nom, dim, vin, v0, wf in (("k", "[0 2 -2 0 0 0 0]", k_in, k0, "kqRWallFunction"),
                                      ("omega", "[0 0 -1 0 0 0 0]", om_in, om0, "omegaWallFunction")):
            med = f"    entrada_media {{ type fixedValue; value uniform {vin:.6g}; }}\n" if media else ""
            escribir(caso, f"0/{nom}", "volScalarField", f"""
dimensions      {dim};
internalField   uniform {v0:g};
boundaryField
{{
    pared       {{ type {wf}; value uniform {v0:g}; }}
    entrada     {{ type fixedValue; value uniform {vin:.6g}; }}
{med}    atmosfera   {{ type inletOutlet; inletValue uniform {v0:g}; value uniform {v0:g}; }}
    salida      {{ type inletOutlet; inletValue uniform {v0:g}; value uniform {v0:g}; }}
{comunes}}}
""")
        escribir(caso, "0/nut", "volScalarField", """
dimensions      [0 2 -1 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    pared       { type nutkWallFunction; value uniform 0; }
    ".*"        { type calculated; value uniform 0; }
    simetria    { type symmetry; }
    frenteYfondo { type empty; }
}
""")
        a._k_in, a._om_in = k_in, om_in


def generar(a):
    caso = os.path.join(a.raiz, a.nombre)
    os.makedirs(caso, exist_ok=True)
    info = malla(os.path.join(caso, "malla.msh"), a.N)
    escribir(caso, "system/controlDict", "dictionary", control(a))
    escribir(caso, "system/fvSchemes", "dictionary", ESQ)
    escribir(caso, "system/fvSolution", "dictionary", SOL)
    escribir(caso, "system/decomposeParDict", "dictionary",
             f"numberOfSubdomains {a.np};\nmethod {'scotch' if a.np > 1 else 'simple'};\n"
             "coeffs { n (1 1 1); }\n")
    escribir(caso, "system/changeDictionaryDict", "dictionary", """
boundary
{
    frenteYfondo { type empty; inGroups 1(empty); }
}
""")
    x1 = E0 / 2 if a.N % 2 == 0 else (a.N // 2) * E0 / a.N
    turb = ""
    if a.modelo != "laminar":   # la columna inicial lleva la turbulencia de la entrada
        campos(caso, a, a.N)
        turb = f" volScalarFieldValue k {a._k_in:.6g} volScalarFieldValue omega {a._om_in:.6g}"
    reg = f"""    boxToCell
    {{
        box (-1 {Y_COL:g} -1) ({x1:.10g} 1 1);
        fieldValues ( volScalarFieldValue alpha.water 1 volVectorFieldValue U (0 {-V0:.6g} 0){turb} );
    }}
"""
    if a.N % 2 == 1:
        reg += f"""    boxToCell
    {{
        box ({x1:.10g} {Y_COL:g} -1) ({x1 + E0 / a.N:.10g} 1 1);
        fieldValues ( volScalarFieldValue alpha.water 0.5 volVectorFieldValue U (0 {-V0:.6g} 0){turb} );
    }}
"""
    escribir(caso, "system/setFieldsDict", "dictionary", f"""
defaultFieldValues ( volScalarFieldValue alpha.water 0 volVectorFieldValue U (0 0 0) );
regions
(
{reg});
""")
    escribir(caso, "constant/g", "uniformDimensionedVectorField",
             "dimensions [0 1 -2 0 0 0 0];\nvalue (0 0 0);\n")
    escribir(caso, "constant/transportProperties", "dictionary", f"""
phases          (water air);
water           {{ transportModel Newtonian; nu {MU_W / RHO_W:.6g}; rho {RHO_W:g}; }}
air             {{ transportModel Newtonian; nu {MU_A / RHO_A:.6g}; rho {RHO_A:g}; }}
sigma           {SIGMA:g};
""")
    if a.modelo == "laminar":
        tp = "simulationType  laminar;\n"
    else:
        tp = f"simulationType  RAS;\nRAS {{ RASModel {a.modelo}; turbulence on; printCoeffs on; }}\n"
    escribir(caso, "constant/turbulenceProperties", "dictionary", tp)
    campos(caso, a, a.N)
    meta = dict(nombre=a.nombre, N=a.N, co=a.co, modelo=a.modelo, tfin=a.tfin, np=a.np, E0=E0, V0=V0,
                H=H, LX=LX, B=B, Y_COL=Y_COL, rho_w=RHO_W, mu_w=MU_W, rho_a=RHO_A, mu_a=MU_A, sigma=SIGMA,
                malla={k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in info.items()})
    if a.modelo != "laminar":
        meta.update(k_entrada=a._k_in, omega_entrada=a._om_in)
    json.dump(meta, open(os.path.join(caso, "meta.json"), "w"), indent=1, default=float)
    print(json.dumps({k: meta["malla"][k] for k in ("celdas", "nx", "ny", "dx_min", "dy_min", "dy_pared",
                                                    "AR_max_xy", "n_entrada", "x_entrada_max")}, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--co", type=float, default=0.5)
    ap.add_argument("--modelo", default="laminar")
    ap.add_argument("--tfin", type=float, default=1.2e-3)
    ap.add_argument("--tescr", type=float, default=1e-4)
    ap.add_argument("--tsup", type=float, default=1e-5)
    ap.add_argument("--np", type=int, default=1)
    ap.add_argument("--nombre")
    ap.add_argument("--raiz", default="D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/casos_e1")
    a = ap.parse_args()
    if not a.nombre:
        a.nombre = f"N{a.N}_Co{a.co:g}_{'lam' if a.modelo == 'laminar' else a.modelo}"
    generar(a)
