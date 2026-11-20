# Brazo de la U en SOLIDWORKS: chorros, golpe accidental y placa diagonal (10/11/2026)

**Estado.** EJECUTADO en SOLIDWORKS Simulation 2024 (licencia educativa), sobre HIPÓTESIS de carga y de unión. Es una verificación por simulación, sin validación experimental. No es una decisión: la placa queda por decidir con el asesor.

**Motivo.** En la exposición del 10/11 el asesor preguntó si la reacción de los chorros genera momentos en los brazos opuestos de la U. Si es así, sugirió una placa atiesadora diagonal entre el transversal y el brazo. El usuario pidió verificarlo en SOLIDWORKS además del cálculo a mano (`../scripts/r07_reaccion_chorros_U.py`).

## Modelo

**Geometría.** Es el brazo A real del plano ASP-220 (`planos/sw/fuente/BRAZO_V15B.step`, R07 V15B; los brazos A y B son iguales, D-072). Incluye:
- transversal DN50 Sch 10S (60,3 × 2,77, 520,2 mm);
- codo reductor 2" × 1-1/2" de radio largo;
- brazo DN40 Sch 10S (48,3 × 2,77, 720 mm);
- coplas y niples de las boquillas, pie DN15 y bloque B-MEC;
- brida deslizante DN50.

Los tubos son huecos. Coordenadas del STEP: x a lo largo del transversal desde la cara de la brida, y vertical, z fuera del plano de la U.

**Arreglos para el FEM** (`scripts/s00_contactos_brazo.py`, `geometria/contactos_log.txt`):
1. El tubo DN50 y la brida tienen 0,6 mm de holgura (brida deslizante). Se agregó un anillo que la llena, que representa la soldadura W1 de ASP-220 rev. B.
2. El bloque B-MEC se solapaba 1 574 mm³ con el tubo DN15: se recortó para que solo se toquen.

**Variante con placa** (`scripts/s01_brazo_con_placa.py`). Pletina de 40 × 6 mm en el plano de la U, entre el transversal en x = 770 global y el brazo en Z 1550 global, recortada contra los tubos [HIPÓTESIS: posición tomada de la imagen del usuario; sin silletas].

**Uniones y material:**
- contacto pegado entre piezas (soldadura continua idealizada, sin geometría de cordón);
- cara de la brida empotrada (abulonada al cubo);
- 316L con E 193 GPa y fluencia 153 MPa a 62 °C [HIPÓTESIS de B1].

**Cargas** (`scripts/s02_cargas_brazo.py` → `geometria/cargas_brazo_A.csv`):
- 8 chorros como carga remota distribuida en las caras de su copla o bloque, ubicada en el vértice de la boquilla. F = ṁ·v, del CFD O7+C2, con el giro de −4° de LAT_1. El brazo suma 28,34 N hacia afuera y 8,78 N hacia arriba.
- Golpe accidental de 1 000 N a Z1400, sobre el tubo DN40: fuera del plano (tangencial, el caso de B1) y en el plano (radial).

**Malla:** curvatura combinada, tetraedros de 2.º orden.
- Base: 5 a 1 mm, con 186 mil nodos (192 mil con la placa).
- Control: 3 a 0,7 mm, con 608 mil nodos.

## Resultados (von Mises máximo, MPa; desplazamiento en mm)

| Caso | Codo | Unión de la placa | DN50 a x = 150 | Desplazamiento máx. (boquillas) |
|---|---|---|---|---|
| Chorros, sin placa | **11,3** (11,5 con malla fina) | — | 2,92 | 0,67 |
| Chorros, con placa | 2,6 | 14,4 | 2,92 | 0,39 |
| Golpe fuera del plano, sin placa | **150** (151 con malla fina) | — | 78,8 | 11,8 |
| Golpe fuera del plano, con placa | 147 | 77 | 78,8 | 11,7 |
| Golpe en el plano, sin placa | **202** | — | 51,3 | 11,0 |
| Golpe en el plano, con placa | 48 | **266** | 51,3 | 6,1 |

**Control frente a la teoría de vigas** (DN50 a x = 150, lejos de uniones):

| Caso | SOLIDWORKS | A mano |
|---|---|---|
| Chorros | 2,92 MPa | 2,86 MPa (pórtico, M ≈ 19,7 N·m) |
| Golpe fuera del plano | 78,8 MPa | 78,1 MPa (M = 449 N·m, T = 340 N·m) |
| Golpe en el plano | 51,3 MPa | 51,4 MPa (M = 340 N·m + axial) |

**Picos que no se reportan como tensión real.** En la esquina de la brida con el tubo (170 → 187 MPa con malla fina) el pico crece al refinar, porque es una esquina sin cordón modelado: es una singularidad. El del codo converge (+0,9 a +1,6 %).

**Estudio descartado.** CHORROS_X2 con placa no cumplió la linealidad: su desplazamiento no fue el doble del de CHORROS. Sin placa sí cumple exactamente, y el caso × 2 es solo una escala lineal del × 1.

## Lectura

1. **Los chorros sí doblan cada brazo,** pero poco. El codo llega a 11,3 MPa (7 % de la fluencia) y las boquillas se mueven 0,67 mm, menos que la tolerancia de ±2 mm de las coplas. Los dos brazos se equilibran en el cubo. **La placa no hace falta por los chorros.**
2. **El codo es el punto crítico de la U,** porque ovaliza. El golpe de costado lo lleva a 150 MPa, casi la fluencia: es el caso que ya gobernaba en B1 (0,93). **La placa no lo cambia:** 147 MPa, porque trabaja en el plano de la U.
3. **Con un golpe en el plano, la placa sí descarga el codo** (202 → 48 MPa), pero **traslada el problema a su unión con el DN50:** 266 MPa, porque la pared de 2,77 mm recibe la fuerza de la placa en una zona pequeña. Así como está dibujada, la placa necesitaría silletas o un refuerzo en sus extremos.
4. **El pico del codo bajo el golpe es 1,5 veces el valor de ASME B31.3 de B1** (100,6 MPa con 0,75·i). El factor de B31.3 no representa el pico local de ovalización. Si se quiere más margen frente al golpe, lo eficaz es actuar en el codo (por ejemplo, codo y tramos Sch 40S, por evaluar) o en el resguardo durante el mantenimiento, no con la placa diagonal.

## Limitaciones

- Sin presión interna ni peso propio: B1 da 3,3 MPa longitudinales y 6,5 MPa circunferenciales por presión, y el peso es una carga sostenida pequeña.
- Uniones sin la geometría del cordón.
- Placa sin silletas y en posición supuesta.
- El golpe de 1 000 N es una hipótesis de R03.
- Análisis lineal: por encima de la fluencia solo indica plastificación local.

## Archivos

| Carpeta | Contenido |
|---|---|
| `geometria/` | STEP sin y con placa, cargas y registros |
| `modelo/` | `BRAZO_SIN_PLACA_SW_*.SLDPRT` y `BRAZO_CON_PLACA_SW_*.SLDPRT`, con los 4 estudios |
| `resultados/` | imágenes `VM_*` (vista frontal y codo), `DESPL_*`, `salida_malla_5mm.txt` y `sw_log_*.txt` |
| `scripts/` | s00 a s03 |

En `resultados/`, las imágenes con `_h3` son de la malla fina.
