# INFORME_R3_comparacion — T7 (generado por r3_comparar.py; no editar a mano)

Fuentes: `resultados/KPI/<caso>/<caso>_resumen.csv` (r3_post.py), `KPI/REF_*` (r3_ref_resumen.py), `05_VERIF_PREVIA/PREDICCION_N1_O7C2.csv`, `resultados/destino_*.csv`. Con obstaculos; ventana 25-50 ms.

| superficie | kpi | REF_CB | REF_C2 | R3_01_kit | R3_02_caso2 | R3_03_B_caso2 | R3_02_03_AB |
|---|---|---|---|---|---|---|---|
| OD | D̄ 10 mm | 26,38 | 26,38 | 25,82 | 25,83 | 25,82 | 25,82 |
| OD | CV 10 mm | 0,304 | 0,265 | 0,661 | 0,643 | 0,653 | 0,648 |
| OD | D_min 10 mm | 0,27 | 14,56 | 0,13 | 12,00 | 9,07 | 10,53 |
| OD | zona seca 10 mm % | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| OD | zona seca 2 mm % | 1,17 | 0,00 | 1,56 | 0,00 | 0,00 | 0,00 |
| OD | η % | 94,2 | 94,2 | 79,1 | 79,1 | 79,1 | 79,1 |
| OD bajo z 890-1000 | D̄ | 29,34 | 29,34 | 28,69 | 28,70 | 28,66 | 28,68 |
| OD bajo z 890-1000 | D_min | 26,28 | 26,28 | 11,99 | 12,00 | 9,07 | 10,53 |
| OD alto z 1000-1405 | D̄ | 25,59 | 25,59 | 25,06 | 25,06 | 25,06 | 25,06 |
| OD alto z 1000-1405 | CV | 0,345 | 0,299 | 0,357 | 0,309 | 0,312 | 0,309 |
| OD alto z 1000-1405 | D_min | 0,27 | 14,56 | 0,13 | 14,56 | 14,88 | 15,69 |
| Cara inferior | D̄ 10 mm | 5,46 | 5,45 | 14,19 | 14,19 | 14,13 | 14,16 |
| Cara inferior | CV 10 mm | 0,626 | 0,626 | 0,428 | 0,429 | 0,435 | 0,430 |
| Cara inferior | D_min 10 mm | 2,83 | 2,83 | 7,51 | 7,54 | 7,12 | 7,33 |
| Cara inferior | zona seca 10 mm % | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| Cara inferior | zona seca 2 mm % | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| Cara inferior | η % (INF_EXT+C2+INF_INT) | 30,9 | 30,9 | 48,3 | 48,3 | 48,1 | 48,2 |
| Z1 r 450-521 | D̄ | 10,17 | 10,17 | 12,11 | 12,11 | 11,75 | 11,93 |
| Z2 r 521-617 (pared proyectada) | D̄ | 3,77 | 3,77 | 9,60 | 9,60 | 9,87 | 9,73 |
| Z3 r 617-710 | D̄ (D-047: ≥ 15,8) | 4,14 | 4,13 | 20,09 | 20,10 | 19,89 | 19,99 |
| Z3 r 617-710 | CV (D-047: ≤ 0,4) | 0,246 | 0,244 | 0,298 | 0,298 | 0,306 | 0,298 |
| Z3 r 617-710 | D_min 2 mm | 2,41 | 2,41 | 10,95 | 10,95 | 11,16 | 11,11 |

## N1 / estimado / CFD

| superficie | caso N1 | magnitud | N1 | estimado | R3_01 S9 | R3_02 S9 | Caso 2 A+B |
|---|---|---|---|---|---|---|---|
| cara_inferior | O7+C2 (kit) | D_media_A+B | 13.88 | 13.95 | 14.19 | 14.19 | 14.16 |
| cara_inferior | O7+C2 (kit) | CV | 0.412 | ~0.41 | 0.4285 | 0.4286 | 0.4303 |
| cara_inferior | O7+C2 (kit) | D_min_10mm | 7.63 | 7.40-7.67 | 7.505 | 7.541 | 7.332 |
| cara_inferior | O7+C2 (kit) | zona_seca_10mm_pct | 0.00 | 0 | 0 | 0 | 0 |
| cara_inferior | O7+C2 (kit) | D_min_2mm | 6.68 |  | 6.141 | 6.195 | 6.831 |
| cara_inferior | O7+C2 (kit) | Z1_D_media | 11.95 |  | 12.11 | 12.11 | 11.93 |
| cara_inferior | O7+C2 (kit) | Z2_D_media | 9.70 |  | 9.596 | 9.596 | 9.734 |
| cara_inferior | O7+C2 (kit) | Z3_D_media | 19.58 |  | 20.09 | 20.1 | 19.99 |
| OD | O7+C2 + Caso 2 | D_media_A+B | 25.98 |  | 25.82 | 25.83 | 25.82 |
| OD | O7+C2 + Caso 2 | CV | 0.645 |  | 0.6609 | 0.6434 | 0.6479 |
| OD | O7+C2 + Caso 2 | D_min_10mm | 11.59 | ~9.4 (9-12) | 0.1331 | 12 | 10.53 |
| OD | O7+C2 + Caso 2 | zona_seca_2mm | 0 | 0 | 1.558 | 0 | 0 |

- franja sin deposito del OD, R3_01_kit, D_libre: 4 bandas de 2 mm, z 1030-1038
- franja sin deposito del OD, R3_01_kit, D_obst_media_theta: 4 bandas de 2 mm, z 1030-1038

- franja sin deposito del OD, R3_02_caso2, D_libre: 0 bandas de 2 mm, z ninguna
- franja sin deposito del OD, R3_02_caso2, D_obst_media_theta: 0 bandas de 2 mm, z ninguna

- franja sin deposito del OD, R3_03_B_caso2, D_libre: 0 bandas de 2 mm, z ninguna
- franja sin deposito del OD, R3_03_B_caso2, D_obst_media_theta: 0 bandas de 2 mm, z ninguna

- franja sin deposito del OD, R3_02_03_AB, D_libre: 0 bandas de 2 mm, z ninguna
- franja sin deposito del OD, R3_02_03_AB, D_obst_media_theta: 0 bandas de 2 mm, z ninguna
