# N3 global bajo K2-M v5.7.1: verificación en CalculiX y corrección por alabeo (29/09/2026)

**Estado:** EJECUTADO como verificación provisional (HPGR D-038). No sustituye la corrida SAP2000 para el anexo, ni aprueba la mesa, la mordaza o la fabricación. K2-M sigue siendo CANDIDATO.

## 1. Qué se hizo

1. **Réplica del pórtico SAP en CalculiX 2.22** (`scripts\r061_n3_ccx_portico.py`). Lee los `.s2k` del paquete de Codex Desktop (`..\codex_desktop_v571\sap_n3_k2m_preliminar\`) y reproduce su geometría, la sección W6×9, el A36, los apoyos de las ruedas, las cargas ENV208 y el peso propio.
   - La torsión es de Saint-Venant, como en SAP.
   - **Limitación hallada:** el elemento U1 de CalculiX calcula la torsión con el momento polar I11+I22 e ignora J (comprobado con un voladizo). Por eso G·J se asigna con una cadena U1 paralela de I11 = I22 = J/2.
   - Las reacciones que imprime CalculiX con U1 no son fiables; el equilibrio se comprueba en el modelo matricial (paso 2).
2. **Parrilla de pared delgada con 7 GDL por nudo** (`scripts\r061_n3_portico_vlasov.py`). Incluye la torsión no uniforme G·J + E·Cw (Cw = 4,755·10⁹ mm⁶, tabla SAP) y se calcula en tres modos:
   - **SV:** Saint-Venant, Cw = 0;
   - **LIBRE:** bimomento nulo en las uniones;
   - **IMPEDIDO:** alabeo nulo en las uniones entre barras en X y en Y.
3. **Flecha radial a Z955** con los coeficientes del requerimiento SAP v5.7.1 §5.2, y total δ = δ_global + δ_local (§5.3, paso 4). δ_local = FEM pegado v5.7.1 de 800 mm (malla 2) − viga de Vlasov de 800 mm impedida (`scripts\r061_n3_delta_total_v571.py`).
4. **Cálculo independiente de Codex** (solo lectura): `..\seleccion\codex_k2m\K7_vlasov_n3.out.txt`.

## 2. Verificación

| Control | Resultado | Referencia | Estado |
|---|---|---|---|
| CAL-1 (M06 empotrado, 1 860 mm), J18 | R1 = −0,13662 rad; R3 = −0,4944·10⁻³ rad; U2 = 0,2430 mm; δ = 27,846 mm | Requerimiento §5.5: −0,1366; −0,494·10⁻³; 0,243 (Euler-Bernoulli); 27,8 | Cumple (±2 %) |
| CAL-2 (empotrado en M07, 1 593 mm) | R1 = −0,080938 rad; R3 = −0,3231·10⁻³ rad; U2 = 0,0613 mm; δ = 16,426 mm | −0,0809; −0,323·10⁻³; 0,061 (Euler-Bernoulli); 16,4 | Cumple |
| Parrilla SV frente a CalculiX (todas las juntas y los 11 casos) | Diferencia relativa máxima 5,8·10⁻⁵ | — | Cumple |
| Tramos aislados de Vlasov (giro en X = 388, mrad; SV / libre / impedido) | 800 mm: −71,15 / −4,76 / −1,27; 1 593 mm: −80,94 / −10,37 / −1,82; 1 860 mm: −136,62 / −30,92 / −8,35 | §5.3: −71,1 / −4,8 / −1,27; −80,9 / −10,4 / −1,82; −136,6 / −30,9 / −8,35 | Cumple |
| Equilibrio global (fuerza y momento, 30 soluciones) | Residuo ≤ 3·10⁻¹¹ (Claude); ≤ 2,6·10⁻⁸ N y 1,2·10⁻⁸ N·m (Codex) | ≤ 1 % | Cumple |
| Cálculo independiente de Codex | Coincide: p. ej. ENV208_PPP, U1 libre/impedido 1,2841/0,8791 frente a 1,284/0,879 mm | — | Cumple |
| Variante de apoyos del Excel R01 (U1 en J13/J16) | Cambia δ_SV < 0,1 % | — | Sin efecto práctico |

## 3. Resultados: flecha radial a Z955 (mm; + = el soporte cede hacia fuera)

**Solo el modelo global** (`N3_VLASOV_RIG.json`):
- **SV:** 13–17 mm en U1 y 11–15 mm en U3. Es una cota superior no física, que es lo que dará SAP.
- **Con alabeo, casos ENV208:**
  - U1: 0,56–1,28 mm (libre) y 0,22–0,88 mm (impedido);
  - U3: 0,24–0,97 mm (libre) y −0,05 a 0,61 mm (impedido).

**Total con la parte local del FEM pegado v5.7.1** (`DELTA_TOTAL_v571_pegado.json`). La parte local vale U1 0,353/0,333 mm (s+1/s−1) y U3 0,319/0,341 mm.

| Caso que gobierna | U1 total libre / impedido | U3 total libre / impedido |
|---|---|---|
| ENV208_PPP (U1) | **1,637 / 1,232** | 0,555 / 0,272 |
| ENV208_PMP (U1) | 1,610 / 1,204 | 0,576 / 0,293 |
| ENV208_MMM (U3) | 0,897 / 0,557 | **1,313 / 0,951** |
| ENV208_MPM (U3) | 0,924 / 0,585 | 1,292 / 0,930 |

**Lectura:**
- **HPGR D-034 (≤ 1,0 mm):** U1 no cumple en ninguna de las dos cotas de alabeo, y U3 está al límite. Eso ocurre aun con la mordaza **pegada**, es decir, sin la apertura de la unión B–alma.
- **Causa:** la torsión global de M05 y M06, W6×9 de sección abierta, entre el datum (X = 388) y las uniones con M01, M07 y M02.
- **HPGR D-031:** el término de datums de la precisión final, d·u₂ = 1,0851·δ₁ + 0,8846·δ₃, llegaría a ~1,6 mm (impedido) y ~2,3 mm (libre) en los casos que gobiernan (PPP, PMP y MMM). La estimación de la v5.7 con el FEM pegado local era |d| ≈ 0,75 mm.

## 4. Sensibilidad: encajonar M05/M06 (HIPÓTESIS de diseño; modifica N3)

Una placa lateral interior de 6 mm entre alas cierra una celda (J = 2,57·10⁶ mm⁴, 152 veces el W6×9; `SENS_CAJON.json`):

| Variante | U1 total libre / impedido | U3 total libre / impedido |
|---|---|---|
| Base | 1,637 / 1,232 | 1,313 / 0,951 |
| Cajón X 388–663 (datum–M07) | **0,994 / 0,957** | **0,742 / 0,708** |
| Cajón X −331,5–663 | 0,982 / 0,946 | 0,732 / 0,698 |

El cajón entre el datum y M07 basta para bajar de 1,0 mm, pero con poco margen en U1. Lo que resta es la parte local (≈ 0,35 mm) y la flexión de M07. Hay que verificarlo con geometría real (CAD y FEM).

**Restricción constructiva:** la mordaza ocupa X ≈ 388 ± 90 y la pieza A va por el lado interior del alma. Fuera de esa zona el cajón rinde menos (`SENS_TRAVESANO_CAJON.json`, `scripts\r061_n3_sens_travesano_v571.py`):

| Variante | U1 total libre / impedido | U3 total libre / impedido |
|---|---|---|
| Cajón interior X 480–663 | 1,070 / 1,020 | 0,810 / 0,764 |
| Cajón interior X 520–663 | 1,142 / 1,074 | 0,873 / 0,812 |
| **Travesaño W6×9 nuevo M05–M06 en X = 388** | **0,743 / 0,736** | **0,499 / 0,492** |
| Travesaño en X = 300 | 0,733 / 0,707 | 0,509 / 0,485 |
| Travesaño en X = 250 | 0,752 / 0,703 | 0,537 / 0,492 |

El travesaño es la medida global más eficaz: los torsores de U1 y U3 son opuestos y el travesaño los equilibra por flexión en su eje fuerte. Deja un margen de ~25 % sobre 1,0 mm, aún con la parte local del FEM pegado. Es poco sensible a su posición entre X = 250 y 388, así que puede ir fuera de la zona de la mordaza.

**Riesgos [VERIFICAR] en el CAD:**
- queda bajo el aro, cuya cara inferior está a ~Z890 frente al ala superior a ~Z805;
- puede dar sombra a la aspersión inferior (L con salidas exteriores);
- puede interferir con los PAD, el drenaje, la puerta y el traslado;
- suma ~15 kg a N3.

## 5. Limitaciones

- **Deformación por cortante:** Euler-Bernoulli, sin cortante (SAP la incluye). Efecto < 0,3 % en R1, R3 y δ según el §5.5, mayor en U2 y R2.
- **Apoyos y cargas:** ruedas bilaterales, como en el `.s2k`; no se modelan el aro, los PAD ni la grúa. El peso propio va como cargas nodales.
- **Uniones:** son ideales (continuidad de barras); su detalle real está [VERIFICAR]. Las dos cotas de alabeo acotan su efecto.
- **Parte local:** sale del FEM **pegado** v5.7.1. La unión real atornillada añade flexibilidad (≈ +0,3 mm con la junta cerrada, según K6) y la v5.7.2 la cambiará.
- **Superposición:** global más local es algo conservadora (en 1 860 mm suma ≈ 2,2 mm frente a 1,82 mm del FEM; requerimiento §5.3).

## 6. Archivos

- **JSON:** `N3_K2M_CAL1/CAL2_*_resultados.json`, `N3_K2M_V571_ENV208_RIG_resultados.json`, `N3_K2M_V571_ENV208_R01B_EXCEL_RESTRAINTS_RIG_resultados.json`, `N3_VLASOV_RIG.json`, `DELTA_TOTAL_v571_pegado.json` y `SENS_CAJON.json`.
- **Entradas CalculiX de muestra:** `N3_K2M_V571_ENV208_RIG.inp` y `N3_K2M_CAL1_M06_U1_SP.inp`.
- **Guiones:** `scripts\r061_n3_ccx_portico.py`, `scripts\r061_n3_portico_vlasov.py`, `scripts\r061_n3_delta_total_v571.py` y `scripts\r061_n3_sens_cajon_v571.py`.
- **Codex:** `..\seleccion\codex_k2m\K7_vlasov_n3.out.txt` (contraste) y `V6_amarre_v572.out.txt` (propuesta del amarre).

## 7. Adenda tras la verificación adversarial (29/09/2026, la misma tarde)

Fuente: `VERIFICACION_ADVERSARIAL_N3_V572.md` (tres revisores independientes). **Corrige** varias afirmaciones de las secciones 2 a 5.

**Se sostiene:**
- La implementación de la parrilla es correcta: matrices, transformación de las barras en Y, torsión de Hermite, combinaciones y coeficientes.
- «Sin travesaño, U1 supera 1,0 mm» se mantiene con la cota LIBRE en todas las variantes probadas.

**Se corrige:**
1. **El travesaño solo funciona con unión a momento y continuidad de alas.**
   - Las alas deben soldarse a tope contra las alas de M05/M06, o llevar placas de ala PL 8×80: con eso k_RX ≈ 1,6e10 y k_RZ ≈ 1,4e9 N·mm/rad, y U1 = 0,80/0,73 mm.
   - Con unión solo al alma: U1 0,96–1,06 mm. Con unión atornillada a cortante: 1,44/1,01 mm.
   - Criterio mínimo: k_RX ≥ 2e9 y k_RZ ≥ 1e9 N·mm/rad.
2. **La parte local del FEM pegado es una cota inferior de la flexibilidad**, no conservadora. Con la junta atornillada cerrada (K6, +0,32 mm), el travesaño da 1,03–1,10 mm. La frase «margen de ~25 % aún con la parte local del FEM pegado» (§4) es **incorrecta**.
3. **ENV208 no es una envolvente:**
   - FALLO_EMP (s2 = +): U1 base 1,70/1,34 mm; con travesaño 0,86/0,80 mm.
   - Un solo datum en contacto (transitorio de captura): base 2,66/2,27 mm; con travesaño 1,47/1,40 mm.
   - Faltan ASIM y NOM_V2.
4. **Uniones existentes del N3:** si M07–M05/M06 y las esquinas M05/M06–M01/M02 van solo al alma, la base empeora a 2,1–7,1 mm en U1 (LIBRE). El N3 R05 **no define sus uniones** (`estructura_mesa\V5.2_N3_R05_CIERRE_HALLAZGOS_R04\12_README_R05.md:21`), así que deben especificarse.
5. **Retención en Y de las ruedas:** la mitad de δ_global es Uy de J18. Con Y restringido en las cuatro ruedas, la base da 1,30/0,89 mm y el travesaño 0,55/0,48 mm. Hay que definir el apoyo real [VERIFICAR].
6. **La cota IMPEDIDO no es física con uniones al alma.** Con uniones rígidas, el rango honesto con travesaño es ≈ 0,77–0,78 mm; sin travesaño, 1,51–1,64 mm. La frase «las dos cotas de alabeo acotan su efecto» (§5) es incorrecta.
7. **Variante ART de M07** (requerimiento §5.4), no evaluada antes: base 7,16/1,41 mm; con travesaño 0,98/0,73 mm.
8. **D-031:** hay que evaluarlo con NOM_V2 (base |d| ≈ 1,70/1,17 mm), no con ENV208. La carrera de captura base (≈ 6,8 mm) sigue siendo ≥ 5 mm.
9. **Riesgo nuevo:** el travesaño M08 en X = 200, con cara superior en Z805, queda a **5,3–7,7 mm** bajo el pie giratorio de la lanza interior (Z810,3–812,7; r ≈ 233–373).

**Lectura corregida:**
- El criterio de 1,0 mm (HPGR D-034) nació como criterio **provisional del soporte local**.
- El requisito funcional de colocación del rodamiento es **≤ 5 mm** (HPGR D-019, provisional), y la carrera de captura debe ser ≥ 5 mm tras tolerancias (HPGR D-031).
- La conclusión sobre el travesaño depende de a qué magnitud se aplique el 1,0 mm, y eso lo decide el usuario.
