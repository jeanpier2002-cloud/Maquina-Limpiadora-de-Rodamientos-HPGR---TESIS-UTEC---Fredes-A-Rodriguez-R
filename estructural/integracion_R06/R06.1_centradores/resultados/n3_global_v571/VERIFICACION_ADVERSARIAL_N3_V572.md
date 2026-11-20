# Verificación adversarial: N3 global (Vlasov), travesaño M08 y código v5.7.2 (29/09/2026)

Workflow `verificar-n3-v572` (Claude): tres revisores independientes en modo de refutación, solo lectura. Hallazgos literales a continuación. Sus guiones auxiliares quedaron en el scratch (rev1, v572/rev3_calc.py, grid_resortes.py, sweep1-6.py). Nada de esto libera fabricación.

#####  — VEREDICTO: No encontré errores de signo ni en U1 ni en U3. Tampoco rompe nada el corte del alma. Pero la v5.7.2 no está en condiciones de pasar a FEM ni a SAP.

**Lo que resiste la refutación**
- B, CQ, hex_q, prisma_qz y el taladro del W reflejan bien en −Y.
- Lo comprobé en el BREP guardado de run11\R061_K2M_CANDIDATO.FCStd: CTX_M05 y CTX_M06 son Part::Feature con Placement identidad. Cada uno tiene 2 superficies cilíndricas en X298/478 y Z766,5, con ejes en Y=+570,175 y Y=−570,175, y el volumen retirado es 1236,15 mm³. Por tanto, el recompute no borra los taladros.
- Los CG de las piezas de U3 son el espejo de los de U1.
- El chequeo, los barridos y la sombra leen el W con taladros. M08 (unidad 'N3') no rompe los análisis de nombre: los int(split) solo se aplican a los _ACTIVO.
- El FEM pegado pasa el control de solape: los taladros restan un 0,09 %, frente al límite de 0,995.

**Lo que sí encontré (en orden de gravedad)**
1. **M08 bajo la lanza.** M08, con su cara superior en Z805, queda debajo del pie giratorio de la lanza interior (Z810,29–812,69 y r≈233–373). La holgura es de 5,3–7,7 mm, un riesgo nuevo que D-039 no recoge.
2. **Posición del amarre distinta de D-039.** El CAD pone el amarre en a±90 y Z766,5. D-039 registra a±40 y Z783. Hay que preguntar al usuario y registrar el cambio.
3. **Unión de M08 sin definir.** La mejora de 0,71–0,78 mm en U1 supone una unión rígida. Con una unión 'a tope' solo a cortante, la flecha vuelve a 1,23–1,64 mm.
4. **Cuenta manual optimista.** En U1, el perno de X298 carga unos 5,1–6,1 kN, no 2,88 kN. La tracción total es 6,21 kN, no 5,75 kN. El margen al deslizamiento es de ~1,4, no de 2,40.
5. **El FEM pegado no dice nada del amarre.** Con EXTRA=TALON_, CARTELA_MORDAZA_ y ASIENTO_AMARRE_ la cara B–alma sigue pegada y no hay pernos. Solo mide el alargamiento del collar, con una sola malla y sin convergencia. Es una cota inferior, no una verificación.
6. **Asiento sin función clara.** El asiento B queda a 1 mm de la pared y de la tapa, y bloquea sus cordones. Además incumple la distancia al borde.

**Qué mirar con lupa en el chequeo que está corriendo** (R061_K2M_CHEQUEO.json)
- **Categoría W6X9.** PERNO_TRANSVERSAL_1/2 de U1 y U3 frente a CTX_M06 y CTX_M05. Debe dar unos 0,75 mm y volumen 0. Si aparecen unos 488 mm³ por perno, los taladros se perdieron. M08 frente a M05 y M06 debe dar volumen <0,01, porque solo tienen caras en contacto.
- **Categoría GIRO_R05.** M08 frente a TUBO_LANZA_PIE_DN25, CODO_LANZA_PIE_90/25, TAPA_LANZA_PIE, BOQUILLA_22_INF_INT y la purga. Espero unos 5–8 mm. Lo mismo, luego, en C2_GIRO_E1 y C4 de los barridos (LIMITE_CERCANO de 10 mm).
- **Categoría AUTOINTERFERENCIA.** Revisar toda fila con union_prevista_mm3>0 que incluya tornillería o ASIENTO_AMARRE: en esta categoría el chequeo oculta los choques. Revisar además las distancias ASIENTO_AMARRE_B frente a PARED_LATERAL y PLACA_SUPERIOR; debe salir 1,0 mm.
- **Categoría HUELLA_805_890.** M08 aparecerá a 0 mm porque toca el plano Z805. Es contacto de cara, no invasión.
- **Categoría PIES_TRASLADO.** M08 frente a los pies de la U debe dar 18,8 mm.
- **Categorías R06_OTROS y PUERTA.** Sin cambios esperados.

**Qué leí**
- _hacer_v572.py y V7 completos.
- La comparación del generador v572 con el v571_base (la copia es idéntica).
- R061_K2M_CANDIDATO.json y R061_K2M_GENERACION.json.
- bbox_v571.json, D-034 a D-039, K6 y V6.
- r061_chequeo_k2m.py y partes de r061_barridos.py y r061_sombra_exterior.py.
- _fem_u1_v572.py, con su comparación contra el script del repositorio y contra _fem_u3_v572.py.
- INFORME_N3_GLOBAL_V571.md, SENS_TRAVESANO_POSICIONES.json y r061_n3_sens_travesano_v571.py.
- R061_ENVOLVENTES_PROHIBIDAS.json, movimientos_r05.json y el BREP y Document.xml de los FCStd (leídos como zip).

**Qué no hice**
- No ejecuté FreeCAD ni CalculiX.
- No modifiqué ningún archivo. Solo creé el cálculo auxiliar scratchpad\r06\v572\rev3_calc.py.
- chequeo_log.txt estaba vacío, así que el chequeo sigue en curso.

- [alta] El travesaño M08 (ala superior en Z805) queda justo debajo del pie de la lanza interior giratoria. La holgura vertical nominal es de unos 5,3–7,7 mm. HPGR D-039 no incluye este riesgo: menciona PAD, drenaje, puerta, traslado y sombra, pero no la lanza.
  EFECTO: Holgura nominal de 805 a 810,29–812,69, es decir, 5,3–7,7 mm. Es un 28–41 % de los 18,8 mm de referencia y no tiene presupuesto de tolerancias, flecha de la lanza, excentricidad del rotor ni flecha de N3. No es interferencia nominal, pero es un hallazgo nuevo de la v5.7.2.
  ARREGLO: En el chequeo y en los barridos C2/C4, revisar los pares M08 frente a TUBO_LANZA_PIE_DN25, CODO_LANZA_PIE_90/25, TAPA_LANZA_PIE, la purga y BOQUILLA_22. Hay que preguntar al usuario antes de aceptar la solución. Opciones: (a) bajar M08 para que su cara superior quede en Z≤~790 (canto menor o unión rebajada), recalculando la parrilla; (b) otra sección o posición fuera de r≈390, que choca con la mordaza (X273–503); (c) presupuesto formal de holgura aprobado.

- [alta] El amarre generado no coincide con la decisión registrada. D-039 fija los M12 en X=a±40 y Z=783 (opción A de V6, arandelas Ø30). El CAD v5.7.2 los pone en X=a±90 y Z=766,5, con arandelas Ø24, y alarga el collar a a±115. El cambio no está en DECISIONES.md.
  EFECTO: El brazo supuesto pasa de 121 a 104,5 mm y la tracción total de 4,97 a 5,75 kN (+16 %). Los taladros de N3 cambian de sitio: X348/428 → X298/478 y Z783 → 766,5. Todo el cribado de D-039 sobre flexión del alma (~155 MPa) se hizo con la posición a±40, Z783.
  ARREGLO: No dar por buena la v5.7.2 frente a D-039 sin preguntar. Hay que presentar al usuario los dos valores con sus fuentes y registrar la enmienda (HPGR D-040 o una enmienda de D-039) antes de seguir con FEM o SAP. Motivo aparente del cambio: en Z783 el agujero sobrepasa el collar (Z789,75 > 786,5) y la arandela choca con el acuerdo R6.

- [alta] El beneficio global del travesaño depende de una unión rígida a momento que el CAD no tiene. La parrilla de Vlasov modela M08 como barra continua con 'uniones ideales'. En el CAD, M08 va 'a tope': las alas se cortan en la punta de ala de M05/M06 (Y±524,137), el alma toca la cara del alma (Y±572,016) y la unión figura como NO_MODELADA. Además, el W6x9 del CAD no tiene acuerdos alma–ala, así que el tope real del alma de M08 choca con el radio k sin despunte.
  EFECTO: Con unión solo a cortante, el travesaño apenas restringe la torsión y la flecha vuelve a la base: U1 1,23–1,64 mm y U3 0,95–1,31 mm a Z955, frente a 0,71–0,78 y 0,51–0,57 con continuidad (SENS_TRAVESANO_POSICIONES.json, base frente a X200). Eso incumple el criterio de ≤1,0 mm de D-034. Radio k del W6x9 ≈ 11,8 mm (≈6,4 mm de acuerdo): el alma de M08 necesita un despunte de ~12 mm arriba y abajo.
  ARREGLO: Especificar la unión a momento: CJP ala–punta de ala o placas de continuidad, con doble filete del alma y despuntes. Comprobar la punta de ala de M05/M06 bajo la fuerza de ala (M/d). Hacer además una sensibilidad de la parrilla con la unión semirrígida o articulada. Mientras tanto, citar los 0,71–0,78 mm solo como 'unión rígida HIPÓTESIS'.

- [media] La cuenta manual del amarre es optimista. (1) Toma la reacción horizontal inferior en Z662. Con el chaflán de 13 mm, el contacto B–alma empieza en Z673,6 y el labio solo aporta rozamiento en q. (2) Reparte la tracción por igual entre los dos pernos. En U1 la línea de acción de Fq está en X≈324 y hay un par Mz, así que el perno de X298 se lleva casi toda la tracción. (3) El deslizamiento compara μN con |F|=2,121 kN. Esa resultante incluye la componente normal a la cara (2,05 kN, que resisten los pernos) y omite el momento en el plano Fx·(955−766,5).
  EFECTO: - Tracción total con la reacción en Z673,6: T=2050·(955−673,6)/(766,5−673,6)=6,21 kN, un 8 % más que 5,75 (7,10 kN si el contacto sube a Z690).
- Reparto en U1 con cuerpo rígido: el perno de X298 lleva el 98–100 %, unos 5,1–6,1 kN, es decir, 2,1 veces los 2,88 kN. U3 queda repartido de forma casi uniforme (42–53 %).
- Deslizamiento: la cortante en el plano es Fx≤1,29 kN y el momento en el plano Fx·188,5 ≈ 0,24 kN·m, unos 1,35 kN por perno. Resultante por perno ≈ 1,50 kN frente a μ(15,6−5,3) = 2,06 kN: margen ≈ 1,37, no 2,40 (HIPÓTESIS sin reparto con el labio).
- La descompresión por perno sigue siendo positiva: 15,6/6,1 ≈ 2,6.
  ARREGLO: Rehacer la cuenta: reacción inferior en Z≥673,6, reparto por palanca con Fq en X real y Mz, ambos signos, U1 y U3 por separado, y deslizamiento con cortante y momento en el plano del grupo (compartido o no con el labio). Mantener 26 kN y 15,6 kN como HIPÓTESIS y especificar el método de apriete.

- [media] El FEM pegado con R061_FEM_EXTRA=TALON_,CARTELA_MORDAZA_,ASIENTO_AMARRE_ no representa el amarre. La unión B–alma ya está pegada: está cerrada por construcción, no hay pernos, ni pretensión, ni taladros en su W, y el talón pegado trabaja a tracción. Solo mide el efecto de alargar collar, labio y contraplaca de 150 a 230 mm. Además corre con una sola malla, así que no hay convergencia.
  EFECTO: Cabe esperar un δ local igual o menor que los 0,64/0,59 mm de v5.7.1, porque el collar es más largo. No aporta nada sobre la apertura B–alma, que fue la causa de D-037 (1,0–1,4 mm de abertura mediana y 3,3–6,2 mm a Z955 en el modelo de contacto). Si se usa como 'parte local' de δ_total, subestima la flecha real de la unión atornillada (≈ +0,3 mm aun con la junta cerrada, K6).
  ARREGLO: Presentarlo solo como cota inferior y sensibilidad a la longitud del collar. Para validar la v5.7.2 hace falta el FEM de contacto (r061_fem_contacto_v571.py) reconstruido con taladros en el W, pernos a±90 con pretensión de 15,6 y 26 kN, holgura de agujero, contacto B–alma y A–alma y talón solo a compresión, en ambos signos y al menos dos mallas. R061_FEM_EXTRA no cambia ese guion.

- [media] ASIENTO_AMARRE_B queda a 1 mm nominal de PARED_LATERAL_1/2 y de PLACA_SUPERIOR, y ese hueco ocupa el pie del cordón exterior de la caja al collar. Sus distancias al borde del agujero no cumplen el mínimo de EN 1993-1-8. Con los pernos en a±90 ya no hay acuerdo R6 que librar: su función real es la de una arandela gruesa que añade dos interfaces al paquete apretado.
  EFECTO: - El cordón exterior pared–collar queda bloqueado en Z750,5–770: 19,5 de 65 mm (30 %) por cada pared. El mismo hueco de 1 mm afecta a la tapa.
- Filete mínimo recomendable para chapa de 13,8 mm: ~6 mm, frente a 1 mm disponible.
- Distancias al borde del asiento: e_X = 14 mm y e_Z = 16 mm, menores que 1,2·d0 = 16,2 mm.
- Pérdida extra de pretensión por asentamiento de dos interfaces más: del orden de 1 kN [VERIFICAR, VDI 2230].
  ARREGLO: Quitar los asientos A/B, con la arandela directamente sobre el collar, o hacerlos parte integral del collar (más espesor local). Si se mantienen: ancho ≥ 2·16,2 en X y holgura ≥ 8–10 mm a la caja. En el chequeo, revisar la distancia ASIENTO_AMARRE_B frente a PARED_LATERAL y PLACA_SUPERIOR: se espera 1,0 mm.

- [media] El chequeo en curso no puede detectar choques de tornillería de la misma unidad: cualquier solape entre piezas FIJO de la misma unidad se clasifica como UNION_PREVISTA y se pone interferencia=False. Eso incluye pernos, arandelas y tuercas desmontables. Tampoco hay radios k en el W del CAD.
  EFECTO: Un choque real perno–placa en U1/U3 aparecería solo en union_prevista_mm3. Por geometría analítica no espero ninguno (vástago r6 frente a agujeros r6,75; cabeza, arandelas y tuerca en contacto de cara), pero el chequeo no lo demuestra.
  ARREGLO: Al leer R061_K2M_CHEQUEO.json, filtrar las filas AUTOINTERFERENCIA con union_prevista_mm3>0 en las que aparezca *_TRANSVERSAL_*, ASIENTO_AMARRE_*, PERNO_*, ARANDELA_* o TUERCA_*: cualquier volumen ahí es un choque. En una versión posterior, dar a la tornillería un grupo rígido propio.

- [baja] M08 se da de alta como pieza de K2-M: agregar(..., n=0) con origen 'R06.1 K2-M / HPGR D-029'. Así entra en MASAS y en los totales de K2-M. Además, las cadenas de revisión del chequeo y de los barridos están fijadas en el código y no dicen v5.7.2.
  EFECTO: La 'masa K2-M' sube 23,7 kg, de los que 14,4 kg (61 %) son estructura N3. El CG X pasa de −169 a −40 mm. Hay riesgo de contar dos veces esos 14,4 kg en la tabla de cargas SAP si M08 también se modela como barra con peso propio. Los resultados de run11 pueden confundirse con los de v5.7.1.
  ARREGLO: Separar M08 en los totales (por ejemplo, centrador 'N3', origen D-039) y etiquetar como v5.7.2 las salidas del chequeo y de los barridos en el anexo de trazabilidad.

- [baja] Otros detalles de la tornillería y de las extensiones:
(a) Con una tuerca ISO 4032 M12 real (m=10,8), el perno M12×60 sobresale ~1,2 mm, menos de un paso (1,75 mm); la tuerca modelada tiene 10 mm.
(b) El labio, la contraplaca y los talones se extienden hasta a±115, pero los M12 verticales siguen en a±50: los tramos entre a±75 y a±115 quedan sin apriete vertical.
(c) movimientos_r05.json sigue listando M05/M06 en CONTEXTO_R05_SIN_MODIFICAR.
  EFECTO: (a) Falta ~0,5–1 mm de rosca. (b) 40 mm por extremo de talón y labio sin apriete. (c) Una regeneración que tome los W de R05 perdería los taladros sin avisar: el control de penetración del generador compara con W en memoria y ya no con los taladros.
  ARREGLO: Usar M12×65. Si los talones extendidos deben trabajar, llevar lainas o pernos a los extremos, o recortarlos a a±75. Anotar M05/M06 como modificados por D-039 en el inventario de la copia.

#####  — VEREDICTO: No encontré errores en la implementación.
- **Elemento y transformación:** las matrices de flexión, la transformación para barras en Y y la torsión de Hermite GJ + E·Cw son correctas.
- **Cotas de alabeo:** el reparto de GDL es coherente con lo que el guion declara.
- **Casos y signos:** la combinación de ENV208 y la asignación s+1 → SP y s−1 → SM de la parte local son correctas. Lo comprobé con las fuerzas del FEM frente a las de la Tabla B.
- **Coeficientes de §5.2:** son correctos.
- **Doble conteo:** no lo hay. El FEM de 800 mm y la viga que se le resta tienen los mismos empotramientos.
- **Reproducción:** reproduje 1,637/1,232 mm (base) y 0,779/0,706 mm (travesaño en X=200).

**«Sin travesaño, U1 supera 1,0 mm»:** se sostiene en la cota LIBRE en todas las variantes que probé:
- apoyos: 1,29 mm con Y restringido en las 4 ruedas;
- sesgo conservador de la superposición: ~1,45 mm;
- casos FALLO_EMP y con un solo datum: 1,70–2,66 mm.

En IMPEDIDO no es robusta. Si la traslación en Y se restringe también en J13/J16, U1 baja a 0,889 mm y cumple.

**«Con travesaño W6x9 en X=200 queda en 0,71–0,78 mm»:** no se sostiene tal como está redactada. Solo vale si se dan a la vez cinco supuestos favorables no verificados:
1. unión del travesaño rígida a momento (articulado: 1,56/1,13 mm; hace falta k ≳ 1e8 N·mm/rad);
2. parte local del FEM pegado, que es una cota inferior de la flexibilidad (con K6 +0,32 mm: 1,10/1,03 mm);
3. ENV208 tomado como envolvente (FALLO_EMP s2=+: 0,86/0,80 mm; con K6: 1,18/1,12 mm);
4. M07 rígida (ART: 0,98/0,73 mm);
5. aro sostenido solo por la grúa (RG).

El travesaño es eficaz y probablemente necesario. Pero la frase de INFORME:74 («margen de ~25 % … aún con la parte local del FEM pegado») es incorrecta en su lógica y debe quedar como HIPÓTESIS. Antes de proponer el travesaño para el CAD hace falta:
- especificar la unión a momento y verificar su rigidez;
- recalcular con la parte local atornillada (v5.7.2);
- añadir FALLO_EMP, ASIM y NOM_V2;
- añadir la variante ART;
- definir la retención en Y.

Guiones de revisión, sin tocar el proyecto, en C:\Users\<usuario>\AppData\Local\Temp\claude\C--Users-enriq-Documents-Codex-2026-07-06-ho\7cc8ba95-012d-479a-9d89-b713f0aefa81\scratchpad\rev1\: grid.py y t1.py a t6.py.

- [alta] El travesaño solo funciona si su unión con M05/M06 transmite momento. El modelo lo conecta como continuidad rígida y el informe no dice que haga falta una unión a momento. Con una unión de alma (clip atornillado o chapa de cortante) vuelve a fallar.
  EFECTO: Travesaño en X=200, U1 total (LIBRE/IMPEDIDO):
- articulado: 1,555/1,127 mm;
- k=1e7 N·mm/rad: 1,322/0,987;
- k=3e7: 1,180/0,949;
- k=1e8: 0,988/0,871;
- k=1e9: 0,808/0,738;
- rígido: 0,779/0,706.

En X=300, articulado: 1,546/1,057. Para quedar bajo 1,0 mm en LIBRE hace falta k ≳ 1e8 N·mm/rad. Un clip de alma típico para un W6 está en ~1e7–3e7 y no llega; la unión rígida supone ≳1e9.
  ARREGLO: Declarar como condición del resultado una unión a momento: alas del travesaño soldadas a tope a las alas de M05/M06 (son coplanares, las dos de 149,9 mm), o chapa de testa con rigidizadores. Añadir la curva δ–k_rx y el caso articulado a SENS_TRAVESANO. Verificar la rigidez real de la unión con un FEM local del nudo antes de dar por buena la medida.

- [alta] La parte local sale del FEM pegado, que es la unión más rígida posible, y no una cota conservadora. El informe dice que el margen de ~25 % se mantiene "aún con la parte local del FEM pegado", como si el pegado fuera desfavorable. Al sumar la flexibilidad atornillada que el propio informe cita (K6), el travesaño deja de cumplir.
  EFECTO: Travesaño en X=200, ENV208_PPP con K6: U1 = 0,779+0,32 = 1,10 mm (LIBRE) y 0,706+0,32 = 1,03 mm (IMPEDIDO). En X=300: 1,05/1,03 mm. En X=388 (inviable por la mordaza): 1,06/1,06 mm. El margen "~25 %" pasa a un exceso de 3–10 %. Con la apertura del FEM de contacto el exceso sería mucho mayor.
  ARREGLO: Reescribir INFORME:74. El total con la parte local pegada es una cota inferior de la flexibilidad local. Dar también la columna con +0,32/+0,30 mm (K6) y dejar la conclusión del travesaño pendiente de la v5.7.2 (amarre B–W), marcada HIPÓTESIS.

- [alta] ENV208, con las tres unidades a 2 080 N a la vez, no es envolvente de δ. La carga de U3 reduce la flecha de U1 (y al revés) en ~1,3 mm, así que los casos con el otro datum menos cargado dan más flecha. Se procesó solo ENV208, aunque FALLO_EMP está en la lista mínima de casos.
  EFECTO: FALLO_EMP s2=+, U1 total:
- base: 1,704/1,339 mm (frente a 1,637/1,232 de ENV208_PPP);
- travesaño X=200: 0,861/0,795 mm (frente a 0,779/0,706). El margen baja de ~22 % a ~14 %, y con K6 (+0,32) queda en 1,18/1,12 mm.

Con un solo datum en contacto (U1_SP+U2, U3 = 0, aro sostenido por la grúa): base 2,66/2,27 mm; con travesaño 1,47/1,40 mm.

NOM_V2_PPM base: U1 1,19/0,88 mm.
  ARREGLO: Tratar ENV208 como un caso más y no como envolvente. Evaluar δ con FALLO_EMP (s2 = ±), ASIM (μd = 0 y 0,30) y NOM_V2, o bien maximizar δ1 sobre 0 ≤ N3 ≤ 2 080 compatible con el equilibrio del aro. Corregir la tabla de §3.3 y la lectura D-034 del informe.

- [media] No se evaluó la variante ART de la unión M07–M05/M06, que el requerimiento exige. Además, la cota "LIBRE" no es un máximo: mantiene el alabeo continuo de M05/M06 a través de M07. Si el perfil se interrumpe en esa unión, la flecha casi se duplica.
  EFECTO: Base, U1 (LIBRE/IMPEDIDO):
- ART: 7,16/1,41 mm;
- alabeo partido: 2,96/1,23 mm.

Travesaño en X=200, U1:
- con M07 ART: 0,98/0,73 mm (margen de ~2 % en LIBRE, y >1,0 mm con K6);
- con alabeo partido: 0,85/0,71 mm.
  ARREGLO: Correr y reportar ART. Documentar el detalle real de la unión M07–M05/M06 (continuidad de las alas de M05/M06 en X = 663) y, si es incierto, añadir la cota de alabeo partido como límite superior real. Corregir la descripción de LIBRE en el docstring y en INFORME:13.

- [media] La conclusión "U1 no cumple en ninguna de las dos cotas" no se sostiene en IMPEDIDO: cambia según dónde se restrinja la traslación en Y (dirección de marcha). La mitad de δ_global viene del desplazamiento en planta Uy de J18, que depende de un apoyo sin verificar (bloqueo o freno solo en J2).
  EFECTO: Con Y restringido en las 4 ruedas:
- base U1: 1,295 (LIBRE) / 0,889 mm (IMPEDIDO), que cumple en IMPEDIDO; antes 1,637/1,232;
- travesaño X=200: 0,547/0,475 mm.

Con X restringido en las 4 ruedas: variación < 0,01 mm, lo que confirma INFORME:28.
  ARREGLO: Definir con el CAD R05 dónde y con qué rigidez se retiene la mesa en Y durante el centrado (bloqueo, freno de cadena o guiado de las ruedas) y correr ambas variantes. Declarar en el informe que el veredicto en IMPEDIDO depende de ese apoyo.

- [media] Solo se modela el apoyo RG (el aro colgado de la grúa, sin enlaces con los PAD). El requerimiento pide también RP10, con enlaces horizontales PAD–aro, que acoplan el giro de M05/M06 en J7/J8 (la cara del PAD está a +159,9 mm del eje) y el desplazamiento en planta.
  EFECTO: No cuantificado: requiere modelar el aro como cuerpo rígido con enlaces. Es probable que RP10 reduzca δ (el aro funciona como diafragma), pero la referencia de δ pasa a ser relativa al aro, y el estado solo es físico si |V| ≤ μN en los PAD.
  ARREGLO: Añadir RP10 lineal a la parrilla (nudo B, tres enlaces PAD y contrapartidas R_Ui) y medir δ relativa al aro. Hasta entonces, limitar las conclusiones a RG.

- [baja] Hay dos problemas en el análisis de D-031. Se compara d·u₂ de ENV208 con |d| nominal de la v5.7 (0,75 mm), cuando la referencia de ENV208 es 1,08 mm y D-031 se evalúa con NOM_V2. Además, se omite δ2 (U2, empujador), necesario para la carrera de captura; el travesaño no lo mejora.
  EFECTO: NOM_V2 base: |d| ≈ 1,70/1,17 mm (LIBRE/IMPEDIDO), frente a 0,74 mm del FEM local. Con travesaño, δ1 baja a 0,54/0,49 mm, pero δU2 global sigue en 0,99/0,70 mm; con la parte local de U2 (0,63 mm/kN × 1,45) queda ≈ 1,6–1,9 mm. La carrera de captura base (10,38 − 1,70 − 1,9 ≈ 6,8 mm) sigue ≥ 5 mm: no cambia el veredicto, pero corrige la comparación.
  ARREGLO: Rehacer el párrafo D-031 con NOM_V2 (y ENV208 solo como sensibilidad frente a 1,08 mm), con la fórmula de |d| y la de d·u₂ por separado, e incluir δ2 = δ_global,U2 + δ_local,U2.

- [baja] La superposición global + local tiende a sobreestimar, porque la parrilla no incluye la rigidización local de la mordaza. Esto no invierte el veredicto en LIBRE, pero reduce el exceso en IMPEDIDO y el travesaño queda algo mejor.
  EFECTO: Escalando el sobrecálculo (~24 % de la parte torsional en 1 860 mm) al término de torsión de ENV208_PPP (a_R1·R1 = 0,39 mm en IMPEDIDO y 0,79 mm en LIBRE), el sesgo es de ≈ −0,09 a −0,19 mm. Base: U1 ≈ 1,14/1,45 mm, que sigue superando 1,0 mm.
  ARREGLO: Citar el sesgo en la lectura y, si se quiere afinar, validar con un FEM de la subestructura M06+M07+M01/M02 con la mordaza.

- [baja] La parte local mezcla puntos de medida y cargas distintos. El FEM mide en el alojamiento del pivote, no en el contacto, y aplicó T_piv con R735 (M_z unos 10,4 N·m menor con s = +1). La viga de Vlasov de 800 mm que se le resta usa el contacto y las cargas de la Tabla B.
  EFECTO: Término R3 en la viga de 800 mm: −0,003 mm. Omisiones del FEM: ~+0,02 mm. Efecto del T_piv reducido en la parte local s+1: menos de ~0,03 mm. En total ≤ ~0,05 mm, subestimando la parte local con s = +1.
  ARREGLO: Tomar δ del FEM en el contacto (o en el centro del rodillo) incluyendo el giro del alojamiento alrededor de Z, y repetir el FEM de la v5.7.2 con las cargas de la Tabla B (contacto en R710).

- [baja] Algunos controles son más débiles de lo que se presentan. El "equilibrio global" de Claude es casi tautológico: suma K·u, que se anula por la invariancia de sólido rígido de K para cualquier u. El contraste de Codex comparte todas las hipótesis de modelado (definición de LIBRE e IMPEDIDO, apoyos, cargas y coeficientes) y solo prueba la aritmética.
  EFECTO: Sin efecto numérico. Riesgo de sobreconfianza: la "verificación independiente" no cubre ninguno de los supuestos de los hallazgos anteriores.
  ARREGLO: Sustituir el control por la comparación de reacciones con cargas (ΣR + ΣF, usando solo los GDL fijos) y por el residuo en los GDL libres. En el informe, presentar el contraste de Codex como verificación de implementación, no de modelo.

- [baja] Hay pequeñas omisiones de carga y un error en la explicación del mecanismo del travesaño.
  EFECTO: Peso de K2-M: ≈ +0,01 mm en δ1. El mecanismo no cambia los números.
  ARREGLO: Incluir G_K2M_ACT en los casos. Explicar que el travesaño funciona como apoyo flexional del giro de M06 contra M05, no como equilibrio de torsores.

#####  — VEREDICTO: La parrilla da 0,71–0,78 mm en U1 y 0,51–0,57 mm en U3 con el travesaño en X = 200, pero solo porque supone uniones rígidas en los seis GDL. Esa conclusión depende del detalle de unión: con los detalles plausibles se refuta en parte, y con el detalle adecuado se sostiene.

Resultados con la parrilla copiada de resolver() y resortes en memoria. Reproduce exactamente SENS_TRAVESANO_POSICIONES: 0,7788/0,7064 mm.
- (a) Soldada solo al alma: k_RX ≈ 1,3e8–8e8 N·mm/rad, frente a 2EI/L = 2,38e9. Al recortar las alas, además, RZ ≈ 0. U1 libre queda entre 0,96 y 1,06 mm, y el alma plastifica localmente.
- (b) Rigidizadores de altura completa en el lado opuesto: k_RX ≈ 1,6–1,9e9, suficiente por sí solo (+0,017 mm). Pero sin continuidad de alas RZ ≈ 0 y U1 = 0,913 mm. Con M07 semirrígida, 1,017 mm.
- (c) Placas o soldadura a tope entre alas: k_RX ≈ 1,6e10 y k_RZ ≈ 1,4e9. U1 = 0,803/0,731 mm y U3 = 0,592/0,527 mm; se conserva el ~97 % del beneficio.
- Unión atornillada a cortante (k ≈ 0): 1,44/1,01 mm, con lo que se pierde casi todo el beneficio.

Uniones existentes:
- M07–M05/M06 es del mismo tipo que la del travesaño. Si va solo al alma, la base sin travesaño empeora a 2,07–7,1 mm (U1 libre). Con el travesaño (c), el resultado se mantiene en 0,87 mm.
- La continuidad RZ en las esquinas M05/M06–M01/M02, junto con los apoyos del s2k (solo J2 restringe U2), gobierna el término lateral U2. Es el mayor término de la δ global: 0,285 de 0,426 mm. Con RZ = 0 en esas esquinas, el travesaño rígido da 1,094 mm (no cumple). Con U2 restringido en las cuatro ruedas, 0,58 mm.
- La cota IMPEDIDO supone una restricción del alabeo que una unión al alma no da. El rango físico con uniones rígidas es ≈ 0,77–0,78 mm, no 0,71–0,78. INFORME:86 es incorrecto.

Detalle mínimo propuesto (HIPÓTESIS, pendiente de CAD y de interferencias con el aro: ala superior a Z805, cara inferior del aro a ~Z890):
- Travesaño W6×9 con el alma recortada solo lo necesario para librar el acuerdo, y con soldadura de filete por ambas caras al alma de M05/M06 (cortante y axil).
- Continuidad de alas arriba y abajo en los dos extremos: soldadura a tope de penetración completa de cada ala contra la punta del ala de M05/M06, o placas de empalme PL 6–8 × ~90 soldadas en todo el contorno sobre el ala superior y bajo el ala inferior.
- El rigidizador opuesto es opcional con este detalle.
- Criterios: k_RX ≥ 2e9 y k_RZ ≥ 1e9 N·mm/rad.
- Además: comprobar la unión de M07 y las esquinas M05/M06–M01/M02 en el CAD R05 con el mismo criterio de continuidad de alas, o garantizar y documentar la restricción lateral de las cuatro ruedas.

Qué leí: r061_n3_portico_vlasov.py, r061_n3_sens_travesano_v571.py, r061_n3_delta_total_v571.py, la cabecera de r061_n3_ccx_portico.py, INFORME_N3_GLOBAL_V571.md, el requerimiento (§2.1, §3.2–3.4 y §5.4), la fila D-039 y 12_README_R05.md:21.

Qué no leí: el CAD, el contenido de V6/K7 (solo búsqueda de texto) y el FEM local.

No modifiqué ningún archivo del proyecto ni ejecuté FreeCAD o CalculiX. Los guiones propios están en C:\Users\<usuario>\AppData\Local\Temp\claude\C--Users-enriq-Documents-Codex-2026-07-06-ho\7cc8ba95-012d-479a-9d89-b713f0aefa81\scratchpad\ (grid_resortes.py, placa_alma.py, plano_b.py, sweep1–6.py, apoyosY.py y comp.py).

- [alta] Si el travesaño se suelda solo al alma de M06/M05 (opción a: alas recortadas y alma soldada al alma), la unión es mucho más flexible que el travesaño. La delta vuelve a acercarse a 1,0 mm y el alma plastifica localmente. Una unión atornillada simple (cartela o angulares a cortante) anula casi todo el beneficio. D-039 deja abierta la unión («soldada o atornillada [VERIFICAR]»).
  EFECTO: Referencias del travesaño (L = 1148,35 mm): EI/L = 1,19e9; 2EI/L = 2,38e9 (curvatura simple, torsores opuestos); 4EI/L = 4,75e9 N·mm/rad. Rigidez de la opción (a), flexión fuera del plano del alma: 1,4e8 N·mm/rad con soldadura de 100 mm y bordes articulados en las alas; 4,5e8 con 120 mm articulada; 1,1e9 con 120 mm empotrada. En serie con el tramo recortado (EI_alma/Lc = 2,4e9 para hc = 120 y Lc = 52) queda en ≈1,3e8–8e8, es decir, el 5–35 % de 2EI/L. Momentos en la unión a ENV208: 195–285 N·m (PPP y MMM). δ total a Z955 (U1 libre/impedido): unión rígida 0,779/0,706. Solo el giro RX flexible: k = 1e9 → 0,808/0,738; 4,5e8 → 0,841/0,769; 1,5e8 → 0,935/0,840. Además, el recorte de las alas anula la continuidad RZ del hallazgo 2: con 4,5e8 → 0,957/0,886 mm; con 1,4e8 → 1,060/0,962 mm (U1 libre > 1,0). El margen del ~25 % de INFORME:74 desaparece. Unión a cortante o atornillada con holgura de agujero (holgura de ~15 mrad frente a 0,5–0,7 mrad de trabajo, luego k ≈ 0): 1,438/1,011 mm en U1 y 1,158/0,777 mm en U3. Por la redistribución, el cálculo a mano a_R1·M/k sobrestima: con k = 1,4e8 da 0,41 mm, frente a +0,16 mm de la parrilla. Tensión elástica en el alma de M06, en los extremos de la soldadura, con M = 285 N·m: 330–720 MPa, mayor que Fy = 250 MPa. Es un pico singular que depende de la malla, pero indica plastificación local y una rigidez real menor.
  ARREGLO: No usar la unión solo al alma ni la unión atornillada a cortante. Adoptar la opción (c): continuidad de alas; el detalle mínimo está en el veredicto. Si se atornilla, que sea una unión de momento pretensada, de deslizamiento crítico y sin holgura efectiva. Criterios: k_RX ≥ 2e9 N·mm/rad (≈ 2EI/L; pérdida ≤ 0,015 mm) y k_RZ ≥ 1e9 N·mm/rad.

- [alta] El requerimiento del revisor no considera la continuidad en RZ (flexión de eje débil en planta) entre el travesaño y M05/M06, y esa continuidad pesa más que la rigidez RX. Cualquier detalle con las alas del travesaño recortadas, como (a) o (b), la pierde: el alma sola tiene I débil ≈ 805 mm⁴, así que k_RZ ≈ 3e6 N·mm/rad ≈ 0. Por eso los rigidizadores de altura completa (b) no bastan.
  EFECTO: Con RX rígida y RZ = 0: U1 pasa de 0,779/0,706 a 0,895/0,823 mm (+0,116, +15 %) y U3 a 0,671/0,605. RZ = 1e8 → 0,869; 3e8 → 0,840; 1e9 → 0,808; 3e9 → 0,791 mm. La referencia 4EI22/L del travesaño es 6,4e8. Opción (b), en tensión plana QM6 con malla de 1 y 2 mm: k_RX = 1,62e9 (ts 6), 1,76e9 (ts 8) y 1,86e9 (ts 10) N·mm/rad, gobernada por el alma recortada; con hc = 110 baja a 1,34e9. Con RZ rígida, (b) daría 0,796/0,726 mm (pérdida de 0,017), pero con RZ ≈ 0 da 0,913/0,843 mm. Liberar la torsión del travesaño (RY) en un extremo no influye (0,779).
  ARREGLO: El detalle tiene que dar continuidad a las alas: placas de ala o soldadura a tope de las alas del travesaño con las de M05/M06. Con k_RX ≈ 1,6e10 y k_RZ ≈ 1,4e9 (placas PL 8×80, cálculo a mano), U1 = 0,803/0,731 mm y U3 = 0,592/0,527 mm: se conserva el ~97 % del beneficio.

- [alta] La unión existente M07–M05/M06 también se supone rígida, y es del mismo tipo que la del travesaño: M07 llega al alma de M05/M06 en J9/J11 y restringe su torsión con su flexión de eje fuerte. Si es una unión solo al alma, la referencia «sin travesaño» de D-039 (1,20–1,64 mm) está muy subestimada. Con el travesaño, la conclusión se sostiene solo si el travesaño tiene continuidad de alas.
  EFECTO: Sin travesaño, U1 libre/impedido: M07 rígida 1,637/1,232; k_RX = 1e9 → 1,843/1,270; 4,5e8 → 2,074/1,294; 1,5e8 → 2,768/1,327; articulada → 7,104/1,362 mm. Con k_RX = 4,5e8 y RZ = 0 → 2,126/1,346 mm. Con travesaño rígido y M07 a 4,5e8: 0,831/0,716 mm. Travesaño (b) con M07 flexible (RX 4,5e8, RZ 0): 1,017/0,901 mm, U1 > 1,0. Travesaño (c) con esa misma M07: 0,866/0,750 mm, se cumple. Travesaño (b) con M07 articulada: 1,015/0,748 mm.
  ARREGLO: Revisar en el CAD R05 cómo está resuelta la unión de M07 con M05/M06. Si es solo al alma, aplicarle la misma continuidad de alas, o al menos declarar la cota flexible. Correr en la parrilla y en SAP la variante ART de §5.4 más una variante semirrígida con k ≈ 4,5e8.

- [alta] En las esquinas M05/M06–M01/M02, la continuidad RZ (flexión de eje débil de M05/M06 hacia M01/M02) junto con los apoyos del s2k (solo J2 restringe U2) gobierna el término lateral U2, que es el mayor de la δ global. Si esas uniones son solo al alma, U1 vuelve a superar 1,0 mm aun con el travesaño rígido. RX y RY en esas esquinas pesan poco.
  EFECTO: Travesaño rígido con RZ de M01/M02 = 0: U1 1,094/1,021 mm y U3 0,733/0,668. Con RZ = 1e8 y (c) en el travesaño y en M07: 1,022/0,948; con RZ = 1e9: 0,859/0,785; con 1e10: 0,813/0,740. Sin travesaño y RZ = 0: 2,076/1,671. Con U2 restringido en las cuatro ruedas (J5, J13, J16), la sensibilidad desaparece: 0,552 mm con esquinas rígidas y 0,580 mm con RZ = 0. RX = 1,5e8 en M01/M02 → 0,788 mm; RY = 0 → 0,774 mm (efecto ≤ 0,01 mm).
  ARREGLO: Hay que asegurar una de dos cosas: continuidad de alas en las esquinas M05/M06–M01/M02 (k_RZ ≥ 1e9 N·mm/rad), o la restricción lateral real de las cuatro ruedas o de los bloqueos durante el lavado, documentada con ruedas con pestaña, clips del riel o anclaje [VERIFICAR]. Debe decidirse y reflejarse en el SAP del anexo.

- [media] La cota de alabeo IMPEDIDO fija el alabeo de M05/M06 en J31/J32 (el travesaño) y en J9/J11 (M07), pero una unión al alma no restringe el alabeo del perfil pasante. La frase «Las dos cotas de alabeo acotan su efecto» es incorrecta: las cotas de alabeo no acotan la flexibilidad rotacional de la unión. En varios casos la cota inferior 0,71 mm de D-039 no es física.
  EFECTO: Travesaño rígido: IMPEDIDO 0,706 frente al mixto 0,773 mm en U1 (U3: 0,506 frente a 0,565); LIBRE 0,779. El rango honesto con uniones rígidas es ≈ 0,77–0,78 mm (U1). Base sin travesaño: IMPEDIDO 1,232 frente al mixto 1,510 mm, luego el rango base es 1,51–1,64 y no 1,20–1,64. Con uniones semirrígidas, la cota IMPEDIDO oculta el efecto: con M07 articulada, 1,362 impedido frente a 7,104 libre.
  ARREGLO: Corregir INFORME:86 y el rango de D-039. Usar LIBRE o el modo mixto como referencia de aceptación cuando la unión va al alma. Solo con un detalle que restrinja el alabeo (rigidizadores dobles o placas de ala en las dos alas y a ambos lados) se justifica IMPEDIDO en ese nudo.

- [baja] Limitaciones del cálculo propio de rigidez de la opción (a): placa de Kirchhoff sin cortante transversal, con una holgura soldadura–ala de 12–22 mm (≈ 3–5 t); singularidad en los extremos de la soldadura; convergencia completa con c = 100 mm, pero con c = 120 mm aún crece un ~8 % entre ny = 96 y 144; bordes de ala idealizados como articulados o empotrados. La rigidez de (a) puede estar sobrestimada, y la tensión pico no es un valor de diseño.
  EFECTO: Rango de k_RX de (a): 1,3e8–1,1e9 N·mm/rad. δ U1 libre entre 0,81 y 0,96 mm solo por RX, y entre 0,96 y 1,06 mm con RZ = 0. La conclusión (a = insuficiente, b = insuficiente sin continuidad de alas, c = suficiente) no cambia dentro de ese rango.
  ARREGLO: Si se quiere cerrar (a) o (b) de forma cuantitativa, hacer un FEM de láminas del nudo (CalculiX, cuando la cola quede libre) con el acuerdo real del W6×9. Para (c) basta el cálculo manual: a ENV208, la fuerza en cada placa de ala es ≈ 285e3/158 ≈ 1,8 kN, lo que da tensiones bajas; gobierna la rigidez, no la resistencia.
