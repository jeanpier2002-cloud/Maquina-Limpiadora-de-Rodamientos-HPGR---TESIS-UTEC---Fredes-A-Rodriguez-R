# Soporte superior K32: sismo E.030, placas base, anclajes y uniones (03/11/2026)

**Estado.** Cálculo EJECUTADO; diseño CANDIDATO. **HPGR D-081**, confirmada por el usuario el 03/11 («de igual manera lo que tú recomiendas»). No apto para fabricación (D-045).

## 1. Qué se resolvió

El soporte K32 (D-080) tiene bases empotradas y uniones viga–poste rígidas en el modelo. Faltaba:
- el **sismo**, que no se había revisado nunca;
- las **placas base y los anclajes** a momento;
- las **soldaduras** y el **detalle de la unión viga–poste**.

## 2. Sismo: NTE E.030-2018, método estático equivalente (art. 4.5)

| Parámetro | Valor | Fuente |
|---|---|---|
| Z (zona 4, Lima) | 0,45 | Tabla N.° 1 |
| U (edificación común, categoría C) | 1,0 | Tabla N.° 5 [HIPÓTESIS: planta industrial sin riesgo adicional] |
| S y TP (suelo S2) | 1,05 y 0,6 s | Tablas N.° 3 y 4 [HIPÓTESIS: no hay estudio de suelo; S2 es más conservador que S1] |
| T del soporte | 1/f1 = 1/3,74 = 0,27 s < TP | modelo SAP |
| C | 2,5 | art. 2.5 |
| R = R0 · Ia · Ip | 4 · 1 · 1 = 4 | Tabla N.° 7: acero, pórticos ordinarios resistentes a momento y arriostrados concéntricos: R0 = 4 |
| **V/P = Z·U·C·S/R** | **0,295** (C/R = 0,625 ≥ 0,11) | art. 4.5.2 |
| Sismo vertical | ±2/3 del horizontal = ±0,197·P | art. 6.5, equipos |

Fuente de la norma: traducción al inglés de la E.030-2018 publicada por el IISEE (Building Research Institute, Japón). [VERIFICAR contra el texto oficial en español de la RM N.° 355-2018-VIVIENDA].

**Aplicación en SAP** (modelo K34 = K32 con `sismo=0.2953`):
- fuerzas de 0,295 × peso en cada masa: cartucho, ménsula y motor;
- **rotor en su centro de gravedad real** (z 2 208, de `MASAS_ROTOR_V15B.json`), con el momento que genera respecto del cojinete inferior;
- peso propio de las barras como carga repartida.

**Combinaciones:**
- U4 = 1,397 D + BELT + TORQ ± E;
- U5 = 0,703 D ± E;
- S3 = D + BELT + TORQ + E, para los desplazamientos.

**Resultados** (`resultados_cabina/K34_K32_SISMO_E030.json` y tablas SAP en `anexo_sap/tablas_sap/K34_K32_SISMO_E030_api/`):
- barras: D/C máx. 0,18, que sigue gobernado por el caso accidental; con sismo, los postes llegan a 0,17;
- **desplazamiento del cojinete superior con S3_SX: 4,22 mm elástico → 0,75·R = 3 veces → 12,6 mm inelástico, menor que la holgura de 22,9 mm** del paso del eje por el techo. En Y son 0,40 mm, porque la celosía arriostra;
- bases: N hasta 6,8 kN de compresión; **levantamiento de hasta 2,85 kN** (U5 con sismo en Y); M ≤ 1,07 kN·m y V ≤ 0,91 kN.

## 3. Anclajes: ACI 318-19, cap. 17

**Hipótesis** (las mismas que D-073):
- losa de 200 mm con f'c = 21 MPa, fisurada y sin bordes cercanos [HIPÓTESIS: dato de planta pendiente];
- anclaje adhesivo de varilla A4-70, tratada como frágil (φ 0,65 en tracción y 0,60 en corte);
- φ = 0,55 para adherencia y cono (condición B, categoría 2).

**Sismo** (ACI 17.10, porque el sismo aporta más del 20 % de la tracción):
- la tracción sísmica se amplifica por **Ω0 = 3** (17.10.5.3 d) [HIPÓTESIS: la E.030 no define Ω0; 3 es el de pórticos ordinarios de acero en ASCE 7];
- las resistencias gobernadas por el concreto o la adherencia se multiplican por **0,75** (17.10.5.4).

**Placa rígida:** la compresión se ubica a 0,9 de la media placa, como en D-073. La tracción de cada anclaje se calcula con la carga axial y los dos momentos simultáneos.

**Demandas:** las reacciones simultáneas de cada base y cada combinación salen de la tabla `Joint_Reactions.csv` exportada de SAP: 4 bases, U2, U3, U4 y U5, estas dos con Ω0.

**Resultados** (`scripts/s07_placas_base_k32.py` → `resultados_cabina/CALCULO_PLACAS_BASE_K32.json`):

| Configuración (4 anclajes por base) | D/C con la adherencia mínima de ACI (1,4 MPa) | Adherencia del producto requerida para D/C ≤ 1 | Caso que gobierna |
|---|---:|---:|---|
| M12, h_ef 100, placa 200 | 3,98 | 5,56 MPa | U4 con −SX y Ω0, base 6 |
| M12, h_ef 110, placa 250 | 2,44 | 3,42 MPa | ídem |
| **M16, h_ef 125, placa 250 × 250 × 12 (elegida)** | 1,83 | **2,56 MPa** | ídem |
| M16, h_ef 150, placa 250 | 1,52 | 2,13 MPa | ídem |

**Lectura:**
- La adherencia mínima de ACI (tabla 17.6.5.2.5) es un valor genérico para no depender de un producto. El D-073 quedó en 0,98 por la misma razón.
- Un adhesivo calificado para sismo (ACI 355.4 / ETA, categorías C1/C2) da valores **varias veces mayores** [VERIFICAR con la ficha del producto elegido].
- **El requisito queda al producto:** adherencia característica en concreto fisurado, con calificación sísmica, **≥ 2,6 MPa** para M16 con h_ef 125.
- Se elige **M16**, el mismo diámetro y la misma familia de adhesivo que los pedestales del riel, para que toda la máquina use un solo producto.

**El corte no gobierna:** D/C ≤ 0,08.

## 4. Placa base y soldadura poste–placa

- **Placa** (AISC Design Guide 1): la fila traccionada carga un voladizo de 45 mm desde la cara del SHS80.
  - Con la tracción máxima por anclaje (5,7 kN con Ω0), el espesor requerido es **7,1 mm**.
  - Se adopta **12 mm** (antes eran 20): queda rígida (t/m = 0,27) y se ahorran 16 kg.
- **Soldadura poste–placa:** filete **a3 en todo el contorno** del SHS80, por el método elástico de líneas.
  - Esfuerzo máximo de 65,7 MPa frente a φRn = 0,75 × 0,6 × 482 = 216,9 MPa (AISC J2.4, E70XX): **D/C 0,30**.

## 5. Unión viga–poste

**Fuerzas máximas** en el nudo, de `Element_Forces_Frames.csv` de SAP, en todas las combinaciones últimas con sismo:
- M = 1,28 kN·m;
- V = 2,4 kN;
- T = 0,29 kN·m;
- P = 1,6 kN.

**Detalle:**
- la **viga RHS150×100×3 pasa continua sobre el poste**;
- **placa de cabeza de 120 × 120 × 10** en el extremo del SHS80, con a3 en todo el contorno del poste;
- la viga se suelda a la placa con a3 en todo el contorno de su apoyo (100 × 100 mm).

El detalle evita que la viga, de 100 mm de ancho, quede de canto contra un poste de 80 mm.

**Verificación:**
- **weld poste–placa:** σ = M/S_w + P/A_w = 1,28·10⁶ / 18 100 + 2 400 / 679 ≈ 74 MPa → **D/C 0,34**;
- **weld viga–placa:** S_w = (100 · 100 + 100²/3) · 0,707 · 3 = 28 280 mm³ → σ ≈ 45 MPa → **D/C 0,21**.

En el modelo, el nudo es rígido en el eje de la viga, lo que es coherente con este detalle.

## 6. Cómo defender esta decisión

**«¿En qué te basaste?»:**
- **Cargas:**
  - sismo según la **E.030-2018**, con sus tablas y el método estático equivalente;
  - caso accidental de R03;
  - reacciones de SAP2000 con el **Método de Análisis Directo** de AISC 360-16.
- **Anclajes:** **ACI 318-19, cap. 17**, incluida la sección sísmica 17.10 (Ω0 y 0,75).
- **Placa:** **AISC Design Guide 1.**
- **Soldaduras:** **AISC 360-16 J2.4.**

**«¿Qué pruebas hiciste?»:**
- **Numéricas:** modelo SAP2000 con sismo, con 248 reacciones por base y combinación exportadas de sus tablas.
- **Barrido de 5 configuraciones**, para mostrar cómo cambia la exigencia al producto.
- **Verificación a mano del orden de magnitud:**
  - cortante sísmico total ≈ 0,295 × 7,2 kN = 2,1 kN, unos 0,53 kN por poste;
  - en un pórtico con bases empotradas, M_base ≈ V·h/2 = 0,53 × 2,79 / 2 ≈ 0,74 kN·m, frente a 1,07 kN·m de SAP;
  - la diferencia viene de que SAP suma la gravedad excéntrica del motor y la rigidez reducida;
  - el orden coincide.
- **La adherencia no se ensaya en esta tesis:** la garantizan los **ensayos de calificación del producto** (ACI 355.4 / EAD 330499, con ensayos sísmicos C1/C2), que el fabricante certifica en su ESR o ETA.
  - La tesis fija el valor mínimo que el producto debe cumplir.
  - Como trabajo futuro (D-045) queda una prueba de carga de un anclaje instalado (proof load).

**Lo que hay que admitir:**
- suelo, losa y uso supuestos;
- Ω0 tomado de ASCE 7 porque la E.030 no lo define;
- traducción de la norma no oficial [VERIFICAR];
- **los pedestales del riel (D-073) todavía no tienen revisión sísmica** (pendiente).
