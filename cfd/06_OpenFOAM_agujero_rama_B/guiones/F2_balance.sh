#!/bin/bash
# F2 - extrae el balance de masa del ULTIMO resumen de nube de cada log y lo saca en CSV
source /usr/lib/openfoam/openfoam2606/etc/bashrc
B="$HOME/cfd01/F2_piloto"
echo "variante,solver,coupled,placa,pared_s,parcels_finales,masa_en_vuelo_kg,parcels_inyectados,masa_inyectada_kg,dep_placa_kg,escape_abierto_kg,residuo_kg,residuo_rel"
for v in V1_ico_absorbe V2_aco_absorbe V3_ico_adhiere V4_ico_rebota V5_ico_RR V6_aco_RR V7_aco_RR_minpp; do
  c="$B/$v"; [ -d "$c" ] || continue
  L=$(ls "$c"/log.* 2>/dev/null | grep -vE "blockMesh|checkMesh|test" | head -1)
  [ -n "$L" ] || continue
  app=$(grep -m1 "^application" "$c/system/controlDict" | awk '{print $2}' | tr -d ';')
  cp=$(grep -m1 "coupled" "$c/constant/kinematicCloudProperties" | awk '{print $2}' | tr -d ';')
  pl=$(grep -A1 "placa   {" "$c/constant/kinematicCloudProperties" | head -1 | sed 's/.*type //;s/;.*//')
  # ultimo bloque de resumen
  ultimo=$(awk '/^Cloud: kinematicCloud$/{buf=""} {buf=buf"\n"$0} END{print buf}' "$L")
  vuelo=$(echo "$ultimo"  | grep -m1 "Current mass in system" | awk '{print $6}')
  npar=$(echo "$ultimo"   | grep -m1 "Current number of parcels" | awk '{print $6}')
  niny=$(echo "$ultimo"   | grep -m1 "parcels added" | awk '{print $5}')
  miny=$(echo "$ultimo"   | grep -m1 "mass introduced" | awk '{print $5}')
  # masa en la placa: suma de escape + stick de ese patch
  dep=$(echo "$ultimo" | awk '/patch placa/{f=1;next} /patch (fondo|abierto)/{f=0} f&&/escape|stick/{gsub(",","",$0); s+=$NF} END{printf "%.10g", s+0}')
  esc=$(echo "$ultimo" | awk '/patch abierto/{f=1;next} /patch (fondo|placa)/{f=0} f&&/escape|stick/{gsub(",","",$0); s+=$NF} END{printf "%.10g", s+0}')
  # con 'stick' la gota depositada SIGUE en la nube, asi que su masa ya esta
  # contada dentro de 'masa en vuelo': no se puede restar dos veces
  if [ "$pl" = "stick" ]; then dep_bal=0; else dep_bal=$dep; fi
  res=$(python3 -c "print('%.6g' % ($miny - $vuelo - $dep_bal - $esc))")
  rel=$(python3 -c "print('%.3g' % (($miny - $vuelo - $dep_bal - $esc)/$miny))")
  # tiempo de pared si quedo registrado
  w=$(grep -m1 "ExecutionTime" "$L" | awk '{print $3}')
  wl=$(grep "ExecutionTime" "$L" | tail -1 | awk '{print $3}')
  echo "$v,$app,$cp,$pl,${wl:-NA},$npar,$vuelo,$niny,$miny,$dep,$esc,$res,$rel"
done
