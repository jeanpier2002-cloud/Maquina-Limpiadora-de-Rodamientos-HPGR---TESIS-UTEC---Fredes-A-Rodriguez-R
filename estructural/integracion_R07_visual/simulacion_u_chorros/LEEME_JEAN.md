# Brazo de la U en SOLIDWORKS: reacción de los chorros y refuerzo del codo (para Jean, 10/11/2026)

Hola Jean. Esto es lo que analizamos con Ismael después de la exposición del 10/11. El asesor preguntó si la reacción de los chorros genera momentos en los brazos opuestos de la U y sugirió una **placa diagonal (atiesadora) entre el transversal y el brazo**. Aquí está el estudio en SOLIDWORKS del brazo real, sin y con esa placa, más el cálculo a mano.

**Estado:** verificación por simulación, sin ensayo. La placa **no está decidida**: queda por conversar con el asesor.

## Qué hay en el ZIP

| Carpeta | Qué es |
|---|---|
| `modelo/` | Los dos modelos de SOLIDWORKS con sus estudios definidos: `BRAZO_SIN_PLACA_SW_043142.SLDPRT` y `BRAZO_CON_PLACA_SW_043845.SLDPRT`. |
| `geometria/` | STEP del brazo sin y con placa, cargas de cada boquilla (`cargas_brazo_A.csv`) y registros de geometría. |
| `imagenes/` | Von Mises y desplazamiento de cada estudio (vista frontal y detalle del codo). Las que terminan en `_h3` son de la malla fina. |
| `registros/` | Salida completa de SOLIDWORKS con la malla de 5 mm y con la de 3 mm. |
| `calculo_a_mano/` | Reacción F = ṁ·v de cada boquilla y pórtico plano de media U: script, JSON y figura. |
| `scripts/` | Cómo se generó todo: FreeCAD (s00, s01), cargas (s02) y la API de SOLIDWORKS (s03). |
| `Memoria_seccion7_chorros_U.pdf` | Las páginas de la memoria con la explicación completa: fórmulas, tablas y lectura. |
| `LEEME.md` | La descripción técnica completa del estudio. |

## Cómo abrirlo

1. Abre el `.SLDPRT` en SOLIDWORKS 2024. Está guardado con la versión educativa (SP5).
2. Cada modelo tiene 4 estudios estáticos:
   - **CHORROS:** las 8 reacciones de las boquillas del brazo;
   - **CHORROS_X2:** arranque brusco de la bomba;
   - **ACC_FUERA_PLANO:** golpe de 1 000 N de costado a Z1400;
   - **ACC_EN_PLANO:** el mismo golpe en el plano de la U.
3. **Los resultados no vienen en el ZIP**: pesan unos 1,2 GB. Haz clic derecho en el estudio y elige **Ejecutar**; cada uno tarda unos 20–30 s. El material, las sujeciones, las cargas y la malla ya están puestos.
4. Para ver tensiones en MPa, crea el trazado de von Mises en N/mm².
5. **No uses CHORROS_X2 del modelo con placa:** no cumplió la linealidad, así que lo descartamos. Como es solo una escala, toma CHORROS × 2.

## Cómo está armado

- **Geometría:** es el brazo A real del plano ASP-220, el mismo de R07 V15B.
  - transversal DN50 Sch 10S (60,3 × 2,77), codo reductor 2" × 1-1/2" de radio largo y brazo DN40 Sch 10S (48,3 × 2,77);
  - coplas, pie DN15, bloque B-MEC y brida deslizante;
  - 316L, con E 193 GPa y fluencia de 153 MPa a 62 °C (hipótesis).
- **Ejes del STEP:** x a lo largo del transversal desde la cara de la brida, y vertical y z fuera del plano de la U. Desde las coordenadas globales: x = X − 300,75; y = Z − 1740; z = −Y.
- **Uniones:** contacto pegado entre piezas, como soldadura continua idealizada. La brida va empotrada. El STEP original tenía 0,6 mm de holgura entre la brida deslizante y el tubo, que en la realidad llena la soldadura W1: se agregó un anillo que la representa. Sin él, el brazo queda suelto.
- **Cargas de los chorros:** salen de **tu** `boquillas_O7_C2.json`, con la reacción F = ṁ·v opuesta a cada chorro y LAT_1 girada −4° (Caso 2). Van como carga remota distribuida en la copla de cada boquilla, ubicada en el vértice. El brazo suma 28,3 N hacia afuera y 8,8 N hacia arriba.
- **Placa (variante):** pletina de 40 × 6 mm en el plano de la U, del transversal en x = 770 global al brazo en Z 1550, recortada contra los tubos. No lleva silletas.

## Resultados (von Mises máx. en MPa; desplazamiento de las boquillas en mm)

| Caso | Codo | Unión de la placa | Boquillas |
|---|---:|---:|---:|
| Chorros, sin placa | **11,3** | — | **0,67** |
| Chorros, con placa | 2,6 | 14,4 | 0,39 |
| Golpe de costado, sin / con placa | **150** / 147 | — / 77 | 11,8 / 11,7 |
| Golpe en el plano, sin / con placa | 202 / 48 | — / **266** | 11,0 / 6,1 |

**Control:**
- **Teoría de vigas:** en el DN50, lejos de las uniones, SOLIDWORKS coincide con M/W: 2,92 frente a 2,86 MPa, 78,8 frente a 78,1 y 51,3 frente a 51,4.
- **Malla fina:** el pico del codo cambia de +0,9 a +1,6 %.
- **Esquina de la brida:** su pico crece al refinar la malla porque es una singularidad (no hay cordón modelado). No es tensión real.

## Lectura

1. **Los chorros sí doblan cada brazo,** pero poco. Los dos brazos se equilibran en el cubo, y el codo llega al 7 % de la fluencia.
2. **Para tu CFD:** las boquillas se mueven **0,67 mm** por la reacción de los chorros (1,3 mm en un arranque brusco). Es menos que la tolerancia de ±2 mm / ±1° de las coplas, que ya habíamos visto que no cambia el mojado (D-079). **No hace falta cambiar la geometría del CFD.**
3. **El codo es el punto crítico de la U** porque ovaliza. Manda el golpe accidental de costado: 150 MPa, casi la fluencia. La placa no lo cambia, porque trabaja en el plano de la U.
4. **Con un golpe en el plano, la placa descarga el codo, pero crea 266 MPa en su unión con el tubo de 2,77 mm:** así dibujada, necesitaría silletas.

**Propuesta, por decidir con el asesor:** no poner la placa. Si se quiere más margen frente al golpe, reforzar el codo (por ejemplo, Sch 40S, aún sin calcular).

## Lo que no incluye

- La presión interna (+3,3 MPa longitudinales, a mano) ni el peso propio.
- El cordón de soldadura modelado.
- El golpe de 1 000 N es una hipótesis de R03.
- La posición de la placa salió de un dibujo.

Cualquier duda, pregúntale a Ismael. La ruta en el proyecto es `01_DISENO_VIGENTE/integracion_R07_visual/simulacion_u_chorros/`.
