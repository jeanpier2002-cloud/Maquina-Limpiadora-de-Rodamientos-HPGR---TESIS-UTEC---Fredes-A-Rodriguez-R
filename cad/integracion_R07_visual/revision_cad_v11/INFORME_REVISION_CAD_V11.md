# Revisión a detalle del CAD R07 V11 (27/10/2026, madrugada)

**Encargo.** El usuario pidió revisar el CAD a fondo después del caso del manillar. Antes de la corrección, su unión a M03 no sujetaba nada.

**Estado de lo que se hizo:**
- **EJECUTADO:** auditoría en solo lectura.
- **No se corrigió nada** del CAD ni de los planos: cada hallazgo trae una propuesta para que el usuario decida.
- El diseño sigue siendo CANDIDATO y no es apto para fabricación (HPGR D-045).

## 0. Resumen

**Qué se revisó.** Los **587 sólidos vigentes** de V11 (los visibles en la GUI, sin los superados):
- todos contra todos, con volumen común exacto y distancia;
- su conectividad;
- la tornillería;
- el barrido de la mesa contra la aspersión inferior.

Hubo una segunda opinión con **SOLIDWORKS** y una lectura de los generadores R04–R07 con **Codex**.

**Por qué no se detectó antes.** Los chequeos de R07 solo comparaban cada bloque nuevo contra el contexto. **La parte heredada de R05 y R04 nunca se auditó entre sí** ni funcionalmente; se aceptó como «heredada». El manillar no aparece en ningún `CHEQUEO_*.csv`.

**Lo que se encontró, en lo vigente:**
- **4 hallazgos de gravedad alta:**
  - el receptor del bloqueo en la estación LOAD flota, sin patas;
  - el pasador de estacionamiento del rotor no engancha nada;
  - el soporte superior R04 está implantado contra los muros de la cabina;
  - un delantal de reserva no físico se ve y se cruza con 8 soportes de riel.
- **10 de gravedad media:** equipos e instrumentos sin fijación ni conexión, uniones representadas con solapes y mecanismos sin validar.
- **Varios de gravedad baja**, que son representaciones aceptables para declarar.

No apareció otra unión estructural «que no sujeta», como la del manillar, en la tornillería: todos los pernos atraviesan 2 o 3 piezas.

**Falso positivo importante, descartado.** La rótula comercial `B_COM_ROTULA_INF_EXT` choca con M01/M02 durante los primeros 950 mm de la traslación. Pero B-COM es la alternativa que R06.2 declaró **no viable** y está oculta en la GUI. Esto llevó a una lección de método: la visibilidad de consola no es la de la GUI (§6).

## 1. Método

| Fase | Herramienta | Archivo | Resultado |
|---|---|---|---|
| 1. Geometría | FreeCAD 1.1 (OCC); booleanos exactos | `scripts/rv01_auditoria_geometrica.py` → `resultados/rv01_*` | 738 objetos con sólido. Se compararon 2 641 pares cuyas cajas se tocan (±0,5 mm), sin errores. Corrida de 160 s |
| 1b. Piezas sueltas | Distancia a la más cercana y apoyo en el piso de referencia (Z 0) | `rv01b_aisladas.py` → `rv01b_aisladas.json` | Distancias de 37 piezas y 4 grupos |
| 1c. Fijaciones y barrido | Piezas a ≤ 1,5 mm de cada perno o pasador; M01/M02 desplazadas de 0 a 3 320 mm en −Y | `rv01c_fijaciones_y_barrido.py` → `rv01c_*.json` | 62 fijaciones; 40 choques, todos con B-COM, que no está vigente |
| 1d. Conjunto vigente | Visibilidad leída de `GuiDocument.xml` de `cad/R07_COMPLETO_COLOR_V10.FCStd`, con los mismos nombres que V11 | `rv04_reanalisis_visibles.py` → `rv04_vigente.json`, `rv00_visibilidad_gui_color_v10.json` | 151 sólidos ocultos en la GUI; 587 vigentes; 168 solapes (27 entre grupos) |
| 2. Segunda opinión | Detección de interferencias de SOLIDWORKS 2024 | `rv02_interferencias_sw.ps1` → `rv02_interferencias_sw.csv`, `rv02_resumen_sw.md` | MES-000: 87; MES-520: 13; MES-521: 5; MES-600: 2; MES-200, 400 y 700: 0 |
| 3. Generadores | Codex en solo lectura: R04, R05, R06.x, R07 y el `Document.xml` de V11 | `resultados/rv03_codex_placeholders.md` | Piezas esquemáticas, uniones pendientes y 7 contradicciones de versión |
| 5. Capturas | matplotlib sobre teselas de FreeCAD | `rv05_teselar_hallazgos.py`, `rv05b_capturas.py` → `capturas/H0x_*.png` | 6 capturas |

**Criterios:**
- **Solape:** volumen común > 0,5 mm³.
- **Contacto:** distancia ≤ 0,1 mm.
- **Pieza suelta:** no toca ni se solapa con nada.

Un solape **no** se cuenta como falla automáticamente, y una distancia > 0 tampoco: se clasificó cada caso con criterio físico (qué la sostiene y qué transmite la carga).

## 2. Hallazgos en el conjunto vigente

**Escala de gravedad:**
- **Alta:** afecta función o seguridad, o lo que se presenta como diseño. Hay que corregirlo o declararlo antes de la P3.
- **Media:** detalle incompleto o representación que puede cuestionarse en la sustentación.
- **Baja:** representación aceptable que conviene declarar.

| ID | Gravedad | Hallazgo | Evidencia | Propuesta | Esfuerzo |
|---|---|---|---|---|---|
| **H01** | **Alta** | **El receptor fijo del bloqueo en la estación LOAD flota**: base y orejas a Z 470–640, sin patas. El de WASH sí tiene patas, las `R06_PATA_RECEPTOR_WASH_IZQ/DER`. La pieza más cercana está a 370 mm | `rv01b_aisladas.json`; captura `H01`; R05:820–826 («Foundation, bearing and weld verification pending») | En V12, copiar las patas de WASH trasladadas a LOAD (Y −4170). La cimentación queda como DATO EXTERNO PENDIENTE | 30 min |
| **H02** | **Alta [VERIFICAR]** | **El pasador de estacionamiento del rotor** (`R04_PASADOR_ESTACIONAMIENTO_ROTOR`, x 150–180, Z 2740–2890) **solo toca su placa base**: no engancha ninguna pieza que gire. D-003 exige el rotor estacionado a 0° para trasladar la mesa | `rv01c_fijaciones_y_barrido.json` (1 pieza a ≤ 1,5 mm); captura `H03` | Verificar si está retraído a propósito. Si no, modelar su receptor en la pieza giratoria (disco o agujero) y mostrarlo enganchado | 30–60 min |
| **H03** | **Alta (implantación)** | **Soporte superior R04 contra los muros de la cabina.** Las 4 columnas SHS150×6 quedan fuera de los muros (\|x\| 2095–2245) y sus placas base (\|x\| ≤ 2320) pasan bajo los muros laterales, con 600 000 mm³ por lado | `rv04_vigente.json`; captura `H02`; Diagnóstico R07 §4 C (soporte superior = trabajo futuro, sin SAP/FEM ni anclajes) | Declararlo en la tesis como limitación (contexto R04). Si se mantiene en las figuras, rotularlo «contexto, no verificado» o recortar las placas base | 15 min para declararlo; 1 h para mover |
| **H04** | **Media–alta** | **El delantal exterior de reserva** (`R06_DELANTAL_EXTERIOR_RESERVA`, declarado `RESERVA_NO_FISICA` en R06v2:381–422) **se ve** y se cruza con 8 soportes de riel: 2,1 L con cada uno | `rv04_vigente.json`; captura `H04`; `rv03` | Ocultarlo o pasarlo a un grupo `NO_VIGENTE`, para que no salga en figuras ni en chequeos | 5 min |
| H05 | Media | Las bandejas eléctricas T5/T6 no tienen soportes: quedan a 7 mm de la columna R04 | `rv01b`; captura `H05` | Agregar ménsulas o declarar que son esquemáticas | 20 min |
| H06 | Media | **Equipos eléctricos sin fijación:**<br>• ATV320 a 0,38 mm de la placa de montaje y CFW300 a 1,0 mm;<br>• placa pasacables a 1,46 mm;<br>• seccionador a 0,5 mm de la puerta.<br>La puerta V9 del Rittal se solapa con el cuerpo (12 975 mm³) y con 3 bisagras (301 mm³ cada una) | `rv01b`; `rv04` | Apoyarlos en la placa; ajustar la puerta | 20 min |
| H07 | Media | **Instrumentos y conexiones sin unir:**<br>• FTL31 ×3 (0,38 mm), TM131 (0,68), LT (5,0);<br>• reposición 1" (3,3), llenado 3/4" (2,65);<br>• WIKA a 9,1 mm del tubo de impulsión;<br>• purga de punto bajo (0,5);<br>• manguera de detergente a 2,0 y 12,5 mm | `rv01b` | Llevar cada uno a su tubuladura o cupla. La mayoría son genéricos (`[placeholder generico]`, `rv03`) | 45 min |
| H08 | Media | **Guarda de la transmisión V9 sin fijación** (a 3 mm de la ménsula). La ménsula V9 se solapa con la tornapunta R04 (2 731 mm³) | `rv01b`; `rv04`; RESUMEN_R07 (solapes heredados aceptados) | Fijar la guarda; recortar la ménsula o declarar el solape | 20 min |
| H09 | Media | Las luminarias IP65 quedan a 10 mm del muro, sin soporte | `rv01b` | Agregar soporte | 10 min |
| H10 | Media | Las patas del receptor WASH atraviesan el piso húmedo (280 000 mm³ cada una), sin pasamuros ni sello | `rv04` | Definir el pase y el sello, o apoyar las patas en la losa bajo el piso | 20 min o declarar |
| H11 | Media | El bloque B-MEC se solapa con el tubo del pie DN15 (1 574 mm³ cada uno): la unión pie–B-MEC (rosca o soldadura) no está definida | `rv04`; `rv03` (R06.2: el portaboquilla no define filete ni sello) | Detalle de unión en el plano P-04 de aspersión, como [VERIFICAR] | — |
| H12 | Media | **Accionamiento R04 representado con envolventes:**<br>• polea motriz contra correa: 814 301 mm³;<br>• correa contra polea conducida: 261 552 mm³;<br>• alojamiento del apoyo inferior contra el resalte axial del eje: 92 394 mm³, sin rodamiento ni sello modelados | `rv04`; RESUMEN_R07 (envolventes de R04) | Declararlo, o modelar el apoyo (rodamiento y sello) en P-05 | Declarar |
| H13 | Media (ya declarada) | **Uniones por solape:**<br>• bastidor N3: 23 solapes, 761 832 mm³, con rigidizadores y el conector del bloqueo;<br>• K2-M: 56 solapes, clasificados como `UNION_PREVISTA` en R06.1.<br>No hay cortes ni preparaciones de junta | `rv04`; `rv02_resumen_sw.md`; D-040 (trabajo futuro) | Tabla de limitaciones del CAD (A5) | Declarar |
| H14 | Media | **El mecanismo de disparo y limitación del K2-M** (varilla, cartucho y resortes) es una reserva funcional: piezas sueltas con holguras de 1,0 a 1,5 mm, sin validar | `rv01b`; `rv03` (K2:255–264, 1197–1219) | Declararlo como HIPÓTESIS funcional y trabajo futuro (ensayo) | Declarar |
| H15 | Baja | **Holguras de ajuste dibujadas sin contacto:**<br>• eje–horquilla de rueda: 0,5 mm radial;<br>• pasador del bloqueo: Ø25 en Ø27 (el buje Ø32/Ø25 H7 de D-050 está en el plano MES-700, no en el CAD);<br>• tirantes de U2: 0,5 mm | `rv01b`; `rv03` (C) | En V12, modelar los bujes de D-050. Lo demás es correcto (es holgura) | 30 min |
| H16 | Baja | **Representaciones aceptables:**<br>• ruedas como envolvente (eje solapado 57 727 mm³ por rueda);<br>• clips Gantrex simplificados (8 750 mm³ cada uno);<br>• piso de referencia sin hueco para pozo y colector;<br>• flotador colgado (sin cable);<br>• bridas de la bomba (≤ 36 mm³);<br>• 4 BRep inválidos de fabricante (ATV320, CRN 15-3 y 2 DDA) | `rv04`; `rv01_resumen.json` | Tabla de limitaciones | Declarar |

## 3. Falsos positivos y casos fuera del conjunto vigente

| Caso | Por qué no es falla vigente | Riesgo |
|---|---|---|
| `B_COM_ROTULA_INF_EXT_A/B` contra M02/M01 (195 mm³; el barrido choca de 0 a 950 mm) | B-COM fue una comparativa **no viable** en R06.2 (`R06.2_rodamiento_skf_c2/LEEME.md`, «B-COM — comparativa no viable en esta implantación»). Está oculta en la GUI y excluida de los barridos de R07 (`r07_barridos_movimiento.py`, `OCULTOS_GRUPOS`) | Sigue en el archivo con el nombre «CANDIDATO». Cualquier proceso que lea la visibilidad de consola la toma como vigente |
| Portaboquillas viejos contra B-MEC (3 408 mm³) | Están ocultos y fueron reemplazados por el B-MEC (`OCULTOS` de R07) | Ídem |
| Lanza y manguera activas contra las guardadas, cadena portamangueras contra la lanza guardada, rodillos activos contra retraídos | Son dos estados del mismo mecanismo; la lanza guardada y los retraídos están ocultos en la GUI | Si alguien muestra los dos estados juntos, parecen choques |
| `CTX_BEARING_REFERENCE` contra el SKF real | Envolvente de referencia, oculta | — |
| Superados `G_R061_SUPERADOS_H9` (22 objetos, cassettes de R05) | Reemplazados por K2-M; en V10 ya chocaban con el poste del manillar | Ídem |

## 4. Contradicciones entre documentos

Las encontró Codex; detalle en `rv03` §C. Ninguna cambia un dato vigente:
- **Manillar:** el plano antiguo 100×125 frente al V11 100×150. Resuelta.
- **Bloqueo:** el alojamiento Ø27 del CAD frente al buje Ø32 del plano. Abierta: ver H15.
- **Material del pasador:** C45 frente a dúplex. Ya corregida en el plano MES-700.
- **Objetivo de centrado:** 1 mm en R04 frente a 5 mm en R05; rige R05.
- **Resistencias del tanque:** 3 × 8 kW frente a 3 × 12 kW. Los de 8 kW están ocultos y rigen los de 12 kW.
- **Diagnóstico del 26/10:** decía que el Caso 2 no estaba aplicado, y V10 ya lo aplicó.
- **SAP:** el LEEME de R06.1 dice «SAP no ejecutado», pero después se ejecutó la etapa lineal v5.7.3. Es una diferencia de fecha, no de contenido.

## 5. Qué falta para una máquina real

Esta lista combina tres fuentes: el Diagnóstico R07 §4, las uniones pendientes que listó Codex (`rv03` §B) y los hallazgos de arriba.

**A. Imprescindible para la P3 (22/11)**

| # | Qué | Base |
|---|---|---|
| A1 | **V12 con correcciones rápidas:**<br>• H01: patas del receptor LOAD;<br>• H04: ocultar el delantal de reserva;<br>• H05/H06/H09: fijaciones eléctricas y luminarias;<br>• H07: conectar los instrumentos;<br>• H08: guarda;<br>• H15: bujes de D-050.<br>Además, aclarar H02 (pasador de estacionamiento) | Este informe; unas 3–4 h |
| A2 | **Tabla de limitaciones del CAD** en la tesis:<br>• uniones por solape (bastidor y K2-M);<br>• envolventes comerciales y de R04;<br>• placeholders genéricos;<br>• soporte superior y planta de cabina como contexto;<br>• mecanismo de disparo como hipótesis | H03, H11–H16; Diagnóstico A5 |
| A3 | **Definir el conjunto vigente de forma explícita:** pasar lo no vigente (B-COM, estados guardado y retraído, superados, reservas, versiones anteriores) a grupos `NO_VIGENTE_*`, o sacarlo del STEP de presentación | §3 y §6 |
| A4 | **Pendientes del Diagnóstico** que siguen abiertos:<br>• figuras CAD (A2 del Diagnóstico);<br>• P&ID y unifilar (A4);<br>• tablas (A5);<br>• control de calidad (A6);<br>• planos P-01 (conjunto general) y P-04 (aspersión con B-MEC y tabla de boquillas) | Diagnóstico R07 §4 A |

**B. Deseable**
- Planos MES-510/530 y el despiece de MES-522 a 525.
- El modelo del apoyo inferior del rotor (H12).
- El accionamiento de la guillotina (Diagnóstico B1), el extractor (B2) y el plano del accionamiento (B3).
- Cotas de catálogo de los placeholders con ficha (B4).

**C. Trabajo futuro** (declarar):
- Detalle de fabricación de las uniones: cortes y unión a momento del bastidor (D-040), WPS e inspección, cordones del K2-M, del tope y del bloqueo.
- Anclajes y cimentación: losa, rieles y receptores (`PENDIENTE_EXTERNO`).
- Soporte superior con SAP/FEM.
- Ensayo del mecanismo de disparo del K2-M.
- Prueba de inserción del pasador del bloqueo («Interlocked proof-of-engagement required», R05:819).
- Selección comercial de los placeholders genéricos: válvulas, flexibles, instrumentos y recipientes.

## 6. Lecciones del método

Se registran también en la wiki y en la memoria.

1. **«Heredado» no es «verificado».** Lo que viene de una revisión anterior se audita con el mismo rigor que lo nuevo, entre sí y funcionalmente, no solo contra lo nuevo.
2. **Un volumen común no es una unión, y una distancia no es un defecto.** Hay que clasificar cada caso:
   - un solape puede representar una soldadura o ser un error;
   - una distancia > 0 puede ser una holgura de ajuste o una pieza flotante.
   La pregunta es física: qué sostiene la pieza y por dónde pasa la carga.
3. **La visibilidad de consola no es la de la GUI.** `Document.xml` no guarda lo que se oculta en la GUI; eso está en `GuiDocument.xml`. Sin definir el conjunto vigente, una alternativa descartada (B-COM) aparece como choque.
4. **Comprobar la fuente antes de escribir un dato.** El material del pasador del bloqueo se puso como C45 por hipótesis, y R05 ya decía dúplex.
5. **Revisar las fijaciones por su función.** Un perno debe atravesar al menos dos piezas con su holgura. Un pasador de bloqueo debe enganchar las dos piezas que bloquea (H02).
6. **Confirmar con una herramienta independiente.** SOLIDWORKS confirmó los mismos patrones que FreeCAD.

## 7. Qué se leyó, qué no y limitaciones

**Se leyó:**
- la geometría completa de V11, en solo lectura;
- `GuiDocument.xml` de la versión coloreada de V10;
- los ensambles de los planos en SOLIDWORKS;
- los generadores R04–R07, a través de Codex, con citas de archivo y línea en `rv03`;
- el Diagnóstico R07 §4 y los LEEME de R06.2 y R07, para B-COM y la lista `OCULTOS`.

**No se hizo:**
- No se abrió la GUI de FreeCAD.
- No se revisaron a mano los 168 solapes uno por uno: se clasificaron por grupo y se inspeccionaron los mayores y los que cruzan grupos.
- No se rehízo el barrido del rotor (V8, vigente). V9, V10 y V11 no cambian lo que gira, salvo LAT_1, ya chequeada en V10.

**Limitaciones:**
- La visibilidad vigente sale de V10 coloreado. V11 solo cambia la forma de los postes del manillar, con los mismos nombres.
- El umbral de contacto de 0,1 mm marca como sueltas las piezas con holgura de ajuste, y se revisaron una por una.
