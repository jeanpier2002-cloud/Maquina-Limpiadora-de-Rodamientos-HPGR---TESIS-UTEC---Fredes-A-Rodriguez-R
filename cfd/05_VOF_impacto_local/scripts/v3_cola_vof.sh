#!/bin/bash
# v3 (CORRIDA 2, 24/10/2026) - cola del VOF en WSL por carriles, desacoplada de wsl.exe (setsid + nohup), basada en
# v2_cola_wsl.sh de la tanda 1. Cada carril corre sus casos en serie con v3_e1_correr.sh <etapa> <caso> <np>.
# Especificacion de caso: etapa:caso:np:timeout_s (timeout 0 = sin tope). Por caso escribe
# logs/<etapa>/<caso>/FIN (End y sin FOAM FATAL) o .../ERROR. Salta los que ya tienen FIN (reanudable).
# Antes de cada caso comprueba disco (> 50 GB) y RAM de WSL (< 90 %).
# Uso:  bash v3_cola_vof.sh lanzar <carril> spec1 spec2 ...   (vuelve enseguida; el carril sigue solo)
#       bash v3_cola_vof.sh estado
S=/mnt/d/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/scripts
LOGS=/mnt/d/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/logs
V3=/home/piermoto/vof3
mkdir -p $V3 $LOGS
if [ "$1" = lanzar ]; then
  shift; CAR=$1
  setsid nohup bash $S/v3_cola_vof.sh carril "$@" > $V3/carril_$CAR.out 2>&1 < /dev/null &
  disown; echo "carril $CAR lanzado $(date -Iseconds)"; exit 0
fi
if [ "$1" = estado ]; then
  for f in $V3/carril_*.log; do echo "== $f"; tail -3 $f; done
  for d in $LOGS/e1/*/ $LOGS/e1od/*/; do [ -d "$d" ] || continue; n=$(basename $d); et=$(basename $(dirname $d))
    L=$V3/$et/$n/log.interFoam
    printf "%-36s %-6s %s | %s pasos\n" $n "$(ls $d | grep -E '^(FIN|ERROR)$')" "$(grep '^Time = ' $L 2>/dev/null | tail -1)" \
      "$(grep -c '^Time = ' $L 2>/dev/null)"; done
  echo "interFoam activos: $(pgrep -x interFoam | wc -l)"
  free -m | awk 'NR==2{printf "RAM WSL %d de %d MB (%.0f %%)\n", $3, $2, 100*$3/$2}'; df -h /home/piermoto | tail -1
  exit 0
fi
# --- carril ---
shift; CAR=$1; shift
LOG=$V3/carril_$CAR.log
for SPEC in "$@"; do
  IFS=: read ET NOM NP TMAX <<< "$SPEC"
  OUT=$LOGS/$ET/$NOM; mkdir -p $OUT
  [ -f $OUT/FIN ] && { echo "$(date -Iseconds) salto $NOM (ya tiene FIN)" >> $LOG; continue; }
  LIBRE=$(df -BG --output=avail /home/piermoto | tail -1 | tr -dc 0-9)
  RAMP=$(free | awk 'NR==2{printf "%d", 100*$3/$2}')
  if [ "$LIBRE" -lt 50 ] || [ "$RAMP" -gt 90 ]; then
    echo "$(date -Iseconds) PARO $NOM: disco ${LIBRE}G RAM ${RAMP}%" >> $LOG; echo "recursos" > $OUT/ERROR; continue
  fi
  rm -f $OUT/ERROR
  echo "$(date -Iseconds) inicio $ET/$NOM np=$NP tope=${TMAX}s" >> $LOG
  if [ "${TMAX:-0}" -gt 0 ]; then
    timeout -k 60 $TMAX bash $S/v3_e1_correr.sh $ET $NOM $NP >> $LOG 2>&1
  else
    bash $S/v3_e1_correr.sh $ET $NOM $NP >> $LOG 2>&1
  fi
  RC=$?
  L=$V3/$ET/$NOM/log.interFoam
  if grep -q '^End' $L 2>/dev/null && ! grep -q 'FOAM FATAL' $L; then
    date -Iseconds > $OUT/FIN; echo "$(date -Iseconds) FIN $NOM $(head -1 $OUT/resumen.txt)" >> $LOG
  else
    echo "rc=$RC $(grep -m1 -A3 'FOAM FATAL' $L 2>/dev/null | tr '\n' ' ')" > $OUT/ERROR
    echo "$(date -Iseconds) ERROR $NOM rc=$RC (124 = tope de tiempo)" >> $LOG
    # si lo corto el tope, copiar lo que haya para no perderlo
    [ "$RC" = 124 ] && { cp $V3/$ET/$NOM/log.* $OUT/ 2>/dev/null; [ -d $V3/$ET/$NOM/postProcessing ] && cp -r $V3/$ET/$NOM/postProcessing $OUT/; }
  fi
done
echo "$(date -Iseconds) CARRIL_TERMINADO" >> $LOG
