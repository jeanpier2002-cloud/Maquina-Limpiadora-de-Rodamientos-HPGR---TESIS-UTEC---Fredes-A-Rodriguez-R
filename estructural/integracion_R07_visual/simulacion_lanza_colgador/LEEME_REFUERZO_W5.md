# Refuerzo de la unión transversal–tambor (cordón W5): cinco variantes en SOLIDWORKS (12/11/2026)

**Pregunta.** El submodelo de `LEEME.md` mostró que, con el golpe accidental de 1 000 N de R03 en el brazo de la U, el transversal DN50 Sch 10S fluye localmente junto al fin del cordón W5 (unos 185 MPa a 1,0t; fluencia supuesta de 153 MPa). ¿Qué refuerzo lo resuelve con menos costo y sin sobrediseñar?

**Estado.**
- Verificación por simulación (D-045), sin ensayo.
- Las cuatro variantes de refuerzo son una **PROPUESTA**: sus medidas no salen de ningún plano.
- **No hay decisión tomada.** La recomendación final es un CANDIDATO, por discutir con el asesor.

## Variantes

Esquema acotado: `resultados/union_variantes/fig_esquema_variantes.png` (script `scripts/s10_esquema_variantes.py`).

| Clave | Qué cambia | Masa |
|---|---|---|
| BASE | Actual: tramo central DN50 Sch 10S (t = 2,77 mm) | tubo central 2,33 kg |
| S40 | Tramo central en Sch 40S (t = 3,91 mm); mismo diámetro exterior, 60,3 mm | 3,21 kg (+0,88) |
| S80 | Tramo central en Sch 80S (t = 5,54 mm) | 4,39 kg (+2,06) |
| LENG | Sch 10S + **lengüeta horizontal** de 8 mm que prolonga la placa inferior del tambor sobre el tubo. Semiancho de 50 mm en el borde del tambor y de 14 mm en la punta (x = 255). Cordones como el W5 | +0,24 kg por lado |
| CART | Sch 10S + **cartela vertical** de 8 mm en el plano de la U, soldada a la pared del tambor (R200) y sobre el tubo. Punta en x = 266; cordones de filete a ambos lados | +0,16 kg por lado |

- Espesores según ASME B36.19M.
- Masas del CAD de cada variante, tomadas de `geometria/variantes_w5/geometria_variantes.json`.

## Modelo

**Geometría** (`scripts/s07_geometria_union_variantes.py`):
- Es el mismo submodelo de `s05`: copia del CAD R07 V18D, cordones W5 modelados y perfil del cordón como HIPÓTESIS.
- La zona fina se alarga de x = 170 a 272 para que entren las puntas de los refuerzos.
- No hay solapes entre cuerpos (`resumen_s07.txt`).

**SOLIDWORKS** (`scripts/s08_sw_union_variantes.cs/.ps1`):
- Contacto pegado y eje empotrado en Z2840.
- Material: 316L a 62 °C, E = 193 GPa, fluencia supuesta de 153 MPa (hipótesis de B1).
- Cargas: el golpe de 1 000 N en el brazo A a Z1400, de dos formas:
  - **FUERA del plano:** es el caso que gobierna. Da flexión horizontal del transversal (M = 700 N·m en x = 200) y torsión (T = 340 N·m).
  - **EN el plano.**
- Malla:
  - control de 1 mm en las caras de la zona fina: 16 caras en BASE, S40 y S80; 26 en LENG y CART;
  - con 1 mm, entre 0,92 y 1,38 millones de nodos, según la variante;
  - con 0,6 mm, 2,97 millones en BASE y 3,81 millones en S40.
- La corrida de S80 con 0,6 mm se malló (4,7 millones de nodos) pero se detuvo antes de extraer los resultados, por tiempo: unos 35–55 min de extracción por estudio. No hay resultados de esa corrida.

**Corridas.** Las variantes se corrieron en tres tandas, una por registro de `resultados/union_variantes/`:

| Registro | Corrida |
|---|---|
| `sw_variantes_log_080019.txt` | BASE (las tres mallas) y S40 (FUERA en 1 y 0,6 mm; EN en 1 mm) |
| `sw_variantes_log_103416.txt` | S80 |
| `sw_variantes_log_120814.txt` | LENG y CART |

Todas terminaron con `CreateMesh err=0` y `RunAnalysis err=0`. Los modelos están en `modelo/UNION_W5_<VAR>_<sello>.SLDPRT`.

**Resumen** (`scripts/s09_resumen_union_variantes.py`). Genera `RESUMEN_VARIANTES_W5.json`, `RESUMEN_VARIANTES_W5.md` y `fig_union_variantes.png`. Todas las métricas son von Mises en la pared del tubo:

| Métrica | Qué mide |
|---|---|
| **Fin de la unión a 1,0t** | Máximo sobre la circunferencia a una distancia t más allá del fin de la unión. En CART se mide en los dos extremos (el fin del W5 en x = 200 y la punta de la cartela) y se toma el peor. |
| **Pie del cordón a 1,0t** | Sobre la línea del pie del cordón, a t del pie. |
| **Cara interior** | Superficie sin aristas singulares. Si no fluye, la fluencia no atraviesa la pared. |
| **Membrana** | Promedio de los tensores de la cara exterior y de la interior en el mismo punto, sin las zonas singulares. |
| **Sonda en x = 240** | Control frente a la viga calculada a mano. |

Los valores a 0,4t, el punto caliente IIW y los picos de arista **no convergen**: son singulares y **no se usan**.

## Controles

**Convergencia de malla** (golpe fuera del plano; MPa):

| Métrica | BASE, malla 1 mm | BASE, malla 0,6 mm | Δ | S40, malla 1 mm | S40, malla 0,6 mm | Δ |
|---|---:|---:|---:|---:|---:|---:|
| Fin a 1,0t | 188,5 | 183,9 | 2,5 % | 119,4 | 115,6 | 3,3 % |
| Pie a 1,0t | 204,2 | 199,2 | 2,5 % | 140,6 | 138,8 | 1,3 % |
| Cara interior | 239,6 | 237,3 | 1,0 % | 170,9 | 168,7 | 1,3 % |
| Membrana | 162,9 | 161,9 | 0,6 % | 107,2 | 107,3 | 0,1 % |
| A 0,4t (singular) | 321,0 | 243,1 | no converge | 173,3 | 156,9 | no converge |

Las cuatro métricas usadas difieren en un 1–3 %, y la malla de 1 mm da valores algo **más altos**, del lado seguro. Por eso la comparación entre variantes usa la malla de 1 mm.

**Viga a mano en x = 240.** Viga calculada como σ = √[(M/W)² + 3(T/2W)²], con M = 1 000 N × 660 mm y T = 340 N·m.

| Variante | A mano | FEM | Diferencia |
|---|---:|---:|---:|
| BASE | 105,0 MPa | 114,2 MPa | +8,8 % |
| S40 | 78,8 MPa | 83,1 MPa | +5,5 % |
| S80 | 60,4 MPa | 62,3 MPa | +3,1 % |
| CART | 105,0 MPa | 109,3 MPa | +4,1 % |

En LENG la comparación no aplica, porque x = 240 queda dentro de la lengüeta. El exceso del FEM baja con el espesor: es la influencia del borde del tambor, que está a 40 mm.

## Resultados (malla 1 mm; von Mises en MPa; fluencia supuesta de 153 MPa)

**Golpe de 1 000 N fuera del plano** (el que gobierna):

| Variante | Fin a 1,0t | Pie a 1,0t | Cara interior | Membrana | Golpe sin fluencia local* | Golpe sin fluencia de membrana* |
|---|---:|---:|---:|---:|---:|---:|
| BASE | 188,5 | 204,2 | **239,6** | **162,9** | 639 N | 939 N |
| S40 | 119,4 | 140,6 | **170,9** | 107,2 | 895 N | 1 427 N |
| S80 | 71,7 | 96,5 | 123,9 | 71,5 | **1 235 N** | 2 140 N |
| LENG | 199,8 (punta) | 207,1 | **232,9** | 128,0 | 657 N | 1 195 N |
| CART | 143,8 (fin del W5) / 89,0 (punta) | 178,8 | **205,0** | 143,1 | 746 N | 1 069 N |

\* El modelo es elástico lineal, así que la tensión escala con la fuerza: F = 1 000 N × 153 / σ. Para «fluencia local» se toma el mayor valor entre el fin, el pie y la cara interior.

**Golpe de 1 000 N en el plano:** todas las variantes quedan por debajo de la fluencia.

| Variante | Fin a 1,0t | Pie a 1,0t | Cara interior | Membrana |
|---|---:|---:|---:|---:|
| BASE | 112,9 | 78,1 | 75,9 | 66,6 |
| S40 | 74,8 | 42,8 | 52,8 | 45,7 |
| S80 | 49,0 | 23,6 | 36,1 | 31,8 |
| LENG | 95,4 | 54,9 | 64,4 | 58,5 |
| CART | 92,9 (punta) / 30,5 (fin del W5) | 34,2 | 60,4 | 55,9 |

En el plano, la cartela sí trabaja bien: el fin del W5 baja de 113 a 31 MPa. Pero este caso no gobierna.

Figura: `resultados/union_variantes/fig_union_variantes.png`.
- (a) Máximo sobre la circunferencia a lo largo del tubo.
- (b) Las cuatro métricas por variante.

## Lectura: por qué cada variante da lo que da

**1. Aumentar el espesor ataca las dos partes del problema.** La tensión junto al fin del W5 tiene dos partes:
- la de viga, que escala con 1/Z;
- la flexión local de la pared (el tubo se ovaliza bajo la placa), que escala más o menos con 1/t².

| Variante | Z | Z relativo | Fin a 1,0t relativo | Cara interior relativa |
|---|---:|---:|---:|---:|
| Sch 10S | 6 886 mm³ | 1 | 1 | 1 |
| Sch 40S | 9 176 mm³ | 0,75 | 0,63 | 0,71 |
| Sch 80S | 11 970 mm³ | 0,58 | 0,38 | 0,52 |

El FEM baja más que 1/Z porque la pared más gruesa también se ovaliza menos.

**2. La lengüeta solo traslada el problema.**
- En su raíz, la lengüeta es muy rígida para el golpe que gobierna: I = t·b³/12 = 8 × 100³ / 12 ≈ 6,7·10⁵ mm⁴. Es más de 3 veces la del tubo, I = Z·R ≈ 2,1·10⁵ mm⁴.
- Por eso toma el momento, pero lo devuelve al mismo tubo de 2,77 mm en su punta (x = 255).
- En la punta, el momento casi no bajó: 645 frente a 700 N·m (−8 %), porque el golpe está a 900 mm.
- La nueva arista da prácticamente lo mismo que la BASE: 200 frente a 189 en el fin, 207 frente a 204 en el pie y 233 frente a 240 en la cara interior.

**3. La cartela vertical está orientada para el otro golpe.**
- El golpe fuera del plano dobla el transversal en el plano horizontal.
- Para esa flexión, una chapa vertical de 8 mm trabaja por su eje débil: I = h·t³/12 = 60 × 8³ / 12 ≈ 2 560 mm⁴, cerca del 1 % del tubo.
- Su aporte es solo local: rigidiza la parte de arriba del tubo junto al tambor. Así baja la tensión del fin del W5 de 163 a 144 MPa (−12 %), medida en los dos casos fuera de la franja de la cartela.
- Pero la cara interior sigue en 205 MPa.
- En el plano trabaja por su eje fuerte (I = t·h³/12 ≈ 1,4·10⁵ mm⁴), por eso allí sí ayuda. Pero ese no es el caso que gobierna.

**4. Sch 40S cumple a medias.**
- La membrana queda en 107 MPa (70 % de la fluencia): la pared no fluye en todo su espesor.
- La cara interior llega a 171 MPa, un 12 % por encima de la fluencia, en x ≈ 196 y θ ≈ 21° (junto al pie del W5).
- Es fluencia superficial y local.

**5. Sch 80S cumple con todas las métricas.**
- La más alta es la cara interior, con 124 MPa: margen de 1,23 sobre la fluencia supuesta.
- Aguanta unos 1 235 N sin fluencia local.

**6. La comprobación nominal del código no distingue las variantes.**
- `resultados/CALCULO_B1_ROTOR_U_EJE_CUBO.md` aplica ASME B31.3 al golpe como carga ocasional: S_L = √[S_b² + (2S_t)²] + 13,4 MPa sostenidos, frente a 1,33·S_h = 135,7 MPa.
- Para Sch 10S da 126,4 MPa (cociente 0,93). Con este cálculo: 98,2 MPa en Sch 40S y 78,4 MPa en Sch 80S. Todas cumplen.
- Ese cálculo nominal no incluye la concentración de esta unión de placa tangente al tubo. B31.3 no da su factor de intensificación (SIF) en el apéndice D [VERIFICAR: B31J o el FEM]. Por eso aquí gobierna el FEM.

## Comparación para decidir (seguridad, servicio, costo, sobrediseño)

| | BASE | S40 | S80 | LENG | CART |
|---|---|---|---|---|---|
| Sin fluencia de membrana con 1 000 N | no (163) | sí (107) | sí (72) | sí (128) | sí, justo (143) |
| Sin fluencia local con 1 000 N | no (240) | no (171) | **sí (124)** | no (233) | no (205) |
| B31.3 ocasional, nominal | 0,93 | 0,72 | 0,58 | 0,93 | 0,93 |
| Pérdida de carga en 0,3 m de tubo** | 1,9 mm | 2,3 mm | 3,1 mm | 1,9 mm | 1,9 mm |
| Masa añadida al rotor | — | +0,9 kg | +2,1 kg | +0,5 kg (2 lados) | +0,3 kg (2 lados) |
| Piezas y cordones nuevos | — | ninguno | ninguno | 2 piezas y 4 cordones | 2 piezas y 4 cordones |
| Planos que cambian | — | nota de tubería | nota de tubería | pieza nueva + detalle de soldadura | pieza nueva + detalle de soldadura |

\*\* Supuestos:
- el caudal de 221 L/min del P&ID HPGR-HID-001 (`planos/scripts/p49_esquema_hidraulico.py`), repartido por igual entre las 24 boquillas (HIPÓTESIS), da 9 boquillas por brazo y 1,38 L/s por mitad del transversal;
- agua a 62 °C con ν ≈ 0,46·10⁻⁶ m²/s, y Swamee–Jain con ε = 0,0015 mm.

Frente a los 51 m de altura de la bomba, la diferencia son milímetros: despreciable.

**Lo que no cambia con S40 ni con S80:**
- El diámetro exterior es el mismo (60,3 mm).
- Las bridas EN 1092-1 tipo 01 se enchufan sobre el diámetro exterior (`resultados/VERIFICACION_CATALOGO_2026-11-02.md`), así que valen para cualquier schedule.
- El cordón W5 sigue siendo a4.
- **Criterio de taller, no calculado:** un filete a4, con garganta de 4 mm, sobre una pared de 2,77 mm es más grueso que la propia pared. Sobre 5,54 mm la proporción es la habitual y hay menos riesgo de perforar o deformar el tubo al soldar.

**Costo:**
- S40 y S80 solo cambian el tubo del tramo central (unos 0,6 m).
- La diferencia de precio entre Sch 10S y Sch 80S en 316L **no está cotizada** [VERIFICAR] y no se agrega al presupuesto de D-077 hasta tener cotización.
- LENG y CART agregan corte, armado, soldadura e inspección de 4 piezas, y no resuelven el problema.

## Recomendación (CANDIDATO, por decidir con el asesor)

1. **Tramo central del transversal en DN50 Sch 80S.**
   - Es la única variante que deja todas las métricas convergidas por debajo de la fluencia supuesta con el golpe de 1 000 N de R03.
   - No cambia la geometría: mismo diámetro exterior, mismas bridas, mismo cordón W5.
   - Su costo de servicio es despreciable: unos 3 mm de pérdida de carga y +2,1 kg en el rotor.
   - No es sobrediseño: el margen local es de 1,23, para una carga que ya es hipótesis.
2. **Alternativa más liviana: Sch 40S.** Sirve si el asesor acepta fluencia superficial local ante un golpe accidental y único. La membrana tiene margen de 1,43 y solo la cara interior pasa la fluencia, en un 12 %.
3. **Descartadas para este fin, con evidencia:**
   - **La lengüeta horizontal:** solo traslada la concentración a su punta, con valores iguales a los actuales.
   - **La cartela vertical:** trabaja por su eje débil frente al golpe que gobierna (−12 %).
   - Ninguna de las dos se descarta para otros usos: la cartela sí ayuda con golpes en el plano.
4. **El golpe de 1 000 N es una hipótesis de R03.** Si se justificara un golpe menor, la unión actual aguanta unos 640 N sin fluencia local y unos 940 N sin fluencia de membrana. Esa es la otra vía que ya se anotó en `LEEME.md`.

## Pendientes

- **Registrar la decisión** con el próximo número libre de `00_CONTEXTO/DECISIONES.md` (el último es D-083), una vez que el asesor elija la variante o el golpe de diseño. Después:
  - nota de tubería en ASP-150 y ASP-200;
  - CAD en una revisión nueva, sobre una copia;
  - lista de materiales y presupuesto;
  - lote de la wiki.
- **Repetir las imágenes de SOLIDWORKS de LENG y CART.** Salieron sin el modelo (la vista no lo encuadró). Los resultados numéricos no dependen de ellas, y los modelos `.SLDPRT` tienen los estudios.
- **Silleta envolvente** (una chapa curvada que abraza el tubo 120–180°): no se simuló. La lengüeta es plana. Si el asesor la prefiere, hay que simularla en el mismo submodelo.

## Limitaciones

- El perfil del cordón W5 y la forma de los refuerzos son HIPÓTESIS. El plano ASP-150 pide «a4 contorno», sin perfil.
- Todas las uniones tienen contacto pegado.
- El modelo es elástico lineal: no se modela qué pasa después de la fluencia.
- **Malla:**
  - S80, LENG y CART tienen una sola malla (1 mm).
  - La convergencia se comprobó en BASE y S40 (1–3 %).
  - LENG y CART tienen aristas nuevas en las puntas, sin comprobar con malla de 0,6 mm.
- **Fluencia de 153 MPa:** es la hipótesis de B1 para el 316L a 62 °C. Si se usa la del material certificado del proveedor, los márgenes cambian en proporción.
- **Fatiga:**
  - no se evaluó para el golpe, que es accidental;
  - en servicio, el transversal trabaja a 13,4 MPa sostenidos (B1).
