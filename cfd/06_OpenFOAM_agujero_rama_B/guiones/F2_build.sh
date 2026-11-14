#!/bin/bash
# =============================================================================
#  F2 - Piloto de herramienta: una boquilla contra una placa a 143,3 mm
#  Construye el caso base y las variantes. NO corre nada (eso lo hace F2_run.sh)
#
#  Marco local del piloto, elegido para ser FIEL al caso real:
#     y = direccion del chorro (radial, +Y global en INT_1..INT_5)
#     x = apertura del abanico  (== Z global, vertical: el abanico es radial-vertical)
#     z = fuera del plano del abanico (== acimut theta en la pared del agujero)
#  Por eso la gravedad va en -x, no en -z.
# =============================================================================
source /usr/lib/openfoam/openfoam2606/etc/bashrc

BASE="$HOME/cfd01/F2_piloto"
rm -rf "$BASE"; mkdir -p "$BASE"
CASO="$BASE/base"

# --------------------------------------------------------------- geometria
XMIN=-0.12; XMAX=0.12      # apertura del abanico (vertical en el caso real)
YMIN=0.0;   YMAX=0.1478    # 4,5 mm (vertice->punta) + 143,3 mm (punta->pared)
ZMIN=-0.05; ZMAX=0.05      # fuera del plano del abanico
NX=60; NY=37; NZ=25        # celdas de ~4 mm  ->  55 500 celdas

# --------------------------------------------------------------- aire
# rho = p/(R T) con p = 76 243,854 Pa (JSON, altitud de planta) y T = 293,15 K
RHO_AIRE=0.90610
NU_AIRE=2.0141e-05

mkdir -p "$CASO"/{0.orig,constant,system}

# ============================================================ blockMeshDict
cat > "$CASO/system/blockMeshDict" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object blockMeshDict; }

scale 1;

vertices
(
    ($XMIN $YMIN $ZMIN)   //0
    ($XMAX $YMIN $ZMIN)   //1
    ($XMAX $YMAX $ZMIN)   //2
    ($XMIN $YMAX $ZMIN)   //3
    ($XMIN $YMIN $ZMAX)   //4
    ($XMAX $YMIN $ZMAX)   //5
    ($XMAX $YMAX $ZMAX)   //6
    ($XMIN $YMAX $ZMAX)   //7
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ($NX $NY $NZ) simpleGrading (1 1 1)
);

edges ();

boundary
(
    placa                       // pared objetivo, a 143,3 mm de la punta
    {
        type wall;
        faces ( (3 7 6 2) );
    }
    fondo                       // plano de la boquilla
    {
        type wall;
        faces ( (0 1 5 4) );
    }
    abierto                     // contorno libre: las gotas escapan
    {
        type patch;
        faces ( (0 4 7 3) (1 2 6 5) (0 3 2 1) (4 5 6 7) );
    }
);

mergePatchPairs ();
DICT

# ============================================================ campos
cat > "$CASO/0.orig/U" <<DICT
FoamFile { version 2.0; format ascii; class volVectorField; object U; }

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);

boundaryField
{
    placa   { type noSlip; }
    fondo   { type noSlip; }
    abierto { type pressureInletOutletVelocity; value uniform (0 0 0); }
}
DICT

cat > "$CASO/0.orig/p" <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object p; }

dimensions      [0 2 -2 0 0 0 0];     // presion cinematica (incompresible)
internalField   uniform 0;

boundaryField
{
    placa   { type zeroGradient; }
    fondo   { type zeroGradient; }
    abierto { type fixedValue; value uniform 0; }
}
DICT

cat > "$CASO/0.orig/k" <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object k; }

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 1e-04;        // aire practicamente quieto al arrancar

boundaryField
{
    placa   { type kqRWallFunction; value uniform 1e-04; }
    fondo   { type kqRWallFunction; value uniform 1e-04; }
    abierto { type inletOutlet; inletValue uniform 1e-04; value uniform 1e-04; }
}
DICT

cat > "$CASO/0.orig/epsilon" <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object epsilon; }

dimensions      [0 2 -3 0 0 0 0];
internalField   uniform 1e-05;

boundaryField
{
    placa   { type epsilonWallFunction; value uniform 1e-05; }
    fondo   { type epsilonWallFunction; value uniform 1e-05; }
    abierto { type inletOutlet; inletValue uniform 1e-05; value uniform 1e-05; }
}
DICT

cat > "$CASO/0.orig/nut" <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object nut; }

dimensions      [0 2 -1 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    placa   { type nutkWallFunction; value uniform 0; }
    fondo   { type nutkWallFunction; value uniform 0; }
    abierto { type calculated; value uniform 0; }
}
DICT

# ============================================================ constant
cat > "$CASO/constant/g" <<DICT
FoamFile { version 2.0; format ascii; class uniformDimensionedVectorField; object g; }

dimensions      [0 1 -2 0 0 0 0];
value           (-9.81 0 0);   // -x = vertical: el abanico se abre en la vertical
DICT

cat > "$CASO/constant/transportProperties" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object transportProperties; }

transportModel  Newtonian;
nu              $NU_AIRE;      // aire a 20 C y 76,24 kPa (presion de planta, JSON)
rhoInf          $RHO_AIRE;
DICT

cat > "$CASO/constant/turbulenceProperties" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object turbulenceProperties; }

simulationType  laminar;       // se sobrescribe a RAS en la variante acoplada
DICT

# ============================================================ system
cat > "$CASO/system/controlDict" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }

application     icoUncoupledKinematicParcelFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         0.05;          // ~8,6 tiempos de vuelo (vuelo ~5,8 ms)
deltaT          2e-04;         // fijo: asi la inyeccion dispara todas las entradas cada paso
writeControl    runTime;
writeInterval   0.01;
purgeWrite      0;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable false;
adjustTimeStep  no;
maxCo           0.5;
DICT

cat > "$CASO/system/fvSchemes" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object fvSchemes; }

ddtSchemes      { default Euler; }
gradSchemes     { default Gauss linear; }
divSchemes
{
    default          none;
    div(phi,U)       Gauss upwind;
    div(U)           Gauss linear;
    div(phi,k)       Gauss upwind;
    div(phi,epsilon) Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes    { default Gauss linear corrected; }
interpolationSchemes { default linear; interpolate(HbyA) linear; }
snGradSchemes       { default corrected; }
DICT

cat > "$CASO/system/fvSolution" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object fvSolution; }

solvers
{
    p      { solver PBiCGStab; preconditioner DIC; tolerance 0; relTol 0.05; }
    pFinal { \$p; tolerance 1e-07; relTol 0; }
    U      { solver smoothSolver; smoother GaussSeidel; tolerance 1e-06; relTol 0.01; }
    UFinal { \$U; tolerance 1e-07; relTol 0; }
    "(k|epsilon)"      { solver PBiCGStab; preconditioner DILU; tolerance 1e-07; relTol 0.01; }
    "(k|epsilon)Final" { solver PBiCGStab; preconditioner DILU; tolerance 1e-07; relTol 0; }
}

PIMPLE
{
    momentumPredictor yes;
    correctPhi        no;
    nOuterCorrectors  1;
    nCorrectors       2;
    nNonOrthogonalCorrectors 0;
}

relaxationFactors { equations { ".*" 1; } }
DICT

cat > "$CASO/system/decomposeParDict" <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }

numberOfSubdomains 4;
method          scotch;
DICT

# ============================================================ malla
cd "$CASO" || exit 1
blockMesh > log.blockMesh 2>&1 || { echo "FALLO blockMesh"; tail -20 log.blockMesh; exit 1; }
checkMesh > log.checkMesh 2>&1
echo "malla base:"
grep -E "^ *cells:|Mesh OK|\*\*\*" log.checkMesh | head -5
echo "patches:"
grep -A8 "Boundary patches" log.checkMesh | head -10 || true
echo
echo "BASE construida en $CASO"
