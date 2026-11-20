# Auditoría del CAD R07 V18B (03/11/2026)

**Estado.** Auditoría EJECUTADA sobre un diseño CANDIDATO. No apto para fabricación.

**Conclusión:** de todo lo que marcó la auditoría, hay **un defecto real: el disco de bloqueo del volante**, heredado de la V14. Se corrigió en la **V18C** (`../R07_V18C_CAMBIOS.md`). Los cambios de la V18B no introdujeron ningún solape ni fijación mal resuelta.

## Método

Es el mismo de las revisiones V11 y V12, aplicado a todas las piezas visibles, incluida la herencia:

| Fase | Script | Salida en `resultados/` |
|---|---|---|
| Pares, solapes, contactos, piezas aisladas y grupos | `scripts/rv07_auditoria_v18b.py` (envuelve `rv06` y `rv06b`) | `rv07_resumen_v18b.json`, `rv07b_aisladas_v18b.json` |
| Fijaciones: piezas a ≤ 1,5 mm de cada perno, tuerca o pasador | `scripts/rv07c_fijaciones_v18b.py` (envuelve `rv01c`) | `rv07c_fijaciones_v18b.json` |
| Clasificación física y comparación con la V12 | `scripts/rv07d_clasificacion_v18b.py` | `rv07d_clasificacion_v18b.json` |

**Alcance:** 802 piezas revisadas, 2 860 pares evaluados y 0 errores booleanos. Lo reemplazado (`NO_VIGENTE_*`) no se cuenta.

## Solapes: 148, todos clasificados

Criterio de la lección del 27/10: un solape no es por sí mismo un error; se pregunta qué representa.

| N.° | Qué son | Volumen máx. (mm³) | Respecto de la V12 |
|---:|---|---:|---|
| 56 | K2-M: uniones soldadas representadas por solape (`UNION_PREVISTA` de R06.1) | 98 280 | Iguales |
| 29 | Empotrados previstos: anclajes del riel (24) y del soporte (1 objeto), pozo, colector y patas del receptor en el piso húmedo | 6 800 000 | 25 posteriores (anclajes), 2 iguales, 2 renombrados |
| 24 | Clips Gantrex con el riel (envolvente comercial) | 2 132 | Iguales |
| 12 | Partes internas de STEP de fabricante o entre equipos comerciales | 38 176 | Iguales |
| 7 | Bastidor N3: rigidizadores, topes y cuerpo del bloqueo; uniones por solape ya declaradas (H13 de la revisión V11) | 34 190 | Iguales, con otro nombre de viga desde la V16 |
| 7 | Uniones representadas en piezas heredadas de R04, V9 y el manillar | 92 394 | Iguales |
| 4 | Asiento B-MEC con el pie y la boquilla | 1 574 | Iguales |
| 4 | **Contacto numérico:** chapa de tiro y rigidizadores contra M04 | 49,8 | Posteriores (V14 y V16) |
| 3 | Tubería o pedestal contra el STEP de la bomba | 36 | Iguales |
| 2 | Envolvente de la correa sobre las poleas (R04) | 814 301 | Iguales |

**Contacto numérico:** en la chapa, la zona común mide 120 × 150 mm con un espesor menor que 0,01 mm (49,8 mm³). Es contacto entre la chapa y el ala, no un cruce.

**Comparación con la V12:** bajó de 157 a 148 solapes, porque la V16 rehízo las uniones del bastidor y la V17 los apoyos del riel; se suman los anclajes nuevos.

## Piezas aisladas: 20

| Pieza | Holgura | Lectura |
|---|---:|---|
| Resortes, varillas, cartuchos y tirantes del K2-M (16) | 0,5–1,5 mm | Holguras de ajuste de R06.1, igual que en la V12 |
| `R07_F_FLOTADOR_NIVEL` | 90 mm | Flota en el pozo: es su función |
| `R07_STEP_GRUNDFOS_DDA_INHIBIDOR` | 0 mm | Es uno de los 4 STEP inválidos; ya estaba en la V12 |
| `R07_V9_MANGUERA_DETERGENTE` | 2 mm | Igual que en la V12 |
| **`R07_V14_DISCO_BLOQUEO`** | **0,5 mm** | **Defecto real; ver abajo** |

### Defecto: el disco de bloqueo no trababa nada

Es el único caso nuevo, y sale de preguntar «qué lo sostiene y por dónde pasa la carga»:

- tenía un agujero de 21 mm sobre el eje de 20, sin cubo ni pasador, así que **no estaba sujeto al eje**;
- **no tenía modelados los 12 agujeros** en los que entra el émbolo, aunque la lista de MES-800 los nombra;
- estaba en el CAD desde la V14 y pasó a MES-800 sin detectarse, porque los chequeos por versión solo buscaban solapes.

**Importa porque** el émbolo es lo que sostiene la mesa detenida: el sinfín i = 5 no es autobloqueante (`resultados/CALCULO_V14_TRASLADO_CADENA.md`, §3.3).

**Corrección:** V18C, con disco, cubo y pasador; verificación en `../R07_V18C_CAMBIOS.md`.

## Grupos que no llegan al piso: 7

| Grupo | Causa | Lectura |
|---|---|---|
| Brazos A y B de la U; bridas A y B (4 grupos) | Holgura radial de 0,6 mm entre la brida y el tubo DN50 | Holgura de brida deslizante; la cierra la soldadura de HPGR-ASP-220. Sin defecto |
| Tanque de enjuague, bidón de inhibidor y bidón de detergente (3 grupos) | La referencia de piso del CAD termina en y 2600 | Sí llegan a z 0 (`apoya_en_piso: true`); igual que en la V12. Sin defecto |

## Fijaciones: 108

- **Pernos y pasadores:** 54, de los cuales 50 tienen al menos dos piezas a ≤ 1,5 mm.
- **Los otros 4:**
  - `CTX_TABLE_LOCK_PIN`: pasador de bloqueo en su buje;
  - `R04_PASADOR_ESTACIONAMIENTO_ROTOR`: se modela retraído, en operación (H02 de la V12);
  - `R07_V18B_ANCLAJES_M16_ARANDELA` y `_TUERCA`: el filtro los toma como anclajes por su nombre, pero son la arandela y la tuerca, que apoyan en la placa y en la varilla.
- **Tuercas sin pieza cerca (16):** apoyan en su arandela, y el filtro no cuenta otras fijaciones. Sin defecto.

## Sólidos inválidos: 4

Son los mismos 4 STEP de fabricante de la V12 (ATV320, CRN 15-3 y dos DDA). Sirven como envolvente visual; no se usan para calcular.

## Limitaciones

- **No se repitió la detección de interferencias en SOLIDWORKS** (`rv02`) sobre el conjunto completo. La segunda herramienta queda pendiente.
- **La auditoría es estática:** revisa la posición de lavado. No se repitió el barrido de la traslación de la mesa. Las piezas nuevas de la V18B no están en su recorrido: las placas base y las tuercas empiezan en |x| ≥ 1895 y las correas están en z ≥ 2490.
- **Los solapes heredados se clasificaron por grupo**, con el criterio de la revisión V11, no uno por uno.
