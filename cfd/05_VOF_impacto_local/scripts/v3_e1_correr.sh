#!/bin/bash
# v3 (CORRIDA 2, 24/10/2026): copia de CORRIDA_1_13a21oct/06_VOF/scripts/e1_correr.sh con rutas cambiadas a 02_VOF_v3 y /home/piermoto/vof3 (sed); sin otros cambios.
# Etapa 1/2 - corre un caso generado en D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/casos_eX/<nombre> dentro de WSL (ext4).
# Uso: bash e1_correr.sh <etapa: e1|e2> <nombre> <np> [maxSteps]
#  - copia el caso a /home/piermoto/vof3/<etapa>/<nombre>; fluentMeshToFoam; changeDictionary (frenteYfondo -> empty en 2D);
#    checkMesh; setFields; (decomposePar scotch); interFoam; copia registros ligeros a D:.
#  - maxSteps > 0: prueba corta (escalado): para tras ese numero de pasos con stopAt writeNow via foamDictionary.
source /usr/lib/openfoam/openfoam2606/etc/bashrc
ET=$1; NOM=$2; NP=${3:-1}; MAXS=${4:-0}
SRC=/mnt/d/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/casos_${ET}/$NOM
C=/home/piermoto/vof3/$ET/$NOM
OUT=/mnt/d/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/logs/$ET/$NOM
mkdir -p /home/piermoto/vof3/$ET "$OUT"
rm -rf "$C"; mkdir -p "$C"
cp -r "$SRC"/system "$SRC"/constant "$SRC"/0 "$SRC"/meta.json "$C"/
cp "$SRC"/malla.msh "$C"/
cd "$C"
sed -i "s/^numberOfSubdomains .*/numberOfSubdomains $NP;/" system/decomposeParDict
[ "$NP" -gt 1 ] && sed -i "s/^method .*/method scotch;/" system/decomposeParDict
fluentMeshToFoam malla.msh > log.fluentMeshToFoam 2>&1 || { echo "FALLO fluentMeshToFoam" > "$OUT/ESTADO"; exit 1; }
rm -f malla.msh
if [ -f system/changeDictionaryDict ]; then changeDictionary > log.changeDictionary 2>&1; fi
checkMesh -allGeometry -allTopology > log.checkMesh 2>&1
cp -r 0 0.orig
setFields > log.setFields 2>&1
if [ "$MAXS" -gt 0 ]; then
  # prueba de escalado: tiempo final grande y parada por numero de pasos (endTime = maxSteps * deltaT no sirve
  # con paso adaptable); se usa stopAt nextWrite tras ~MAXS pasos con un writeInterval en pasos.
  foamDictionary system/controlDict -entry writeControl -set timeStep > /dev/null
  foamDictionary system/controlDict -entry writeInterval -set $MAXS > /dev/null
  foamDictionary system/controlDict -entry stopAt -set nextWrite > /dev/null
  foamDictionary system/controlDict -entry functions -remove > /dev/null
fi
T0=$(date +%s)
echo "CORRIENDO np=$NP inicio $(date -Iseconds)" > "$OUT/ESTADO"
if [ "$NP" -gt 1 ]; then
  decomposePar -force > log.decomposePar 2>&1
  /usr/bin/time -v mpirun -np $NP interFoam -parallel > log.interFoam 2> log.time
else
  /usr/bin/time -v interFoam > log.interFoam 2> log.time
fi
RC=$?
T1=$(date +%s)
NPASOS=$(grep -c '^Time = ' log.interFoam)
{
  echo "nombre=$NOM np=$NP rc=$RC pared_s=$((T1-T0)) pasos=$NPASOS"
  echo "End=$(grep -c '^End' log.interFoam) FATAL=$(grep -c 'FOAM FATAL' log.interFoam)"
  grep -E 'Maximum resident' log.time
  grep 'ClockTime' log.interFoam | tail -1
  grep '^Time = ' log.interFoam | tail -1
} > "$OUT/resumen.txt"
cp log.* "$OUT"/ 2>/dev/null
cp meta.json "$OUT"/
rm -f "$OUT"/log.interFoam
# el log del solver puede ser grande: se guarda comprimido
gzip -c log.interFoam > "$OUT/log.interFoam.gz"
[ -d postProcessing ] && { rm -rf "$OUT/postProcessing"; cp -r postProcessing "$OUT"/; }
echo "TERMINADO rc=$RC $(date -Iseconds)" > "$OUT/ESTADO"
