# Precedencia y resolución de conflictos de fuentes

**Trabajo:** `V5.2_ASPERSION_AUDIT_AND_HANDOFF_I01`  
**Estado máximo actual:** `PENDIENTE_DATOS_DE_ENTRADA`

No existe una jerarquía universal para todos los temas. Claude debe aplicar la fuente que gobierna cada dominio y conservar `source_id`, página física PDF o celda.

## Precedencia por dominio

| Dominio | Orden de precedencia | Regla |
|---|---|---|
| Restricciones del encargo y estado | `START_HERE_CLAUDE.md` → handoff vigente | No elevar el estado ni ampliar el alcance por inferencia. |
| Arquitectura mecánica | V5.2 → V5.1 → V5 → antecedentes | V5.1 representa la operación de V5; Layout B, manifold U y lanza axial activa están superseded. |
| Identidad y dimensiones del rodamiento | `EXT-001` ficha SKF del `241/900 ECAK30/W33` → parámetros internos | Una discrepancia se registra; no confundir con SKF 24088 ni con `241/900-2CS5...` sellado. |
| Limpieza, inspección y preservación del rodamiento | `EXT-002` SKF + `EXT-003` FAG/Schaeffler → literatura general | Son prácticas de mantenimiento, no criterios automáticos de presión o caudal. |
| Restricciones HPGR específicas | Manual oficial autorizado del equipo exacto → documentación interna aprobada | `EXT-007` es restringido y corresponde a otra máquina; no usar si no existe autorización. |
| Selección de proceso de limpieza | Ensayo validado del proyecto → ASM `EXT-005` → papers análogos | El ensayo sobre cupón/rodamiento representativo prevalece sobre tendencias bibliográficas. |
| Hidráulica y componentes | Catálogo oficial del modelo real + curva del sistema → ecuaciones reproducibles → escenarios antiguos | Ningún ejemplo genérico selecciona boquilla, bomba, filtro, tanque o tubería. |
| Diseño mecánico de soportes | Cargas/reacciones reales + norma aplicable → Shigley `EXT-006` | El texto es referencia metodológica, no aprobación para fabricar. |

## Regla de resolución

1. Verifica que la fuente corresponda al producto, edición, máquina y dominio correctos.
2. Distingue página física PDF de página impresa.
3. Distingue `DOCUMENTADO`, `CALCULADO`, `SUPUESTO_DE_ESCENARIO`, `PENDIENTE` y `SUPERSEDED`.
4. Si dos fuentes válidas discrepan, crea un conflicto con ambas citas y solicita decisión; no promedies ni elijas en silencio.
5. Si la fuente no está realmente adjunta, no afirmes haberla leído. Usa el resumen como índice de búsqueda y marca `FUENTE_NO_ADJUNTA`.
6. Ninguna analogía académica sustituye una curva de catálogo o un ensayo del sistema actual.

## Identificaciones que no deben corregirse por el nombre del archivo

- `EXT-003` FAG/Schaeffler: citar **2004**. El propio documento muestra copyright 2003, depósito legal 2004 y edición 04/04; “2015” solo aparece en el nombre local.
- `EXT-001`: el producto base es abierto `241/900 ECAK30/W33`, no el rodamiento 24088 y no la variante sellada `241/900-2CS5K30/C3HGEA8`.

## Antecedentes superseded

Los contenidos de `outputs/diseno_preliminar/` y los protocolos que todavía nombren Layout B, manifold U o lanza axial pueden aportar ecuaciones, factores, respuestas, instrumentación y lógica de validación. Antes de usarlos deben remapearse a la arquitectura vigente: rodamiento fijo, un trolley, monorriel 360°, `theta/R/Z/beta` y Head A.
