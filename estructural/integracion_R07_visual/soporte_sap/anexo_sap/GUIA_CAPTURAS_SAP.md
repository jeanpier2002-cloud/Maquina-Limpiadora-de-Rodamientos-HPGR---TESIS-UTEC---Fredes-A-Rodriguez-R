# Guía de capturas de SAP2000: soporte superior (D-065) y cabina (D-078)

Sigue el mismo esquema que el anexo de la mesa (`estructura_mesa/SAP_ANEXO_N3_V573/GUIA_CAPTURAS_SAP.md`).

## Capturas que ya están hechas

Se sacaron por API con `scripts/a04_captura_ventana_sap.ps1` (PrintWindow de la ventana de SAP) y están en `capturas_sap/`:

| Archivo | Qué muestra |
|---|---|
| `K0_O10R_MARCO_SOLO_01_modelo.png` | Modelo del soporte de D-065 |
| `K0_O10R_MARCO_SOLO_02_analizado.png` | Deformada de peso propio (DEAD) |
| `K0_O10R_MARCO_SOLO_03_diseno.png` | Secciones con los colores de la razón D/C de AISC 360-16: todas las barras en la franja 0–0,5 |
| `K16_ANGOSTO_X1150_MISMOS_01/02/03_*.png` | Lo mismo con los postes dentro de la cabina |
| `K14_CABINA_SOLA_T15_LINEAL_02_analizado.png` | Cabina sola de 1,5 mm: el techo se hunde dentro de la cabina por su propio peso (D-078) |

## Capturas manuales

Las vistas que SAP solo muestra desde los menús se sacan a mano.

**Preparación:**
1. Ejecuta el script, que deja SAP abierto con una copia del modelo ya analizada y diseñada (unidades kN, mm, °C):
   ```
   powershell -STA -File scripts\a03_abrir_para_capturas.ps1 -Modelo K0_O10R_MARCO_SOLO
   ```
2. Captura con `Win + Shift + S` y guarda los PNG en `capturas_sap/`, con el nombre que indica cada paso.
3. Al terminar, **cierra SAP sin guardar**.

**Atención: rigidez reducida.** Al reabrir un modelo ya diseñado, SAP lo reanaliza con la **rigidez reducida del Método de Análisis Directo** (0,8·EI y 0,8·EA, AISC 360-16 C2.3). Por eso los valores esperados de abajo son los de las tablas del anexo, no los del estudio comparativo:
- frecuencias × 0,894;
- desplazamientos × 1,25.

### Modelo K32: soporte vigente de D-080 (SHS80×4 y RHS150×100×3)

Repite los pasos 1 a 6 de K0 con `-Modelo K32_M_80x4_150x100x3`. Los números de los nudos salen de `tablas_sap/K32_M_80x4_150x100x3_api/Joint_Coordinates.csv`. Esperado, con 0,8·EI:
- D/C máximo 0,179 en una viga;
- cojinete superior en S2 ≈ 2,82 mm;
- flecha de la viga en S1 ≈ 2,47 mm (L/1000 = 4,04);
- f1 ≈ 3,35 Hz (3,74 Hz con rigidez nominal);
- momento en las bases ≤ 0,66 kN·m.

Las capturas automáticas ya están en `capturas_sap/K32_M_80x4_150x100x3_01/02/03_*.png`.

### Modelo K0: soporte de D-065 (reemplazado por D-080; se conserva para comparar)

| Nudo | Qué es |
|---|---|
| 84 | Cojinete superior (0, 0, 3450) |
| 83 | Cojinete inferior (0, 0, 2850) |
| 87 | Motor (800, 0, 3280) |
| 68 | Centro de la viga y = +300 (0, 300, 2790) |
| 39 | Centro de la viga y = −300 (0, −300, 2790) |
| 1, 6, 11 y 16 | Bases |

1. **`K0_04_DC_valores.png`: D/C con valores.**
   - Menú: `Design > Steel Frame Design > Display Design Info… > P-M Ratio Colors & Values`.
   - Esperado: máximo **0,119**, en la celosía o la planta L40×4, con U3_AYN. Todas las barras en la franja 0–0,5.
2. **`K0_05_deformada_S2_AXN.png`: deformada accidental.**
   - Menú: `Display > Show Deformed Shape` (F6), caso **S2_AXN**.
   - Clic derecho en el nudo **84**. Esperado: desplazamiento horizontal ≈ **1,23 mm** (0,99 mm con rigidez nominal).
3. **`K0_06_flecha_S1.png`: flecha de la viga en servicio.**
   - Menú: F6 con el caso **S1**.
   - Clic derecho en el nudo **68**. Esperado: U3 ≈ −1,46 mm respecto de los extremos de la viga (1,17 mm con rigidez nominal; L/1000 = 4,04 mm).
4. **`K0_07_modo1.png` a `K0_10_modo4.png`: modos.**
   - Menú: F6 con el caso **MODAL**, modos 1 a 4.
   - Esperado:
     - modo 1, 4,65 Hz, en X;
     - modo 2, 10,7 Hz, en Y;
     - modo 3, vertical;
     - modo 4, torsional, ≈ 25,5 Hz (28,5 Hz con rigidez nominal; motor ≈ 23,3 Hz [VERIFICAR]).
5. **`K0_11_reacciones_U3_AXP.png`: reacciones en las bases.**
   - Menú: `Display > Show Forces/Stresses > Joints`, caso **U3_AXP**.
   - Esperado: momento en las bases ≤ 0,77 kN·m; sin levantamiento.
6. **`K0_12_diagramas_viga.png`: diagramas de la viga.**
   - Menú: F8 con el caso **U2** y la componente **Moment 3-3**.
   - Clic derecho sobre una viga RHS160×80×5 para abrir **Diagrams for Frame Object**.

### Modelo K16: postes dentro de la cabina (x = ±1 150)

Repite los pasos 1 a 4 con `-Modelo K16_ANGOSTO_X1150_MISMOS`. Esperado:
- D/C 0,076;
- cojinete superior en S2 ≈ 1,15 mm;
- flecha en S1 ≈ 0,22 mm;
- f1 ≈ 5,2 Hz.

### Modelos de la cabina (D-078)

1. **`K14_04_deformada_S1.png`: cabina sola con el cartucho apoyado en el techo.**
   - Ejecuta con `-Modelo K14_CABINA_SOLA_T15_LINEAL`; F6 con el caso **S1**.
   - Esperado: techo de varios metros, en el análisis lineal (8,6 m en el centro).
2. **`K13_05_pandeo_muro.png`: el muro abolla bajo la viga.**
   - Ejecuta con `-Modelo K13_K9_PANDEO60`; F6 con el caso **PAND_U2**.
   - Busca el **primer modo con factor positivo** (0,24): el borde del muro abolla bajo el apoyo de la viga.
3. **`K10_06_deformada_S2.png`: la chapa como diafragma (reserva no contada).**
   - Ejecuta con `-Modelo K10_DIAF_O10_COMPLETO`; F6 con el caso **S2_AXN**.
