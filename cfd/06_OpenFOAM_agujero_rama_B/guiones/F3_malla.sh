#!/bin/bash
# =============================================================================
#  F3 - prueba de mallado del dominio del agujero con snappyHexMesh
#  Solo comprueba que la geometria malla y mide el coste. El estudio de malla
#  de tres niveles es de F4 y va sobre el caso S2.
#    $1 = tamano de celda base en mm      $2 = nivel de refino en la pared
# =============================================================================
source /usr/lib/openfoam/openfoam2606/etc/bashrc
BASE_MM=${1:-16}
NIVEL=${2:-2}
SP=/mnt/c/Users/Usuario/AppData/Local/Temp/claude/G--Mi-unidad-Semestre-X-TESIS-II-Sistema-de-aspersi-n-CFD01-OPENFOAM/217d7132-3a5c-4cff-aaed-21d01264a2f8/scratchpad
C=$HOME/cfd01/F3_geometria/malla_${BASE_MM}mm_n${NIVEL}
rm -rf "$C"; mkdir -p "$C"/{system,constant/triSurface}
cp "$SP"/geom/{pared_agujero,cara_inf_rodamiento,cara_sup_rodamiento,lanza}.stl "$C/constant/triSurface/"
cd "$C" || exit 1

# --- caja del dominio, en metros ---
X0=-0.5; X1=0.5; Y0=-0.5; Y1=0.5; Z0=0.790; Z1=1.445
NX=$(python3 -c "print(max(1,round(($X1-($X0))*1000/$BASE_MM)))")
NY=$(python3 -c "print(max(1,round(($Y1-($Y0))*1000/$BASE_MM)))")
NZ=$(python3 -c "print(max(1,round(($Z1-$Z0)*1000/$BASE_MM)))")

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

cat > system/controlDict <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }
application     snappyHexMesh; startFrom startTime; startTime 0; stopAt endTime;
endTime 1; deltaT 1; writeControl timeStep; writeInterval 1;
writeFormat ascii; writePrecision 8; runTimeModifiable false;
DICT
cat > system/fvSchemes  <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object fvSchemes; }
gradSchemes { default Gauss linear; } divSchemes { default none; }
laplacianSchemes { default Gauss linear corrected; }
DICT
cat > system/fvSolution <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object fvSolution; }
solvers {}
DICT
cat > system/meshQualityDict <<'DICT'
FoamFile { version 2.0; format ascii; class dictionary; object meshQualityDict; }
#includeEtc "caseDicts/meshQualityDict"
DICT

cat > system/snappyHexMeshDict <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object snappyHexMeshDict; }

castellatedMesh true;
snap            true;
addLayers       false;

geometry
{
    pared_agujero.stl        { type triSurfaceMesh; name pared_agujero; }
    cara_inf_rodamiento.stl  { type triSurfaceMesh; name cara_inf_rodamiento; }
    cara_sup_rodamiento.stl  { type triSurfaceMesh; name cara_sup_rodamiento; }
    lanza.stl                { type triSurfaceMesh; name lanza; }
}

castellatedMeshControls
{
    maxLocalCells   2000000;
    maxGlobalCells  6000000;
    minRefinementCells 10;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 2;

    features ();

    refinementSurfaces
    {
        pared_agujero       { level ($NIVEL $NIVEL); patchInfo { type wall; } }
        cara_inf_rodamiento { level (0 0);           patchInfo { type wall; } }
        cara_sup_rodamiento { level (0 0);           patchInfo { type wall; } }
        lanza               { level ($NIVEL $NIVEL); patchInfo { type wall; } }
    }

    resolveFeatureAngle 30;
    refinementRegions {}

    // dentro del agujero, lejos de la lanza (que esta en y=+0,25)
    locationInMesh (0.2 -0.2 1.1);
    allowFreeStandingZoneFaces false;
}

snapControls
{
    nSmoothPatch    3;
    tolerance       2.0;
    nSolveIter      50;
    nRelaxIter      5;
    nFeatureSnapIter 10;
    implicitFeatureSnap false;
    explicitFeatureSnap false;
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
    // estas dos son propias de snappyHexMesh y NO vienen en el diccionario
    // compartido: sin ellas snappy aborta al empezar a ajustar (snap)
    nSmoothScale    4;
    errorReduction  0.75;
    relaxed { maxNonOrtho 75; }
}
writeFlags ( );
mergeTolerance 1e-6;
DICT

echo "=============================================================="
echo " malla base ${BASE_MM} mm  (${NX} x ${NY} x ${NZ}), refino nivel ${NIVEL} en pared y lanza"
echo "=============================================================="
t0=$(date +%s)
blockMesh > log.blockMesh 2>&1 || { echo "FALLO blockMesh"; tail -15 log.blockMesh; exit 1; }
echo "  blockMesh : $(grep -m1 'nCells:' log.blockMesh | awk '{print $2}') celdas"
snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
rc=$?
t1=$(date +%s)
echo "  snappyHexMesh exit=$rc, $((t1-t0)) s"
grep -iE "FOAM FATAL" log.snappyHexMesh | head -3
checkMesh -allGeometry -allTopology > log.checkMesh 2>&1
echo "  --- checkMesh ---"
grep -E "^ *cells:|^ *faces:|^ *points:|Mesh OK|\*\*\*|Max skewness|Max aspect ratio|non-orthogonality" log.checkMesh | head -12
echo "  --- patches y area de la pared ---"
grep -A12 "Boundary patches" log.checkMesh | head -14 || true
python3 - <<'PY'
import re
s = open("log.checkMesh").read()
m = re.search(r"Patch\s+Faces\s+Points\s+Surface topology.*?\n((?:.*\n)+?)\n", s)
print(m.group(1) if m else "  (no se pudo leer la tabla de patches)")
PY
echo "  --- area de cada patch ---"
postProcess -func 'patchIntegrate(patch=pared_agujero, field=p)' -time 0 > /dev/null 2>&1
surfaceCheck constant/triSurface/pared_agujero.stl 2>/dev/null | grep -E "Total area|area" | head -2
du -sh "$C" | awk '{print "  tamano en disco: "$1}'
