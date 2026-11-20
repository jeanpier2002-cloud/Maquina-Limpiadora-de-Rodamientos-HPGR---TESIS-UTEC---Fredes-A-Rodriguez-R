# Fase 2: detección de interferencias de SOLIDWORKS (27/10/2026)

**Qué es.** Una segunda opinión, con otra herramienta, sobre los ensambles de los planos. MES-000, MES-600 y MES-700 salen de R07 V11; el resto, de V10, porque en esas piezas V10 y V11 son iguales.
- Script: `scripts/rv02_interferencias_sw.ps1`.
- Detalle: `rv02_interferencias_sw.csv`.
- Criterio: las coincidencias (contactos) no cuentan como interferencia. Sí cuentan los choques entre cuerpos de una misma pieza multicuerpo, porque cada subconjunto del STEP es una pieza multicuerpo.

| Ensamble | Interferencias |
|---|---:|
| MES-000 Mesa | 87 |
| MES-520 Centrador empujador | 13 |
| MES-521 Soporte del pivote | 5 |
| MES-600 Manillar | 2 |
| MES-700 Bloqueo | 0 |
| MES-200 Apoyo sectorial | 0 |
| MES-400 Tope de retención | 0 |

**Agrupadas por par de componentes** (volumen total en mm³):

| Par | N | Volumen | Lectura |
|---|---:|---:|---|
| Bastidor MES-100 con sí mismo | 18 | 486 302 | Los perfiles W6x9 se solapan en sus ejes (R05). No hay corte ni preparación de las uniones a momento (D-040: trabajo futuro) |
| Rueda MES-300 con sí misma | 4 | 230 907 | 57 727 por rueda: eje, horquilla y envolvente de la rueda Blickle se solapan |
| Centrador 520 consigo mismo | 13 | 131 509 | Uniones del K2-M representadas por solape |
| Centrador 530 consigo mismo | 24 | 113 495 | Ídem |
| Centrador 510 consigo mismo | 23 | 111 439 | Ídem |
| MES-521: placa 28 con silla superior | 2 | 98 280 | Solape grande entre la placa y la silla. [VERIFICAR en la fase 1] |
| Bastidor con bloqueo MES-700 | 1 | 34 190 | «Conector solapado con M03» de R05 |
| MES-521: placa con pedestal | 1 | 16 186 | Zona del cordón W1 a tope; el pedestal entra en la placa |
| MES-521: pedestal con soporte de retención | 1 | 8 447 | Unión prevista (D-055) |
| Bastidor con topes MES-400 | 2 | 8 270 | La placa del tope baja 5 mm dentro del ala de M05 y M06 |
| MES-521: placa con soporte del limitador | 1 | 3 211 | Unión soldada W4 |
| Pivote y brazo MES-523 consigo mismo | 2 | 3 116 | [VERIFICAR en la fase 1] |
| Manillar: barra con postes | 2 | 2 162 | Los extremos de la barra entran 21 mm en el tubo del poste; falta la boca de pescado |
| MES-521 con limitador MES-524 | 2 | 1 530 | [VERIFICAR] |
| MES-523 con tope y pasador MES-525 | 3 | 717 | [VERIFICAR] |
| MES-524 consigo mismo | 1 | 24 | Pequeña |

**Conclusión preliminar.** SOLIDWORKS confirma lo que se esperaba: el CAD representa uniones soldadas y montajes con solapes de volumen, en lugar de piezas cortadas y en contacto. Esto no es un choque funcional, pero sí una limitación del CAD que hay que declarar. Para los planos de fabricación hay que definir cortes y preparaciones. La fase 1 separa los solapes que representan uniones de los choques reales.
