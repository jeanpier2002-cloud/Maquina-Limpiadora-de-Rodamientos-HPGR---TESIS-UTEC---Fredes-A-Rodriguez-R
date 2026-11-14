# Requerimiento de simulación y exportación SAP2000 — R05

Estado: `PREPARADO_NO_EJECUTADO`.

## Modelo recomendado

1. Conservar geometría global N3 y verificar sección interna W6X9.
2. Incorporar masas actualizadas de R05 con fuente y coordenadas.
3. Representar las cuatro ruedas con links de compresión/contacto unilateral. Un apoyo U3 bilateral puede producir tracciones físicamente imposibles.
4. Representar el rodamiento mediante un nodo/cuerpo rígido en su CG conectado a los tres PAD con contacto compresivo. Aplicar peso y fuerza horizontal en el CG.
5. Alternativa simplificada: aplicar reacciones verticales PAD equivalentes para `e_físico+a·h/g` y aplicar la fuerza horizontal en el plano PAD, sin añadir de nuevo el momento `H·h`.
6. Aplicar las fuerzas horizontales a su altura física; no en Z=0 por conveniencia.

## Patrones y casos mínimos

- `LC_G_FRAME`: peso propio del bastidor, multiplicador 1.0; sin cargas externas duplicadas.
- `LC_G_BEARING`: peso del rodamiento 29.743920 kN; multiplicador de peso propio 0.0.
- `LC_E5_000...LC_E5_345`: ocho orientaciones físicas de colocación radial de 5 mm, o geometría equivalente del nodo de CG.
- `LC_H_000...LC_H_345`: fuerza horizontal del rodamiento `m·a=0.9096 kN` en ocho orientaciones, aplicada a Z del CG.
- `NL_CONTACT_*`: análisis estático no lineal con ruedas y PAD de compresión solamente; incluir estados de tres contactos cuando correspondan.
- Casos de reparto igual impuestos, si se conservan, etiquetarlos `CASOS_DE_CRIBADO_CON_REPARTO_IMPUESTO` y separar `COMPARABILIDAD_NUMERICA` de `ADECUACION_FISICA`.

## Combinaciones a reconstruir y documentar

- `SLS_NOMINAL = 1.0 LC_G_FRAME + 1.0 LC_G_BEARING`.
- `SLS_R05_ENV`: envolvente de las orientaciones E5 y H, con el factor vertical 1.15 aplicado una sola vez según la convención del libro.
- `ULS_R05_1_4`: factor 1.40 sobre la envolvente local documentada; conservar explícitos todos los factores y su justificación.
- No reutilizar una combinación por nombre sin comparar factores y patrones internos.

## Tablas exactas que se deben exportar a XLSX

### Definición

- Program Control / unidades.
- Coordinate Systems.
- Material Properties y modificadores.
- Frame Section Properties y Frame Section Assignments.
- Joint Coordinates.
- Connectivity — Frame, Joint, Link y Constraint.
- Joint Restraint Assignments.
- Frame Releases / Partial Fixity.
- Frame Local Axes Assignments.
- Link Property Definitions y Link Property Assignments, incluidos gaps/contactos.
- Diaphragm/Body/Constraint Assignments.
- Mass Source Definition y Joint/Element Mass Assignments.
- Load Pattern Definitions con multiplicador de peso propio.
- Joint Loads — Force; Frame Loads — Point/Distributed; Link Loads si existen.
- Load Case Definitions y Static Load Assignments.
- Load Combination Definitions con factores.
- Analysis Options / Active Degrees of Freedom.

### Resultados

- Joint Displacements: U1, U2, U3, R1, R2, R3.
- Joint Reactions: F1, F2, F3, M1, M2, M3.
- Link Forces, Link Deformations y estado abierto/cerrado.
- Frame Output Station Assignments.
- Element/Frame Forces: P, V2, V3, T, M2, M3.
- Base Reactions y equilibrio global de fuerzas/momentos.
- Steel Design Summary: demanda/capacidad, combinación gobernante y mensajes.
- Analysis Messages, warnings e inestabilidades.

## Postproceso obligatorio

- U3 de cada PAD, diferencia de nivel e inclinación entre PAD.
- Flecha relativa L/800 respecto de la cuerda deformada de cada miembro; no usar U3 global.
- Equilibrio de fuerzas y momentos por caso.
- Separar conclusión numérica de adecuación física del contacto.
