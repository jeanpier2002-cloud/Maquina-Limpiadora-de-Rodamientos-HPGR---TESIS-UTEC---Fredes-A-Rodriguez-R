# Números adimensionales v3 — Froude por fenómeno y cotas de la gravedad (T1)

> 24/10/2026, CORRIDA 2. Estado: CANDIDATO (cálculo del asistente, por auditar). No sustituye a `CORRIDA_1_13a21oct/06_VOF/NUMEROS_ADIMENSIONALES_v2.md`; la completa en lo que pidió Kevin el 21/10 (gravedad con Froude).
> Script: `02_VOF_v3/scripts/v3_froude.py` → `02_VOF_v3/datos/v3_froude.csv`, `v3_cotas_gravedad.csv`.
> Propiedades: TABLA_PARAMETROS_v2 (agua a 62 °C, ρ = 982,12 kg/m³, σ = 0,0662 N/m); g = 9,81 m/s².

## 1. Qué cambia respecto de la v2
- **Froude, no Bond, decide si la gravedad cambia el flujo.** Bond (ρgL²/σ) compara gravedad con tensión superficial: dice que la gravedad **no deforma** la lámina (Bo = 0,013 con e₀ = 0,30 mm; 3,5·10⁻⁴ con 0,049 mm). Froude compara inercia con gravedad.
- Se usa **Fr = v/√(gL)** (la forma de Kevin). La ficha de la tanda 1 daba Fr² = v²/(gL) (3,8·10³ para E1): es el mismo número al cuadrado (Fr = 62).
- **Lectura cuantitativa sin umbral prestado:** por energía mecánica, a lo largo de L la gravedad cambia v² como mucho en 2gL, es decir **Δ(v²)/v² ≤ 2/Fr²**. No hace falta un «Froude crítico» de la literatura (no se encontró uno verificado para este caso `[SIN FUENTE]`); la columna 2/Fr² da el efecto directamente.
- **No sabemos con qué v y L calculó Kevin su Froude «bajo»** (Jean no tiene el audio; las transcripciones están en la PC de Ismael). El único fenómeno con Fr ≪ 1 y escalas «naturales» de la máquina es el **rotor** (Fr ≈ 0,03) o la **película que escurre**; es probable que haya usado uno de esos `[HIPÓTESIS]`.

## 2. Froude por fenómeno

| Fenómeno | v (m/s) | L | Fr | 2/Fr² | Gravedad | Fuente de v / L |
|---|---:|---:|---:|---:|---|---|
| Chorro en vuelo, LAT → OD | 27,47 | 130,35 mm | **24** | 0,34 % | despreciable | E2_LAT3A.md l. 17 / TABLA_MAESTRA_22 |
| Chorro en vuelo, SUP → cara superior | 27,47 | ≈ 189 mm | 20 | 0,49 % | despreciable | ídem / PROMPT §A |
| Chorro en vuelo, INT → agujero | 27,47 | ≈ 148 mm | 23 | 0,39 % | despreciable | ídem / PROMPT §A |
| Lámina, L = e₀ (E1) | 27,47 | 0,30 mm | 506 | 8·10⁻⁴ % | despreciable | E1 |
| Lámina, L = e_OD (E1-OD) | 27,47 | 0,049 mm | 1,3·10³ | 1·10⁻⁴ % | despreciable | lámina intacta (escenario) |
| Dominio de E1 (impacto + película cercana) | 27,47 | 20 mm | **62** | 0,05 % | despreciable | E1 |
| Película junto al impacto (alto de huella) | 26,6 | 121,6 mm | 24 | 0,34 % | despreciable | u_f de E1 (NUMEROS_v2 l. 13) / 2·130,35·tan 25° |
| Película que escurre lejos del impacto | 0,1-1 | 515 mm | 0,04-0,45 | ≫ 100 % | **domina** | `[CÁLCULO, orden de magnitud]` / ancho del rodamiento |
| Gotas de INF_EXT llegando rasantes a la cara inferior | 4,4 (v_n) | 260 mm | **2,8** | 26 % | **no despreciable** | K6 (G7) / ancho radial de la cara inferior |
| Gotas de INF_INT a la cara inferior | 9,7 (v_n) | 260 mm | 6,1 | 5 % | moderada | K6 (G5) |
| Drenaje y goteo bajo la cara inferior | ≈ 0,1 | 2,6 mm (longitud capilar) | 0,6 | ≫ 100 % | **domina** | `[CÁLCULO, orden de magnitud]` |
| Rotor a 1,7 rpm, L = OD | 0,126 | 1,42 m | **0,034** | — | no aplica al impacto | ω·R, R = 0,71 m |
| Rotor a 1,7 rpm, L = radio | 0,126 | 0,71 m | 0,048 | — | no aplica al impacto | ídem |

**Lectura (para Kevin):**
1. **En el impacto (lo que mide el VOF) la gravedad no cambia nada:** Fr = 20-1300, efecto ≤ 0,5 % en v².
2. **Donde la gravedad manda es después:** película que escurre, drenaje y goteo de la cara inferior. Eso **no es el objetivo del VOF** (Kevin aceptó el laminar porque el objetivo es el impacto, no la distribución posterior). En el DPM de Fluent la gravedad **sí está activada** (0, 0, −9,81), y por eso el DPM recoge la caída de las gotas rasantes de la cara inferior (Fr 2,8-6): es coherente con que la cara inferior sea el punto débil.
3. **El Fr del rotor (0,03) es bajo, pero no habla de la gravedad sobre el chorro:** compara la velocidad de la pared (0,13 m/s) con la gravedad. Lo que sí justifica es la simplificación del **rotor congelado**: la pared se mueve 0,6 mm durante los 4,7 ms de vuelo de la gota (0,126 × 4,745·10⁻³) `[CÁLCULO]`.

## 3. Cotas analíticas de la gravedad en el impacto (§2.2.1 del prompt) `[CÁLCULO, por verificar]`

| Cota | Valor | Relativo |
|---|---|---|
| Velocidad ganada en la ventana de E1 (1,2 ms), Δw = g·t | 0,012 m/s | 0,04 % de 27,47 m/s |
| Velocidad ganada en 10 ms (ventana de E2) | 0,098 m/s | 0,36 % |
| Tiempo de vuelo LAT → OD | 4,745 ms | — |
| Caída durante el vuelo, ½·g·t² | 0,11 mm | 0,09 % del alto de huella (121,6 mm) |
| Desvío angular del chorro al llegar, atan(g·t/v) | 0,097° | — |
| Gravedad a lo largo de la pared en el dominio de E1 (20 mm), 2gL/u_f² | — | 0,055 % de u_f² (cota de V4, «gravedad en el plano») |

## 4. Orientación de la gravedad en E1 (corrige el documento de Ismael, §2.2 del prompt)
- E1 es un corte x–y a través del **espesor** de la lámina (x a lo largo de la pared, y normal a ella; z vacío). En las 22 boquillas el plano del abanico es radial-vertical (supuesto I3 de R05), así que la dirección delgada de la lámina es la **tangencial (horizontal)** y la gravedad (−z) queda **fuera del plano del corte**. Un 2D con `empty` en z no puede contenerla y el problema **sigue siendo simétrico**.
- Por eso: (a) se responde con las cotas de §3; (b) V3 («2,5D»: una celda en z con frontera cíclica y g = (0, 0, −9,81)) es una demostración numérica opcional; (c) V4 (g a lo largo de la pared, x) cubre el caso de abanico girado 90° (I3 falso), con una cota analítica de 0,055 %.

## 5. Pendiente
- Confirmar con Kevin qué v y qué L usó (pregunta para la reunión del 27/28).
- `[VERIFICAR]` si se quiere citar un texto para Fr y para el balance de energía (p. ej. White, *Fluid Mechanics*, capítulo de análisis dimensional; edición y página por verificar). Son definiciones y un balance que se deducen a mano: según el criterio de Kevin, son **teóricos**.
