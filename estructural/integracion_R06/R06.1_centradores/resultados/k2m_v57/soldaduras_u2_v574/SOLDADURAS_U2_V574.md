# Soldaduras del soporte de U2 y hueco de 2 mm (K2-M v5.7.4, HPGR D-054) — 20/10/2026

**Estado:** EJECUTADO (cribado). Se apoya en tres fuentes:

- **Medición en una copia del CAD v5.7.4** (`cad/R061_K2M_V574_CANDIDATO.FCStd`, sin modificar).
- **Resultados globales del FEM de U2 v5.7.4** (mallas 1 y 2, signos ±1, solo lectura). Se tomaron del respaldo `RESPALDO_R061_FEM_SCRATCH_V574_CTRL_2026-09-30.zip`.
- **Cálculo manual** (EN 1993-1-8, IIW).

**Hipótesis:**

- material equivalente a S235 (el proyecto usa A36: Fy 250 / Fu 400);
- cargas del FEM a 2,08 kN, linealizables;
- número de ciclos.

Nada es definitivo ni está liberado para fabricación.

## 1. Respuesta corta

1. **El pico que no converge es una singularidad de modelo, no un defecto del diseño.** El FEM une placa, pedestal, silla y soporte del limitador con aristas vivas a 90°. En elasticidad lineal, la tensión en una arista viva crece sin límite al refinar la malla: 146 → 158 MPa y 139 → 169 MPa (K20). Las magnitudes con significado físico sí convergen:
   - la flecha: 0,910719 → 0,910715 mm;
   - la tensión de sección, membrana + flexión: 127,5 → 129,1 MPa (K20);
   - la tensión de punto caliente en la raíz placa–silla: −2 % entre mallas (§5).
2. **El CAD no deja sitio para un cordón en ángulo al pie del pedestal.**
   - En unos 270° la placa sobresale solo 2 mm del pedestal (disco R32 sobre el pedestal r30).
   - El disco no puede crecer: con R34 el cartucho del limitador queda a 1 mm, y con R36 o más choca.
   - Un cordón de 6 mm chocaría además con el soporte de retención (347 mm³).

   **Esa unión tiene que ser a tope con penetración completa** (pedestal biselado y enrasado al disco). Así la representa de hecho el FEM.
3. **Espacio medido para los demás cordones:**
   - placa–silla arriba: **6 mm**;
   - placa–silla abajo: **4 mm**, porque con 6 mm toca las tuercas cautivas;
   - soporte del limitador: **6 mm solo arriba**, porque abajo choca con el cartucho.
4. **Todas las verificaciones cumplen con margen** (a 2,08 kN; en operación, a 1,45 kN, es un 30 % menos):

   | Comprobación | Resultado |
   |---|---|
   | Garganta placa–silla | aprovechamiento ≤ 0,34 |
   | Garganta del soporte del limitador | aprovechamiento ≤ 0,53 |
   | Pedestal a tope (metal base) | 20 MPa |
   | Placa, tensión de sección | 102–129 MPa (Fy 250) |
   | Placa del limitador (flexión nominal) | 91 MPa |
   | Fatiga por punto caliente, con 73 000 ciclos HIPOTÉTICOS | daño **0,008** |
5. **Hueco de 2 mm entre la placa (Z778) y el soporte de retención (Z780).** No es una holgura funcional: el chequeo oficial clasifica pedestal–soporte de retención como `UNION_PREVISTA` (7 679 mm³), así que placa, pedestal y soporte son **un mismo conjunto soldado y rígido**, sin movimiento relativo. El riesgo es de fabricación:
   - una rendija de 2 mm que no se puede soldar ni limpiar, con agua alcalina de lavado (corrosión por rendija);
   - un ajuste incierto por tolerancias.

   **Se recomienda cerrarlo:** el soporte de retención baja 2 mm, apoya sobre la placa donde se solapan (r 744–758) y se suelda. Hay que soldar primero el pedestal a la placa.

## 2. Por qué el pico no converge

| Magnitud (FEM U2 v5.7.4, 2,08 kN) | Malla 1 | Malla 2 | Converge | Uso |
|---|---|---|---|---|
| Flecha radial a Z955, signo −1 (mm) | 0,910719 | 0,910715 | sí | precisión y captura |
| Tensión de sección máx. en la placa, r ≈ 36, signo −1 (MPa) | 127,5 | 129,1 | sí | **resistencia estática** |
| Pico nodal, pie pedestal–placa, signo −1 (MPa) | 145,9 | 158,4 | **no** | ninguno: singularidad |
| Pico nodal, banda inferior / soporte del limitador, signo +1 (MPa) | 138,8 | 169,4 | **no** | ninguno: singularidad |
| Pico nodal, raíz hacia la silla, signo −1 (MPa) | 113,8 | 140,3 | **no** | ninguno: singularidad |
| Punto caliente IIW, placa–silla arriba, signo −1 (MPa) | 59,6 | 58,4 | sí | **fatiga** |

Fuentes: K20 (`codex_k2m/K20_evaluar_v574.out.txt` §2) y `SOLDADURAS_U2_V574.json`.

**Criterio de evaluación:**

- La **resistencia estática** del metal base se juzga con la tensión de sección (membrana + flexión), sin el pico.
- La **resistencia del cordón**, con su garganta.
- El pico solo es relevante para la **fatiga**, y para eso se usa el punto caliente (IIW).

Un submodelo con radio en la arista exigiría una geometría que la unión real no tendrá: a tope en el pedestal, con un labio de 2 mm. Además, el daño a fatiga ya es 0,008, así que no aportaría una decisión distinta. Queda como opcional (submodelo de entalla efectiva IIW, r = 1 mm), una vez definido el procedimiento de soldadura.

## 3. Espacio para los cordones (medido en el CAD)

| Raíz | Cordón de 6 mm | Cordón de 4 mm | Decisión propuesta |
|---|---|---|---|
| Pedestal–placa (pie) | ✗ labio de 2 mm en ~270°; choca con el soporte de retención | ✗ | **Penetración completa**: bisel en el pedestal, enrasado al disco R32, sobreespesor amolado |
| Placa–silla, arriba (Z778, x = −868) | ✓ | ✓ | Cordón de 6 mm, L = 130 mm |
| Placa–silla, abajo (Z750) | ✗ toca las tuercas cautivas 3 y 4 (1,6 mm³) | ✓ (queda a 0,61 mm) | Cordón de 4 mm, o de 6 mm interrumpido en las tuercas |
| Soporte del limitador, arriba (Z760) | ✓ | ✓ | Cordón de 6 mm, una sola cara, L ≈ 36 mm |
| Soporte del limitador, abajo (Z755) | ✗ choca con el cartucho (79 mm³) | ✗ (15 mm³) | Sin cordón. Carga en el plano de la placa, sin flexión que abra la raíz [VERIFICAR] |
| Disco mayor (R34 / R36 / R38) | — | — | R34 deja el cartucho a 1,0 mm; R36 o más choca con el cartucho y el resorte. No se agranda |

Archivos: `medidas_u2.json`, `medidas_disco.json` y `medidas_cordones.json` (scripts `r061_medir_*_u2_v574.py`).

## 4. Resistencia estática (EN 1993-1-8, 4.5.3.3, simplificado)

f_vw,d = f_u / (√3·β_w·γ_M2) = 360 / (√3·0,8·1,25) = **207,8 MPa**. Los esfuerzos en la raíz placa–silla salen de la estática, con F en el eje del pivote a Z955 y el par del pivote:

| Caso | F (N) | Par (N·m) | My (N·m) | Mz (N·m) | Placa–silla abajo, 4 mm: f / f_Rd | Arriba, 6 mm | Limitador, 6 mm: f / f_Rd |
|---|---|---|---|---|---|---|---|
| s = −1 | (−2 119; −101) | −97,3 | −404,7 | −393,3 | 189 / 582 = **0,33** | 0,22 | 347 / 873 = **0,40** |
| s = +1 | (−1 917; −908) | −129,8 | −366,1 | −482,4 | 196 / 582 = **0,34** | 0,22 | 463 / 873 = **0,53** |

**Pedestal a tope** (resiste como el metal base): flexión de 18,2 MPa + cortante y torsión de 4,9 MPa → σ_vm = **20 MPa**.

**Placa del soporte del limitador:**

- Tiene 5 mm y saca el par del pivote como fuerza tangencial q = par/50 mm = **2,6 kN** a 38 mm del disco.
- Flexión nominal en su raíz: 6·q·38/(5·36²) = **91 MPa** a 2,08 kN, y 70 MPa a 1,60 kN (disparo).
- El pico del FEM (169 MPa) es la arista viva de esa raíz.

**Placa de 28 mm:** tensión de sección de 102–129 MPa a 2,08 kN (K20); 90–99 MPa a 1,45–1,60 kN. Queda por debajo de Fy = 250 MPa y del filtro de cribado de 150 MPa.

## 5. Fatiga por punto caliente (IIW)

**Método.** Extrapolación lineal σ_hs = 1,67·σ(0,4t) − 0,67·σ(1,0t) sobre la superficie, con la componente perpendicular a la raíz (σ_xx en placa–silla; σ_zz en la pared del pedestal):

- placa: t = 28 mm;
- pared del pedestal: t = 18 mm;
- interpolación por distancia inversa sobre los nudos de la superficie.

| Raíz, máx. \|σ_hs\| (MPa), signo −1 / +1 | Malla 1 | Malla 2 | Cambio |
|---|---|---|---|
| Placa–silla, arriba | 59,6 / 50,2 | 58,4 / 49,3 | −2 % |
| Placa–silla, abajo | 40,9 / 33,3 | 40,7 / 33,5 | 0 % |
| Pared del pedestal (lado ancho de la placa, ~135–150°) | 61,2 / 51,9 | 68,4 / 57,9 | +11 % (la malla 1 encuentra 14 puntos y la malla 2, 24) |

**Daño acumulado:**

| Paso | Valor |
|---|---|
| Δσ en operación (1,45 kN, D-043), con el peor σ_hs de la malla 2 (68,4 MPa × 1,45/2,08) | **47,7 MPa** |
| Categoría y factor | FAT 90 (cordón portante, conservador), γ_Mf = 1,15 [HIPÓTESIS] |
| N admisible = 2·10⁶·(90 / (1,15·47,7))³ | **8,9·10⁶ ciclos** |
| Ciclos supuestos: 10 centrados/día × 365 × 20 años [HIPÓTESIS] | 73 000 |
| Daño | **0,008** |

La placa del limitador (5 mm) no se resuelve con la malla global (elementos de 3,5–5 mm frente a 0,4t = 2 mm). Se cubre con el cálculo nominal del §4.

## 6. Especificación propuesta (HIPÓTESIS de diseño, a ratificar)

| Unión | Detalle |
|---|---|
| Pedestal–placa (U2) | A tope con penetración completa, todo el contorno; bisel en el pedestal; enrasado al disco R32; sobreespesor amolado |
| Placa–silla | Cordón de 6 mm arriba y de 4 mm abajo, L = 130 mm. Abajo, de 6 mm interrumpido junto a las tuercas cautivas si se prefiere |
| Soporte del limitador–disco | Cordón de 6 mm arriba, una sola cara, L ≈ 36 mm |
| Soporte de retención | Bajar 2 mm hasta apoyar sobre la placa (r 744–758) y soldarlo (cierra la rendija). **Secuencia:** pedestal–placa primero |

## 7. Limitaciones y pendientes

- **Material:** A36 frente a S235 [VERIFICAR el material de compra]. Con f_u = 400 MPa, f_vw,d sería mayor.
- **Fatiga:** FAT 90, γ_Mf y el número de ciclos son HIPÓTESIS. Con daño 0,008 el margen es amplio aun con 100 veces más ciclos.
- **Soporte del limitador:**
  - el reparto del par (parches en r 20/70, igual que el FEM) es una idealización;
  - el cordón de una sola cara exige que no haya flexión que abra la raíz [VERIFICAR con el diseño del mecanismo];
  - falta la tensión en la placa de 5 mm con malla fina.
- **Fabricación:** procedimiento de soldadura (WPS), inspección de la soldadura a tope, acceso de la antorcha y protección contra la corrosión con agua alcalina [PENDIENTE].
- **Planos:** revisión CAD con estos detalles, D-050 y D-053 [PENDIENTE]. Los archivos existentes no se modificaron.

## 8. Trazabilidad

- **Scripts:**
  - `scripts/r061_soldaduras_u2_v574.py`: punto caliente, gargantas y fatiga;
  - `scripts/r061_medir_u2_v574.py`, `r061_medir_disco_u2_v574.py` y `r061_medir_cordones_u2_v574.py`: mediciones del CAD con freecadcmd sobre una copia.
- **Salidas** (`resultados/k2m_v57/soldaduras_u2_v574/`): `SOLDADURAS_U2_V574.json`, `medidas_*.json`.
- **Entradas:**
  - FRD de U2 v5.7.4 `fem_v574b_u2/R061_FEM_LOCAL_U2/malla_{1,2}/F2080_s{−,+}1/*.frd`, del ZIP de respaldo, extraídos en el scratchpad;
  - K20;
  - chequeo `R061_K2M_CHEQUEO_v574.csv` (par MONTANTE–SOPORTE_RETENCION, `UNION_PREVISTA`).
