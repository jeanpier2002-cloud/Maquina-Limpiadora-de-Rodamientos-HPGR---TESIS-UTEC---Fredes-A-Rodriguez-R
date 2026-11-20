# C3: tolerancias de las coplas frente a la aspersión (03/11/2026)

**Estado.** Cribado geométrico N1 EJECUTADO; no equivale a CFD ni a limpieza. **HPGR D-079: decidida por Claude por delegación (02–03/11), pendiente de revisión del usuario.** Diseño CANDIDATO.

**Pregunta.** Los planos HPGR-ASP-220 y ASP-600 dan para las coplas ±2 mm y ±1° como [HIPÓTESIS: confirmar con la sensibilidad del CFD]. ¿Esa tolerancia cambia la aspersión sobre el aro?

## Método

**Modelo:** se reutiliza **sin modificarlo** el cribado N1 por rayos de D-047, D-060 y D-061: `cfd/CFD_ANSYS/02_ANALISIS/cara_inferior/alternativas_2026-10-07/decision_o7c2_vs_o8b/scripts/estudio_n1.py` y `rayos_r05.py`.
- rayos rectos durante una vuelta del rotor, con los obstáculos de R05;
- sin gravedad ni arrastre.

**Boquillas:** las 24 del caso 2 vigente (`integracion_R06/R06.4_o7_c2_caso2/boquillas_O7_C2_caso2.json`).
- Las 1520 (INF_EXT y C2) tienen un abanico de 16,8° [HIPÓTESIS de la ficha].
- Las 5020 tienen 50°.

**Perturbaciones:** se mueve **una boquilla a la vez**, con las otras 23 en su posición nominal:
- vértice ±2 mm en las direcciones radial, tangencial y vertical;
- eje ±1° alrededor de la normal del abanico (giro en su plano) y alrededor de su ancho (fuera del plano).

**Medidas:** en cada superficie del aro (OD, cara superior, agujero y zonas Z1–Z3 de la cara inferior):
- masa del primer impacto por vuelta (D);
- cobertura K1 (celdas tocadas).

**Criterio fijado antes de correr [HIPÓTESIS]:**
- la cota combinada debe ser ≤ 10 % en cada superficie. Es la suma de los peores |ΔD| de las 24 boquillas, como si todas se desviaran a la vez en su peor sentido; una cota muy conservadora;
- ninguna perturbación debe bajar K1 más de 1 punto.
- También se informa la cota **solo de pérdidas**, que es la que importa para limpiar.

**Script:** `c3_tolerancias_coplas.py [--dang-bloque 0.5] [--dpos-bloque 1]` → `resultados/C3_TOLERANCIAS*.json` y `C3_RESUMEN*.csv`. En las etiquetas de las perturbaciones, el signo es el que vale; la magnitud es la de la pasada.

## Resultados (cota combinada, %; entre paréntesis, solo pérdidas)

| Superficie | Todas a ±2 mm / ±1° | Bloque (INF_EXT y C2) a ±0,5° | Bloque a ±0,5° y ±1 mm |
|---|---:|---:|---:|
| Z1 (cara inferior, interior) | 24,4 (3,8) ✗ | 13,9 (3,6) ✗ | 13,0 (**3,6**) ✗ en \|ΔD\| |
| Z2 | 18,1 (18,1) ✗ | 10,0 (10,0) ✗ | **9,4 (9,4)** ✓ |
| Z3 | 6,5 (5,8) ✓ | 6,5 (5,8) ✓ | 3,1 (2,4) ✓ |
| OD | 2,8 (2,8) ✓ | 2,5 (2,3) ✓ | 1,9 (1,8) ✓ |
| Cara superior | 1,7 (1,7) ✓ | 1,7 | 1,7 |
| Agujero | 2,7 (2,7) ✓ | 1,9 | 1,9 |
| **Caída de K1** | **0,0 puntos en todos los casos** | 0,0 | 0,0 |

El escape nominal es del 1,80 % del caudal.

**Lectura:**
1. **Las coplas soldadas de los brazos y de la lanza** (SUP, LAT, INT; boquillas 5020 de 50°) son **insensibles** a ±2 mm y ±1°:
   - OD, cara superior y agujero cambian ≤ 2,8 % en la cota combinada;
   - la peor boquilla sola mueve ≤ 0,5 %;
   - K1 no cambia en ningún caso.
   - **La tolerancia del plano queda justificada.**
2. **La sensibilidad está en las salidas del bloque inferior** (INF_EXT y C2, boquillas 1520 de 15°, que barren la cara inferior en rasante). Un giro de ±1° en su plano cambia la elevación del chorro y pasa dosis entre Z1 y Z2: −7,1 % en Z2 y +9,2 % en Z1 con la INF_EXT_A sola.
3. **Esas salidas no son coplas soldadas: son agujeros del bloque portaboquillas mecanizado** (ASP-220-08). Con ±0,5° (ISO 2768-m para longitudes de 10–50 mm) y ±1 mm en la posición del vértice (bloque fijado con plantilla), las pérdidas quedan ≤ 9,4 % en todas las zonas.
4. **Z1 no cumple el criterio |ΔD| ni aun así,** pero son **aumentos** de dosis: las pérdidas suman solo 3,6 %. Se declara como redistribución, no como falta de mojado.

## Decisión (HPGR D-079, decidida por Claude por delegación, pendiente de revisión del usuario)

- **Coplas soldadas** (brazos y lanza): **±2 mm y ±1°**, con plantilla. Pasan de [HIPÓTESIS] a verificadas por el cribado N1.
- **Salidas del bloque portaboquillas inferior** (INF_EXT y C2): **±0,5° en el eje del agujero y ±1 mm en la posición del vértice**, con el bloque mecanizado y fijado con plantilla.
- **[PENDIENTE]** llevar estas tolerancias a una rev. C del ASP-220 (nota 4) y al plano del bloque, que todavía no existe.

## Limitaciones

- N1: sin gravedad, arrastre ni salpicadura; primer impacto, no remoción (D-045).
- Abanico de las 1520 de 16,8° [HIPÓTESIS]; obstáculos de R05.
- Una boquilla a la vez; la cota combinada suma linealmente, que es conservador.
- Sin desgaste ni obstrucción de la boquilla.
