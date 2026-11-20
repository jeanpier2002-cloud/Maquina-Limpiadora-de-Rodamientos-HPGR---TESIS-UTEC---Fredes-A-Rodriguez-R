# Revisión del CAD R07 V18D (03/11/2026)

**Estado.** Revisión EJECUTADA, solo lectura, sobre un diseño CANDIDATO. Cierra lo que la revisión de la V18B dejó pendiente: el barrido de la traslación y la detección de interferencias en SOLIDWORKS.

## 1. Auditoría geométrica

`scripts/rv08_auditoria_v18d.py` → `resultados/rv08_resumen_v18d.json`.

- **146 solapes** frente a 148 de la V18B. Salen los 2 de los topes con el ala. El del soporte de retención 2 con el montante baja de 8 447 a 4 224 mm³. **Ningún par nuevo.**
- **Piezas aisladas:** 19 frente a 20; son holguras internas conocidas de K2-M, de 0,5 a 1,5 mm.

## 2. Barrido de la traslación

`scripts/rv08c_barrido_traslacion_v18d.py` → `resultados/rv08c_barrido_v18d.json`. De LAVADO a CARGA, 3 320 mm, cada 40 mm (84 pasos). **292 piezas móviles contra 323 fijas**, con la puerta abierta, la lanza guardada (D-003) y los brazos de K2-M activos y retraídos como envolvente. Antes solo se habían barrido las piezas nuevas de cada versión.

**Resultado: sin choques reales.** La herramienta marcó 3 pares, y los 3 se explican:

| Par | Dónde | Lectura |
|---|---|---|
| Pasador de bloqueo con el receptor de LAVADO | dy −40 | El CAD lo dibuja insertado: traba la mesa, que es su función. Se retira antes de mover (D-041) |
| Pasador de bloqueo con el receptor de CARGA | dy −3 280 | Igual, al llegar a CARGA |
| Cuerpo del bloqueo con los bujes | dy −40 | Falso: un solo objeto del CAD agrupa los bujes fijos y el de la orejeta móvil (|x| ≤ 20), que viaja con la mesa |

**Limitación:** es un barrido de sólidos cada 40 mm. El rodamiento se barre como sólido; no se revisa la cadena en movimiento, y la U se toma estacionada a 0° (D-003).

## 3. Interferencias en SOLIDWORKS

`scripts/rv08b_interferencias_sw_v18d.ps1` → `resultados/rv08b_interferencias_sw_v18d.csv`. Segunda opinión con otra herramienta, sobre los ensambles de las revisiones nuevas. Las coincidencias no cuentan; los choques dentro de una pieza multicuerpo sí.

| Ensamble | Interferencias |
|---|---:|
| MES-000_MESA_CONJUNTO | 79 |
| MES-520_CENTRADOR_EMPUJADOR | 13 |
| MES-521_SOPORTE_SOLDADO_PIVOTE | 5 |
| MES-400_TOPE_RETENCION | 0 |
| MES-410_TOPE_190 | 1 |
| MES-900_PEDESTAL | 0 |
| MES-800_TRASLADO | 0 |

| Ensamble | Par | N | Volumen (mm³) |
|---|---|---:|---:|
| MES-000_MESA_CONJUNTO | MES-520_CENTRADOR_EMPUJADOR_190 con MES-520_CENTRADOR_EMPUJADOR_190 | 13 | 127285 |
| MES-520_CENTRADOR_EMPUJADOR | MES-521_SOPORTE_SOLDADO_PIVOTE con MES-521_SOPORTE_SOLDADO_PIVOTE | 5 | 121900 |
| MES-000_MESA_CONJUNTO | MES-530_CENTRADOR_REFERENCIA_300 con MES-530_CENTRADOR_REFERENCIA_300 | 24 | 113495 |
| MES-000_MESA_CONJUNTO | MES-510_CENTRADOR_REFERENCIA_60 con MES-510_CENTRADOR_REFERENCIA_60 | 23 | 111439 |
| MES-521_SOPORTE_SOLDADO_PIVOTE | MES-521-1_PLACA_28 con MES-521-3_SILLA_SUPERIOR | 2 | 98280 |
| MES-000_MESA_CONJUNTO | MES-100_BASTIDOR_SOLDADO con MES-100_BASTIDOR_SOLDADO | 8 | 38396 |
| MES-000_MESA_CONJUNTO | MES-100_BASTIDOR_SOLDADO con MES-700_BLOQUEO_CENTRAL | 1 | 34190 |
| MES-521_SOPORTE_SOLDADO_PIVOTE | MES-521-1_PLACA_28 con MES-521-2_PEDESTAL_D60 | 1 | 16186 |
| MES-521_SOPORTE_SOLDADO_PIVOTE | MES-521-2_PEDESTAL_D60 con MES-521-5_SOPORTE_RETENCION | 1 | 4224 |
| MES-410_TOPE_190 | REF_MONTANTE_REF_MONTANTE con REF_SOPORTE_RET_REF_SOPORTE_RET | 1 | 4224 |
| MES-521_SOPORTE_SOLDADO_PIVOTE | MES-521-1_PLACA_28 con MES-521-4_SOPORTE_LIMITADOR | 1 | 3211 |
| MES-520_CENTRADOR_EMPUJADOR | MES-523_PIVOTE_Y_BRAZO con MES-523_PIVOTE_Y_BRAZO | 2 | 3116 |
| MES-000_MESA_CONJUNTO | MES-600_MANILLAR con MES-600_MANILLAR | 2 | 2165 |
| MES-520_CENTRADOR_EMPUJADOR | MES-521_SOPORTE_SOLDADO_PIVOTE con MES-524_LIMITADOR_Y_DISPARO | 2 | 1530 |
| MES-520_CENTRADOR_EMPUJADOR | MES-523_PIVOTE_Y_BRAZO con MES-525_PASADOR_Y_TOPE_CARRERA | 3 | 716 |
| MES-000_MESA_CONJUNTO | MES-100_BASTIDOR_SOLDADO con MES-815_BARRAS_DE_TIRO | 8 | 101 |
| MES-520_CENTRADOR_EMPUJADOR | MES-524_LIMITADOR_Y_DISPARO con MES-524_LIMITADOR_Y_DISPARO | 1 | 24 |

**Lectura:**
- **Los topes no interfieren con nada:** MES-400 da 0. MES-410 solo da el montante con el soporte de retención, ambos de referencia (4 224 mm³, unión prevista de K2-M).
- **MES-800 y MES-900 dan 0.**
- **MES-000 baja de 87 a 79.** El bastidor consigo mismo baja de 18 pares (486 302 mm³) a 8 (38 396 mm³), porque D-076 definió las uniones; lo que queda son los 4 rigidizadores de alma de R05 metidos en M01 y M02, ya declarados como H13 en la revisión V11.
- **El resto ya estaba declarado:** las uniones de K2-M representadas por solape, el conector de MES-700 con M03 (34 190 mm³, de R05) y las uniones del manillar (2 165 mm³). Las barras de tiro con M04 suman 101 mm³ en 8 contactos numéricos.
- **MES-520 y MES-521 dan lo mismo que antes** (13 y 5), salvo el soporte de retención con el pedestal, que baja de 8 447 a 4 224 mm³.
- **Limitación:** SOLIDWORKS revisó cada ensamble por separado. Las interacciones entre subsistemas están cubiertas por la auditoría geométrica y el barrido.
