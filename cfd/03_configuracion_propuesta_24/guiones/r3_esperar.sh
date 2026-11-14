#!/usr/bin/env bash
# CORRIDA 3 · espera a que r3_procesar_auto.py escriba la aceptacion de un caso (o a un estado terminal de la cola).
# Solo mira las lineas de cola_r3.log escritas DESPUES de arrancar (el log tambien guarda las colas de humo).
# Uso: bash r3_esperar.sh <caso> <max_s>     (sale con una linea de estado; la usa la sesion de Claude para despertarse)
FL=/d/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT
LOG=$FL/logs/cola_r3.log
caso=$1; max=${2:-14400}; t0=$(date +%s)
n0=$(wc -l < "$LOG")
while true; do
  for f in "$FL/resultados/${caso}_aceptacion.txt" "$FL/resultados/${caso}_humo_aceptacion.txt"; do
    if [ -f "$f" ]; then echo "ACEPTACION $(cat "$f")"; tail -n 3 "$LOG"; exit 0; fi
  done
  nuevas=$(tail -n +"$((n0 + 1))" "$LOG")
  if echo "$nuevas" | grep -q -E "${caso} fallo dos veces|DETENIDA|cola detenida"; then
    echo "COLA: $(echo "$nuevas" | tail -n 3)"; exit 0
  fi
  if [ $(( $(date +%s) - t0 )) -gt "$max" ]; then
    echo "TIEMPO MAXIMO de espera (${max} s) sin aceptacion de ${caso}"; tail -n 3 "$LOG"
    tr="$FL/casos/${caso}/${caso}_transcript.txt"; [ -f "$tr" ] && grep -o "time step = [0-9]*" "$tr" | tail -n 1
    exit 0
  fi
  sleep 30
done
