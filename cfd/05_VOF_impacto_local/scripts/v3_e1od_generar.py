#!/usr/bin/env python3
"""
CORRIDA 2 · T3/T2 · E1-OD: lamina plana 2D que incide normal sobre la pared, con el espesor de la lamina en el OD.
Derivado de v3_e1_generar.py (E1, e0 = 0,30 mm; copia de la tanda 1). Cambios:
  1. Espesor e0 parametrico (--e0, por defecto 0,049 mm = lamina de LAT_3_A si llegara intacta a 130,35 mm).
     TODAS las longitudes del dominio y de la malla y los tiempos (fin, escritura, muestreo) se escalan con
     S = e0 / 0,30 mm, asi que N (celdas en el espesor) significa lo mismo que en E1 y el numero de pasos por
     tiempo adimensional t*v/e0 tambien. Lo que NO se escala es la fisica viscosa y capilar (Re = rho v e0/mu
     baja de 1,8e4 a 2,9e3): eso es justo lo que E1-OD mide.
  2. Gravedad parametrica (--g gx gy gz). En el corte x-y (x a lo largo de la pared, y normal a ella):
       g = (0, -9.81, 0): gravedad hacia la pared (chorro vertical hacia abajo: cara superior), simetrica;
       g = (0, +9.81, 0): gravedad alejandose de la pared (chorro hacia arriba: cara inferior), simetrica;
       g = (-9.81, 0, 0): gravedad a lo largo de la pared (abanico girado 90 grados, I3 falso): asimetrica,
                          exige --completo (dominio a ambos lados del eje).
     La gravedad del OD real (-z) queda fuera del plano y no se puede representar en 2D (ver
     NUMEROS_ADIMENSIONALES_v3.md §4); con la formulacion p_rgh de interFoam una g en una direccion ciclica la
     absorbe la presion hidrostatica, por eso no se usa el «2,5D ciclico» del prompt.
  3. --completo: dominio completo -LX..LX (salida a la atmosfera en ambos extremos, sin plano de simetria).
  4. Perfiles normales a la pared (function object 'sets', en cada escritura) en x = S*(0,5 1 2 4 5 8 10) mm,
     es decir, en las mismas posiciones adimensionales x/e0 que E1 y B4; en --completo tambien en -x.
Velocidad: la de E1 (27,4711 m/s, salida de LAT_3_A, sin frenado por el aire): lamina intacta = cota superior.

Uso: python -I v3_e1od_generar.py --N 20 [--e0 0.049e-3] [--co 0.5] [--g 0 0 0] [--completo] [--np 2]
     [--tfin <s>] [--nombre X] [--raiz D:/.../02_VOF_v3/casos_e1od]
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from msh_writer import write_structured  # noqa: E402  (copia sin editar, SHA-256 0841df58...)

BASE = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
E0_REF = 0.30e-3                     # espesor de E1 (m), referencia del escalado
V0 = 27.4711                         # m/s, como E1 (tabla_maestra_22_boquillas.csv, LAT_3_A)
RHO_W, MU_W = 982.12, 4.5227e-4      # agua 62 C
RHO_A, MU_A = 0.9061, 1.825e-5       # aire a 76 240 Pa
SIGMA = 0.0662                       # N/m
XR_LINEAS = (0.5, 1, 2, 4, 5, 8, 10)  # posiciones de E1 en mm; en E1-OD se multiplican por S


def tramo_geom(L, n, E):
    """n celdas en longitud L con razon ultima/primera = E (E>1 crece). Devuelve los n tamanos."""
    if n == 1 or abs(E - 1) < 1e-12:
        return np.full(n, L / n)
    r = E ** (1.0 / (n - 1))
    a = L * (r - 1) / (r ** n - 1)
    return a * r ** np.arange(n)


def distribucion(tramos, N):
    s = []
    for L, n5, E in tramos:
        n = int(round(n5 * N / 5))
        s.append(tramo_geom(L, n, E))
    return np.concatenate([[0.0], np.cumsum(np.concatenate(s))])


def geometria(e0):
    S = e0 / E0_REF
    return dict(S=S, E0=e0, H=20e-3 * S, LX=15e-3 * S, B=1e-4 * S, Y_COL=2e-3 * S)


def nodos(N, G, completo=False):
    """Igual que E1 (mismos tramos y razones), con longitudes escaladas por S."""
    S, LX, H = G["S"], G["LX"], G["H"]
    x = distribucion([(0.84e-3 * S, 14, 1.0), (LX - 0.84e-3 * S, 60, 10.0)], N)
    y = distribucion([(0.12e-3 * S, 3, 3.0), (0.72e-3 * S, 12, 1.0), (H - 0.84e-3 * S, 50, 20.0)], N)
    x[-1], y[-1] = LX, H
    if completo:
        x = np.concatenate([-x[::-1], x[1:]])
    return x, y


def malla(path, N, G, completo):
    E0 = G["E0"]
    x, y = nodos(N, G, completo)
    z = np.array([0.0, G["B"]])
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    xc = 0.5 * (x[1:] + x[:-1])
    hx = np.diff(x)

    def techo(i, k):
        # celda del techo: entrada (lamina), entrada al 50 % (N impar, celda partida por el borde) o atmosfera
        a, b = abs(xc[i]) - hx[i] / 2, abs(xc[i]) + hx[i] / 2
        if b <= E0 / 2 * (1 + 1e-9):
            return ("entrada", "velocity-inlet")
        if a < E0 / 2 * (1 - 1e-9):
            return ("entrada_media", "velocity-inlet")
        return ("atmosfera", "pressure-outlet")

    bc = {"imin": ("salida", "pressure-outlet") if completo else ("simetria", "symmetry"),
          "imax": ("salida", "pressure-outlet"), "jmin": ("pared", "wall"), "jmax": techo,
          "kmin": ("frenteYfondo", "symmetry"), "kmax": ("frenteYfondo", "symmetry")}
    info = write_structured(path, X, Y, Z, bc, title=f"lamina2D_OD N{N}")
    hy = np.diff(y)
    ent = [i for i in range(len(xc)) if techo(i, 0)[0] != "atmosfera"]
    info.update(dict(N=N, delta_m=E0 / N, nx=len(hx), ny=len(hy), dx_min=hx.min(), dx_max=hx.max(),
                     dy_min=hy.min(), dy_max=hy.max(), dy_pared=hy[0],
                     AR_max_xy=float(max((hx.max() / hy.min()), (hy.max() / hx.min()))),
                     x_entrada_min=float(x[min(ent)]), x_entrada_max=float(x[max(ent) + 1]), n_entrada=len(ent)))
    return info


CAB = """/*--------------------------------*- C++ -*----------------------------------*\\
  Generado por v3_e1od_generar.py (CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3). OpenFOAM v2606 (ESI).
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


def lineas(G, completo):
    S, B = G["S"], G["B"]
    yfin = 3e-3 * S
    txt = []
    for xr in XR_LINEAS:
        xm = xr * 1e-3 * S
        nom = ("xr%g" % xr).replace(".", "p")
        txt.append(f"            {nom} {{ type midPoint; axis y; start ({xm:.8g} 1e-12 {B / 2:.6g}); "
                   f"end ({xm:.8g} {yfin:.6g} {B / 2:.6g}); }}")
        if completo:
            txt.append(f"            m{nom} {{ type midPoint; axis y; start ({-xm:.8g} 1e-12 {B / 2:.6g}); "
                       f"end ({-xm:.8g} {yfin:.6g} {B / 2:.6g}); }}")
    xe = 1e-7 * G["S"]
    txt.append(f"            eje {{ type midPoint; axis y; start ({xe:.6g} 1e-12 {B / 2:.6g}); "
               f"end ({xe:.6g} {yfin:.6g} {B / 2:.6g}); }}")
    return "\n".join(txt)


def control(a, G):
    return f"""
application     interFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {a.tfin:.8g};
deltaT          1e-10;
writeControl    adjustable;
writeInterval   {a.tescr:.8g};
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
maxDeltaT       {1e-5 * G["S"]:.6g};

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
        writeInterval   {a.tsup:.8g};
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
    lineas
    {{
        type            sets;
        libs            (sampling);
        interpolationScheme cell;
        setFormat       raw;
        writeControl    writeTime;
        fields          (alpha.water U p);
        sets
        {{
{lineas(G, a.completo)}
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
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes   { default corrected; }
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
    "U.*"
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


def campos(caso, completo):
    lat = "    salida      { type %s; }\n"
    sim = "" if completo else "    simetria { type symmetry; }\n"
    comunes = sim + "    frenteYfondo { type empty; }\n"
    escribir(caso, "0/U", "volVectorField", f"""
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{{
    pared       {{ type noSlip; }}
    entrada     {{ type fixedValue; value uniform (0 {-V0:.6g} 0); }}
    entrada_media {{ type fixedValue; value uniform (0 {-V0:.6g} 0); }}
    atmosfera   {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
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
    entrada_media {{ type fixedFluxPressure; value uniform 0; }}
    atmosfera   {{ type totalPressure; p0 uniform 0; }}
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
    entrada_media {{ type fixedValue; value uniform 0.5; }}
    atmosfera   {{ type inletOutlet; inletValue uniform 0; value uniform 0; }}
    salida      {{ type inletOutlet; inletValue uniform 0; value uniform 0; }}
{comunes}}}
""")


def generar(a):
    G = geometria(a.e0)
    S, E0 = G["S"], G["E0"]
    a.tfin = a.tfin if a.tfin else 1.2e-3 * S
    a.tescr = a.tescr if a.tescr else 1e-4 * S
    a.tsup = a.tsup if a.tsup else 1e-5 * S
    caso = os.path.join(a.raiz, a.nombre)
    if os.path.exists(caso):
        raise SystemExit("ya existe %s (no se sobrescribe)" % caso)
    os.makedirs(caso)
    info = malla(os.path.join(caso, "malla.msh"), a.N, G, a.completo)
    escribir(caso, "system/controlDict", "dictionary", control(a, G))
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
    # columna inicial de agua: x en el ancho de la entrada (a 0,5 la celda partida si N es impar)
    xe = info["x_entrada_max"]
    x1 = E0 / 2 if a.N % 2 == 0 else (a.N // 2) * E0 / a.N
    reg = f"""    boxToCell
    {{
        box ({-x1 if a.completo else -1:.10g} {G['Y_COL']:.8g} -1) ({x1:.10g} 1 1);
        fieldValues ( volScalarFieldValue alpha.water 1 volVectorFieldValue U (0 {-V0:.6g} 0) );
    }}
"""
    if a.N % 2 == 1:
        reg += f"""    boxToCell
    {{
        box ({x1:.10g} {G['Y_COL']:.8g} -1) ({x1 + E0 / a.N:.10g} 1 1);
        fieldValues ( volScalarFieldValue alpha.water 0.5 volVectorFieldValue U (0 {-V0:.6g} 0) );
    }}
"""
        if a.completo:
            reg += f"""    boxToCell
    {{
        box ({-x1 - E0 / a.N:.10g} {G['Y_COL']:.8g} -1) ({-x1:.10g} 1 1);
        fieldValues ( volScalarFieldValue alpha.water 0.5 volVectorFieldValue U (0 {-V0:.6g} 0) );
    }}
"""
    escribir(caso, "system/setFieldsDict", "dictionary", f"""
defaultFieldValues ( volScalarFieldValue alpha.water 0 volVectorFieldValue U (0 0 0) );
regions
(
{reg});
""")
    gx, gy, gz = a.g
    escribir(caso, "constant/g", "uniformDimensionedVectorField",
             f"dimensions [0 1 -2 0 0 0 0];\nvalue ({gx:g} {gy:g} {gz:g});\n")
    escribir(caso, "constant/transportProperties", "dictionary", f"""
phases          (water air);
water           {{ transportModel Newtonian; nu {MU_W / RHO_W:.6g}; rho {RHO_W:g}; }}
air             {{ transportModel Newtonian; nu {MU_A / RHO_A:.6g}; rho {RHO_A:g}; }}
sigma           {SIGMA:g};
""")
    escribir(caso, "constant/turbulenceProperties", "dictionary", "simulationType  laminar;\n")
    campos(caso, a.completo)
    meta = dict(nombre=a.nombre, N=a.N, co=a.co, modelo="laminar", tfin=a.tfin, tescr=a.tescr, tsup=a.tsup,
                np=a.np, E0=E0, E0_ref=E0_REF, S=S, V0=V0, H=G["H"], LX=G["LX"], B=G["B"], Y_COL=G["Y_COL"],
                g=[gx, gy, gz], completo=bool(a.completo), x_lineas_mm=[xr * S for xr in XR_LINEAS],
                xr_lineas_mm_E1=list(XR_LINEAS), rho_w=RHO_W, mu_w=MU_W, rho_a=RHO_A, mu_a=MU_A, sigma=SIGMA,
                Re_lamina=RHO_W * V0 * E0 / MU_W, x1_columna=x1, x_entrada_max_malla=xe,
                malla={k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in info.items()})
    json.dump(meta, open(os.path.join(caso, "meta.json"), "w"), indent=1, default=float)
    print(json.dumps({k: meta["malla"][k] for k in ("celdas", "nx", "ny", "dx_min", "dy_pared", "AR_max_xy",
                                                     "n_entrada", "x_entrada_min", "x_entrada_max")}, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--e0", type=float, default=0.049e-3)
    ap.add_argument("--co", type=float, default=0.5)
    ap.add_argument("--g", type=float, nargs=3, default=[0.0, 0.0, 0.0])
    ap.add_argument("--completo", action="store_true")
    ap.add_argument("--tfin", type=float, default=None)
    ap.add_argument("--tescr", type=float, default=None)
    ap.add_argument("--tsup", type=float, default=None)
    ap.add_argument("--np", type=int, default=1)
    ap.add_argument("--nombre")
    ap.add_argument("--raiz", default=BASE + "/casos_e1od")
    a = ap.parse_args()
    if a.g[0] != 0 and not a.completo:
        raise SystemExit("g a lo largo de la pared (x) rompe la simetria: use --completo")
    if not a.nombre:
        gtag = "" if not any(a.g) else "_g%s" % "_".join("%g" % v for v in a.g)
        a.nombre = f"OD_N{a.N}_Co{a.co:g}{gtag}{'_completo' if a.completo else ''}"
    generar(a)
