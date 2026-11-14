#!/bin/bash
# =============================================================================
#  F4 - caso de aspersion sobre el agujero del rodamiento (geometria R05)
#
#    $1  nombre del caso
#    $2  celda base en mm            (16 por omision)
#    $3  boquillas, separadas por espacios, entre comillas
#        p.ej. "INT_3"  o  "INT_1 INT_2 INT_3 INT_4 INT_5 INF_INT"
#    $4  endTime en s                (0.035 por omision)
#
#  Configuracion fijada en F2 con evidencia:
#    kinematicParcelFoam acoplado (RAS kEpsilon)
#    kinematicLookupTableInjection, randomise false, minParticlesPerParcel 1e-6
#    parcelsPerSecond >= 1/deltaT
#    localInteraction: todo escape, para que el balance se desglose por patch
#    deltaT 5e-5 s por el Courant del aire
# =============================================================================
source /usr/lib/openfoam/openfoam2606/etc/bashrc

NOMBRE=${1:-S1r_INT3}
BASE_MM=${2:-16}
BOQUILLAS=${3:-INT_3}
ENDTIME=${4:-0.035}

SP=/mnt/c/Users/Usuario/AppData/Local/Temp/claude/G--Mi-unidad-Semestre-X-TESIS-II-Sistema-de-aspersi-n-CFD01-OPENFOAM/217d7132-3a5c-4cff-aaed-21d01264a2f8/scratchpad
C=$HOME/cfd01/F4/$NOMBRE
DT=5e-05
PPS=22000
RHO_LIQ=982.1203530851709
RHO_AIRE=0.90610
NU_AIRE=2.0141e-05

rm -rf "$C"; mkdir -p "$C"/{system,constant/triSurface,0.orig}
cp "$SP"/geom/{pared_agujero,cara_inf_rodamiento,cara_sup_rodamiento,lanza}.stl "$C/constant/triSurface/"
cd "$C" || exit 1

X0=-0.5; X1=0.5; Y0=-0.5; Y1=0.5; Z0=0.790; Z1=1.445
NX=$(python3 -c "print(max(1,round(($X1-($X0))*1000/$BASE_MM)))")
NY=$(python3 -c "print(max(1,round(($Y1-($Y0))*1000/$BASE_MM)))")
NZ=$(python3 -c "print(max(1,round(($Z1-$Z0)*1000/$BASE_MM)))")

# ------------------------------------------------------------------ malla
cat > system/blockMeshDict <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object blockMeshDict; }
scale 1;
vertices
(
    ($X0 $Y0 $Z0) ($X1 $Y0 $Z0) ($X1 $Y1 $Z0) ($X0 $Y1 $Z0)
    ($X0 $Y0 $Z1) ($X1 $Y0 $Z1) ($X1 $Y1 $Z1) ($X0 $Y1 $Z1)
);
blocks ( hex (0 1 2 3 4 5 6 7) ($NX $NY $NZ) simpleGrading (1 1 1) );
edges ();
boundary
(
    abierto_inferior { type patch; faces ( (0 1 5 4) (0 3 2 1) ); }
    abierto_superior { type patch; faces ( (4 5 6 7) ); }
    lateral_abierto  { type patch; faces ( (1 2 6 5) (0 4 7 3) (3 7 6 2) ); }
);
mergePatchPairs ();
DICT

cat > system/meshQualityDict <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object meshQualityDict; }
#includeEtc "caseDicts/meshQualityDict"
DICT

cat > system/snappyHexMeshDict <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object snappyHexMeshDict; }
castellatedMesh true; snap true; addLayers false;
geometry
{
    pared_agujero.stl        { type triSurfaceMesh; name pared_agujero; }
    cara_inf_rodamiento.stl  { type triSurfaceMesh; name cara_inf_rodamiento; }
    cara_sup_rodamiento.stl  { type triSurfaceMesh; name cara_sup_rodamiento; }
    lanza.stl                { type triSurfaceMesh; name lanza; }
}
castellatedMeshControls
{
    maxLocalCells 4000000; maxGlobalCells 8000000; minRefinementCells 10;
    maxLoadUnbalance 0.10; nCellsBetweenLevels 2; features ();
    refinementSurfaces
    {
        pared_agujero       { level (2 2); patchInfo { type wall; } }
        cara_inf_rodamiento { level (0 0); patchInfo { type wall; } }
        cara_sup_rodamiento { level (0 0); patchInfo { type wall; } }
        lanza               { level (2 2); patchInfo { type wall; } }
    }
    resolveFeatureAngle 30; refinementRegions {};
    locationInMesh (0.2 -0.2 1.1); allowFreeStandingZoneFaces false;
}
snapControls
{
    nSmoothPatch 3; tolerance 2.0; nSolveIter 50; nRelaxIter 5;
    nFeatureSnapIter 10; implicitFeatureSnap false; explicitFeatureSnap false;
    multiRegionFeatureSnap false;
}
addLayersControls
{
    relativeSizes true; layers {}; expansionRatio 1.0; finalLayerThickness 0.3;
    minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 3;
    nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10;
    maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90;
    nBufferCellsNoExtrude 0; nLayerIter 50;
}
meshQualityControls
{
    #includeEtc "caseDicts/meshQualityDict"
    nSmoothScale 4; errorReduction 0.75; relaxed { maxNonOrtho 75; }
}
writeFlags (); mergeTolerance 1e-6;
DICT

# ------------------------------------------------------------------ campos
PAREDES='"(pared_agujero|cara_inf_rodamiento|cara_sup_rodamiento|lanza)"'
ABIERTO='"(abierto_inferior|abierto_superior|lateral_abierto)"'

cat > 0.orig/U <<DICT
FoamFile { version 2.0; format ascii; class volVectorField; object U; }
dimensions [0 1 -1 0 0 0 0];
internalField uniform (0 0 0);
boundaryField
{
    $PAREDES { type noSlip; }
    $ABIERTO { type pressureInletOutletVelocity; value uniform (0 0 0); }
}
DICT
cat > 0.orig/p <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object p; }
dimensions [0 2 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{
    $PAREDES { type zeroGradient; }
    $ABIERTO { type fixedValue; value uniform 0; }
}
DICT
cat > 0.orig/k <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object k; }
dimensions [0 2 -2 0 0 0 0];
internalField uniform 1e-04;
boundaryField
{
    $PAREDES { type kqRWallFunction; value uniform 1e-04; }
    $ABIERTO { type inletOutlet; inletValue uniform 1e-04; value uniform 1e-04; }
}
DICT
cat > 0.orig/epsilon <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object epsilon; }
dimensions [0 2 -3 0 0 0 0];
internalField uniform 1e-05;
boundaryField
{
    $PAREDES { type epsilonWallFunction; value uniform 1e-05; }
    $ABIERTO { type inletOutlet; inletValue uniform 1e-05; value uniform 1e-05; }
}
DICT
cat > 0.orig/nut <<DICT
FoamFile { version 2.0; format ascii; class volScalarField; object nut; }
dimensions [0 2 -1 0 0 0 0];
internalField uniform 0;
boundaryField
{
    $PAREDES { type nutkWallFunction; value uniform 0; }
    $ABIERTO { type calculated; value uniform 0; }
}
DICT

# ------------------------------------------------------------------ constant
cat > constant/g <<'DICT'
FoamFile { version 2.0; format ascii; class uniformDimensionedVectorField; object g; }
dimensions [0 1 -2 0 0 0 0];
value (0 0 -9.81);
DICT
cat > constant/transportProperties <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object transportProperties; }
transportModel Newtonian;
nu      $NU_AIRE;
rhoInf  $RHO_AIRE;
DICT
cat > constant/turbulenceProperties <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object turbulenceProperties; }
simulationType RAS;
RAS { RASModel kEpsilon; turbulence on; printCoeffs off; }
DICT

# --- tablas de inyeccion y bloque de inyectores ---
INY=""
ID=0
for b in $BOQUILLAS; do
  ID=$((ID+1))
  cp "$SP/tablas_S2/$b/tabla_$b" constant/
  MT=$(grep -m1 "massTotal" "constant/tabla_$b" | sed -E 's/.*massTotal = ([0-9.e+-]+) kg.*/\1/')
  INY="$INY
        $b
        {
            type             kinematicLookupTableInjection;
            inputFile        \"tabla_$b\";
            duration         $ENDTIME;
            parcelsPerSecond $PPS;
            randomise        false;
            massTotal        $MT;
            parcelBasisType  mass;
            minParticlesPerParcel 1e-6;
            injectorID       $ID;
            SOI              0;
        }
"
done

cat > constant/kinematicCloudProperties <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object kinematicCloudProperties; }

solution
{
    active true; coupled yes; transient yes;
    cellValueSourceCorrection no; maxCo 0.3;
    sourceTerms { schemes { U semiImplicit 1; } }
    interpolationSchemes { rho cell; U cellPoint; mu cell; muc cell; }
    integrationSchemes { U Euler; }
}

constantProperties { rho0 $RHO_LIQ; }

subModels
{
    particleForces { sphereDrag; gravity; }

    injectionModels
    {$INY    }

    dispersionModel none;

    patchInteractionModel localInteraction;
    localInteractionCoeffs
    {
        patches
        (
            // todo escape: la gota se retira al tocar y su masa queda contabilizada
            // por patch, que es lo que cierra el balance. En la pared del agujero
            // 'escape' equivale a deposicion perfecta (absorcion)
            pared_agujero       { type escape; }
            cara_inf_rodamiento { type escape; }
            cara_sup_rodamiento { type escape; }
            lanza               { type escape; }
            abierto_inferior    { type escape; }
            abierto_superior    { type escape; }
            lateral_abierto     { type escape; }
        );
    }

    stochasticCollisionModel none;
    collisionModel none;
    surfaceFilmModel none;
}

cloudFunctions
{
    campos_de_impacto { type patchInteractionFields; resetMode none; }
    impactos
    {
        type              particlePostProcessing;
        maxStoredParcels  8000000;
        patches           (pared_agujero);
        fields            (position U d nParticle rho age typeId origId);
    }
}
DICT

# ------------------------------------------------------------------ system
cat > system/controlDict <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }
application     kinematicParcelFoam;
startFrom       startTime; startTime 0; stopAt endTime;
endTime         $ENDTIME;
deltaT          $DT;
writeControl    runTime; writeInterval 0.005;
purgeWrite      0; writeFormat ascii; writePrecision 8; writeCompression off;
timeFormat      general; timePrecision 8;
runTimeModifiable false; adjustTimeStep no; maxCo 0.5;
DICT
cat > system/fvSchemes <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object fvSchemes; }
ddtSchemes  { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(phi,U) Gauss upwind;
    div(U) Gauss linear;
    div(phi,k) Gauss upwind;
    div(phi,epsilon) Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited corrected 0.33; }
interpolationSchemes { default linear; interpolate(HbyA) linear; }
snGradSchemes { default limited corrected 0.33; }
DICT
cat > system/fvSolution <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object fvSolution; }
solvers
{
    p      { solver GAMG; smoother GaussSeidel; tolerance 0; relTol 0.05; }
    pFinal { $p; tolerance 1e-06; relTol 0; }
    U      { solver smoothSolver; smoother GaussSeidel; tolerance 1e-06; relTol 0.01; }
    UFinal { $U; tolerance 1e-07; relTol 0; }
    "(k|epsilon)"      { solver PBiCGStab; preconditioner DILU; tolerance 1e-07; relTol 0.01; }
    "(k|epsilon)Final" { solver PBiCGStab; preconditioner DILU; tolerance 1e-07; relTol 0; }
}
PIMPLE { momentumPredictor yes; correctPhi no; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 1; }
relaxationFactors { equations { ".*" 1; } }
DICT
cat > system/decomposeParDict <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains 8;
method scotch;
DICT

echo "=================================================================="
echo " caso $NOMBRE : base $BASE_MM mm, boquillas [$BOQUILLAS], endTime $ENDTIME s"
echo "=================================================================="
blockMesh > log.blockMesh 2>&1 || { echo "FALLO blockMesh"; exit 1; }
snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
echo "  snappyHexMesh exit=$? ; celdas = $(grep -m1 'Finished meshing' log.snappyHexMesh >/dev/null && echo ok)"
checkMesh > log.checkMesh 2>&1
echo "  celdas: $(grep -m1 '^ *cells:' log.checkMesh | awk '{print $2}')   $(grep -oE 'Mesh OK|Failed [0-9]+ mesh checks' log.checkMesh | head -1)"
rm -rf 0; cp -r 0.orig 0
N=0
for b in $BOQUILLAS; do N=$((N + $(grep -c '^    (' constant/tabla_$b))); done
echo "  entradas de tabla (total): $N   -> parcels/paso = $(python3 -c "print(int($N*$DT*$PPS))")  (debe ser >= $N)"
echo "  parcels por segundo      : $(python3 -c "print(int($N*$PPS))")"
echo "  pasos                    : $(python3 -c "print(int($ENDTIME/$DT))")"
echo "  caso listo en $C"
