# DECISIONES_PARA_REGISTRAR — borradores para Ismael (CORRIDA 3, 25-26/10/2026)

> **No registradas.** Las decisiones HPGR D-0xx las registra Ismael en su `DECISIONES.md`; los números D-0xx quedan `[VERIFICAR número]`. Texto de trabajo para que Jean lo revise y se lo pase a Ismael. Las cifras CFD se completan con `03_FLUENT/resultados/` (ver `ESTADO_CORRIDA_3.md`).

## D-0xx-a · El diseño vigente O7+C2 incluye el Caso 2 (LAT_1 a −4°) `[VERIFICAR número]`
- **Decisión de Jean (25/10/2026, noche):** sí, el Caso 2 forma parte del diseño vigente.
- **Por qué:** con LAT_1 horizontal (CAD R06.3 y kit tal cual) reaparece en el OD una franja sin impacto directo cerca de z ≈ 1031–1039 mm (N1), que antes tapaba la cola del INF_EXT viejo. Ver la comparación R3_01 frente a R3_02 en el PDF de resultados.
- **Qué falta en el lado de Ismael `[INTERFAZ ISMAEL]`:** incorporar LAT_1_A/B a −4° (punta fija; eje (−0,99756; 0; −0,06976)) en el CAD R06.3 y en `boquillas_O7_C2.json`; comprobar la holgura LAT_5–LAT_1 en el CAD (en R05 subía de 12,5 a 15,3 mm, G8). El Caso 3 (SUP_2 +15 mm) sigue sin decidir para el diseño vigente (no afecta a esta tanda).

## D-0xx-b · Región en la que se evalúa el CV ≤ 0,4 del criterio D-047 `[VERIFICAR número]`
- **Abierto.** Jean no respondió; esta tanda informa **las dos**: cara inferior completa y Z3 (r 617,5–710 mm, sin contacto de PAD). Hay que fijarla con Ismael.

## D-0xx-c · O7+C2 (+ Caso 2) verificado numéricamente, no validado `[VERIFICAR número]`
- **Propuesta de texto:** «El caso Fluent del sector exterior (OD + cara inferior, 7 inyecciones) con O7+C2 y LAT_1 a −4° está **verificado** numéricamente (CORRIDA 3, 25-26/10/2026): balance de masa 0,02–0,13 % en las 7 corridas; malla con Courant de gota constante (202 616 / 430 560 / 846 960 celdas): cambio fina–base ≤ 0,63 % en D̄ y ≤ 0,004 en CV; parcelas ×0,5/×1/×2: ≤ 0,42 % en D̄ y ≤ 0,009 en CV; ramal B explícito: −0,4 % en D̄ de la cara inferior (S9 aceptable). Valor final (A+B): cara inferior D̄ 14,16, CV 0,430, D_min 7,33; Z3 D̄ 20,0, CV 0,298; OD D̄ 25,82, CV 0,648, D_min 10,5; sin zona seca (10 y 2 mm).»
- **No validado:** abanico 16,8° de la 1520 y 4 bar son HIPÓTESIS hasta el ensayo de huella (VALIDACIÓN EXPERIMENTAL PENDIENTE); la pared `trap` retiene toda gota (en la cara inferior, que mira hacia abajo, es un supuesto fuerte).
- **Consecuencias a registrar con la decisión:** el OD retrocede (D_min 14,56 → 10,5; CV 0,265 → 0,648) como precio de la mejora de la cara inferior; la boquilla C2 manda 16–17 % de su caudal al agujero.

## Aviso para Ismael (no es una decisión): error en el journal del kit `G3_A_O7_O4.jou`
- El primer `/report/dpm-sample` responde con líneas en blanco a la pregunta «Injection Name(i)» (Enter acepta el siguiente nombre por defecto) y **una línea en blanco más cierra la lista**. La base G3 tenía 6 inyecciones y 7 líneas en blanco; el kit tiene **7 inyecciones y conserva 7 líneas**, así que la séptima acepta `lat_5_a`, después «od», «cara_inf»… se leen como nombres de inyección y la lista de fronteras queda vacía. Fluent avisa «At least one boundary zone or one plane needs to be selected…» y **no escribe ninguna muestra DPM** (sin `od.dpm` ni `cara_inf.dpm`): la corrida «termina bien» pero no deja nada que post-procesar.
- Evidencia: humo R3_00, intento 1, `03_FLUENT/casos/R3_00_humo/_fallo1/R3_00_humo_transcript.txt`; corregido con 8 líneas en blanco (intento 2: 8/8 muestras).
- Consecuencia: si Ismael o Jean hubieran lanzado el kit tal cual (2–3 h), no habría salido ningún resultado. Conviene corregir el journal del kit en su origen.
