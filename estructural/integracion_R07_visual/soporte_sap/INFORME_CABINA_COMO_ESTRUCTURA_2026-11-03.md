# ¿Basta la cabina? El soporte del rotor frente a la cabina como estructura (SAP2000, 03/11/2026)

**Estado.** Análisis EJECUTADO en SAP2000 v27 por API, con un modelo de cáscaras de la cabina. **HPGR D-078: decidida por Claude por delegación (02–03/11), pendiente de revisión del usuario.** Nada es apto para fabricación (HPGR D-045).

**Pedido del usuario (02/11, noche).** «Revisar la estructura que sostiene el motorreductor del techo, el que gira la tubería en U invertida, o mejor dicho la cabina, ya que por ejemplo creo que sin estructura y que tal vez solo la cabina sea suficiente.»

## Respuesta corta

1. **La cabina sola no basta.** Con chapa plana de inox de 1,5 mm (la del presupuesto), el techo de 4 m no aguanta ni su propio peso: se hunde 1 037 mm en el cálculo lineal (K3) y pandea con factores menores que 1. Con el cartucho encima, la flecha es de 8,6 m (K14), y con 3 mm, de 1,2 m (K15). Para que un techo plano sostenga el cartucho con flecha L/1000, la chapa tendría que ser de **23 mm** (3,1 t).
2. **Quitar los postes tampoco funciona.** Si las vigas apoyan directamente en los muros de 1,5 mm, el borde del muro abolla bajo la reacción de la viga. El factor de pandeo es 0,23 y el cálculo a mano da F_cr ≈ 1,35 kN, frente a 1,2–1,9 kN de reacción.
3. **Donde la cabina sí ayuda es en la rigidez lateral.** Si la chapa se atornilla al marco como diafragma, f1 pasa de 5,2 a 14–16 Hz y el cojinete superior se mueve 0,61–0,77 mm en lugar de 0,99 mm, incluso con postes más livianos, bases articuladas y sin celosía.
4. **No conviene contar con ese aporte.** Ahorraría ~90 kg de acero (≈ S/ 1 400, el 0,4 % de la máquina), pero:
   - la estructura quedaría dependiendo de paneles que se abren, se cortan o se cambian en mantenimiento;
   - habría que diseñar las uniones de la chapa como diafragma, para lo que no hay norma directa con chapa plana;
   - la chapa plana abolla: el primer factor de pandeo positivo es 1,10 frente a las cargas últimas (K12), por debajo del criterio de 3.
5. **El soporte de D-065 se mantiene y cumple con el rotor real** (231 kg, CG a 79,6 mm): D/C 0,12, f1 5,20 Hz, lateral del cojinete 0,99 mm y flecha L/3 456. La chapa queda como **reserva no contada**.
6. **Hallazgo colateral:** el techo de chapa necesita **correas propias**. Basta con 5 RHS 80×40×3 de inox (110 kg, D/C 0,68), que caben en el +20 % de refuerzos del presupuesto.

## 1. Qué se comparó

| Caso | Qué representa | Postes | Celosía en muros | Bases | Vigas + X en planta | Chapa |
|---|---|---|---|---|---|---|
| **K0** | Marco de D-065 (O10) con el rotor real; la chapa no trabaja | SHS100×5 | L40×4 | empotradas | RHS160×80×5 + L40×4 | — |
| K14, K15 (y K1) | **Cabina sola**: el cartucho apoya en el techo. K1 es K14 con S1 no lineal; K2, su par de 3 mm, no llegó a correr | — | — | — | — | 1,5 / 3 mm, con su peso |
| K3, K4 | Vigas sobre los muros, sin postes | — | — | — | sí | 1,5 / 3 mm, con su peso |
| K9 | Ídem, con la chapa solo como diafragma | — | — | — | sí | 1,5 mm, diafragma |
| K5 | Chapa como diafragma; postes articulados, sin celosía | SHS100×5 | — | articuladas | sí | 1,5 mm, diafragma |
| K7 | Ídem, con postes más livianos | SHS80×4 | — | articuladas | sí | 1,5 mm, diafragma |
| K6, K8, K11 | K5 y K7 con uniones flexibles (cortante de la chapa al 10 % y al 30 %) | | | | | |
| K10 | Marco de D-065 completo más la chapa como diafragma (la reserva) | SHS100×5 | L40×4 | empotradas | sí | 1,5 mm, diafragma |
| K12, K13 | K7 y K9 con 60 modos de pandeo, para hallar el primer factor positivo | | | | | |

## 2. Modelo

**Archivos:**
- modelo paramétrico: `scripts/SoporteCabinaSAP.cs`. Extiende `SoporteSAP.cs` de D-065, que no se modifica;
- ejecución: `scripts/s04_correr_cabina.ps1`;
- resumen y chequeos a mano: `scripts/s05_resumen_cabina.py` → `resultados_cabina/RESUMEN_CABINA.csv` y `CHEQUEOS_MANO.json`;
- modelos: `modelos_cabina/*.sdb`.

**Cabina** (planos medios de `CTX_CABIN` en el CAD V17B):
- muros en x = ±2 020 e y = ±2 070, de z 0 a 2 610;
- techo en z 2 610;
- vano de la puerta en el frente: x ±1 070, z 140–1 605;
- cáscara delgada de inox 304 (E = 193 GPa, ν = 0,29, 8 000 kg/m³, F_y = 205 MPa), con malla de ≤ 150 mm (2 768 áreas);
- espesor de 1,5 mm (el del presupuesto) o de 3 mm, ambos **[HIPÓTESIS]**;
- base de los muros articulada y continua sobre el bordillo **[HIPÓTESIS]**;
- esquinas y bordes unidos en continuidad **[HIPÓTESIS]**.

**«Chapa como diafragma» (diaf = 1):** la chapa conserva su rigidez, pero su peso y su masa los llevan los nervios de los paneles, que no se modelan. Así se aísla lo que la chapa aporta como diafragma, sin el problema de su propio peso.

**Uniones flexibles:** el modificador f12 baja la rigidez a cortante de membrana al 10 % y al 30 %. Representa la flexibilidad de tornillos o remaches **[HIPÓTESIS]**.

**Marco, cartucho y cargas:** iguales a D-065 (`INFORME_SOPORTE_SAP.md` §2), con un cambio: el rotor es el real de D-075 (231,0 kg → 2 266 N; CG a 79,6 mm → 180 N·m, en el mismo sentido que la accidental). Las combinaciones son AISC 360-16 LRFD (U1–U3) y de servicio (S1, S2).

**Análisis:**
- estático lineal;
- modal de 12 modos;
- pandeo lineal con las cargas de U2 y U3 (X e Y);
- en K1, además, S1 no lineal con grandes desplazamientos. No convergió y se detuvo; K2 no llegó a correr.

**Criterios:**
- los de D-065, fijados antes de ver los resultados: D/C ≤ 0,6, flecha S1 ≤ L/1000, lateral del cojinete superior en S2 ≤ 1,20 mm y f1 no menor que la del soporte vigente;
- para la chapa, criterios propios **[HIPÓTESIS]**: σ_VM ≤ F_y/1,1 en U y factor de pandeo ≥ 3 frente a las cargas reales;
- los factores negativos corresponden a la carga invertida, que no puede ocurrir.

## 3. Resultados

Tabla completa en `resultados_cabina/RESUMEN_CABINA.csv`. Notas de la tabla:
- «Lateral»: desplazamiento horizontal del cojinete superior en S2.
- «Flecha»: flecha del apoyo del cartucho en S1.
- «λ+»: primer factor de pandeo positivo frente a las cargas últimas; «—» indica que no se halló con 6 modos, todos negativos.
- «σ_VM»: tensión máxima de la chapa en las combinaciones U.

| Caso | Barras (kg) | Chapa (kg) | D/C barras | f1 (Hz) | Lateral (mm) | Flecha (mm) | Techo, w máx. S1 (mm) | λ+ | σ_VM (MPa) | Lectura |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **K0** marco D-065, rotor real | 360,0 | — | **0,12** | **5,20** | **0,99** | 1,17 (L/3 456) | — | 165 | — | **cumple** |
| K14 cabina sola, 1,5 mm (lineal) | 0 | 676 | — | 0,17 | 2 465 | 8 552 | 8 781 | 0,25 | 12 852 | no |
| K15 cabina sola, 3 mm (lineal) | 0 | 1 351 | — | 0,44 | 308 | 1 201 | 1 231 | 1,41 | 3 383 | no |
| K1 cabina sola, 1,5 mm (S1 no lineal) | — | — | — | — | — | — | — | — | — | no convergió: se detuvo en el 38 % de S1 tras 5 min |
| K3 vigas sobre muros, 1,5 mm | 174,6 | 676 | 0,18 | 0,43 | 1,27 | 0,97 | 1 037 | 0,17 | 1 159 | no |
| K4 vigas sobre muros, 3 mm | 174,6 | 1 351 | 0,19 | 0,86 | 1,00 | 0,88 | 259 | 1,09 | 581 | no |
| K9/K13 vigas sobre muros, diafragma | 174,6 | 676 | 0,18 | 12,73 | 1,27 | 0,95 | 0,15 | **0,24** | 49 | no: el muro abolla bajo la viga |
| K5 diafragma, SHS100×5 articulados | 330,4 | 676 | 0,18 | 15,68 | 0,61 | 0,89 | 0,15 | — | 34 | ver K12 |
| K6 = K5 con f12 0,1 | 330,4 | 676 | 0,17 | 14,96 | 0,64 | 0,97 | 0,22 | — | 29 | ver K12 |
| K11 = K5 con f12 0,3 | 330,4 | 676 | 0,18 | 15,33 | 0,63 | 0,93 | 0,18 | — | 32 | ver K12 |
| K7/K12 diafragma, SHS80×4 articulados | 270,4 | 676 | 0,19 | 14,70 | 0,72 | 1,02 | 0,15 | **1,10** | 35 | rígido, pero la chapa abolla cerca de U (λ < 3) |
| K8 = K7 con f12 0,1 | 270,4 | 676 | 0,18 | 14,06 | 0,77 | 1,10 | 0,23 | — | 31 | ídem |
| K10 marco D-065 + chapa como diafragma | 360,0 | 676 | 0,17 | 15,87 | 0,61 | 0,87 | 0,13 | — | 32 | reserva no contada |

**Reacciones en las bases de K0**, para el anclaje de los postes:
- compresión: 2,2 kN en S1 y 3,5 kN en U3;
- cortante: ≤ 0,67 kN;
- momento: 0,32 kN·m en S1 y 0,77 kN·m en U3;
- sin levantamiento.

**Modos de K0:**
- f1 = 5,20 Hz (Ux 0,88);
- f2 = 11,92 Hz (Uy 0,78);
- f3 = 13,61 Hz (Uz 0,60);
- f4 = 28,5 Hz, torsional (Rz 0,67).

**Chequeos a mano** (`CHEQUEOS_MANO.json`):
- **Techo plano apoyado, sin correas** (Timoshenko y Woinowsky-Krieger, placa cuadrada):
  - con 1,5 mm, flecha lineal de 2 148 mm por peso propio y de 15 241 mm por el cartucho (4 771 N);
  - con 6 mm, 134 mm y 238 mm;
  - para L/1000 con el cartucho haría falta t = 23,4 mm (3 124 kg de chapa).
- **Abolladura del borde del muro bajo la viga** (EN 1993-1-5 §6.4, k_F = 6 sin rigidizadores):
  - F_cr = 1,35 kN con 1,5 mm, 3,19 kN con 2 mm y 10,8 kN con 3 mm;
  - la reacción de cada extremo de viga es de 1,2 a 1,9 kN.

## 4. Lectura

1. **El techo de una cabina de chapa no es una estructura.** Una chapa plana de 1,5 mm sobre 4 m no se sostiene sola: en K3, el techo baja 1 037 mm y la tensión pasa de 950 MPa. Con el cartucho apoyado en el techo, la flecha lineal es de 8,6 m con 1,5 mm (K14) y de 1,2 m con 3 mm (K15). Con 3 mm y vigas (K4) sigue fuera de rango. El cálculo no lineal con grandes desplazamientos (K1), que tendría en cuenta el efecto de membrana, no convergió más allá del 38 % de la carga de servicio.
2. **Los muros de chapa no reemplazan a los postes.** Sin postes, el borde superior del muro recibe la viga y abolla: factor 0,23 en K9, que coincide con el cálculo a mano. Haría falta chapa de 3 mm en toda la cabina (+640 kg de inox, ≈ S/ 20 000) o un rigidizador vertical bajo cada viga, que en la práctica es un poste.
3. **Como diafragma, la chapa sí rigidiza mucho.** Con la misma chapa atornillada al marco:
   - f1 sube de 5,2 a 14–16 Hz;
   - el cojinete superior se mueve 0,61–0,77 mm en lugar de 0,99 mm;
   - esto se mantiene aunque las uniones sean flexibles (f12 = 0,1).

   Eso permitiría, en principio, articular las bases, quitar la celosía de los muros y bajar los postes a SHS80×4 (K7: 270 frente a 360 kg).
4. **Por qué no se cuenta con ella:**
   - **Ahorro pequeño:** ≈ 90 kg de A36, unos S/ 1 600 de material y taller, menos ~S/ 200 por bases articuladas, más los tornillos estructurales de las costuras. Neto ≈ S/ 1 400, el 0,4 % de S/ 317 954.
   - **Robustez:** la estabilidad lateral dependería de paneles que se abren, se perforan para ductos o se cambian. Un panel retirado en mantenimiento dejaría el marco con 4–9 mm de lateral (O3/O4 de D-065).
   - **Montaje:** el marco tendría que llevar arriostramiento provisional hasta cerrar la cabina.
   - **Pandeo:** con 60 modos, el primer factor positivo de K7 es 1,10 (K12), por debajo del criterio de 3. La chapa abollaría cerca de las cargas últimas y seguiría trabajando por campo diagonal, con menos rigidez.
   - **Justificación:** el diseño de diafragmas (EN 1993-1-3 §10.3 y la guía ECCS) está hecho para chapa perfilada. La chapa plana trabaja por campo diagonal, lo que exige bordes rígidos y uniones calculadas. En la tesis sería una hipótesis más sin validar.
   - **Si la chapa es cerramiento,** su abolladura local (oil-canning) es estética: el marco lleva las cargas.
5. **El marco de D-065 cumple con el rotor real** (K0):
   - D/C 0,12 (la cota de D-075 era ≤ 0,134);
   - f1 5,20 Hz (antes 5,34);
   - lateral del cojinete en S2 0,99 mm;
   - flecha de la viga en S1 L/3 456.

   Se cierra la contradicción del lote 31 (masa del rotor de R03 frente al CAD).
6. **Momentos en las bases empotradas** (K0, D-065 no los había exportado):
   - S1: 0,32 kN·m;
   - U3: 0,77 kN·m.

   Con compresión de 2,2–3,5 kN, cortante ≤ 0,67 kN y sin levantamiento. Son el dato para diseñar la placa base y sus anclajes, con la misma losa supuesta en D-073.
7. **Modo torsional:** en K0 está en 28,5 Hz (Rz 0,67), a 1,22 veces la velocidad supuesta del motor, de 23,3 Hz **[VERIFICAR]**, fuera de la banda de ±15 %.

## 5. Decisión (HPGR D-078, decidida por Claude por delegación, pendiente de revisión del usuario)

1. **Se mantiene el soporte de D-065** (marco de la cabina O10):
   - postes SHS100×5 con bases empotradas;
   - celosía L40×4;
   - vigas RHS160×80×5 con X en planta.

   Ahora está verificado con el rotor real (K0).
2. **La cabina es cerramiento:** paneles de inox de 1,5 mm atornillados al marco. Su aporte como diafragma (K10: f1 15,9 Hz, lateral 0,61 mm) queda como **reserva no contada**. No se cuenta con ella para quitar barras ni para articular bases.
3. **El techo de chapa lleva correas propias:** 5 RHS 80×40×3 de inox 304 a ~0,8 m, apoyadas en los muros laterales.
   - Cubierta no transitable, categoría H de EN 1991-1-1 **[HIPÓTESIS]**.
   - D/C 0,68 a flexión; flecha ≤ L/200.
   - 110 kg, cubiertos por el +20 % de refuerzos del presupuesto C1.
   - Quedan **[PENDIENTE]**: el CAD y el plano de la cabina.
4. **Alternativa documentada, no adoptada:** K7, la chapa diseñada como diafragma, con postes SHS80×4 articulados y sin celosía. Queda como trabajo futuro, solo si se diseña la cabina como diafragma con uniones calculadas y paneles estructurales no desmontables.

## 6. Limitaciones

- **Uniones idealizadas:** la chapa se modela unida en continuidad a los postes, a las esquinas y al bordillo. Las uniones reales (tornillos, remaches, juntas selladas de D-057) son más flexibles; f12 = 0,1 lo acota solo en parte.
- **Chapa plana sin nervios:** los paneles reales tendrán pliegues que cambian su rigidez y su pandeo, y eso no se modela.
- **Malla de 150 mm:** sirve para comparar, pero el pandeo local de la chapa queda aproximado.
- **Cartucho rígido**, como en D-065.
- **Cargas envolventes de R03**, con el rotor real de D-075.
- **Sin fatiga, sin viento interior y sin sobrepresión del extractor.**

## 7. Archivos

| Archivo | Contenido |
|---|---|
| `scripts/SoporteCabinaSAP.cs` | Modelo paramétrico con cáscaras (nuevo) |
| `scripts/s04_correr_cabina.ps1` | Casos K0 a K13 |
| `scripts/s05_resumen_cabina.py` | Resumen y chequeos a mano |
| `modelos_cabina/K*.sdb` | Modelos de SAP2000 (se pueden abrir para sacar capturas) |
| `resultados_cabina/K*.json`, `RESUMEN_CABINA.csv`, `CHEQUEOS_MANO.json` | Resultados |
