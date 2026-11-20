# FEM de contacto del amarre U1/U3 (v5.7.3, mordaza v5.7.2b): CalculiX y contraste en SOLIDWORKS — 19/10/2026

**Estado:** EJECUTADO (simulación). Son resultados de **cribado**, con HIPÓTESIS de precarga, material y rozamiento, y sin validación experimental (D-045: la tesis decide con simulación y bibliografía). Nada aquí es definitivo ni está liberado para fabricación.

**Preguntas:**
- ¿Cuánto se mueve el datum U1/U3 (alojamiento del pivote, cota Z955) bajo la carga del rodillo de 2,08 kN cuando la mordaza v5.7.2b trabaja como unión **atornillada con contacto y rozamiento**, y no como cuerpo pegado?
- ¿Se abre o desliza la unión?
- ¿Cambia el presupuesto D-019/D-031?

## 1. Respuesta corta

1. **La unión no se abre ni desliza.**
   - Apertura máxima: 0,016 mm.
   - Deslizamiento p99: ≤ 0,006 mm.
   - La fuerza de los pernos varía como mucho 75 N sobre 26 kN, en todas las mallas y casos.
   - Con la precarga mínima de unos 16 kN, el desplazamiento cambia +0,5 %.
2. **El contacto añade entre 6 y 8 % de flexibilidad** respecto de las mismas superficies pegadas, comparando a igual malla.
   - El cociente crece al refinar: 1,061, 1,069 y 1,078.
   - Extrapolado da 1,128; se adopta **1,13** (conservador).
3. **Soporte local (FEM de 800 mm):**
   - Con contacto, 1,13 × FEM pegado v5.7.2b da **0,667 mm en U1 s+** y entre 0,54 y 0,62 mm en los demás casos.
   - Cumple el criterio de ≤ 1,0 mm.
   - No cumple el objetivo de 0,5 mm (REQ573 §6.2, D-034).
4. **δ_local del presupuesto** = FEM 800 con contacto − viga de Vlasov de 800 mm impedida, porque la parrilla global ya incluye la viga.
   - U1 s+ 0,379 mm, U1 s− 0,359 mm, U3 s+ 0,345 mm y U3 s− 0,368 mm.
   - Con el FEM pegado v5.7.1 eran 0,353, 0,333, 0,319 y 0,341 mm; el aumento es de 7 a 8 %.
5. **Presupuesto NOM_V2:**
   - LIBRE: A = **4,09 mm ✓** (antes 4,06) y B conservador = **6,44 mm ✓** (antes 6,48).
   - IMPEDIDO: A = 3,02 ✓ y B = 7,30 ✓.
   - La sensibilidad ENV208 LIBRE sigue fallando en A (5,18 ✗, antes 5,15 ✗) y B queda en 5,04 ✓, justo en el límite.
6. **Los valores absolutos con C3D4 no han convergido.**
   - Van de 0,464 a 0,511 mm con 23 000 a 55 000 nodos.
   - Por eso el resultado se apoya en el cociente a igual malla y en el FEM pegado fino.
   - **SOLIDWORKS confirma esa base pegada** con tetraedros de 2.º orden: 0,574, 0,580 y 0,586 mm con mallas de 8, 6 y 4 mm (hasta 735 000 nodos), frente a 0,590 mm de CalculiX; diferencia −0,7 %.
   - La variante de SOLIDWORKS con contacto **no convergió** en un solo paso (§6).
7. **Hallazgo de diseño:** la retención axial de la mordaza sobre el W depende solo del rozamiento por precarga; sin rozamiento, el modelo es un mecanismo.
   - Hay que verificar la capacidad a deslizamiento y el control de apriete [VERIFICAR].

## 2. Modelo CalculiX

| Aspecto | Valor | Estado |
|---|---|---|
| Geometría | Copia `R061_K2M_V573_COPIA.FCStd` del CAD candidato v5.7.3. Cuatro cuerpos: tramo W6x9 de 800 mm con taladros Ø13,5 (W), mitades del collar A y B, contraplaca C | CANDIDATO |
| Malla | Cuatro submallas independientes de tetraedros lineales C3D4 (gmsh). Refinamiento local h_local en las aristas circulares de los taladros | 3 niveles |
| Uniones | Siete parejas superficie a superficie: almas A/B, labios A/B, ala–contraplaca y talones A/B. Penalización K = E/h_local (80 000–100 000 N/mm³). Rozamiento μ = 0,20 | HIPÓTESIS (μ) |
| Pernos | 4 verticales y 2 transversales M12 8.8 (A_s = 84,3 mm²). Resorte axial no lineal SPRINGA (F = P0 + k·e; 0 si se afloja). Rigidez k = E·A_s/(agarre + 0,8d) = 448 404 N/mm (verticales) y 361 803 N/mm (transversales). Acoplamientos cinemáticos en las coronas de cabeza (r 6,7–9,1) y arandela (r 6,7–12,1). Sin contacto perno–agujero | HIPÓTESIS |
| Precarga | 26 kN por perno, calibrada: resorte = 26 000/0,635 en los verticales y 26 000/0,912 en los transversales; lograda 25,9–26,6 kN. Caso mínimo ≈ 16 kN (REQ573: 26 kN nominal, 15,6 kN mínimo) | HIPÓTESIS |
| Material | Acero E = 200 000 MPa, ν = 0,30, elástico lineal, sin certificar | HIPÓTESIS |
| Apoyos | Extremos del tramo W (X −12 y 788) empotrados en traslaciones; igual que el FEM pegado v5.7.1/v5.7.2b | idealización |
| Carga | ENV208: 2,08 kN normal con rozamiento del rodillo 0,20 (U1, s = +1, θ = 60°). F = (544,1; 2 050,2; 0) N, con resultante en el eje del pivote a Z955, repartida entre los casquillos Z817–837 y Z910–930. Par del pivote Mz = −124,07 N·m, como par de fuerzas en el limitador (r = 20 y 70 mm, Z753–762). U3 con s = −1. Misma carga y geometría del rodillo que los FEM pegados v5.7.1 y v5.7.2b | DATO de cribado |
| Pasos | 1) solo precarga; 2) precarga + carga del rodillo | — |
| Magnitud informada | u radial del alojamiento: nudos a r < 20,5 mm del eje del pivote, base Z811–825 y cabeza Z920–934, extrapolado a Z955. **Se informa solo el efecto de la carga (paso 2 − paso 1).** La precarga sola mueve el alojamiento entre −0,004 y −0,008 mm | — |

## 3. Resultados de contacto

| Corrida | h / h_local (mm) | Nodos | u carga Z955 (mm) | Giro (mrad) | Pernos fin paso 2 (kN) | ΔF perno máx. (N) | Apertura máx. (mm) | Desliz. p99 (mm) | Equil. M |
|---|---|---|---|---|---|---|---|---|---|
| U1 s+ | 12 / 2,5 | 23 039 | 0,4635 | 2,24 | 25,9–26,2 | 51 | 0,014 | 0,005 | 0,94 % |
| U1 s+ | 9 / 2,5 | 32 497 | 0,4823 | 2,32 | 26,0–26,6 | 55 | 0,014 | 0,005 | 0,98 % |
| U1 s+ | 7 / 2 | 54 533 | 0,5112 | 2,45 | 26,0–26,5 | 57 | 0,016 | 0,006 | 1,00 % |
| U3 s− | 9 / 2,5 | 32 075 | 0,4469 | 2,19 | 26,0–26,7 | 68 | 0,014 | 0,005 | **1,05 %** [VERIFICAR] |
| U1 s+, P0 ≈ 16 kN | 9 / 2,5 | 32 497 | 0,4847 | 2,32 | 15,5–16,9 | 73 | 0,009 | 0,006 | 0,61 % |

**Equilibrio.**
- Las fuerzas cierran a 2·10⁻⁶.
- Los momentos cierran entre 0,6 y 1,3 % (criterio: 1 %), tanto con contacto como pegado.
- El error aparece igual en la variante pegada lineal, así que no viene del contacto y no afecta al cociente. Causa [VERIFICAR].

**Parejas de contacto (malla de 7 mm).**
- Cobertura de proyección: entre 89 y 95 %. En los talones baja al 64 %, porque sus franjas de 8 mm tienen nudos fuera del parche maestro.
- Apertura máxima: 0,016 mm, en el ala–contraplaca.
- Presión de contacto máxima: 445 MPa en el ala y unos 365 MPa en los talones. Son picos puntuales en bordes, propios del contacto por penalización con C3D4 [VERIFICAR; no es criterio de fallo].

**Von Mises (malla de 7 mm).**
- W: p99 35 MPa, máximo 57 MPa.
- A y B: p99 entre 60 y 74 MPa, máximo 111 MPa.
- C: p99 143 MPa, máximo 243 MPa; 118 nudos superan 150 MPa.
  - Esa concentración está bajo la corona de la cabeza del perno: es el aplastamiento por la precarga de 26 kN sobre unos 39 mm² del acoplamiento.
  - Con precarga de unos 16 kN, C baja a un máximo de 119 MPa.
  - Falta verificar la presión bajo cabeza con VDI 2230 (p_G según el material de C) [VERIFICAR]. *(20/10, `VERIFICACION_PERNOS_AMARRE_V573.md`: sin arandela, 549 MPa > 490 MPa; con arandela templada ISO 7089 Ø24, 132 MPa ✓ → arandelas obligatorias.)*

## 4. Efecto del contacto a igual malla y δ_local

`r061_fem_pegado_v573.py` repite cada corrida con el mismo CAD, la misma malla, pernos y cargas, pero con las siete parejas unidas por `*TIE`. Los nudos esclavos sin cara maestra enfrente (498 en la malla de 9 mm) quedan libres en ambas variantes; es el mismo efecto que la cobertura de proyección.

| Caso | Nodos | Contacto (mm) | Pegado *TIE (mm) | Cociente |
|---|---|---|---|---|
| U1 s+ 12 mm | 23 039 | 0,4635 | 0,4370 | 1,061 |
| U1 s+ 9 mm | 32 497 | 0,4823 | 0,4511 | 1,069 |
| U1 s+ 7 mm | 54 533 | 0,5112 | 0,4740 | 1,078 |
| U3 s− 9 mm | 32 075 | 0,4469 | 0,4217 | 1,060 |

**Extrapolación del cociente.**
- Se hizo lineal en el tamaño efectivo h_ef = N^(−1/3), con las dos mallas más finas: da 1,128.
- Es indicativa, porque los C3D4 todavía no están en el rango asintótico.
- Se adopta **1,13**, redondeando hacia arriba.
- Se aplica a los cuatro datum y signos. U3 s− con malla de 9 mm da el mismo cociente que U1 s+ (1,060 frente a 1,069) [HIPÓTESIS].

**Separación entre local y global.** La parrilla SAP/Vlasov ya contiene la flexión y la torsión del W6x9. Por eso, como en v5.7.1 (`INFORME_N3_GLOBAL_V571.md` §1, `r061_n3_delta_total_v571.py`):

δ_local = FEM 800 − viga de Vlasov de 800 mm impedida

La carga ENV208 y la geometría del rodillo son las mismas, así que la parte de viga se toma de `DELTA_TOTAL_v571_pegado.json` como fem800 − local.

| Datum | FEM 800 pegado v5.7.2b, malla 2 mm (mm) | FEM 800 con contacto ×1,13 (mm) | Viga Vlasov 800 impedida (mm) | **δ_local con contacto (mm)** | δ_local v5.7.1 pegado, usado hasta hoy (mm) |
|---|---|---|---|---|---|
| U1 s+ | 0,590 | 0,667 | 0,288 | **0,379** | 0,353 |
| U1 s− | 0,528 | 0,597 | 0,239 | **0,359** | 0,333 |
| U3 s+ | 0,476 | 0,538 | 0,193 | **0,345** | 0,319 |
| U3 s− | 0,547 | 0,618 | 0,251 | **0,368** | 0,341 |

**Criterio de soporte local.** Se aplica al FEM de 800 mm: 0,667 mm ≤ 1,0 mm ✓, pero > 0,5 mm (objetivo).

**De dónde viene el aumento de δ_local frente a v5.7.1 (+7–8 %).**
- El FEM pegado v5.7.2b es más rígido que el v5.7.1: 0,590 frente a 0,641 mm en U1 s+.
- El contacto añade un 13 %.
- Los dos efectos casi se compensan.

## 5. Presupuesto D-019 / D-031 con δ_local de contacto (p21)

Se calcula con `p21_presupuesto_local_contacto.py`.
- Ejecuta p14 (variante LOCK) y p20 sin modificarlos; solo cambia el origen de δ_local.
- Escribe en `SAP_ANEXO_N3_V573/resultados/v573/local_contacto/`.
- Con los valores v5.7.1 reproduce exactamente el presupuesto vigente (A NOM_V2 LIBRE = 4,06 mm).

| Familia | Alabeo | ‖d‖ (mm) | A suma H7/g6 (mm) | B conservador H7/g6 (mm) | Antes: A / B (mm) |
|---|---|---|---|---|---|
| NOM_V2 | LIBRE | 2,51 | **4,09 ✓** | **6,44 ✓** | 4,06 / 6,48 |
| NOM_V2 | IMPEDIDO | 1,44 | 3,02 ✓ | 7,30 ✓ | 2,99 / 7,34 |
| ENV208 (sensib.) | LIBRE | 3,60 | 5,18 ✗ | 5,04 ✓ | 5,15 / 5,09 |
| ENV208 (sensib.) | IMPEDIDO | 1,87 | 3,45 ✓ | 6,28 ✓ | 3,41 / 6,33 |

En NOM_V2, la familia de evaluación (REQ573 §6.2), se siguen cumpliendo D-019 (A ≤ 5 mm) y D-031 (B ≥ 5 mm después de tolerancias). El margen de A queda en 0,91 mm.

Pendientes del presupuesto:
- las partidas de tolerancia siguen como HIPÓTESIS K17;
- el OD del aro es un DATO EXTERNO SKF pendiente;
- la sensibilidad ENV208 LIBRE ya no cumplía A antes de este cálculo.

## 6. Contraste independiente en SOLIDWORKS Simulation 2024 (API)

**Automatización.** `r061_sw_contacto_v573.cs`, compilado en C# por `r061_sw_contacto_v573_correr.ps1`:
- importa `U1_CONJUNTO.step`: los mismos cuatro cuerpos exportados por FreeCAD, con volúmenes que coinciden al mm³;
- acero E = 200 GPa, ν = 0,30;
- contacto global sin penetración, más siete contactos locales superficie a superficie con μ = 0,20; los encuentra solo y coinciden con las parejas de CalculiX;
- 6 conectores de perno con precarga axial de 26 kN y coronas de Ø18,2 y Ø24,2 mm;
- extremos del tramo W fijos;
- dos cargas remotas distribuidas: la fuerza, en el eje del pivote a Z955 sobre los dos casquillos, y el par Mz, en el limitador;
- tetraedros de 2.º orden de 6 mm: 263 505 nodos y 790 698 GDL.

**Diferencias con CalculiX.**
- SOLIDWORKS aplica precarga y carga en un solo paso, así que su u_radial incluye la precarga (unos −0,007 mm en CalculiX).
- Los pernos son conectores, no resortes calibrados.
- Las cargas remotas reparten la resultante de forma estáticamente equivalente, no con el mismo reparto nodal.

**Variante pegada (bonded global, sin pernos; lineal)**, convergencia con tetraedros de 2.º orden (`SW_RESUMEN_V573.md`):

| Modelo | Malla (mm) | Nodos | GDL | u base (mm) | u cabeza (mm) | Giro (mrad) | **u Z955 (mm)** |
|---|---|---|---|---|---|---|---|
| SOLIDWORKS, pegado | 8 | 124 680 | 372 450 | 0,1932 | 0,4971 | 2,780 | **0,5743** |
| SOLIDWORKS, pegado | 6 | 263 119 | 787 263 | 0,1977 | 0,4994 | 2,807 | **0,5795** |
| SOLIDWORKS, pegado | 4 | 735 326 | 2 202 840 | 0,2000 | 0,5038 | 2,834 | **0,5860** |
| CalculiX, pegado v5.7.2b fusionado (C3D4) | 2 | 703 542 | — | 0,1971 | 0,5136 | 2,858 | **0,5900** |

- **Concordancia entre solvers:** la base pegada que usa δ_local (0,590 mm) queda confirmada por un solver independiente con elementos de 2.º orden, con una diferencia de −0,7 % a 4 mm.
- **Convergencia:** SOLIDWORKS crece de forma monótona: +0,9 % de 8 a 6 mm y +1,1 % de 6 a 4 mm. El valor convergido estimado está en torno a 0,59–0,60 mm.
- **Lectura para el criterio local:** la incertidumbre de discretización de la base pegada es de unos ±2 %. Con el cociente 1,13, el FEM de 800 mm con contacto queda en 0,67–0,68 mm, por debajo de 1,0 mm.

**Variante con contacto (rozamiento + pernos):**
- **Malla de 6 mm:** el primer intento se detuvo porque SOLIDWORKS exige contactos locales junto a los conectores de perno. El segundo, ya con los 7 contactos locales, **no convergió**: hizo 80 iteraciones del Lagrangiano aumentado en 4 ciclos de 20, a unos 2,5 min cada una, con el solver FFEPlus fuera de memoria. Se detuvo a las 23:16.
- **Malla de 8 mm, μ = 0,20:** tampoco convergió. Falló a los 35 min, tras unas 30 iteraciones, con "análisis fallido" (código 24).
- **Malla de 8 mm, μ = 0** (variante de cota, `R061_SW_MU=0`): el solver terminó, pero como **mecanismo**. Los desplazamientos fueron de ~10⁶ mm y SOLIDWORKS pidió activar grandes desplazamientos. Sin rozamiento nada retiene la mordaza a lo largo del eje X del W: los conectores de perno unen A, B y C entre sí, pero no modelan el contacto del vástago con los taladros Ø13,5 del alma.

**Lectura de la variante con contacto:**
1. SOLIDWORKS resuelve precarga y carga en un solo paso. En la primera iteración aún no hay presión de contacto, y por tanto tampoco rozamiento: el conjunto arranca como mecanismo. Por eso el Lagrangiano aumentado no converge. CalculiX lo evita apretando primero (paso 1) y cargando después (paso 2). En SOLIDWORKS habría que usar un estudio no lineal con dos pasos de tiempo [PENDIENTE, opcional].
2. **Hallazgo de diseño:** la retención axial (X) del amarre sobre el W6x9 depende **solo del rozamiento** que genera la precarga. Si la precarga se pierde, la mordaza puede deslizar hasta absorber el juego radial M12/Ø13,5 (0,75 mm) antes de apoyarse en los pernos transversales.
   - Con 26 kN el FEM da un deslizamiento ≤ 0,006 mm, y con unos 16 kN el resultado es igual.
   - Falta verificar la capacidad a deslizamiento (VDI 2230 / EN 1993-1-8, categoría B o C). *(20/10, `VERIFICACION_PERNOS_AMARRE_V573.md`: con 62 N·m y μ = 0,20, margen 3,97 (modelo por componentes) o 1,79 (modelo conservador). Si deslizara, el aplastamiento resiste con margen 29,5, pero el datum podría moverse hasta 0,66 mm radiales.)*
   - Falta fijar el control de apriete, el par y la retención de la tuerca [VERIFICAR].
3. **El contraste independiente útil es la variante pegada.** Confirma la base de 0,59 mm sobre la que se aplica el cociente. El efecto del contacto (+6 a +13 %) queda respaldado solo por CalculiX.

## 7. Limitaciones

- **Convergencia.** Los C3D4 del modelo de contacto no convergen en valor absoluto.
  - δ_local se apoya en el cociente a igual malla, extrapolado, y en el FEM pegado fino.
  - El FEM pegado v5.7.2b de 2 mm no tiene estudio de convergencia propio [VERIFICAR con el contraste de 2.º orden].
- **Precarga y rozamiento.** Son HIPÓTESIS: 26 kN nominal, unos 16 kN como mínimo, y μ = 0,20 sin ensayo. La sensibilidad a la precarga es pequeña (+0,5 %).
- **Pernos.** No se modelan el contacto perno–agujero, la rosca ni la flexión del perno. Los acoplamientos cinemáticos concentran la precarga en las coronas; de ahí la tensión local en C.
- **Apoyos.** Los extremos del tramo W están empotrados, como en el FEM pegado. La flexibilidad del resto de N3 está en SAP/Vlasov, no aquí.
- **Separación local/global.** δ_local = FEM 800 − viga de Vlasov 800 sigue la metodología v5.7.1. Superponer global y local es algo conservador (`INFORME_N3_GLOBAL_V571.md`).
- **Equilibrio de momentos.** Cierra entre 0,6 y 1,3 % (criterio 1 %); U3 s− da 1,05 % [VERIFICAR la causa]. Es común a las variantes con contacto y pegada.
- **Talones.** La cobertura de proyección baja al 64 %, así que la apertura en los talones es un indicador.
- **Valores locales.** Los picos de presión y la tensión bajo cabeza son locales y elásticos. No se evalúan como fallo. La verificación VDI 2230 de la unión se hizo el 20/10 en `VERIFICACION_PERNOS_AMARRE_V573.md`.

## 8. Trazabilidad (anexo)

**Scripts** (`R06.1_centradores/scripts/`):
- `r061_hacer_fem_contacto_v573.py` genera `r061_fem_contacto_v573.py` a partir de v5.7.1, que no se modifica.
- `r061_lote_fem_contacto_v573.ps1` corre el lote de contacto (sufijo `_b`).
- `r061_hacer_fem_pegado_v573.py` genera `r061_fem_pegado_v573.py`, y `r061_lote_fem_pegado_v573.ps1` corre esa variante (sufijo `_tie`).
- Posproceso: `r061_post_fem_contacto_v573.py`, `r061_post_frd_pasos_v573.py` y `r061_cociente_contacto_pegado_v573.py`.
- SOLIDWORKS: `r061_exportar_step_contacto_v573.py`, `r061_sw_contacto_v573.cs` y `r061_sw_contacto_v573_correr.ps1`.
- Presupuesto: `SAP_ANEXO_N3_V573/scripts/p21_presupuesto_local_contacto.py`, con salida en `resultados/v573/local_contacto/`.

**Resultados** (`resultados/k2m_v57/fem_contacto_v573/`):
- Corridas con contacto: `U1_SP_H12_b`, `U1_SP_H9_b`, `U1_SP_H7_b`, `U3_SM_H9_b` y `U1_SP_H9_PMIN_b`, cada una con JSON, FRD, INP y logs.
- Corridas pegadas: `*_tie`.
- Tablas: `RESUMEN_FEM_CONTACTO_V573_b.*`, `PASOS_PRECARGA_CARGA_b/_tie.*`, `COCIENTE_CONTACTO_PEGADO_V573.*` y `LOCAL_CONTACTO_V573_PARA_P21.json`.
- Figuras: `convergencia_contacto_U1_b.png` y `cociente_contacto_pegado_U1.png`.
- `solidworks/`: STEP, SLDPRT, logs (`sw_log_*.txt`, uno por corrida) y la base de resultados de SOLIDWORKS.
- Resumen de SOLIDWORKS: `SW_RESUMEN_V573.md/.json` y la figura `contraste_calculix_solidworks_U1.png`. Script: `r061_sw_resumen_v573.py`.
- Archivos temporales: la corrida de contacto de 6 mm detenida (`U1_CONJUNTO_SW_170403-*`) dejó 75 archivos temporales del solver, 6,22 GB, sin resultados (`.0nn`, `.1nn`, `.P3x`, `.EL0`, `.CWR` incompleto y otros). Con autorización del usuario (20/10) se **enviaron a la Papelera de reciclaje** de Windows, que es recuperable; la eliminación definitiva corresponde al usuario. Se conservan su `.SLDPRT` y los registros `.LOG`, `.OUT` (iteraciones de contacto), `.PCS` y `BenchMark`. Las bases de resultados de las demás corridas no se tocaron.

**Intentos registrados.**
- `U1_SP_H12` y `U1_SP_H9`, sin sufijo: el primer intento se detuvo en el posproceso por un umbral de cobertura del 75 %, que después pasó a ser solo indicador.
- `prueba_*` en el scratchpad: calibración de la precarga.
- El portátil se suspendió por batería crítica entre las 17:19 y las 20:15, lo que alargó a 205 min la corrida de 9 mm.
