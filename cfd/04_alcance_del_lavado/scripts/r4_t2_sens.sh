#!/bin/bash
# CORRIDA 4 · T2 · sensibilidades del N1 de cavidad (secuencial)
cd /d/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO/scripts
python -I -B r4_t2_cavidad_n1.py --tag sinrod --sin-rodillos > ../02_CAVIDAD_N1/log_sinrod.txt 2>&1
python -I -B r4_t2_cavidad_n1.py --tag cil --cilindro > ../02_CAVIDAD_N1/log_cil.txt 2>&1
python -I -B r4_t2_cavidad_n1.py --tag fase4 --fase0 3.913043 > ../02_CAVIDAD_N1/log_fase4.txt 2>&1
python -I -B r4_t2_cavidad_n1.py --tag dens600 --n-plano 600 > ../02_CAVIDAD_N1/log_dens600.txt 2>&1
python -I -B r4_t2_cavidad_n1.py --tag dphi010 --dphi 0.1 > ../02_CAVIDAD_N1/log_dphi010.txt 2>&1
echo FIN > ../02_CAVIDAD_N1/sens_FIN.txt
