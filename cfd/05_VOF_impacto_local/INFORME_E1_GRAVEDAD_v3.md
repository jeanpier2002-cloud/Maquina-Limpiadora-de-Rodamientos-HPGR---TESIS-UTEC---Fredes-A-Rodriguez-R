# INFORME E1 GRAVEDAD v3 — ¿cambia la gravedad el impacto? (T2)

> 25/10/2026, CORRIDA 2. Estado: CANDIDATO · verificado. Datos: `02_VOF_v3/datos/E1OD_gravedad.csv`; figura `figuras/OD_gravedad.png`; Froude en `NUMEROS_ADIMENSIONALES_v3.md`.

## 1. Por qué no el «2,5D cíclico» del prompt
En el OD la gravedad (−z) queda fuera del plano del corte (normal del abanico tangencial, supuesto I3). Una celda en z con frontera cíclica y g en z no demuestra nada en interFoam: con p = p_rgh + ρ g·h y p_rgh periódica, la presión hidrostática absorbe la gravedad en la dirección periódica, así que el resultado sería «sin efecto» por construcción. Se corrieron en su lugar las orientaciones que sí entran en un 2D y que existen en la máquina.

## 2. Corridas (E1-OD, e₀ = 0,049 mm, Co 0,5)
| ID | Gravedad | Orientación real que representa | Malla |
|---|---|---|---|
| V3a | (0, −9,81, 0): hacia la pared | chorro vertical hacia abajo sobre la **cara superior** | N10 |
| V3a2 | (0, +9,81, 0): alejándose de la pared | chorro hacia arriba sobre la **cara inferior** | N10 |
| V3b | (0, −9,81, 0) | ídem V3a | N20 |
| V4a | (−9,81, 0, 0): a lo largo de la pared, dominio completo | abanico girado 90° (I3 falso): «una parte sube y otra baja» (lo que imaginaba Kevin) | N10 |
| V4b | sin g, dominio completo | control de V4a | N10 |

## 3. Resultado
| Caso | p₀ | F/b local | τ_w (0,33 mm) | espesor (0,33 mm) | M (0,33 mm) |
|---|---|---|---|---|---|
| hacia la pared (N10) | +0,005 % | +0,006 % | +0,002 % | −0,001 % | +0,004 % |
| alejándose (N10) | −0,005 % | −0,004 % | −0,002 % | +0,000 % | −0,005 % |
| hacia la pared (N20) | +0,005 % | +0,005 % | +0,002 % | +0,000 % | +0,005 % |
| a lo largo de la pared (N10, completo) | −0,000 % | −0,001 % | −0,005 % | +0,004 % | +0,001 % |
- **Máximo en todas las magnitudes del CSV: ≈ 0,02 %** (M a 0,82 mm con g a lo largo de la pared).
- La asimetría entre los dos lados con g a lo largo de la pared (0,017 % en M) es **igual** a la del control sin g (0,018 %): es ruido numérico, no gravedad.
- Coincide con las cotas a mano: Δ(v²)/v² ≤ 2/Fr² = 0,009 % en el dominio de E1-OD (L = 3,27 mm) y 0,055 % en el de E1 (20 mm).

## 4. Conclusión para Kevin
A la escala del impacto la gravedad no cambia nada (≤ 0,02 %), en ninguna orientación. Donde manda (Fr ≲ 3) es en el escurrimiento posterior de la película y en la cara inferior; eso no es el objetivo del VOF y el DPM de Fluent ya lleva la gravedad activada.
