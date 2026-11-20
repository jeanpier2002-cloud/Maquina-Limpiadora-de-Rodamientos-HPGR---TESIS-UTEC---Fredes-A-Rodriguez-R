# Anexo SAP2000 del soporte superior del rotor y del motorreductor (03/11/2026)

**Estado.** Análisis EJECUTADO en SAP2000 v27.1.0 por API; diseño CANDIDATO (D-065, D-078). No apto para fabricación (D-045).

**Qué es.** La evidencia del soporte superior armada igual que el anexo de la mesa (`estructura_mesa/SAP_ANEXO_N3_V573`):
- modelos `.sdb`;
- tablas originales de SAP (Database Tables);
- un Excel por modelo;
- figuras generadas desde esas tablas;
- capturas de la ventana de SAP;
- una guía para las capturas manuales.

**Pregunta del usuario (03/11).** «¿El soporte de D-065 no es muy grande o muy ancho?»

## 0. Decisión: soporte aligerado K32 (HPGR D-080, confirmada por el usuario el 03/11)

El usuario: «hay que cambiar eso, me pueden observar por sobrediseño». Se hizo un barrido de 14 variantes en SAP con el rotor real. Los criterios son funcionales, en lugar del «no peor que el R04» de D-065:
- D/C ≤ 0,9;
- flecha ≤ L/1000;
- lateral del cojinete en el accidental ≤ 5,0 mm: la holgura del paso del eje por el techo es de 22,9 mm (CAD V17B);
- f1 ≥ 3 Hz y ningún modo con masa ≥ 5 % entre 17,6 y 26,4 Hz. El motor gira a 1,7 rpm × 2 × 388 = 1 319 rpm, es decir, 22 Hz.

`resultados_cabina/BARRIDO_DELGADO.csv` incluye también los criterios iniciales, para mostrar el cambio.

| | D-065 (K0) | **K32 elegido (D-080)** | K31 | K27 (postes dentro) |
|---|---:|---:|---:|---:|
| Postes / vigas | SHS100×5 / RHS160×80×5 | **SHS80×4 / RHS150×100×3** | SHS75×3 / RHS150×100×3 | SHS75×3 / RHS100×50×3 (inox) |
| Acero | 360 kg | **247 kg (−31 %)** | 216 kg | 149 kg |
| Costo del soporte (clase 4) | S/ 6 650 | **S/ 4 564** | S/ 3 994 | S/ 6 069 |
| D/C | 0,12 | 0,18 | 0,20 | 0,30 |
| Lateral accidental (≤ 5 mm) | 0,99 | 2,26 | 3,37 | 3,87 |
| f1 (≥ 3 Hz) | 5,20 | **3,74** | 3,10 (sin margen) | 3,22 |
| Flecha de la viga (≤ L/1000) | L/3 456 | L/2 034 | L/1 841 | L/2 146 |

- **Con el criterio que gobierna, K32 no tiene sobrediseño:** f1 queda al 80 % de su límite y el lateral al 45 %. El D/C de 0,18 es bajo porque la resistencia no gobierna.
- **Tablas de SAP del K32, con 0,8·EI:** D/C 0,179; lateral 2,82 mm; f1 3,35 Hz; flecha 2,47 mm. Las reacciones en las bases son N ≤ 3,2 kN, V ≤ 0,58 kN y M ≤ 0,66 kN·m.
- **CAD:** R07 V18 (`../../R07_V18_CAMBIOS.md`), sin solapes.
- **Presupuesto:** S/ 315 444 (`presupuesto/scripts/c3_presupuesto_v18.py`).

El análisis siguiente (§1 y §2) es el que llevó a esta decisión.

## 1. Respuesta: ¿muy grande o muy ancho?

| Variante (rotor real de D-075) | Acero | D/C | f1 | Lateral del cojinete, accidental | Flecha de la viga, servicio | Modo en 19,8–26,8 Hz (motor ±15 %) |
|---|---:|---:|---:|---:|---:|---|
| **D-065: postes en los muros, luz 4 040 (K0)** | **360 kg** | **0,12** | **5,20 Hz** | **0,99 mm** | 1,17 mm (L/3 456) | no (torsional en 28,5) |
| En los muros, perfiles livianos SHS80×4 y RHS150×100×4 (K19) | 277 kg | 0,15 | 3,66 Hz | 2,19 mm | 1,68 mm | no |
| Postes dentro de la cabina (x ±1 150), mismos perfiles (K16) | 290 kg | 0,08 | 5,84 Hz | 0,92 mm | 0,18 mm | no |
| Postes dentro, livianos SHS80×4 y RHS120×60×4 (K17) | 196 kg | 0,16 | 3,99 Hz | 2,30 mm | 0,49 mm | **sí: 20,8 Hz** |
| Postes dentro, livianos, con bases articuladas (K18) | 196 kg | 0,17 | 1,94 Hz | 9,38 mm | 0,52 mm | — |

Los valores son con rigidez nominal (`resultados_cabina/RESUMEN_CABINA.csv`); la figura A5 los compara. El criterio de D-065 es no superar el soporte anterior R04: lateral ≤ 1,20 mm y f1 ≥ 4,26 Hz.

**Lectura:**
1. **Grande por resistencia, sí:** usa el 12 % de su capacidad.
   - Lo dimensionó la **rigidez** frente a la acción accidental de 1 000 N sobre la U. Esa es una carga de mantenimiento, no de operación: en servicio, el cojinete se mueve **0,008 mm**.
   - Con perfiles más livianos y los postes en los mismos sitios (K19), se ahorran 83 kg (≈ S/ 1 500, el 0,5 % de la máquina). A cambio, el cojinete se mueve 2,2 mm en el caso accidental, más que el R04, y f1 baja a 3,7 Hz, todavía lejos de cualquier excitación.
   - Esa opción pide **relajar el criterio** de D-065 (que el lateral accidental no supere al del R04): la decisión es del usuario.
2. **Ancho, sí, pero porque los postes están en los muros de la cabina.**
   - Llevarlos junto a la mesa (K16) acorta la luz a 2,3 m, ahorra 70 kg y es más rígido. Pero:
     - **los postes quedan dentro de la zona húmeda**, así que irían en inox: ≈ S/ 7 800 frente a S/ 6 700;
     - **el techo hermético necesita 4 pasos sellados** (D-057);
     - **los muros pierden su marco**, porque D-065 usa los mismos postes para la cabina: harían falta montantes aparte, unos 96 kg;
     - la holgura con la mesa (x ±1 000), la puerta (x ±1 070) y la placa base del pedestal 09 queda justa, y habría que comprobarla en el CAD.
   - Con perfiles livianos dentro (K17), aparece un modo de 20,8 Hz en la banda del motor.
   - **No se recomienda mover los postes.**
3. **Recomendación:** mantener la geometría de D-065. Si se quiere «afinar», la única opción con sentido es K19: mismos lugares, perfiles más livianos y criterio accidental relajado.

## 2. Por qué las tablas dan otros números

Al reabrir un modelo ya diseñado, SAP lo reanaliza con la **rigidez reducida del Método de Análisis Directo** (0,8·EI y 0,8·EA, AISC 360-16 C2.3). El anexo de la mesa hizo lo mismo (D-048). Por eso, frente al estudio comparativo, que usa rigidez nominal:
- las frecuencias de las tablas bajan en √0,8;
- los desplazamientos suben en 1/0,8.

| Indicador (Excel, hoja 00_CONTROL) | K0 con 0,8·EI | K0 nominal | K16 con 0,8·EI | K16 nominal |
|---|---:|---:|---:|---:|
| D/C máximo | 0,119 | 0,120 | 0,076 | 0,077 |
| Lateral del cojinete en S2 (mm) | 1,233 | 0,988 | 1,148 | 0,920 |
| f1 (Hz) | 4,65 | 5,20 | 5,23 | 5,84 |
| Flecha de la viga en S1 (mm) | 1,455 | 1,169 | 0,224 | 0,181 |

Con 0,8·EI, la referencia R04 sería de 1,50 mm y 3,81 Hz, así que la comparación no cambia.

## 3. Contenido

| Carpeta o archivo | Qué es |
|---|---|
| `modelos/K*_<hora>/` | Copias de los modelos de `../modelos_cabina/`, analizadas y diseñadas |
| **Modelo vigente (D-080): `tablas_sap/K32_M_80x4_150x100x3_api/`, `SAP_SOPORTE_K32_M_80x4_150x100x3_export.xlsx`, `figuras/A1_modelo_K32.png`, `A2_DC_D065_y_K32.png`, `A3_deformada_accidental.png` (D-065 frente a K32), `A4_modos_K32.png`, `A5_variantes_tamano_ancho.png` (barrido completo) y `capturas_sap/K32_*.png`** | Evidencia del soporte K32. Las figuras `A1_modelo_D065.png`, `A2_DC_D065_y_postes_dentro.png` y `A4_modos_D065.png` son de la primera versión del anexo, con D-065 |
| `tablas_sap/K0_O10R_MARCO_SOLO_api/` y `K16_ANGOSTO_X1150_MISMOS_api/` | 24 tablas originales de SAP en CSV: geometría, secciones, cargas, combinaciones, desplazamientos, reacciones, fuerzas en barras (11 616 filas), modos, pandeo y diseño AISC 360-16 |
| `SAP_SOPORTE_K0_O10R_MARCO_SOLO_export.xlsx` y `SAP_SOPORTE_K16_ANGOSTO_X1150_MISMOS_export.xlsx` | Excel de 12 hojas: control y resumen, nudos, barras, secciones y material, cargas y combinaciones, desplazamientos, reacciones, fuerzas, diseño, modos, pandeo y todas las variantes |
| `figuras/A1_modelo_D065.png` | Modelo con secciones y la cabina de referencia |
| `figuras/A2_DC_D065_y_postes_dentro.png` | Barras coloreadas por D/C |
| `figuras/A3_deformada_accidental.png` | Deformada S2 más desfavorable, ×300 |
| `figuras/A4_modos_D065.png` | Modos 1 a 4 |
| `figuras/A5_variantes_tamano_ancho.png` | Comparación de las variantes |
| `capturas_sap/` | Capturas de la ventana de SAP: modelo, deformada de peso propio y colores de diseño, para K0, K16 y la cabina sola K14 |
| `GUIA_CAPTURAS_SAP.md` | Capturas manuales que faltan (deformadas S1/S2, modos, reacciones, diagramas y pandeo del muro), con nudos y valores esperados |
| `scripts/a01_tablas_sap.ps1` | Exporta las tablas |
| `scripts/a02_excel_y_figuras.py` | Arma el Excel y las figuras |
| `scripts/a03_abrir_para_capturas.ps1` | Deja SAP abierto para las capturas manuales |
| `scripts/a04_captura_ventana_sap.ps1` | Capturas automáticas |

Informes de origen:
- `../INFORME_SOPORTE_SAP.md` (D-065, 11 alternativas O1–O11, con la masa del rotor de R03);
- `../INFORME_CABINA_COMO_ESTRUCTURA_2026-11-03.md` (D-078, casos K0–K19, con el rotor real).

## 4. Limitaciones

- El cartucho, la ménsula y el motor se modelan como cuerpo rígido.
- Las bases son ideales: empotradas o articuladas.
- Las cargas son envolventes de R03 con el rotor real.
- No hay análisis de fatiga.
- Las secciones son rectangulares de esquina recta (SetTube) [VERIFICAR con tablas comerciales].
- Las variantes con postes dentro no tienen comprobación de interferencias en el CAD.
- Los costos son estimaciones de clase 4 (C1).
