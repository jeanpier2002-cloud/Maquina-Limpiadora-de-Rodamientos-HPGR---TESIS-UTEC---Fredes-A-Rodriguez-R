#!/bin/bash
# CORRIDA 4 · T2 · convergencia en densidad: 2400 rayos por plano, rotor cada 0,1 grados, un proceso por boquilla
cd /d/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO/scripts
for b in SUP_1_A SUP_2_A SUP_1_B SUP_2_B INF_EXT_A INF_EXT_B C2_A C2_B INF_INT; do
  python -I -B r4_t2_cavidad_n1.py --tag d2400_$b --boq $b --n-plano 2400 --dphi 0.1 --lote-phi 6 > ../02_CAVIDAD_N1/log_d2400_$b.txt 2>&1 &
done
wait
echo FIN > ../02_CAVIDAD_N1/d2400_FIN.txt
