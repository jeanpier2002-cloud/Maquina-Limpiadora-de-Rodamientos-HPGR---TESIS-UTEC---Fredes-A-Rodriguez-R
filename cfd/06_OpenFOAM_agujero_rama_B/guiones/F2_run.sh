#!/bin/bash
# F2 - corre las variantes del piloto y resume el balance de masa de cada una
source /usr/lib/openfoam/openfoam2606/etc/bashrc
B="$HOME/cfd01/F2_piloto"
VARS="${*:-V1_ico_absorbe V2_aco_absorbe V3_ico_adhiere V4_ico_rebota V5_ico_RR}"

for v in $VARS; do
  c="$B/$v"
  [ -d "$c" ] || { echo "no existe $v"; continue; }
  app=$(grep -m1 "^application" "$c/system/controlDict" | awk '{print $2}' | tr -d ';')
  cd "$c" || continue
  t0=$(date +%s)
  $app > "log.$app" 2>&1
  rc=$?
  t1=$(date +%s)
  echo "=================================================================="
  echo "$v   solver=$app   exit=$rc   pared=$((t1-t0)) s"
  if grep -qiE "FOAM FATAL" "log.$app"; then
    echo "  !! FOAM FATAL:"; grep -A6 "FOAM FATAL" "log.$app" | head -8
    continue
  fi
  echo "  ultima linea            : $(tail -1 "log.$app")"
  echo "  ultimo tiempo escrito   : $(foamListTimes 2>/dev/null | tail -1)"
  # ultimo bloque de resumen de la nube
  awk '/^Cloud: kinematicCloud$/{buf=""} {buf=buf"\n"$0} END{print buf}' "log.$app" \
    | grep -E "Current number of parcels|Current mass in system|parcels added|mass introduced|Parcel fate|escape|stick|rebound|Average particle" | tail -20
  echo "  max Courant del aire    : $(grep -oE "Courant Number mean: [0-9.e+-]+ max: [0-9.e+-]+" "log.$app" | awk '{print $NF}' | sort -g | tail -1)"
  echo "  impactos registrados    : $(cat postProcessing/lagrangian/kinematicCloud/impactos/*/*.dat 2>/dev/null | grep -vc "^#")"
  du -sh "$c" | awk '{print "  tamano en disco         : "$1}'
done
