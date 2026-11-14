# Dimensionamiento hidráulico del sistema de aspersión — geometría R05 (22 boquillas)

Estado: **CANDIDATO** · borrador de trabajo para auditar (2026-09-27). Para la geometría oficial R05 sustituye al caso de 19 boquillas de `CALCULOS_DESARROLLO_ANALITICO_ASPERSION.pdf`, que **no se modifica**. La metodología es la misma: q = Kq·√p, Darcy–Weisbach con Swamee–Jain, Km = n·fT, aproximaciones sucesivas con la toma más desfavorable a 4 bar, Bernoulli depósito → C, potencia y NPSH. Reproducible con `calculo_red_22.py`, que escribe `resultados_22.json`; este documento lo escribe `generar_documento.py`.

## 1. Validación del método

El script reproduce primero el caso de 19 boquillas con las entradas de la Tabla 4 del documento.

| Magnitud | Documento (19) | Script (19) |
|---|---|---|
| Caudal total (L/min) | 173,99 | 173,992 |
| p_C (bar) | 3,998805 | 3,998805 |
| Altura de bomba (m) | 50,74881 | 50,74881 |
| Potencia al eje / eléctrica (kW) | 2,58 / 3,03 | 2,58 / 3,03 |

## 2. Qué cambia respecto del caso de 19 boquillas

| # | Cambio (fuente) | Tratamiento |
|---|---|---|
| H1 | Lados exteriores: misma topología, con la transversal DN50 en Z 1740 hasta X 900 y el ramal DN40 (R05 `red`) | Igual que el documento |
| H2 | LAT_5 pasa de Z 1070 a **Z 1040** (D-5, `00_LEEME_R05.md`) | Tramo E4–E5 = 0,060 m |
| H3 | `VALVULA_RAMAL_A/B` de paso total Ø42,76 en Z 1525–1615 (G-11) | K = 3 fT(DN40) = 0,06, como la bola de paso total del documento |
| H4 | **2 boquillas inferiores exteriores INF_EXT** en R 835,85 y Z 855, a 30° hacia arriba y hacia dentro (D-2) | Ramal DN40 hasta Z 944 (0,096 m), reducción de 1-1/2 × 1/2 y pie DN15 con codo de 45°. L equivalente 0,13 m [VERIFICAR con el CAD]; K = 0,5 + 16 fT + 30 fT (fT DN15 = 0,027, Crane [VERIFICAR]) |
| H5 | La lanza se alimenta por el recorrido real R04/R05: red fija, V-AIS (Cv 38), flexible de 1,26 m, curva de 180° y cuello móvil (`RESULTADOS_CALCULOS_R04.json`, `hidraulica_ramal_lanza`) | La pérdida de R04 (0,98775 m a 54,706 L/min) se usa como **K equivalente = 8,663** sobre la velocidad DN25; tope del cuello en Z 1700. El documento usaba un tramo C–I0 de 0,28 m con ΣK 2,07 |
| H6 | **Boquilla inferior interior INF_INT** en Y 400 y Z 850, a 25° hacia arriba | Pie DN25 bajo INT_1, L = 0,25 m, K = 60 fT [VERIFICAR] |
| H7 | Tomas superiores | En Z 1740, como el documento (no se modela el descenso dentro de la boquilla) |

Recuento: 2 lados × (2 superiores + 5 laterales + 1 inferior exterior) + lanza (5 + 1 inferior interior) = **22 boquillas**.

## 3. Aproximaciones sucesivas

| Iteración | p_C (bar) | p_mín (bar) | Q (L/min) |
|---|---|---|---|
| 0 | 4,000000 | 3,937894 | 200,588635 |
| 1 | 4,062106 | 4,001172 | 201,039492 |
| 2 | 4,060934 | 3,998360 | 202,594551 |
| 3 | 4,062574 | 4,000075 | 202,552204 |
| 4 | 4,062498 | 3,999955 | 202,593500 |
| 5 | 4,062543 | 4,000003 | 202,591269 |
| 6 | 4,062540 | 3,999999 | 202,592400 |
| 7 | 4,062541 | 4,000000 | 202,592311 |
| 8 | 4,062541 | 4,000000 | 202,592343 |
| 9 | 4,062541 | 4,000000 | 202,592340 |

La toma más desfavorable pasa a ser **INT_5, la más alta de la lanza**, por la pérdida del recorrido real que alimenta la lanza (H5). En el caso de 19 boquillas lo era S2 (superior).

## 4. Tramos del estado convergido

| Rama | Tramo | DN | L (m) | ΣKm | Q (L/min) | v (m/s) | hL (m) | z final (m) |
|---|---|---|---|---|---|---|---|---|
| exterior (x2) | C-S1 | DN50 | 0,5360 | 1,140 | 73,886 | 0,523 | 0,01902 | 1,7400 |
| exterior (x2) | S1-S2 | DN50 | 0,0880 | 0,380 | 64,696 | 0,458 | 0,00446 | 1,7400 |
| exterior (x2) | S2-E0 | DN50 | 0,2760 | 0,950 | 55,507 | 0,393 | 0,00842 | 1,7400 |
| exterior (x2) | E0-E1 (con valvula de ramal) | DN40 | 0,3940 | 0,460 | 55,507 | 0,644 | 0,01437 | 1,3463 |
| exterior (x2) | E1-E2 | DN40 | 0,0821 | 0,400 | 46,277 | 0,537 | 0,00657 | 1,2642 |
| exterior (x2) | E2-E3 | DN40 | 0,0821 | 0,400 | 37,039 | 0,430 | 0,00422 | 1,1821 |
| exterior (x2) | E3-E4 | DN40 | 0,0821 | 0,400 | 27,793 | 0,323 | 0,00239 | 1,1000 |
| exterior (x2) | E4-E5 | DN40 | 0,0600 | 0,400 | 18,538 | 0,215 | 0,00104 | 1,0400 |
| exterior (x2) | E5-extension | DN40 | 0,0960 | 0,000 | 9,276 | 0,108 | 0,00004 | 0,9440 |
| exterior (x2) | reduccion + pie DN15 | DN15 | 0,1300 | 1,742 | 9,276 | 0,675 | 0,04578 | 0,8550 |
| lanza | C-I0 (red fija, V-AIS, flexible, cuello) | DN25 | 0,0000 | 8,663 | 54,821 | 1,499 | 0,99190 | 1,7000 |
| lanza | I0-I1 | DN25 | 0,3618 | 0,460 | 54,821 | 1,499 | 0,08903 | 1,3382 |
| lanza | I1-I2 | DN25 | 0,0954 | 0,460 | 45,703 | 1,250 | 0,04337 | 1,2428 |
| lanza | I2-I3 | DN25 | 0,0953 | 0,460 | 36,580 | 1,000 | 0,02787 | 1,1475 |
| lanza | I3-I4 | DN25 | 0,0953 | 0,460 | 27,449 | 0,750 | 0,01577 | 1,0522 |
| lanza | I4-I5 | DN25 | 0,0954 | 0,460 | 18,309 | 0,501 | 0,00708 | 0,9568 |
| lanza | I5-I6 (pie 25 grados) | DN25 | 0,2500 | 1,380 | 9,160 | 0,250 | 0,00530 | 0,8500 |

Se muestra un lado exterior; el segundo es simétrico.

## 5. Presión y caudal en las tomas

| Toma | Cantidad | p (bar) | q (L/min) |
|---|---|---|---|
| S1_SUP_1 | 2 | 4,06360 | 9,18986 |
| S2_SUP_2 | 2 | 4,06317 | 9,18938 |
| E1_LAT_4 | 2 | 4,09891 | 9,22970 |
| E2_LAT_3 | 2 | 4,10618 | 9,23789 |
| E3_LAT_2 | 2 | 4,11369 | 9,24633 |
| E4_LAT_1 | 2 | 4,12137 | 9,25495 |
| E5_LAT_5 | 2 | 4,12705 | 9,26133 |
| E6_INF_EXT | 2 | 4,14046 | 9,27636 |
| I1_INT_5 | 1 | 4,00000 | 9,11767 |
| I2_INT_4 | 1 | 4,00501 | 9,12338 |
| I3_INT_3 | 1 | 4,01151 | 9,13077 |
| I4_INT_2 | 1 | 4,01917 | 9,13949 |
| I5_INT_1 | 1 | 4,02768 | 9,14916 |
| I6_INF_INT | 1 | 4,03746 | 9,16026 |

- Caudal total: **202,59 L/min** (12,16 m³/h). Cada lado exterior aporta 73,886 L/min y la lanza 54,821 L/min.
- p_C = **4,06254 bar**. El caudal varía un 1,74 % entre boquillas (de 9,118 a 9,276 L/min).

## 6. Altura de bomba, potencia y NPSH

| Contribución | Altura (m) |
|---|---|
| Presión requerida en la alimentación central | 42,16616 |
| Desnivel entre el nivel libre y la alimentación central | 0,77000 |
| Fricción y accesorios de la línea estacionaria (DN40, 14 m, ΣK 5,66) | 3,55905 |
| Fricción y codo de la alimentación del distribuidor | 0,41459 |
| Pérdidas de la succión | 0,17746 |
| Unión rotativa (0,30 bar) y filtro (0,20 bar) | 5,18963 |
| Carga cinética en la alimentación central | 0,28178 |
| **Total** | **52,55867** |

| Magnitud | 19 boquillas (documento) | **22 boquillas (R05)** | Comentario |
|---|---|---|---|
| Caudal (L/min) | 173,99 | **202,59** | +16,4 % |
| Altura de bomba (m) | 50,75 | **52,56** | +3,6 % |
| Velocidad en la alimentación DN40 (m/s) | 2,02 | **2,35** | Dentro del criterio de 1,5–3 m/s |
| Potencia hidráulica (kW) | 1,418 | **1,710** | |
| Potencia al eje, η_b = 0,55 (kW) | 2,58 | **3,11** | +20,6 % |
| Consumo eléctrico, η_m = 0,85 (kW) | 3,03 | **3,66** | |
| NPSH disponible con nivel a +0,50 m (m) | 6,01 | **5,97** | Sin nivel inundado: 5,47 m |
| Volumen circulado en 10 min (L) | 1740 | **2026** | Recirculado; no es consumo de agua nueva |

La presión de vapor a 62 °C se toma de la que queda implícita en el documento (NPSH sin nivel inundado = 5,51249 m): p_v = 21,867 kPa. La presión atmosférica sale de ISO 2533 a 2335 m: 76,244 kPa.

**Punto de predimensionamiento de la bomba con 22 boquillas: ≈ 203 L/min (12,2 m³/h) y ≈ 53 m.**

## 7. Sensibilidad a una presión uniforme (22 boquillas)

| p (bar) | q (L/min) | 22·q (L/min) | v_j (m/s) | F (N) |
|---|---|---|---|---|
| 3 | 7,896 | 173,715 | 23,481 | 3,035 |
| 4 | 9,118 | 200,589 | 27,114 | 4,047 |
| 5 | 10,194 | 224,265 | 30,314 | 5,058 |
| 6 | 11,167 | 245,670 | 33,207 | 6,070 |

Se aplica la misma presión a las 22 boquillas; no es una nueva resolución de la red.

## 8. Consecuencias para el CFD (CFD02_ANSYS)

- El CFD exterior (F7) usó **9,1177 L/min por boquilla**, el caudal de catálogo a 4 bar (decisión D1). Con la red de 22, las laterales reciben **9,23–9,28 L/min** y las superiores 9,19 L/min, entre un 0,8 y un 1,7 % más. D y J escalan linealmente con el caudal, así que la D̄ de E-OD sube ≈ 1,3 % y la de E-SUP ≈ 0,8 %; CV y zona seca prácticamente no cambian. Se puede corregir en el post-proceso o con una corrida nueva.
- La lanza pasa a ser la rama crítica (INT_5 a 4,00 bar). Sus caudales, de 9,12 a 9,16 L/min, son casi iguales a los que usó la rama B.

## 9. Limitaciones

- **Heredadas del documento:**
  - propiedades del agua en lugar del detergente;
  - coeficientes Km de predimensionamiento;
  - curvas de boquilla, filtro, unión rotativa y bomba por confirmar;
  - trazado supuesto de la línea estacionaria (14 m).
- **Nuevas en este cálculo:**
  - longitudes de los pies DN15 y DN25 (H4, H6) estimadas, sin medir en el CAD;
  - pérdida de la lanza (H5) tomada de R04 como un K equivalente constante;
  - la derivación de cada boquilla (niple de 3/8") no se modela, igual que en el documento.
- Nada de esto demuestra limpieza: solo define la demanda hidráulica de la configuración R05.
