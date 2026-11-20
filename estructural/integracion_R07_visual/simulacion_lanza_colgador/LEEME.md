# Lanza, carro, mástil y tambor en SOLIDWORKS: ¿se forman momentos en el «cuello» al girar? (12/11/2026)

**Pregunta del asesor (exposición del 10/11).** Cuando el rotor gira, ¿se forman muchos momentos en el «cuello» que une la parte de abajo con el tambor? ¿Convendría soldar toda la parte de abajo al tambor?

**Estado.** Verificación por simulación (D-045), sin ensayo. CAD R07 V18D. 316L a 62 °C, con E = 193 GPa y fluencia de 153 MPa (hipótesis de B1, la misma del brazo de la U).

## Modelo

**Geometría.** `scripts/s01_geometria_lanza.py` toma 37 cuerpos de una copia del CAD:
- el eje del rotor, cortado en Z2840;
- el cubo distribuidor («tambor»);
- el transversal central DN50, con las bridas A y B y un anillo de soldadura que llena la holgura de 0,6 mm (como en la U);
- el colgador (2 placas de 10 × 35), los puentes, las varillas Ø25, la placa de bloqueo, la abrazadera al eje y su brazo;
- el carro, la lanza DN25 y su pie;
- el «cuello» (tubos y codos DN25 hasta el racor de la manguera) y las 6 coplas.

Quedan fuera:
- el husillo (pasa con 0,5 mm de holgura);
- el émbolo y la barra de retención;
- las purgas, la red fija, la manguera y los brazos de la U.

**Marco y apoyo.**
- Marco de SOLIDWORKS: (X, Y, Z)_SW = (−x, z, y) del CAD, con Y vertical.
- Contacto pegado entre todas las piezas: soldaduras y uniones abulonadas idealizadas. El carro pegado a las varillas representa los bujes y el émbolo de bloqueo.
- Eje empotrado en Z2840, el centro del rodamiento inferior. Para los golpes de la U equivale al rotor detenido y retenido.

**Malla.** 6/1,2 mm, 985 629 nodos, unos 1,5 a 2 min por estudio.

**Cargas.** Las genera `scripts/s02_cargas_lanza.py` en `geometria/cargas.csv`, como cargas remotas distribuidas en el punto real.

| Estudio | Qué es |
|---|---|
| CHORROS | Reacción F = ṁ·v de las 6 boquillas de la lanza (paquete O7+C2 de Jean): 24,0 N hacia el eje. |
| GIRO | 1,7 rpm (0,178 rad/s) más una aceleración angular de 0,178 rad/s² (rampa de 1 s, hipótesis). |
| PESO | Gravedad (acero; sin agua ni brazos de la U). |
| SERVICIO | CHORROS + GIRO + PESO. |
| GOLPE_LANZA_RADIAL / _TANG | 200 N en el pie de la lanza (Z838), hacia el eje o en la dirección del giro (interfaz de la guía de R03). |
| MANGUERA_100N | 100 N hacia abajo en el racor de la manguera (arrastre supuesto de R03): carga del «cuello». |
| U_GOLPE_FUERA_PLANO / _EN_PLANO | 1 000 N en el brazo A a Z1400 (hipótesis de R03 usada en la U), aplicado en la cara de la brida A. |

**Corrida.**
- Registro principal: `resultados/sw_log_015836.txt`.
- **PESO y SERVICIO se repitieron** (`sw_log_030017.txt`): en la primera corrida la gravedad quedó hacia arriba. Ahora el pie de la lanza baja 0,039 mm.
- Modelo: `modelo/LANZA_COLGADOR_SW_015836.SLDPRT`, con los 9 estudios. PESO y SERVICIO válidos están en `LANZA_COLGADOR_SW_030017.SLDPRT`.
- Resumen: `resultados/RESUMEN_SW_LANZA.json`, que genera `scripts/s04_resumen_lanza.py`.

## Control con cálculo a mano (secciones estáticamente determinadas)

| Sección y caso | A mano | SOLIDWORKS | Diferencia |
|---|---:|---:|---:|
| Lanza a Z1450, chorros | 4,58 MPa | 4,65 MPa | +1,5 % |
| Lanza a Z1450, golpe radial de 200 N | 64,9 MPa | 65,4 MPa | +0,8 % |
| Lanza a Z1450, golpe tangencial de 200 N | 64,9 MPa | 65,4 MPa | +0,9 % |
| Transversal a x = 240, golpe de la U fuera del plano | 105,0 MPa | 113,3 MPa | +8,0 % |
| Transversal a x = 240, golpe de la U en el plano | 51,4 MPa | 55,6 MPa | +8,2 % |

En el transversal la diferencia sube al 8 %. La sección está a 40 mm del borde del tambor, menos de un diámetro (60,3 mm), así que allí todavía influye la unión. No es un acuerdo «de pocos puntos».

## Resultados (von Mises máx., MPa; fluencia supuesta: 153 MPa)

| Grupo | Chorros | Giro | Servicio | Golpe lanza radial | Golpe lanza tangencial | Manguera 100 N | Golpe U fuera del plano | Golpe U en el plano |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lanza (borde del carro) | 7,6 | 0,03 | 7,8 | 94,9 | 98,9 | 26,4 | 0,3 | 0,8 |
| Carro | 6,3 | 0,02 | 6,3 | 78,3 | 67,0 | 24,2 | 5,3 | 6,3 |
| Varillas | 2,1 | 0,03 | — | 25,8 | 20,4 | 5,4 | 7,1 | 8,4 |
| Colgador | 2,7 | 0,17 | 5,7 | 28,8 | 34,4 | 5,5 | 25,2 | 14,9 |
| Tambor (cubo) | 1,0 | 0,05 | 4,0 | 10,8 | 11,9 | 1,6 | **211** | 80,8 |
| Transversal | 0,07 | 0,01 | — | 0,8 | 0,5 | 0,1 | **212** | **169** |
| Eje | 1,1 | 0,03 | 5,2 | 10,7 | 11,5 | 1,9 | 32,4 | 30,3 |
| «Cuello» (tubos DN25) | 0,03 | 0,03 | 4,9 | 0,3 | 0,3 | **33,1** | 0,05 | 0,1 |
| Boquillas de la lanza (desplazamiento, mm) | 0,50 | 0,005 | 0,71 | 7,0 | 6,3 | 0,34 | 1,7 | 2,2 |

Los máximos son valores de una sola malla. En aristas de contacto pegado, como el borde del carro o el del tambor, son picos locales que no convergen; no son tensiones de diseño.

## Lectura

1. **El giro casi no genera momentos.** A 1,7 rpm, la fuerza centrífuga y la del arranque dejan todo por debajo de **0,2 MPa**. La rotación no es lo que carga el «cuello».
2. **En servicio** (chorros, peso y giro) la lanza llega a 7,8 MPa (5 % de la fluencia) y las boquillas se mueven **0,71 mm**, por debajo de la tolerancia de ±2 mm de D-079. El mástil cede: el cálculo a mano, con el carro rígido, daba 0,27 mm.
3. **No hay fatiga apreciable.** Las cargas giran con la lanza, así que la tensión es constante en su marco; no hay flexión rotativa.
4. **El «cuello» propiamente dicho** (tubos DN25 entre la manguera y la lanza) no está en el camino de las cargas de la lanza. Solo lo carga la manguera: **33 MPa por cada 100 N** en el racor. La fuerza real de la manguera es un dato del fabricante pendiente (Aflex) [DATO EXTERNO PENDIENTE].
5. **Lo que carga de verdad la lanza es un golpe lateral:**
   - 200 N en el pie dan unos 95 MPa en el borde del carro.
   - La sección lisa llega a la fluencia con unos **384 N**.
   - El golpe de 1 000 N que se usó para la U la plastificaría. Qué golpe se acepta para la lanza es una decisión pendiente con el asesor.
6. **El punto crítico del conjunto es la unión del transversal con el tambor (soldadura W5).** Con el golpe de 1 000 N en el brazo de la U, el transversal llega a **212 MPa** (fuera del plano) y 169 MPa (en el plano) junto al borde del tambor.
   - La tensión nominal de viga en esa sección es de unos 110 MPa (M = 700 N·m y T = 340 N·m sobre el DN50 Sch 10S).
   - El resto es concentración en la arista, que se estudia en el submodelo de abajo.
   - **Este es el sentido mecánico de la sugerencia del asesor:** reforzar la unión de abajo con el tambor tiene sentido para el transversal, no para la lanza, que debe subir 640 mm.

## Submodelo de la unión transversal–tambor con el cordón W5

**Por qué.** La revisión de Codex pidió resolver los 212/169 MPa del modelo completo. En ese modelo, entre el tubo tangente y la placa del tambor quedaba una cuña afilada sin cordón, que funciona como una grieta y da un pico singular.

**Modelo** (`scripts/s05_geometria_union_cubo.py` y `s06_sw_union_cubo.cs/.ps1`):
- Piezas: eje, tambor, transversal y bridas.
- **Cordones W5 modelados** a ambos lados del contacto, como filetes de |y| = 3 a 12 mm con cara a 45°, recortados contra el tubo y la huella del tambor. El perfil es una HIPÓTESIS geométrica: el plano ASP-150 pide «a4 contorno», pero no da el perfil entre un tubo y una placa tangente.
- El tramo del transversal de x = 170 a 250 (el fin del contacto está en x ≈ 200) y los cordones de ese tramo llevan control de malla de 2, 1 y 0,6 mm. El resto, 8/1,5 mm.
- Mismos golpes de 1 000 N, apoyo y material que el modelo completo.

**Archivos.** Registro en `resultados/union_cubo/sw_union_log_032217.txt`; modelo en `modelo/UNION_CUBO_SW_032217.SLDPRT`, con los 6 estudios FUERA_h… y EN_h…

**Resultado: tensión en la superficie del tubo, por distancia al fin del contacto** (von Mises, MPa; máximo sobre la circunferencia)

| Golpe | Malla fina | 1,1 mm (0,4t) | 2,8 mm (1,0t) | 5 mm | 10 mm | 40 mm | Sonda x = 240 | Pico del cordón |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Fuera del plano | 2 mm | 312 | 206 | 163 | 125 | 113 | 114,4 | 663 |
| | 1 mm | 305 | 188 | 154 | 123 | 113 | 114,1 | 701 |
| | 0,6 mm (2,4 M nodos) | 241 | 184 | 151 | 121 | 113 | 114,0 | 929 |
| En el plano | 2 mm | 169 | 123 | 97 | 73 | 49 | 53,3 | 303 |
| | 1 mm | 167 | 112 | 92 | 70 | 49 | 53,5 | 362 |
| | 0,6 mm | 141 | 109 | 92 | 70 | 49 | 53,5 | 519 |

**Lectura:**
1. **Lejos del borde coincide con la viga:** 113 MPa fuera del plano y 49–53 en el plano, frente a 105 y 51 a mano. La sonda no cambia con la malla.
2. **Desde 1,0t (2,8 mm) del fin del cordón el valor converge:** unos **185 MPa** fuera del plano, por encima de la fluencia supuesta de 153 MPa, y unos 110 MPa en el plano. A 5 mm del fin del cordón: 151 y 92 MPa.
3. **Lo que no converge:**
   - El máximo en la punta del cordón (663 → 929 MPa) y el valor a 0,4t son singularidades de la arista.
   - Por eso la extrapolación de punto caliente IIW tampoco converge: 384, 383 y 279 MPa.
   - **No se usan como tensión de diseño.**
4. **Conclusión:**
   - Con el golpe accidental de 1 000 N fuera del plano, el tubo DN50 de 2,77 mm fluye localmente en los primeros milímetros junto al fin del cordón W5. La sección general trabaja al 74 % de la fluencia.
   - Para un golpe accidental y único, una fluencia local no implica rotura, pero el margen es poco.
   - **Recomendación (por decidir con el asesor):** reforzar la unión con cartelas o una silleta entre la placa inferior del tambor y el transversal, o justificar un golpe de diseño menor que los 1 000 N de R03.
   - **Este es el sentido mecánico de la sugerencia del asesor de unir la parte de abajo al tambor.**

## Limitaciones

- **Contacto pegado en todas las uniones:**
  - el carro pegado a las varillas, en vez de bujes con émbolo;
  - el colgador pegado al tambor, cuya unión real no está definida en ningún archivo;
  - en el modelo completo no se modela el cordón W5.
- **Faltan cargas en SERVICIO:**
  - el peso de los brazos de la U (unos 22 kg con agua) y el agua en general;
  - la presión interna (unos 4 bar);
  - la fuerza de la manguera.
- **Golpes:**
  - los de 200 y 1 000 N son hipótesis de R03;
  - el de la U se aplica como carga remota en la brida, con el rotor retenido (en marcha, el limitador de par desliza a 60 N·m).
- **Malla:** una sola malla en el modelo completo; los picos de borde (carro, coplas, tambor) no están convergidos. La unión transversal–tambor sí tiene estudio de convergencia (submodelo, tres mallas).
- **Lo que hay que mirar en SOLIDWORKS:** en el modelo 015836, los estudios PESO y SERVICIO tienen la gravedad hacia arriba. Los válidos están en el modelo 030017. El modelo 014928 fue solo la prueba inicial.
