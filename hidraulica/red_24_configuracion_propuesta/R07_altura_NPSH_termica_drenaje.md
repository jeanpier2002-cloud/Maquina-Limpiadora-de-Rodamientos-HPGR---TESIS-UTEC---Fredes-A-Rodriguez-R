# R07: cálculo de los pendientes P1-25 a–f (20/10/2026)

**Estado.** EJECUTADO como predimensionamiento bajo HIPÓTESIS. No es una validación (HPGR D-045).

- **Script:** `scripts/r07_calculos_pendientes.py`, en Python sin dependencias.
- **Datos:** `resultados/CALCULOS_PENDIENTES_R07.json`, con cada entrada, su valor y su fuente o HIPÓTESIS.
- **Decisiones del usuario (20/10)** aplicadas: drenaje **F1**; **tanques en 304 y bomba CRN en 316**.

## a) Altura de bomba con el trazado real de R07 → la CRN 15-3 basta

| Término | m |
|---|---:|
| Presión en C (4,06254 bar, C8) | 42,17 |
| Desnivel del nivel libre a C (Z1,74): normal / nivel bajo (LSL) | 1,08 / 1,39 |
| Impulsión R07: 8,66 m de DN50 (v = 1,56 m/s; f = 0,0206) + 7 codos, bola, retención y te (ΣK = 6,33) | 1,19 |
| Unión rotativa (0,30 bar) + filtro (0,20 bar) | 5,19 |
| Alimentación del distribuidor y carga cinética (C8, escaladas con Q²) | 0,83 |
| Succión: entrada, válvula de 3 vías y colador (K = 3, HIPÓTESIS) | 0,52 |
| **Total: normal / nivel bajo** | **50,98 / 51,29** |

- **Por qué la subida hasta la unión (Z3,795) no suma altura estática:** lo que sube se recupera al bajar hasta C. Solo cuentan las pérdidas.
- **Por qué sale menos que C8 (53,39 m):** C8 suponía 14 m de DN40 a 2,57 m/s; R07 tiene 8,7 m de DN50 a 1,56 m/s.
- **CRN 15-3:** en su curva da ≈ 56 m a 13,3 m³/h, así que **sobran ≈ 4,7 m**. Se recortan con el variador (U21) o con una válvula.
- **Se descarta la CRN 15-4.**

## b) NPSH → con margen

| Nivel | NPSH disponible | NPSH requerido de la CRN 15-3 | Margen |
|---|---:|---:|---:|
| Normal (Z0,66) | 5,55 m | ≈ 2,2 m | 3,35 m (×2,5) |
| Nivel bajo (Z0,35) | 5,24 m | ≈ 2,2 m | 3,04 m (×2,4) |

Con p_atm = 76,24 kPa (2 335 m) y p_v = 21,87 kPa (62 °C), según ME5007/C8. La lectura gráfica del NPSH requerido tiene ±0,3 m.

## d) Térmica → hallazgo: el rodamiento frío enfría el baño

**Datos.**
- El rodamiento (3 032 kg de acero, ~1,4 MJ/K) llega a temperatura ambiente, unos 15 °C (HIPÓTESIS).
- Sus aros son gruesos, pero al rociarlos se igualan con el baño en minutos (Bi > 1; τ ≈ 1,5–2 min).
- Para llevarlo de 15 a 60 °C hacen falta **62,8 MJ (17,4 kWh)**: más que la energía que guarda todo el baño por encima de 45 °C.

| Caso: 10 min de lavado sin precalentar | Baño a los 10 min |
|---|---:|
| Sin aporte de calor; equilibrio con 600 kg / 858 kg (tanque + pozo) | 45,2 / 48,8 °C |
| 24 kW, extractor a 150 m³/h, 858 kg | 50,9 °C |
| 48 kW, extractor a 150 m³/h, 858 kg | 54,0 °C |
| 24 kW, extractor a 800 m³/h, 600 kg | 41,7 °C |
| 24 kW, **rodamiento precalentado a 50 °C**, 858 kg | 59,5 °C |

**El extractor pierde mucho calor.** Su aire sale saturado a ~45 °C, y a 2 335 m de altura carga mucho vapor:

| Caudal del extractor | Pérdida térmica | Evaporación |
|---:|---:|---:|
| 150 m³/h | 8,8 kW | — |
| 300 m³/h | 17,5 kW | — |
| 800 m³/h | 46,7 kW | 61 kg/h |

Por eso **no puede funcionar a pleno durante el lavado**.

**Consecuencia.** Sin precalentar, el lavado real queda en ~46–51 °C, no en 62 °C. Eso está por debajo del umbral del antiespumante (≥ 60 °C, ME5007 F-03).

**Tiempo de precalentamiento** hasta que el baño llegue a 60 °C y el rodamiento a 55 °C (858 kg; recirculando con la puerta cerrada):

| Resistencias | Extractor a 150 m³/h, tanque sin aislar | Extractor parado, tanque aislado |
|---:|---:|---:|
| 24 kW | 57 min | **34 min** |
| 36 kW | 33 min | **23 min** |
| 48 kW | 23 min | **18 min** |

## c) Balance de agua del enjuague en cascada → no cierra sin purga

| Concepto | L por ciclo |
|---|---:|
| Entrada por el enjuague (1 vuelta) | +130 |
| Evaporación en el lavado (300 m³/h, 10 min) + secado (800 m³/h, 2 min) | −5,8 |
| Arrastre en el rodamiento | −1 |
| **Neto al tanque 1** | **+123** |
| Holgura desde el nivel normal hasta el rebose | 47 |

**Qué pasa.** Cada ciclo sobran unos **120 L**, que salen por el rebose o por una purga. A 8 % v/v se llevan unos **10 L de detergente concentrado**. Bajar el nivel del tanque 1 antes del enjuague (a Z ≤ 0,586) evita el rebose de ese ciclo, pero no el excedente acumulado.

**El arreglo de fondo** es una **purga controlada de ~120 L por rodamiento**: una válvula en el tanque 1 hacia el bidón de efluente o tratamiento, que de paso renueva el baño, sumada a la dosificación de detergente. Otra opción es volver al inhibidor en el baño (ME5007 D-06 B), sin tanque 2. Depende de cuántos rodamientos se laven por mes [DATO EXTERNO].

## e) Extractor → dos velocidades

| Uso | Caudal |
|---|---:|
| Depresión de 20 Pa con ~0,02 m² de fugas (HIPÓTESIS) | 285 m³/h |
| Secado de ~1 kg de película en 2 min | 767 m³/h |

- **Ventilador** a 800 m³/h y 250 Pa: unos 110 W de potencia útil. Basta un motor de 0,37 kW.
- **Propuesta:** variador o dos velocidades.
  - **Parado o ~150 m³/h** (depresión de ~5 Pa) en el precalentamiento y el lavado.
  - **~800 m³/h** en el secado y al abrir la puerta.

## f) Drenaje F1

- **Gravedad DN100 al 0,93 %** (Manning, n = 0,010; tubo lleno): **413 L/min**, que es 1,65 veces los 250 L/min.
- **Bomba todo o nada:** **~37 arranques por hora**, demasiados.
- **Con variador** a nivel constante, la bomba tendría que dar ~3,7 L/s, por debajo del inicio de su curva (~4,7 L/s). Hay dos caminos: confirmar con Hidrostal el caudal mínimo, o controlar por banda de nivel ampliando el volumen útil, es decir, un pozo más profundo, para bajar a 6–10 arranques por hora.

## Qué cambia en el diseño (propuesta para decidir)

1. **Precalentamiento.** Fase de precalentamiento recirculando, con la puerta cerrada y el extractor parado, y **tanque 1 aislado** (50 mm de lana mineral con chapa). Con 24 kW tarda ~34 min. **Subir a 36 kW** (3 × 12 kW) baja el tiempo a ~23 min, con la carga total del tablero en ~71 A (54,7 A solo de resistencias), así que el interruptor general pasa a 80 A.
2. **Enjuague.** Mantener la cascada (D-057) con **purga controlada** y dosificación de detergente, o pasar al inhibidor en el baño.
3. **Extractor** de dos velocidades.
4. **Drenaje F1:** banda de nivel con un pozo más profundo, o caudal mínimo confirmado por Hidrostal.
