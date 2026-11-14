# INFORME E1-OD v3 — lámina 2D con el espesor real en el OD (T3)

> 25/10/2026, CORRIDA 2. Estado: **CANDIDATO · verificado (malla, Δt, regresión) ≠ validado**. Lámina intacta = **cota superior** (no se sabe si la VeeJet ya se rompió en gotas a 130 mm). Datos: `02_VOF_v3/datos/E1OD_*.csv` (`v3_e1od_post.py`); figuras `02_VOF_v3/figuras/{CONV_E1OD_*,OD_*}`; costos `00_ADMIN/run_log.csv`.

## 1. Qué se simuló
- Corte 2D x–y a través del espesor de la lámina de LAT_3_A en el OD: e₀ = 0,049 mm (lámina intacta a 130,35 mm), v = 27,4711 m/s, agua a 62 °C, aire a 76,24 kPa (≈ 20 °C), laminar, interFoam v2606, medio dominio con simetría.
- Geometría y tiempos escalados con S = e₀/0,30 mm = 0,1633 respecto de E1 (`v3_e1od_generar.py`): mismo N, mismas celdas (4 810 · (N/5)²) y mismo número de pasos por tiempo adimensional. **Lo que no se escala es la física viscosa y capilar**: Re = ρve₀/μ = 2,9·10³ (E1: 1,8·10⁴) y We = 550 (E1: 3 400).
- N = celdas a través del espesor; Δ = e₀/N = 9,8 / 4,9 / 2,45 / 1,225 µm. Ventana de promedio 0,3-0,5 ms·S (49-82 µs).

## 2. Resultados frente a la malla (Co 0,5)

| N | celdas | p₀ (kPa) / dif. con ½ρv² | F/b local, |x| < 0,163 mm (N/m) / dif. con ρv²e₀ | M por lado en x = 0,33 mm (N/m) / M/M₀ | q/q₀ en 0,33 mm | espesor en 0,33 mm (µm) | τ_w en 0,33 mm (Pa) | costo real (h, procesos) |
|---|---:|---|---|---|---:|---:|---:|---|
| 5 | 4 810 | 364,5 / −1,65 % | 36,88 / +1,5 % | 16,08 / 0,886 | 0,964 | 28,71 | 1 621 | 0,01 (1) |
| 10 | 19 240 | 369,1 / −0,41 % | 36,47 / +0,41 % | 16,81 / 0,926 | 0,991 | 28,31 | 1 879 | 0,09 (1) |
| 20 | 76 960 | 370,4 / −0,06 % | 36,50 / +0,49 % | 16,96 / 0,934 | 0,996 | 28,18 | 1 954 | 1,08 (2)* |
| 40 | 307 840 | 385,6 / +4,06 % en la celda de la esquina; **370,9 / +0,10 % sin ella** (§4) | 36,55 / +0,64 % | 17,00 / 0,936 | 0,998 | 28,17 | 1 977 | 1,87 (4)* |
| 40, Co 0,25 (V1d2) | 307 840 | 383,1 / +3,38 % en la esquina; 370,8 / +0,05 % sin ella | 36,54 / +0,62 % | 17,00 / 0,936 | — | 28,29 | 1 958 | 1,68 (6), aislado |

Teoría (deducción en `TABLA_REFERENCIAS_TEORICAS_v3.md`): p₀ = 370,6 kPa; F/b = 36,32 N/m; M₀ = 18,16 N/m; q₀ = 0,661 kg/(s·m). *Costos con 4 carriles a la vez (9 procesos en 8 núcleos); aislado, E1 tardó 0,77 h (N20) y 2,68 h (N40).

**Orden observado** p = log₂(|φ_N − φ_2N|/|φ_2N − φ_4N|) (`figuras/CONV_E1OD_orden.csv`): M 2,23 (N5-10-20) y 2,10 (N10-20-40); τ_w 1,79 y 1,72; espesor 1,57 y 3,24; p₀ 1,85 (N5-10-20; N10-20-40 no monótono por §4). **≈ 2, como esperaba Kevin.**

**Criterio del 2 % (Kevin):** p₀ cumple desde N10 (−0,41 %); la fuerza del impacto desde N5 (+1,5 %); M en N20 está a 0,2 % de N40. **Malla de trabajo: N20** (como en E1).

## 3. Lectura física
- **El impacto lo predice la teoría a mano** (p₀ y F/b local dentro del 0,5 %): el VOF «no descubre» la fuerza, la confirma.
- **El empuje de la película en el OD es M ≈ 17,0 N/m por lado a 0,33 mm del eje (0,94 M₀)** y baja a 16,1 N/m a 0,82 mm: la fricción con la pared se lleva ≈ 6-12 % del empuje en el primer milímetro (balance dM/dx = −τ_w). Este es el dato que faltaba para el criterio de la grasa (antes se usaba M₀ = 18,2 N/m escalado).
- **Cortante en la pared ≈ 2 kPa a 0,33 mm** (τ_w,max ≈ 9,5 kPa junto al eje); converge con p ≈ 1,7-1,8. La pendiente de Hiemenz junto al eje **no converge** (−25 % en N40, igual que en E1): la capa límite de estancamiento mide ≈ √(ν/a) ≈ 1 µm, del orden de la celda.
- **Fuerza total sobre la pared:** sale +23 / +43 / +100 % (N10 / N20 / N40) sobre ρv²e₀ y crece al refinar. El exceso está en la película lejos del eje, donde la pared está parcialmente mojada (α 0,2-0,9) y la presión es ≈ 2,5-5 kPa ≈ σ/(h/2) con h ≈ 28 µm, en la zona del frente que sigue dentro del dominio `[HIPÓTESIS: presión capilar del borde de la película; en E1 el mismo efecto era +3-10 % porque We es 6 veces mayor]`. **Por eso la fuerza del impacto se informa con la integral local (|x| < 3,3 e₀)**.

## 4. Anomalía de p₀ en N40 — resuelta: es una celda de la esquina, no el paso de tiempo
- Con Co 0,5, N40 da p₀ = 385,6 kPa (+4,06 %) en la **primera cara de la pared**, constante en el tiempo, mientras N5-N20 convergen hacia la teoría (−0,06 % en N20).
- **Hipótesis 1 (límite capilar de Brackbill) — DESCARTADA.** En N40 el Δt medio (1,48·10⁻⁸ s) superaba Δt_σ = √(ρ̄Δ³/(2πσ)) = 1,03·10⁻⁸ s de la celda de pared. La prueba **V1d2 (N40, Co 0,25, Δt 8,2·10⁻⁹ s < Δt_σ; 1,68 h con 6 procesos)** da casi lo mismo: p₀ 383,1 kPa (+3,38 %), fuerza total +100,5 % (frente a +99,6 %). La anomalía no depende del paso de tiempo. Con Co 0,25 frente a 0,5 en N40: F/b local −0,015 %, M +0,008 %, espesor +0,44 %, τ_w −0,9 %.
- **Lo que muestra el perfil de presión:** el exceso está **solo en la primera celda**, la de la esquina donde el plano de simetría toca la pared (x = 0,6 µm). Desde la segunda celda (x = 3,1 µm) N40 coincide con N20 (369,5 frente a 369,2 kPa a x ≈ 3 µm; ≤ 0,8 % en todo el perfil hasta 100 µm).
- **p₀ robusto** (ajuste p = p₀ − ½ρa²x² en |x| < 12 µm, sin la celda de la esquina): N20 370,49 kPa (**−0,02 %**), N40 Co 0,5 370,94 kPa (**+0,10 %**), N40 Co 0,25 370,77 kPa (**+0,05 %**). (N5 y N10 no tienen celdas suficientes en ese tramo; para ellas vale el valor de la primera cara.)
- **Lectura:** es un artefacto numérico local de la celda de la esquina simetría-pared en la malla más fina `[HIPÓTESIS sobre el origen exacto: la celda tiene relación de aspecto ≈ 3 (1,22 × 0,45 µm) junto a dos fronteras]`; no afecta a la fuerza integrada (+0,1 % como mucho) ni al empuje. La malla de trabajo sigue siendo N20; p₀ se informa con N5-N20 (valor directo) y con el ajuste en N20-N40.
- **Lo que sigue abierto:** la fuerza **total** de la pared crece al refinar (+23 / +43 / +100 %) por la presión en la película lejos del eje (§3). No es el impacto y no se usa como KPI; posible origen: presión capilar del frente y error de curvatura del modelo CSF en láminas muy delgadas finamente resueltas `[HIPÓTESIS NO VERIFICADA]`.

## 5. Paso de tiempo (N20, frente a Co 0,25)
| Co | Δt medio | p₀ | F/b local | τ_w (0,33 mm) | espesor | M |
|---|---|---|---|---|---|---|
| 0,5 | 3,3·10⁻⁸ s | +0,012 % | +0,006 % | +0,42 % | −0,12 % | +0,005 % |
| 1 | 6,8·10⁻⁸ s | +0,025 % | +0,035 % | +1,04 % | −0,22 % | +0,06 % |
Todo por debajo del 2 %; Co 0,5 está justificado (como en E1: < 1 % entre Co 0,25 y 2).

## 6. Escalado a las otras superficies de incidencia normal (§A del prompt)
Lámina intacta con e ∝ 1/distancia `[supuesto]`; M₀ = ρv²e/2; aplicando la misma fracción viscosa M/M₀ ≈ 0,94 de E1-OD a 0,33 mm `[supuesto: el Re de esas láminas es 2,0-2,6·10³, parecido al del OD]`:

| Grupo | Distancia | e (mm) | M₀ (N/m) | M ≈ 0,94 M₀ (N/m) |
|---|---|---|---|---|
| LAT_1-4 (OD) | 130,35 mm | 0,049 | 18,2 | **17,0** (simulado) |
| SUP_1-2 (cara superior) | ≈ 189 mm | 0,034 | 12,4 | ≈ 11,6 |
| INT_1-5 (agujero) | ≈ 148 mm | 0,043 | 15,6 | ≈ 14,7 |
Las 5 boquillas oblicuas (LAT_5, INF_EXT, INF_INT) no las representa este corte (su inclinación está en el plano del abanico): las cubre el DPM de Fluent. Cortes propios (V5) o plano del abanico (V6): se le preguntan a Kevin.

## 7. Regresión (V0)
E1 N5 de la tanda 1 corrido desde la ruta v3: `force.dat` y presión de pared con diferencia **0** (idénticos bit a bit), 1565 pasos (`datos/V0_regresion.csv`).
