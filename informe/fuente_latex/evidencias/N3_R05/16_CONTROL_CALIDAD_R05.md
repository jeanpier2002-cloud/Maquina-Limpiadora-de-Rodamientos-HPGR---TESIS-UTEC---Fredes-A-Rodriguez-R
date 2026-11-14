# Control de calidad R05

Fecha: 8 de septiembre de 2026

| Comprobación | Observado | Esperado | Estado |
|---|---:|---:|---|
| Original ZIP R04 preservado | `Hash registrado en memoria` | `9e696924e1e2eeeadb03cd5c7682930acc10d44edc4212c3469601971a952db1` | PASS |
| CAD FCStd/STEP reabierto | `True` | `True` | PASS |
| STEP sólidos | `153` | `153` | PASS |
| Pruebas de propagación XLSX | `True` | `True` | PASS |
| Errores de fórmula XLSX | `0` | `0` | PASS |
| Memoria PDF páginas | `14` | `14` | PASS |
| Planos PDF páginas | `6` | `6` | PASS |
| SAP R05 | `NO EJECUTADO` | `NO EJECUTADO` | PASS |
| Liberación fabricación | `NO` | `NO` | PASS |

## Alcance

- CAD y STEP reabiertos con auditoría geométrica acotada.
- Libro recalculado, sin coincidencias de errores de fórmula y con siete pruebas de modificación/restauración.
- DOCX y ambos PDF rasterizados completamente para inspección visual.
- No se ejecutó SAP2000 y no se atribuyen a R05 resultados de R01.
- No es plano de fabricación; no liberado para fabricación.
