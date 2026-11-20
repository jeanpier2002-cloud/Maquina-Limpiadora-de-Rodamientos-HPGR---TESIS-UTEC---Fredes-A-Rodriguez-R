# Verificación de la unión atornillada del amarre U1/U3 (VDI 2230 + EN 1993-1-8) — 20/10/2026

**Estado:** EJECUTADO (cálculo manual de cribado; script `scripts/r061_vdi2230_amarre_v573.py`, salida `VERIFICACION_PERNOS_AMARRE_V573.json`).

**Hipótesis de partida:**
- material de las piezas A36 (Fy 250 / Fu 400);
- precarga, μ, par de apriete y su dispersión;
- valores de tabla de las normas marcados **[VERIFICAR contra la norma]**: no hay copia de VDI 2230 ni de ISO 4017/7089 en `04_REFERENCIAS`.

Nada aquí es definitivo ni está liberado para fabricación.

**Qué cubre:** la parte que faltaba tras el FEM de contacto (`INFORME_FEM_CONTACTO_V573_2026-10-19.md`):
- montaje y par de apriete;
- precarga admisible;
- asentamiento;
- resistencia del perno;
- presión bajo cabeza y tuerca;
- fuerza residual;
- deslizamiento;
- respaldo por aplastamiento si se perdiera el rozamiento.

**Antecedentes reutilizados:**
- **Cargas y brazos** de K6 (`codex_k2m/K6_despegue_union_BW.out.txt`): vuelco de 601 N·m en U1 y 574 N·m en U3 respecto de Z662; brazo perno–talón de 24 mm.
- **V6** (`codex_k2m/V6_amarre_v572.out.txt`), cuyo cribado era para la posición antigua del amarre (X = a ± 40, Z = 783). Se rehace aquí con la geometría v5.7.2b (X = 388 ± 90, Z = 766,5) y las fuerzas del FEM de contacto.

## 1. Respuesta corta

1. **Especificación propuesta (HIPÓTESIS de diseño, para planos):**
   - M12 clase 8.8 con tuerca clase 8;
   - **arandelas templadas ISO 7089 de Ø24 bajo la cabeza y bajo la tuerca** (obligatorias, ver punto 3);
   - **par de apriete de 62 N·m con llave dinamométrica** y rosca ligeramente aceitada (μ = 0,10–0,16).

   Con eso, la precarga de montaje queda entre **23,6 y 37,8 kN**. El máximo es el 86 % de la admisible por VDI 2230 (44,2 kN), así que el perno no se sobrecarga al apretar.
2. **Perno en servicio:** la tensión equivalente es 501 MPa, el **78 % de Rp0,2**, aun suponiendo que todo el vuelco lo toman los pernos transversales. El FEM da un ΔF ≤ 75 N, con lo que la tensión alterna es de 0,45 MPa: la fatiga es despreciable.
3. **Presión superficial:**
   - **con arandela**, sobre la pieza: 132 MPa ≤ 490 MPa ✓;
   - **sin arandela**, cabeza directa sobre la pieza: **549 MPa > 490 MPa ✗**.

   Por eso las arandelas son un **requisito**. Bajo la cabeza, sobre la arandela, hay 482 MPa: la arandela debe ser templada (ISO 7089, 300 HV) [VERIFICAR la presión límite de la arandela]. El pico de 243 MPa del FEM en la contraplaca C es este mismo aplastamiento de precarga: la corona del FEM reparte 26 kN en 119 mm², unos 218 MPa de media.
4. **Deslizamiento.** El FEM de contacto es la referencia: deslizamiento ≤ 0,006 mm con 26 y con ≈ 16 kN. A mano:
   - **modelo por componentes**, con μ = 0,20: margen **3,97** (1,99 con μ = 0,10);
   - **modelo conservador** de K6/V6, con μ = 0,20: margen 1,79; con μ = 0,10, 0,89 ✗.

   Con la precarga mínima anterior (15,6 kN) el modelo conservador no cumple ni con μ = 0,20 (0,87). Conviene **subir la precarga mínima de diseño a ≈ 23,6 kN** (la del par especificado) y pedir **superficies de contacto limpias, secas y sin pintura** (μ ≥ 0,20, clase D de EN 1090-2), o cepilladas (clase C, μ = 0,30).
5. **Si se perdiera el rozamiento, la unión no falla:** los pernos se apoyan en el alma y el respaldo por aplastamiento tiene un margen de **29,5**. La consecuencia es **funcional**: antes de apoyarse, la mordaza puede moverse hasta el juego del taladro (1,5 mm diametral). Proyectado sobre la dirección radial de U1, eso es **0,66 mm**, casi todo el margen de 0,91 mm de D-019 en NOM_V2. **El deslizamiento se evita para conservar la precisión, no para que la unión resista.**
6. **Apertura del labio** (método K6 con la precarga mínima nueva menos el asentamiento): M_serv / M_decomp = **0,72 en U1 y 0,69 en U3** (< 1 ✓).

## 2. Datos

| Dato | Valor | Fuente / estado |
|---|---|---|
| Rosca M12 × 1,75 | d2 = 10,863; d3 = 9,853; A_S = 84,27 mm² | ISO 724 (fórmulas); el FEM usa 84,3 |
| Clase 8.8 | Rp0,2 = 640 MPa; Rm = 800 MPa | ISO 898-1 (d ≤ 16 mm) |
| Apoyo de cabeza y tuerca | d_w = 16,63 mm | ISO 4017 / 4032, grado A [VERIFICAR] |
| Taladro | Ø13,5 (juego medio) | ISO 273; CAD v5.7.2b |
| Arandela | ISO 7089 M12: 13 / 24 × 2,5 mm | ISO 7089 |
| Piezas | A36: Fy 250 / Fu 400 MPa; presión límite p_G = 490 MPa | HIPÓTESIS del proyecto (`r061_calculo_manual_v57.py` l.17); p_G de S235 según la tabla A9 de VDI 2230 [VERIFICAR] |
| Alma del W6x9 | t_w = 4,318 mm | AISC |
| Rigidez del perno | 448 226 N/mm (vertical, agarre 28) y 361 659 N/mm (transversal, agarre 37) | E·A_S/(agarre + 0,8d), igual que el FEM |
| Rozamiento rosca / apoyo | μ_G = μ_K = 0,10–0,16 | HIPÓTESIS; depende del recubrimiento y la lubricación [VERIFICAR con el suministro] |
| Dispersión del apriete | α_A = 1,6 (llave dinamométrica) | Tabla A8 de VDI 2230 [VERIFICAR] |
| Asentamiento | f_Z = 3 (rosca) + 2 × 2,5 (apoyos) + 4 × 1,5 (juntas internas) = 14 µm | Tabla 5 de VDI 2230, Rz < 10 µm [VERIFICAR] |
| Cargas | \|F\| = 2 121 N (Fx = 544, Fy = 2 050), Mz = 124,07 N·m; vuelco de 601 / 574 N·m respecto de Z662 | FEM de contacto v5.7.3 (ENV208); K6 |
| Coeficientes parciales | γ_M2 = γ_M3 = 1,25 | EN 1993-1-8 |

## 3. Cálculo

**Montaje (VDI 2230).**

Precarga admisible de montaje:

F_M,zul = A_S·ν·Rp0,2 / √{1 + 3[(3/2)(d2/d_S)(P/(π·d2) + 1,155·μ_G)]²}, con ν = 0,9

Da 44,19 kN con μ_G = 0,10 y 43,11 kN con μ_G = 0,12.

Par de apriete:

M_A = F_M·[0,16·P + 0,58·d2·μ_G + μ_K·D_Km/2], con D_Km = (d_w + 13)/2 (cabeza sobre arandela)

- Para 26 kN con μ = 0,12 hacen falta 50,0 N·m.
- Con el par de referencia del proyecto, 62,4 N·m (V6), la precarga queda entre:
  - **F_M,max = 37,8 kN** (μ = 0,10), que es el 86 % de F_M,zul ✓;
  - F_M,min = 25,2 kN, según el rango de μ.
- Con α_A = 1,6, F_M,min = 37,8 / 1,6 = **23,6 kN**. Se adopta el menor de los dos.

**Asentamiento** (cota superior, despreciando la flexibilidad de las piezas): F_Z ≤ f_Z·k_b = **5,06 kN** (transversal) y **6,28 kN** (vertical). En la realidad es menor, porque las piezas también ceden.

**Servicio y perno.** Fuerza separadora en cada perno transversal, suponiendo de forma conservadora que todo el vuelco va a ellos:

F_A = 601 N·m / (766,5 − 662 mm) / 2 = 2,88 kN

- **F_S,max** = 37,8 + 2,88 = 40,7 kN.
- **Tensión equivalente** (k_τ = 0,5): σ_red = 501 MPa = 0,78·Rp0,2 ✓.
- **El FEM da ΔF ≤ 75 N:** Φ efectivo ≈ 0 y σ_a = 0,45 MPa.

**Presión superficial** (con F_S,max = 40,7 kN):

| Apoyo | Área (mm²) | p (MPa) | Límite |
|---|---|---|---|
| Arandela Ø24 sobre la pieza | 309 | **132** | 490 ✓ |
| Cabeza sobre la arandela | 84,5 | 482 | arandela templada [VERIFICAR] |
| Cabeza directa sobre la pieza, sin arandela | 74,1 | **549** | 490 ✗ |

**Fuerza residual del amarre transversal:** F_K,min = F_M,min − F_Z − F_A = 23,6 − 5,06 − 2,88 = **15,7 kN por perno**.

**Deslizamiento, modelo A (conservador, como V6/K6).** La demanda de rozamiento en una sola cara del alma es |F| + Mz/s = 2,121 + 124,07/0,180 = **2,81 kN**. La capacidad es F_s = n·μ·ΣF_K/γ_M3.

| Precarga de montaje | μ = 0,10 | μ = 0,15 | μ = 0,20 | μ = 0,30 |
|---|---|---|---|---|
| Par de 62,4 N·m (F_M,min = 23,6 kN) | 0,89 ✗ | 1,34 | 1,79 | 2,68 |
| Hipótesis anterior, 15,6 kN | 0,44 ✗ | 0,65 ✗ | 0,87 ✗ | 1,31 |
| Nominal, 26 kN | 1,03 | 1,54 | 2,06 | 3,08 |

Con dos caras de rozamiento (A–alma y alma–B) los márgenes se duplican.

**Deslizamiento, modelo B (por componentes).** En la cara B–alma (plano XZ) solo son tangenciales Fx y el momento M_Y = Fx·(955 − 766,5) = 102,6 N·m. Fy es normal al alma y ya está en F_A. La demanda por perno es √[(Fx/2)² + (M_Y/s)²] = **0,63 kN**, y la capacidad, μ·F_K,min/γ_M3:

| | μ = 0,10 | μ = 0,15 | μ = 0,20 | μ = 0,30 |
|---|---|---|---|---|
| Margen | 1,99 | 2,98 | **3,97** | 5,96 |

No se cuenta el rozamiento del labio ni del talón.

**FEM de contacto (referencia).**
- Deslizamiento p99 ≤ 0,006 mm, con μ = 0,20 y precarga de 26 kN o de ≈ 16 kN.
- La unión no se abre; ΔF ≤ 75 N.

El reparto real del vuelco va sobre todo al labio y al talón, no a los pernos transversales. Por eso los modelos manuales A y B son cotas conservadoras.

**Apertura del labio** (método K6): M_decomp = 2·F_K,v·24 mm, con F_K,v = 23,6 − 6,28 = 17,3 kN, da 833 N·m. Cociente 601/833 = **0,72** (U1) y 574/833 = **0,69** (U3).

**Respaldo por aplastamiento** (EN 1993-1-8, tabla 3.4):
- aplastamiento en el alma: F_b,Rd = 2,5·1·400·12·4,318/1,25 = 41,5 kN por perno;
- cortante del perno: F_v,Rd = 0,6·800·84,27/1,25 = 32,4 kN por plano.

Con 2 pernos la capacidad es 82,9 kN frente a 2,81 kN: margen **29,5**. Antes de llegar al apoyo, la mordaza puede deslizar hasta 1,5 mm (juego diametral). Proyectado sobre la dirección radial de U1 (er_x = 0,441), son **0,66 mm**.

**Distancias a bordes** (EN 1993-1-8, tabla 3.3, mínimo 1,2·d0 = 16,2 mm):
- **Pernos transversales:** 25 mm en X (collar a ± 115, pernos a ± 90; REQ573) y 20 mm en Z (borde superior del collar en Z786,5; INFORME_K2M_V57 §10) ✓.
- **Pernos verticales:** e2 = 28 mm (labios hasta qc ± 88; INFORME_K2M_V57 §10) ✓.

## 4. Qué cambia y qué queda

**Para los planos y la especificación** (HIPÓTESIS de diseño, a ratificar):
- M_A = 62 N·m con llave dinamométrica;
- arandelas templadas ISO 7089 bajo la cabeza y bajo la tuerca;
- superficies de contacto limpias, secas y sin pintura (μ ≥ 0,20), o cepilladas (μ = 0,30);
- precarga mínima de diseño de **23,6 kN** (antes 15,6 kN).

**[VERIFICAR]:**
- valores de tabla (d_w, p_G, f_Z, α_A) contra las normas;
- μ real con el agua alcalina de lavado. Con μ = 0,10, el modelo A no cumple y el modelo B y el FEM sí;
- presión límite de la arandela templada.

**[PENDIENTE]:**
- método de apriete y retención de la tuerca para fabricación;
- casos U1 s− y U3 s+ del FEM.

**Con rigor de tesis:** la unión es **resistente con mucho margen**. El requisito que gobierna es **funcional**: que no deslice, porque un deslizamiento de hasta 0,66 mm radiales consumiría casi todo el margen de D-019. Por eso se especifican el par, las arandelas y las superficies.
