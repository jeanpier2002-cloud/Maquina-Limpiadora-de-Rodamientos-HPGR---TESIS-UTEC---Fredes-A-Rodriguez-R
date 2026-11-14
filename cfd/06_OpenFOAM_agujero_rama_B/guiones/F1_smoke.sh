#!/bin/bash
# F1 - Prueba de humo del entorno OpenFOAM v2606 (tutoriales oficiales, sin modificar)
# (sin set -u: el bashrc de OpenFOAM no lo tolera)
source /usr/lib/openfoam/openfoam2606/etc/bashrc
T="$FOAM_TUTORIALS/lagrangian"
BASE="$HOME/cfd01/F1_entorno"
rm -rf "$BASE"; mkdir -p "$BASE"
cd "$BASE" || exit 1

{
echo "=============================================================="
echo " F1 - PRUEBA DE HUMO  $(date -Is)"
echo "=============================================================="
echo "OpenFOAM        : $WM_PROJECT_VERSION  ($(foamVersion 2>/dev/null | head -1))"
echo "WM_OPTIONS      : $WM_OPTIONS"
echo "MPI             : $(mpirun --version 2>/dev/null | head -1)"
echo "nproc / RAM     : $(nproc) hilos / $(free -g | awk '/Mem:/{print $2}') GB"
echo "Directorio      : $BASE"
echo
} | tee informe_F1.txt

run_case () {  # $1 = ruta tutorial, $2 = nombre local, $3 = solver
  local src="$1" name="$2" app="$3"
  echo "-------- CASO $name ($app) --------" | tee -a informe_F1.txt
  cp -r "$src" "$name" || return 1
  cd "$name" || return 1
  [ -d 0.orig ] && cp -r 0.orig 0
  local t0=$(date +%s)
  blockMesh > log.blockMesh 2>&1
  local rc_bm=$?
  checkMesh > log.checkMesh 2>&1
  local ncells=$(grep -m1 "cells:" log.checkMesh | awk '{print $2}')
  local meshok=$(grep -c "Mesh OK" log.checkMesh)
  $app > log.$app 2>&1
  local rc_s=$?
  local t1=$(date +%s)
  local nfatal=$(grep -ciE "FOAM FATAL|FOAM Warning|--> FOAM" log.$app)
  local nerr=$(grep -ciE "FOAM FATAL" log.$app)
  local endt=$(grep -m1 "^End" log.$app)
  {
    echo "  blockMesh exit        : $rc_bm"
    echo "  celdas                : $ncells   (Mesh OK: $meshok)"
    echo "  $app exit             : $rc_s"
    echo "  FOAM FATAL en el log  : $nerr"
    echo "  avisos+errores        : $nfatal"
    echo "  linea final del log   : ${endt:-<no llego a End>}"
    echo "  tiempo de pared       : $((t1-t0)) s"
    echo "  ultimo tiempo escrito : $(foamListTimes 2>/dev/null | tail -1)"
    echo "  parcels finales       : $(grep -E "Current number of parcels" log.$app | tail -1)"
    echo "  masa en la nube       : $(grep -E "Current mass in system" log.$app | tail -1)"
  } | tee -a informe_F1.txt
  # postproceso: nube a VTK (prueba la ruta hacia ParaView)
  foamToVTK -latestTime > log.foamToVTK 2>&1
  echo "  foamToVTK exit        : $?  ($(find VTK -name '*.vt*' 2>/dev/null | wc -l) archivos VTK)" | tee -a informe_F1.txt
  echo | tee -a informe_F1.txt
  cd "$BASE" || return 1
}

run_case "$T/kinematicParcelFoam/spinningDisk"  spinningDisk  kinematicParcelFoam
run_case "$T/reactingParcelFoam/parcelInBox"    parcelInBox   reactingParcelFoam

echo "==== tamano en disco ====" | tee -a informe_F1.txt
du -sh "$BASE" | tee -a informe_F1.txt
echo "FIN $(date -Is)" | tee -a informe_F1.txt
