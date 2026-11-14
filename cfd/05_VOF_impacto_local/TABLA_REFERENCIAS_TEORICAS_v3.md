# Referencias teóricas del VOF: de dónde sale cada valor (T5)

> 24/10/2026, CORRIDA 2. Estado: CANDIDATO (deducciones del asistente, por auditar). Criterio de Kevin (21/10, audio [00:00]-[00:49]): **«teórico» = se resuelve a mano**; si sale de un paper o ensayo es **«experimental»** (error = |φ − φ_exp|/|φ_exp|); si la referencia es la malla más fina, se dice así. Todas las referencias de esta tabla son **teóricas**. Datos: ρ = 982,12 kg/m³, μ = 4,5227·10⁻⁴ Pa·s (agua a 62 °C), v = 27,4711 m/s (salida de LAT_3_A), e₀ = 0,30 mm (E1) y 0,049 mm (E1-OD, lámina intacta en el OD).

## 1. Tabla

| # | Magnitud | Fórmula | E1 (e₀ = 0,30 mm) | E1-OD (e₀ = 0,049 mm) | Tipo | Texto de apoyo |
|---|---|---|---|---|---|---|
| T1 | Presión de estancamiento | p₀ = ½ρv² | 370,6 kPa | 370,6 kPa | teórica | Bernoulli; White, *Fluid Mechanics*, cap. 3 `[VERIFICAR edición y página]` |
| T2 | Fuerza normal por unidad de ancho (lámina completa) | F/b = ρv²e₀ | 222,4 N/m | 36,3 N/m | teórica | Balance de cantidad de movimiento en un volumen de control (chorro plano contra placa); White, cap. 3 `[VERIFICAR]` |
| T3 | Caudal por lado | q₀ = ρve₀/2 | 4,05 kg/(s·m) | 0,661 kg/(s·m) | teórica | Conservación de la masa + simetría |
| T4 | Empuje de la película por lado, sin viscosidad | M₀ = ρv²e₀/2 | 111,2 N/m | 18,2 N/m | teórica | Mismo balance (velocidad de salida = v por Bernoulli) |
| T5 | Pérdida de empuje por fricción | dM/dx = −τ_w | — | — | teórica (balance) | Balance de cantidad de movimiento en la película |
| T6 | Pendiente del cortante junto al eje | dτ_w/dx = f″(0)·μ·a^{3/2}·ν^{−1/2}, f″(0) = 1,2326 | según *a* ajustado | según *a* | teórica (solución de semejanza) | Hiemenz; Schlichting y Gersten, *Boundary-Layer Theory* `[VERIFICAR edición y página]`; f″(0) = 1,232588 verificado numéricamente (tanda 1, `v2_a4_hiemenz.py`) |
| T7 | Fuerza ideal de una boquilla | ṁ·v = 4,154 N; con ⟨cos φ⟩ del abanico, 4,02 N | — | — | teórica | Balance de cantidad de movimiento (§2.4 del prompt) |
| T8 | Alto de la huella (rayos) | 2·d·tan 25° | 121,6 mm (d = 130,35 mm) | — | teórica (geometría) | Abanico de 50° |
| T9 | Efecto de la gravedad en v² a lo largo de L | Δ(v²)/v² ≤ 2/Fr² | 0,05 % (L = 20 mm) | 0,009 % (L = 3,27 mm) | teórica (energía) | `NUMEROS_ADIMENSIONALES_v3.md` |

## 2. Deducciones (una línea de hipótesis + el cálculo)

**T1. p₀ = ½ρv².** Línea de corriente central, del chorro libre (presión atmosférica, velocidad v) al punto de estancamiento sobre la pared (velocidad 0). Hipótesis: régimen permanente, sin viscosidad, incompresible, sin gravedad (Fr ≫ 1, T9). Bernoulli: p_atm + ½ρv² = p₀ ⇒ p₀ − p_atm = ½ · 982,12 · 27,4711² = 370 588 Pa ≈ **370,6 kPa**. No depende del espesor: es la misma en E1 y E1-OD.

**T2. F/b = ρv²e₀.** Volumen de control que encierra la zona de impacto, con presión atmosférica en todo su borde. Entra por arriba un flujo de cantidad de movimiento normal a la pared ρ·v·(v·e₀) por unidad de ancho; sale a lo largo de la pared (velocidad tangencial, sin componente normal). La única fuerza normal externa es la de la pared: F/b = ρv²e₀ = 982,12 · 27,4711² · 0,30·10⁻³ = **222,4 N/m** (E1); con 0,049 mm, **36,3 N/m**.

**T3 y T4. q₀ y M₀ por lado.** Por simetría la mitad del caudal sale por cada lado: q₀ = ρve₀/2. Sin viscosidad y con presión atmosférica en la superficie libre, Bernoulli da la misma velocidad v en la película de salida, así que el flujo de cantidad de movimiento tangencial por lado es M₀ = q₀·v = ρv²e₀/2 = **111,2 N/m** (E1) y **18,2 N/m** (E1-OD).

**T5. dM/dx = −τ_w.** Volumen de control que es una rebanada de película entre x y x + dx: la presión es atmosférica arriba y casi uniforme dentro de la película lejos del impacto, así que lo único que cambia el flujo de cantidad de movimiento tangencial es la fricción de la pared. Por eso, con viscosidad, M(x) < M₀ y baja con x. En la tanda 1 (B4) este balance cerró con la integral de τ_w.

**T6. Hiemenz.** Cerca del eje, el flujo exterior es de estancamiento plano, u = a·x, con p = p₀ − ½ρa²x² (Bernoulli en el flujo exterior). La capa límite admite la solución de semejanza f‴ + f·f″ + 1 − f′² = 0, con f(0) = f′(0) = 0 y f′(∞) = 1, cuya pendiente en la pared es f″(0) = 1,2326. Entonces τ_w = μ·a·x·√(a/ν)·f″(0) ⇒ dτ_w/dx = 1,2326·μ·a^{3/2}/√ν. En el VOF, *a* se obtiene ajustando p(x) junto al eje y se compara la pendiente de τ_w(x).

**T7. ṁv.** ṁ = ρ·q = 982,12 · 9,24/60 000 = 0,15124 kg/s; ṁ·v = 0,15124 · 27,4711 = **4,154 N** (fuerza sobre una pared normal a toda la boquilla). El 4,02 N es ṁ·v·⟨cos φ⟩ (promedio sobre el abanico) y 26,6 m/s es la componente normal media v·⟨cos φ⟩, no otra velocidad (`E2_LAT3A_v2.md` l. 109).

**T8. Huella.** Abanico de 50° (±25° del eje): alto = 2·130,35·tan 25° = **121,6 mm**.

**T9. Gravedad.** Energía mecánica sin pérdidas a lo largo de L: v₂² = v₁² ± 2gL ⇒ |Δ(v²)|/v² ≤ 2gL/v² = 2/Fr².

## 3. Qué se compara con qué en las figuras
- p₀ (VOF) frente a T1; F/b (VOF, integral de p sobre la pared) frente a T2; M(x) y q(x) (perfiles normales a la pared) frente a T4 y T3; pendiente de τ_w frente a T6. Rotuladas «teórica».
- Espesor de película, τ_w lejos del eje y longitud mojada **no tienen referencia a mano**: se comparan con la **malla más fina** (rotulado así) y se informa el orden de convergencia observado p = log₂(|φ_N − φ_2N| / |φ_2N − φ_4N|).
- Ninguna figura del VOF usa referencias experimentales (no hay ensayo propio). Si se agregan datos de papers (p. ej. M_y medido de Chee y Wilson 2021 en el criterio de la grasa), se rotulan «experimental».
