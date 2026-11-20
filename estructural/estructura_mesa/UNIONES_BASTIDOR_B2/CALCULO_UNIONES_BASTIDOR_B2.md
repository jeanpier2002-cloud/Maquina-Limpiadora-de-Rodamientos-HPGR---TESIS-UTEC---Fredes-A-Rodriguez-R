# Uniones soldadas del bastidor N3: diseño de M01–M07 (02/11/2026)

**Estado.** Cálculo EJECUTADO y diseño CANDIDATO. **HPGR D-076 confirmada por el usuario el 02/11** («Detalle completo»). Falta el plano MES-100 con los símbolos ISO 2553. **No apto para fabricación.**

- **Responde a** la observación 3.2 del asesor a la P2: «Diseñar soldaduras: el bastidor depende de las uniones a momento y no las has diseñado».
- **HPGR D-040** especificó las uniones como «soldadas a momento con continuidad de alas». Hasta ahora no estaban dimensionadas.

**Scripts:**
- `../SAP_ANEXO_N3_V573/scripts/p23_vlasov_continuidad_alas.py`: alabeo con continuidad de alas → `../SAP_ANEXO_N3_V573/resultados/v573/continuidad_alas_b2/`;
- `scripts/b2_uniones_calculos.py` → `resultados/CALCULO_UNIONES_B2.json`.

## 1. Las 10 uniones

Barras, nudos y numeración del SAP del anexo (hoja 01_GEOMETRIA): todas son W6X9 de A36 con las alas superiores coplanares (generador de R05, l. 672–679).

| Tipo | Nudos | Barra continua ← barra que llega |
|---|---|---|
| T | 3, 4 | M01 ← M05, M06 |
| T | 14, 15 | M02 ← M05, M06 |
| T | 9, 11 | M05, M06 ← M07 |
| Esquina | 1, 6 | M01 ← M03, M04 |
| Esquina | 12, 17 | M02 ← M03, M04 |

**Hoy el CAD superpone las barras en los nudos** (sólidos completos hasta los ejes): la unión no existe como pieza.

## 2. Detalle propuesto (igual en las 10)

1. **La barra que llega lleva destaje de alas.**
   - Sus alas terminan contra el **canto del ala** de la barra continua: las alas son coplanares.
   - Su alma entra entre las alas de la continua hasta tocar su alma.
2. **Alas: a tope con penetración completa (CJP).** Unión en V simple con resanado y cordón de sello por el reverso, en los 5,46 mm del ala. Las alas de las dos barras forman así **una sola placa** en el nudo.
3. **Alma: filete a3 por ambos lados** contra el alma de la continua, en 120 mm útiles.
4. **Rigidizador de alma en la barra continua**, en el lado opuesto al alma que llega:
   - chapa de 6 × 46 × 127 mm (A36), con chaflán de 10 mm por el radio;
   - filete a3 contra el alma y las dos alas;
   - b/t = 7,6, dentro del límite 0,56·√(E/F_y) = 15,9 (AISC J10.8).
   - **Función:** impedir la distorsión de la sección en el nudo, que es la condición para que el alabeo pase de una barra a otra (Vacharajittiphan y Trahair, 1974 [VERIFICAR referencia]).
5. **Esquinas:**
   - M01 y M02 se prolongan 50 mm, hasta el borde exterior de M03 y M04 (y = ±1 000). Así la esquina queda llena y el contorno exterior no cambia (1 960 × 2 000 mm);
   - se cierran con una **tapa de 6 mm** con filete a3 en todo el contorno, que sella la rendija (D-057) y hace de rigidizador.
6. **Aporte E70XX.** WPS precalificado según AWS D1.1 o procedimiento según ISO 15614 [VERIFICAR con el taller].

## 3. Lo que aporta la continuidad de alas al centrado (E06)

Hasta ahora se usaban dos cotas para el alabeo en los nudos: LIBRE e IMPEDIDO. La continuidad de alas no es ninguna de las dos.

**Condición de compatibilidad:**
- Las alas de las dos barras giran juntas en su plano. En el ala superior:
  - barra en X: w = θ_z − (h/2)·θ'_x;
  - barra en Y: w = θ_z − (h/2)·θ'_y.
- De ahí sale **θ'_x = θ'_y** en el nudo, que se impone exactamente (multiplicadores de Lagrange) en los 10 nudos.
- **Validación:** el modelo reproduce p22 en LIBRE e IMPEDIDO con 5·10⁻⁵ mm.

| Familia (LOCK, rigidez reducida; partidas H7/g6 de 1,58 mm) | A con LIBRE | **A con continuidad de alas** | A con IMPEDIDO |
|---|---:|---:|---:|
| NOM_V2 (1,45 kN) | 4,09 | **3,35** | 3,02 |
| DISP_DAT (1,60 kN) | 4,24 | **3,35** | 3,00 |
| **ENV208 (2,08 kN)** | 5,18 ✗ | **3,91 ✓** | 3,45 |
| ASIM_D03 (algebraico) | 5,51 ✗ | 5,01 | 4,24 |

**Lectura:**
- **Con el detalle de §2, E06 se cumple también en la envolvente de 2,08 kN.** Era la medida 2 de D-074: basta el 10 % del tramo entre LIBRE e IMPEDIDO, y la continuidad aporta el 74 %.
- **Sensibilidad al signo de la condición:** con el signo contrario, ENV208 da 4,06 mm. También cumple.

## 4. Cargas en los nudos (todas, también las nuevas)

Para las uniones se usa la parrilla de Vlasov de p23, con continuidad de alas y rigidez reducida. Se validó contra el SAP: el M33 máximo de M07 en ULS_BASE_R05 da 4,008 kN·m frente a 4,014 (−0,1 %).

| Grupo | Combinación | Fuente |
|---|---|---|
| Centrado (RG, LOCK) | 1,2(G + K2-M) + 1,6H (NOM, DISP, ASIM); 1,0 + 1,0 (ENV208, FALLO); ASIM_D03 aparte (algebraico) | REQ573; SAP del anexo |
| Lavado (LOCK) | RET = 1,4(G + K2-M + rodamiento) + 1,6 chorro; BASE = 1,4(G + rodamiento) | SAP del anexo (p12) |
| **Desvío lateral en el traslado (nuevo)** | 1,35(G + K2-M + rodamiento) + S = 6,51 kN en una rueda, en el contacto (Z290; par de 2,86 kN·m sobre la barra), reaccionado en la rueda del otro riel; 8 variantes | HPGR D-068 (EN 1991-3, S envolvente ya con 1,35) |
| **Tiro de cadenas (nuevo)** | 1,35(G + …) + 1,35 × 1,95 kN por cadena en M04 (x ±600, Z195), en ambos sentidos | HPGR D-071 |

**Los dos casos de traslado no estaban en el SAP del anexo.**

## 5. Resultados (AISC 360-16)

| Nudo | Unión | Alas CJP: σ (MPa) y D/C (0,9·F_y) | Caso | Alma: V (kN) y D/C | Esquina: línea de la CJP, D/C |
|---|---|---|---|---|---|
| 14, 15 | M02 ← M05, M06 | **129,9 / 0,58** | desvío en la rueda 13/16 | 12,0 / 0,15 | — |
| 3, 4 | M01 ← M05, M06 | 66,2 / 0,30 | desvío en la rueda 2/5 | 11,4 / 0,15 | — |
| 9, 11 | M05, M06 ← M07 | 31,1 / 0,14 | centrado DISP | 7,2 / 0,09 | — |
| 1, 6, 12, 17 | esquinas | 46,7–49,3 / 0,21–0,22 | desvío | ≤ 1,5 / 0,02 | ≤ 0,28 (tiro y centrado) |

**Cómo se compara cada parte:**
- **Alas CJP:** σ = P/A + M33/S33 + M22/S22 + B·ω/C_w en el extremo de la barra que llega, con ω = h₀·b_f/4. Con aporte compatible gobierna el metal base (AISC J2, tabla J2.5).
- **Alma:** mínimo entre dos capacidades:
  - filete, 156,5 kN (0,75 · 0,6 · 482 · 3 · 120 · 2);
  - fluencia por corte del alma recortada, 77,3 kN (J4.2).
- **ASIM_D03 (algebraico):** como máximo 0,37 en los nudos.

**Las barras completas también se revisaron con los casos nuevos.** Se mide la tensión de ala con el alabeo y el corte de Saint-Venant:

| Barra | Continuidad de alas: σ y D/C | Alabeo libre (cota): σ y D/C | Caso |
|---|---|---|---|
| **M01 / M02** | 182 / 172 MPa: **0,82 / 0,77** | 198 MPa: **0,89** | desvío lateral en el traslado |
| M05 / M06 | 130 MPa: 0,58 | 94 MPa: 0,42 | desvío / centrado |
| M03, M04, M07 | ≤ 57 MPa: ≤ 0,26 | ≤ 75 MPa: ≤ 0,34 | — |

- El corte de Saint-Venant (G·t·θ') es ≤ 12 MPa (D/C ≤ 0,09 frente a 0,9 · 0,6 · F_y, DG9).

**Hallazgo:**
- **El desvío lateral de las ruedas en el traslado es el caso que gobierna el bastidor:** M01 y M02 llegan a 0,82–0,89. El SAP del anexo no lo tenía. Antes, el máximo era 0,28 (RET).
- **Cumple, pero el margen es menor del que se creía.**
- La envolvente de D-068 es conservadora: pone toda la S en una rueda sin el alivio de su propia banda. Con el reparto nominal de EN 1991-3 serían 3,61 kN en lugar de 6,51.

**Fatiga:**
- No se evalúa: AISC 360-16 Apéndice 3, §3.1 la exime con menos de 20 000 ciclos.
- Estimación: ~2 rodamientos por semana × 50 semanas × 20 años = 2 000 ciclos [HIPÓTESIS].

## 6. Abiertos

- **[PENDIENTE] CAD y plano MES-100:**
  - CAD R07 V16 del bastidor con destajes, rigidizadores, tapas y M01/M02 prolongadas;
  - plano MES-100 con los símbolos ISO 2553 (V con sello para las alas CJP, a3 por ambos lados en el alma y en el rigidizador, a3 en todo el contorno de las tapas);
  - chequeo de interferencias de la prolongación de M01/M02 con la placa de las cadenas en M04 (D-071).
- **[VERIFICAR]**
  - WPS del taller (AWS D1.1 o ISO 15614-1) y calificación del soldador;
  - inspección: visual al 100 % y tintes penetrantes en las CJP [HIPÓTESIS de alcance];
  - referencia de la continuidad del alabeo con rigidizadores (Vacharajittiphan y Trahair, 1974).
- **[HIPÓTESIS]**
  - rodamiento como 3 cargas verticales iguales en los PAD (el SAP con el aro rígido da lo mismo en M07, −0,1 %);
  - número de ciclos;
  - continuidad perfecta de alas (sin distorsión), que se justifica con los rigidizadores.
- **Secuencia de soldadura y planitud:**
  1. soldar primero las alas CJP;
  2. luego las almas;
  3. por último los rigidizadores, en secuencia simétrica;
  4. medir después la planitud de los asientos de los PAD y de los datums. Su tolerancia es la partida de ±0,15 mm de K17.
