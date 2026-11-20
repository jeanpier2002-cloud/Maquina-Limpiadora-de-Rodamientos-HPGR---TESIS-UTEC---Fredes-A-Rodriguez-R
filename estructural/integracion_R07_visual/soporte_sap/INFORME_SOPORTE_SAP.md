# Soporte superior del rotor y del motorreductor: análisis en SAP2000 (27/10/2026)

**Estado.** El análisis está EJECUTADO en SAP2000 v27 por API. La alternativa elegida es un diseño CANDIDATO; queda como propuesta de **HPGR D-065**, que el usuario delegó («lo que decidas arreglas») y debe confirmar. **No es apto para fabricación** (HPGR D-045).

**Pedido del usuario (27/10).** El soporte del motorreductor del techo, el que hace girar la U, le parece exagerado. En otras máquinas vio el motorreductor montado en la propia pared de la cabina. Pidió analizarlo en SAP y decidir.

## 1. Qué sostiene este soporte

No sostiene solo el motorreductor. Carga con:
- el eje del rotor (Ø110), con **dos rodamientos separados 600 mm** (z 2850 y 3450);
- la U giratoria (envolvente de 180 kg, excéntrica 50 mm);
- la polea conducida y la correa HTD 8M 2:1;
- el motorreductor SF47 con el limitador ROBA-slip (D-062).

Fuente: `01_DISENO_VIGENTE/motor_rotor_soporte/LEEME.md` §1–2 y `aspersion/ASPERSION_CIERRE_INGENIERIA_R03/MEMORIA_CIERRE_R03.md` §6.3–6.4. La lección de R01 ya decía que el pórtico no puede eliminarse por parecer sobredimensionado sin verificar el camino de cargas.

**Por qué no puede ir solo en la pared.** El eje del rotor está en el **centro** de la cabina, a 2 m de cada muro, y el motor mueve el rotor con una correa: tiene que quedar junto al eje. Además, la chapa de la cabina no debe cargarse (R03).

**Las máquinas que viste sí tienen estructura.** Lo que pasa es que esa estructura es el **marco de la propia cabina**. Esa es la idea que se analiza aquí: no una torre aparte, sino el soporte integrado en los postes de los muros.

## 2. Modelo

**Archivos:**
- modelo paramétrico: `scripts/SoporteSAP.cs`;
- ejecución de cada caso: `scripts/s01_correr_caso.ps1`;
- modelos: `modelos/*.sdb`, que se pueden abrir en SAP para sacar capturas.

**Geometría actual (R07 V11, soporte R04), del CAD:**
- 4 columnas SHS150×6 en (±2170, ±300), de 0 a 2890;
- 2 vigas RHS200×100×6 en y = ±300, con eje en z 2790;
- en cada costado, una celosía L50×5 en X de dos paneles (z 150–1470–2690), con un travesaño en z 1470;
- el cartucho (placas de 25 mm y postes Ø76×8), con la ménsula del motor.

**Idealización:**
- barras de pórtico;
- arriostramientos articulados;
- el cartucho, la ménsula y el motor como **cuerpo rígido**, apoyado en las vigas en x = ±230 (placa base de 460 mm);
- acero A36 (hipótesis del proyecto), E = 200 GPa y 7 850 kg/m³.

**Cargas en servicio** (R03, salvo lo indicado):

| Caso | Valor | Fuente |
|---|---|---|
| DEAD | Peso propio. Cartucho y alojamientos: 1 789 N (volumen del CAD × 7 850). Ménsula: 412 N. Motorreductor SF47 con brida, 21 kg, más polea y cubo, ~10 kg: 304 N. Rotor: 1 766 N en el cojinete inferior | CAD V11; `SELECCION_COMERCIAL_R07.md`; `CALCULO_CARGA_RADIAL_SF47.md` (polea estimada); R03 |
| BELT | 1 071 N (2T₀ + F_t, con T = 60 N·m y T₀ = 300 N), aplicada en la polea conducida y en el motor | R03 §6.3 |
| TORQ | 60 N·m en el eje (rotor bloqueado, limitador de D-062) | D-062 |
| AXP/AXN/AYP/AYN | Accidental horizontal de 1 000 N a z 1400 sobre la U, llevada al cojinete inferior con su momento, más el peso excéntrico (1 766 N × 50 mm) | R03 §6.3 |

**Combinaciones (AISC 360-16, LRFD):**
- U1 = 1,4D;
- U2 = 1,2D + 1,6(BELT + TORQ);
- U3 = 1,2D + BELT + TORQ + A, con la accidental en cada dirección.

**Servicio:**
- S1 = D + BELT + TORQ;
- S2 = S1 + A.

**Análisis:** modal de 12 modos, con masa de los elementos más las cargas DEAD.

**Criterios de comparación:** son propios del autor (HIPÓTESIS) y se fijaron antes de elegir:
- D/C ≤ 0,6, con margen porque las cargas son envolventes;
- flecha de las vigas en S1 ≤ L/1000;
- desplazamiento lateral del cojinete superior en S2 **no mayor que con el soporte actual** (1,20 mm), muy por debajo de la flecha propia del eje en el accidental (1,9–2,8 mm, R03);
- primera frecuencia no menor que la actual.

## 3. Resultados

Tabla completa en `resultados/RESUMEN_CASOS.csv`; figuras F1–F4 en `figuras/`.

| Caso | Postes / vigas / celosía | Acero (kg) | D/C máx. | f1 / f2 (Hz) | Lateral del cojinete en S2 (mm) | Flecha S1 |
|---|---|---:|---:|---:|---:|---:|
| **O1 actual (V11)**: torres fuera de la cabina, bases articuladas | SHS150×6 / RHS200×100×6 / L50×5 | **584,6** | **0,075** | 4,26 / 7,68 | 1,20 | L/7691 |
| O2: los mismos perfiles, más livianos | SHS100×5 / RHS160×80×5 / L40×4 | 352,9 | 0,143 | 2,59 / 5,46 | 4,19 | L/3035 |
| O3: en el muro de la cabina, articulado | ídem, x = ±2020 | 342,0 | 0,135 | 2,64 / 6,10 | 4,12 | L/3555 |
| O4: en el muro, mínimo | SHS80×4 / RHS150×100×4 | 259,0 | 0,163 | 1,89 / 6,68 | 8,90 | L/2541 |
| O5: O3 + cartelas | + SHS60×4 | 357,9 | 0,130 | 2,97 / 6,13 | 3,13 | L/3908 |
| O6: O5 + bases empotradas | | 357,9 | 0,121 | 6,02 / 6,87 | 0,78 | L/4465 |
| O7: O6 más liviano | SHS80×4 / RHS150×100×4 | 274,9 | 0,151 | 4,33 / 7,04 | 1,65 | L/2995 |
| O8: O6 + arriostramiento en planta | + L40×4 | 376,0 | 0,119 | 5,91 / 12,31 | 0,78 | L/4390 |
| O9: O7 + planta | | 292,9 | 0,129 | 4,24 / 11,34 | 1,65 | L/2944 |
| **O10 ELEGIDO**: marco de cabina empotrado + planta, sin cartelas | SHS100×5 / RHS160×80×5 / L40×4 | **360,0** | **0,120** | **5,34 / 12,35** | **0,99** | L/3783 |
| O11: O10 con postes SHS120×5 | SHS120×5 | 395,1 | 0,121 | 6,62 / 12,90 | 0,63 | L/4527 |

**Lo que muestra el análisis:**
1. **El soporte actual está sobredimensionado en resistencia:** usa solo el 7,5 % de su capacidad (D/C 0,075). Tu impresión era correcta.
2. **Lo que gobierna es la rigidez lateral, no la resistencia.** Si solo se aligeran los perfiles (O2–O4), el cojinete superior se desplaza de 4 a 9 mm bajo el accidental y f1 baja a 1,9–2,6 Hz. Y eso desalinea la correa y la unión rotativa.
3. **La rigidez se consigue con geometría, no con acero:**
   - las bases empotradas resuelven la dirección X, la de los pórticos;
   - el arriostramiento en planta entre las vigas resuelve la dirección Y y sube f2 de 6,9 a 12,3 Hz.
4. **Las cartelas (O8) se descartan:** van de z 2410 a 2730 y atravesarían el techo de la cabina (z 2570–2650), porque las vigas quedan sobre el techo para recibir el cartucho.
5. **Modo torsional:** en todas las opciones, la actual incluida, aparece un modo torsional alrededor de z entre **25 y 28 Hz** (masa participante Rz de 0,6–0,8). Es el giro del cartucho con el motor colgado a 800 mm del eje. Cae cerca de la velocidad del motor (≈1 400 rpm = 23,3 Hz, R03).
   - **[VERIFICAR]** la velocidad real del motor (relación del S47R17) y mantenerla a ±15 % del modo.
   - Si hiciera falta: acercar el motor al eje o rigidizar la ménsula en torsión.
   - Las masas del modelo son puntuales, sin inercia rotacional propia: la frecuencia de este modo es aproximada.

## 4. Decisión (propuesta HPGR D-065, CANDIDATO)

**Se adopta O10, el soporte integrado al marco de la cabina:**
- **4 postes SHS100×5** dentro de los muros laterales (x = ±2020, y = ±300), con **placa base empotrada** (anclajes a momento);
- **celosía en X L40×4** dentro de los muros laterales (z 150–1470–2690);
- **2 vigas RHS160×80×5** sobre el techo, entre postes (luz 3 940 mm libres), con la cara superior en z 2890 para recibir el cartucho;
- **arriostramiento en planta en X L40×4** entre las dos vigas, a cada lado del cartucho.

**Qué gana frente al soporte actual:**
- −225 kg de acero (−38 %);
- el cojinete se mueve menos bajo el accidental (0,99 frente a 1,20 mm);
- f1 sube de 4,26 a 5,34 Hz y f2 de 7,68 a 12,35 Hz;
- no hay torres fuera de la cabina, con lo que también se resuelve el hallazgo **H03** de la revisión del CAD (placas base bajo los muros);
- **una sola estructura** hace de marco de cabina y de soporte. Antes eran dos: la cabina necesita marco igual.

**Lo que queda [VERIFICAR] o PENDIENTE:**
- **Bases empotradas:** placa base y anclajes a momento contra la losa, que es un DATO EXTERNO PENDIENTE. Las reacciones en servicio son de 2,0–3,4 kN verticales y < 0,65 kN horizontales, sin levantamiento. Los momentos en las bases no se exportaron.
- **Uniones:** viga–poste a momento, celosías y planta articuladas. Faltan las soldaduras o los pernos.
- **Modo torsional** de 27,7 Hz frente a la velocidad del motor.
- **Los muros como cerramiento**, no estructural: la chapa no se carga.
- **El cartucho, la ménsula y los alojamientos** no se verificaron (se modelaron rígidos).
- **Pandeo y estabilidad global:** solo se hizo la verificación AISC de cada barra.

## 5. Figuras para la tesis (`figuras/`)

- `F1_comparacion_alternativas.png`: masa, D/C, desplazamiento del cojinete y f1 de las 11 alternativas.
- `F2_aprovechamiento_DC.png`: barras coloreadas por D/C, la actual frente a la elegida.
- `F3_deformada_accidental.png`: deformada S2 más desfavorable (×200), la actual frente a la elegida.
- `F4_modos_elegido.png`: modos 1 a 4 de O10, con su masa participante.

**Capturas propias en SAP.** Abre `modelos/O10_MARCO_CABINA_EMPOTRADO_PLANTA.sdb` o `O1_V11_ACTUAL.sdb`, desbloquea, corre y muestra la deformada, los modos o el D/C.

## 6. Limitaciones

- Las cargas son envolventes de R03: HIPÓTESIS sobre masas y fuerzas de correa reales.
- El cartucho es rígido.
- Las bases son ideales (articuladas o empotradas).
- No se modelan los muros ni el techo como diafragma.
- No hay análisis de fatiga.
- Las secciones son rectangulares de esquina recta, como en SAP con SetTube; la sección comercial con radios da propiedades algo menores. **[VERIFICAR]** con tablas comerciales.
