# Presión y bomba con O7+C2 (24 boquillas): ¿hay que volver a simular todo?

> 25/10/2026 · Ismael, con su asistente (Claude) · Estado: **CANDIDATO**. Cálculo de red bajo HIPÓTESIS; verificado ≠ validado (HPGR D-045).
> **Fuentes:**
> - la red de 24 boquillas, de Codex C8 (`03_CONTEXTO/C8_red_hidraulica_C2.out.txt`), con el método de tu `calculo_red_22.py`: q = K_q·√p, Darcy–Weisbach y Swamee–Jain;
> - la bomba, de la selección comercial R07 (`03_CONTEXTO/R07_bomba_seleccion.md` y `R07_resultados_pendientes.md`) y de la HPGR D-056.

## 1. La pregunta

Si se agregan boquillas, ¿cambia la presión de todas y hay que volver a simular el CFD completo?

## 2. Respuesta corta

- **Con la bomba sin regular, sí cambiaría.** Más área de salida da más caudal, y el punto de operación se mueve sobre la curva de la bomba: baja la presión en todas las boquillas.
- **Pero la red se recalculó con la condición de diseño:** la boquilla más desfavorable (INT_5) se mantiene en **4,00 bar**, reajustando la altura de la bomba. Con eso, la presión del colector C queda igual (**4,0625 bar**) y las demás boquillas casi no cambian (tabla del §3).
- **No hace falta volver a simular todo.** Solo hay que correr el **ramal A (OD + cara inferior)**, porque ahí cambian las propias inyecciones: INF_EXT pasa de 5020 a 30° a 1520 a 15°, y se agrega C2. Esa es la corrida `G3_A_O7_O4` del kit, que ya carga LAT_1…5 con los caudales de la red de 24.
- **La cara superior y el agujero conservan sus resultados** (G6/F3–F4 y G5/F5–F6). Su presión cambia como mucho 0,6 mbar (INT_*, 0).

## 3. Presión y caudal por boquilla (C8)

| Boquilla | 22 boquillas: bar / L/min | 24 boquillas (O7+C2): bar / L/min | Δp | Δq ≈ ½·Δp/p |
|---|---|---|---:|---:|
| SUP_1, SUP_2 A/B | 4,0636 / 9,190 | 4,0631 / 9,189 | −0,5 a −0,6 mbar | −0,01 % |
| LAT_1…LAT_5 A/B | 4,0989–4,1271 / 9,23–9,26 | 4,0975–4,1249 / 9,23–9,26 | −1,4 a −2,2 mbar | ≤ −0,03 % |
| INF_EXT A/B | 4,1405 / 9,276 | 4,1306 / 9,265 | −9,8 mbar | −0,12 % |
| C2 A/B (nueva) | — | 4,1282 / 9,263 | — | — |
| INT_1…INT_5, INF_INT | 4,0000–4,0375 / 9,12–9,16 | iguales | 0 | 0 |
| **Total** | **202,59 L/min; bomba 52,56 m** | **221,07 L/min; bomba 53,39 m** | | **+9,1 % de caudal** |

**Lectura:**
- El mayor cambio en una boquilla existente es −0,24 % de presión en INF_EXT, es decir, −0,12 % de caudal y de velocidad de salida (q y v ∝ √p).
- En tus verificaciones del CFD, la incertidumbre numérica es mayor:
  - malla fina frente a base: ≤ 1 % en D̄ y J̄;
  - ruido A/B: ±1,5 %;
  - balances: 0,02–0,14 %.
- **Los cambios de la red son unas 10 veces menores que esa incertidumbre**, así que no justifican volver a correr las otras superficies.
- **La 1520 tiene la misma capacidad que la 5020.** El «20» significa 2,0 gpm a 40 psi: unos 9,12 L/min a 4 bar, según el catálogo de Spraying Systems (`portal.spray.com`, H3/8U-316SS1520). Por eso vale el mismo K_q del cálculo; lo que cambia es el abanico: 50° frente a 16,8°, este último interpolado a 4 bar (**HIPÓTESIS**).

**Lo que sí cambia y solo el CFD puede decir:** INF_EXT reorientada y C2 también mojan la parte baja del OD. Por trazado de rayos (cribado N1, no CFD), el OD baja −1,3 % y la zona Z3 sube de D̄ 4,27 a 19,72 kg/m²/vuelta. Como el ramal A incluye el OD, la corrida `G3_A_O7_O4` lo cuantifica.

## 4. ¿La bomba alcanza?

| Ítem | Valor | Fuente / estado |
|---|---|---|
| Punto requerido | 221,07 L/min (13,26 m³/h) a 53,39 m | C8 (método ME5007), CANDIDATO |
| Altura recalculada con el trazado R07 | ≈ 51,0–51,3 m (la subida hasta la unión rotativa no suma altura estática) | `R07_resultados_pendientes.md`, CANDIDATO |
| Bomba elegida | **Grundfos CRN 15-3** (316; 4 kW; 60 Hz; 3 × 380 V; brida DN50) | HPGR D-056, CANDIDATO |
| Curva a 13,3 m³/h | H ≈ 56 m; P2 ≈ 3,0 kW; η ≈ 65 % | Catálogo Grundfos CR/CRN 60 Hz, p. 52; lectura gráfica ±1 m |
| Margen de altura | 2,6 m (frente a 53,39) a 4,7 m (frente al trazado R07) | Cálculo |
| NPSH | disponible 5,2–5,5 m frente a ≈ 2,2 m requeridos | R07, CANDIDATO |
| Regulación | Variador **Schneider ATV320U55N4C** (5,5 kW para el motor de 4 kW, por la reducción a 2 335 m) | R07, CANDIDATO |
| Potencia al eje con η_b = 0,55 | 3,45 kW con 24 boquillas (frente a 3,11 kW con 22) | C8 |

**Conclusión: la bomba se eligió para la red de 24 boquillas.** Se seleccionó el 20/10, después de la D-047, con el punto de C8. Le sobran unos 3–5 m, que se recortan con el variador, ajustado para que INT_5 quede en 4,00 bar. Sin variador, ese exceso subiría la presión de todas las boquillas. Si se prefiere otra regulación (por ejemplo, una válvula), hay que cuantificar ese efecto con la curva.

**Quedan abiertos [VERIFICAR]:**
- la lectura de la curva (±1 m);
- la reducción del motor de 4 kW por la altitud (dato del fabricante);
- las pérdidas reales de la T y del bloque B-MEC (C8 supuso K_T = 1 en la derivación nueva);
- la pérdida del filtro Pentair ES2 sucio, si no está ya incluida.

## 5. Qué hay que alinear en la tesis

- **La bomba.** Tu cap. 6 marca como «Seleccionada» una **Grundfos CR 10 (5 etapas, 203 L/min a 53 m)**, que es el punto de las 22 boquillas. Con 24, el punto pasa a 13,3 m³/h y 53,4 m. Hay dos salidas:
  - pasar a la **CRN 15-3 con variador** (la de Ismael, en 316 por el detergente alcalino, HPGR D-058);
  - o comprobar la CR 10 en ese punto con su curva, sin suponer que alcanza.
- **La red.** Pasa de 22 a 24 boquillas (20 × H3/8U-316SS5020 + 4 × H3/8U-316SS1520), con 221,07 L/min y 3,45 kW al eje.
- **Retorno y drenaje.** La demanda pasa a 221 L/min. R07 tiene la gravedad DN100 en ≈ 413 L/min y el drenaje F1 (HPGR D-058).
- **Tiempo de lavado.** Hay que recalcular la cara inferior con el resultado de `G3_A_O7_O4`. Hoy los 13 / 37 / 61 min salen de la cara inferior antigua.
