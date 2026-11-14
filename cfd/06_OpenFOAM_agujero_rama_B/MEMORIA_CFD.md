# Simulación CFD del subsistema de aspersión sobre el agujero del rodamiento

Memoria del trabajo CFD. Versión del 20/09/2026.
Herramienta: OpenFOAM ESI v2606 sobre WSL2. Los informes de cada fase, los datos y las figuras están
en las carpetas que se citan al final.

---

## 1. Qué se quería responder

Cómo se reparte el agua de las boquillas del ramal interior sobre el agujero del rodamiento
SKF 241/900: qué zonas se mojan, con cuánta dosis, con qué uniformidad, dónde quedan zonas secas o con
exceso, y cómo se solapan los chorros de unas boquillas con otros.

La cadena que se modela es **spray → transporte → impacto → deposición → distribución superficial →
cobertura**, con el aire como fase continua Euleriana y el agua como gotas lagrangianas. **No** se
resuelve la atomización interna de la boquilla: el spray se prescribe a partir de los datos
disponibles. Lo que se mide es **mojado**, no remoción de grasa; no se informa ningún porcentaje de
limpieza.

## 2. El sistema físico

En posición de lavado el eje del rodamiento es **vertical** y la pieza permanece inmóvil sobre tres
apoyos; lo que gira, a **1,7 rpm**, es el distribuidor que lleva la lanza. El agujero es un cono de
conicidad diametral **1:30**, de Ø900 mm en la cara inferior (Z 890 mm) a Ø917,17 mm en la superior
(Z 1405 mm), con 515 mm de ancho axial y **1,470219 m²** de superficie.

Dentro del agujero baja una lanza DN25 con seis boquillas Spraying Systems VeeJet **H3/8U-5020**:
cinco de eje radial (INT_1…INT_5, en Z 956,8 / 1052,2 / 1147,5 / 1242,8 / 1338,2 mm) y una inferior
inclinada 25° (INF_INT, en Z 850 mm). Cada una da **9,12–9,17 L/min a 4 bar**, con un abanico plano de
50° orientado en el plano radial-vertical. La velocidad de salida es 27,11 m/s.

El fluido se representa como **agua a 62 °C** (ρ = 982,12 kg/m³) en sustitución del detergente, que no
está caracterizado. El aire se toma a 20 °C y 76,24 kPa, la presión de planta: ρ = 0,9061 kg/m³.

## 3. La idea que hace la simulación asequible

El agujero es axisimétrico y el distribuidor tarda **35,3 s** en dar una vuelta, mientras que una gota
tarda **5,9 ms** en recorrer los 143 mm que la separan de la pared. Durante su vuelo, el punto de la
pared al que apunta la boquilla se desplaza **0,31 mm**, frente a los 6,7 mm de ancho de la propia
huella.

Por tanto se simula **una sola posición de la lanza** y la dosis por vuelta se obtiene integrando el
mapa de deposición sobre el acimut:

$$D(Z) \;=\; \frac{1}{\omega}\int \varphi(Z,\theta)\, d\theta$$

con φ el flujo de deposición en kg·m⁻²·s⁻¹ y ω = 0,17802 rad/s. No se simula la rotación ni las
vueltas sucesivas. La figura `04_FIGURAS/F5/F5_mapa_desarrollado.png` muestra esta construcción: la
huella instantánea ocupa menos de 1° de acimut y, tras integrar, la dosis queda uniforme en acimut y
estructurada en Z.

## 4. El modelo, y por qué cada pieza

Todas las elecciones se tomaron con un caso piloto medido, no por defecto. La ficha completa está en
`03_RESULTADOS/F2_piloto/F2_ficha_decision.csv`.

**Solver: `kinematicParcelFoam`, con el aire acoplado a dos vías** (RAS k-ε). Se descartó la
alternativa barata de aire congelado (`icoUncoupledKinematicParcelFoam`) por una razón medida: con una
distribución de tamaños realista, el aire congelado **nunca alcanza régimen estacionario**. La masa de
agua suspendida crece indefinidamente porque una gota de 50 µm tiene una distancia de frenado de unos
54 mm, menor que los 143 mm que debe recorrer: se para y queda flotando. Con aire acoplado la arrastra
el chorro de aire —que alcanza 27,5 m/s, casi la velocidad de las propias gotas— y llega a la pared.
El error del caudal depositado pasa de **−3,6 % y creciendo** a **−0,014 %**. El coste del
acoplamiento es un factor 3.

**Inyección: `kinematicLookupTableInjection`** con una tabla generada por `scripts/gen_abanico.py`. El
modelo `ManualInjection` que se había previsto no sirve: en v2606 lee sólo posiciones y aplica una
única velocidad a todos los parcels, de modo que no puede representar un abanico. La tabla da por cada
entrada posición, velocidad vectorial, diámetro, densidad y caudal másico. Siguiendo lo decidido para
la geometría de la fuente, el **vértice del abanico está en el orificio** (4,5 mm detrás de la punta,
en el fondo de la ranura en V) y los parcels **nacen en el plano de la punta**, sobre el rayo que sale
del vértice.

**Interacción con la pared: `localInteraction`**, con todas las superficies en `escape`, de modo que
el balance de masa se desglosa por patch. En la pared del agujero, `escape` equivale a **absorción
total**: toda gota que llega cuenta como depositada.

**Paso de tiempo: 5·10⁻⁵ s**, fijo. Lo impone el número de Courant del aire arrastrado, no el del
flujo medio: con 2·10⁻⁴ s el caso diverge en el primer paso.

**Malla:** `snappyHexMesh` sobre una caja de 1000 × 1000 × 655 mm con celda base de 16 mm y refino de
dos niveles (4 mm) en la pared del agujero y en la lanza: **430 294 celdas**, `Mesh OK`.

**Reparto del spray:** 150 rayos por boquilla en el plano del abanico × 3 fuera del plano = 450
entradas por boquilla, con la masa uniforme por unidad de ángulo y los diámetros muestreados de una
Rosin–Rammler **en masa** (λ = 300 µm, n = 2,5, acotada a 50–900 µm; D32 = 354 µm).

## 5. Verificación

### 5.1 Conservación de masa

El balance cierra a **10⁻⁸ relativo o mejor** en las diez corridas. En el caso de las seis boquillas,
de los 0,0314432 kg inyectados en 35 ms: 0,0228 kg en la pared del agujero, 0,00144 kg en la cara
inferior del rodamiento, 0,00217 kg escapados lateralmente y 0,00504 kg en vuelo (el inventario
estacionario). Residuo: 10⁻¹⁰ kg.

Además, el registro por parcel coincide exactamente con el contador interno del solver, y la masa
reconstruida desde los archivos VTK reproduce cifra por cifra la del log.

### 5.2 Dos caminos independientes que coinciden

Antes de simular, se trazaron los rayos del abanico contra el cono para predecir geométricamente dónde
llega cada boquilla. El CFD lo confirma:

| | Trazado de rayos | CFD | Diferencia |
|---|---|---|---|
| INT_3, tramo de Z alcanzado | 1079,14 – 1216,92 mm | 1078,25 – 1217,51 mm | largo +1,1 %, centro −0,15 mm |
| INT_5, fracción de su caudal que llega | 97,45 % | 97,92 % | +0,5 puntos |
| INF_INT, fracción que llega | 22,74 % | 25,86 % | +3,1 puntos |

El CFD da huellas ligeramente más largas, lo esperable: la gravedad y el espesor finito del abanico
añaden dispersión.

### 5.3 Geometría del abanico

En un caso de una boquilla contra una placa plana, la masa acumulada a lo largo de la huella se
comparó con la predicción analítica de un abanico de 50° con masa uniforme por unidad de ángulo,
F(x) = (arctan(x/Y) + 25°)/50°. La desviación máxima fue **0,0165**, que es exactamente **1/60**, la
discretización en los 60 rayos usados en aquel caso. La longitud de la huella medida, 137,84 mm,
coincidió con la geométrica, 137,84 mm.

### 5.4 Convergencia estadística

Partiendo en dos la ventana de promediado, el caudal depositado difiere **0,062 %** y el coeficiente
de variación **0,27 %**. Hay 14 933 parcels por bin de Z, frente al criterio de ≥ 100.

### 5.5 Estudio de malla

Hecho en tres niveles y **sólo sobre el caso de las seis boquillas**, reutilizando después esa densidad:

| Base | Celdas | Caudal depositado | Dosis media | CV | Cobertura (5 kg/m²) |
|---|---|---|---|---|---|
| 22 mm | 217 702 | 0,781666 kg/s | 18,765 | 0,353 | 99,02 % |
| **16 mm** | **430 294** | **0,783494 kg/s** | **18,809** | **0,340** | **100 %** |
| 11 mm | 1 021 875 | 0,777413 kg/s | 18,663 | 0,341 | 100 % |

Se adopta la malla de 16 mm: los indicadores integrales varían menos del 0,8 % al pasar a 1,02 M
celdas y el coeficiente de variación coincide con el de la malla fina dentro del 0,4 %.

**El estudio reveló además un límite que no es de malla.** El RMSE del perfil D(Z) no baja al refinar
(7,43 % con 0,22 M; 6,33 % con 0,43 M), pero sí baja como 1/√(rayos por bin) al ensanchar el bin:
11,71 % con 5,4 rayos por bin, 3,50 % con 21,7. Es decir, **la resolución punto a punto de D(Z) la
limita el número de rayos de la tabla de inyección, no la malla.** Refinar más la malla no mejora el
perfil; añadir rayos sí, a costa de más parcels.

## 6. Resultados

Sobre la malla adoptada, con bines de 10 mm en Z y promediando entre 20 y 35 ms de tiempo simulado.

| Indicador | Valor |
|---|---|
| Caudal depositado en la pared del agujero | **0,783 kg/s** de los 0,898 kg/s inyectados |
| Dosis por vuelta: media / mínima / máxima | **18,81 / 8,47 / 36,89 kg·m⁻²·vuelta⁻¹** |
| Cobertura | **100 %** del área para cualquier umbral hasta 10 kg·m⁻²·vuelta⁻¹ |
| Uniformidad (coeficiente de variación de D(Z)) | **0,340** |
| Zona seca | **0,00 %** |
| Zona con exceso (D > 2 × media) | **0,00 %** |
| Reparto por boquilla | INT_1…INT_5: 18,8 a 19,1 % cada una · **INF_INT: 4,93 %** |
| Velocidad media de impacto | 23,46 m/s |
| Tiempo de vuelo | 5,89 ms |
| Número de Weber en el impacto (medio / máximo) | 2177 / 6655 |

Como el criterio de «mojado» no se fijó de antemano, la cobertura se informa **como curva completa**
frente al umbral D_min (`03_RESULTADOS/F4/F4_cobertura.csv`), y no como un único porcentaje.

### 6.1 Tres lecturas

**No hay zonas secas, y con mucho margen.** La dosis mínima a lo largo del agujero equivale a 8,5 mm
de agua en cada vuelta de 35 s. Cualquier umbral razonable queda muy por debajo, de modo que la curva
de cobertura es plana al 100 % en todo el rango con sentido físico. Con este caudal la pregunta útil
nunca fue si llega suficiente agua, sino dónde llega y con qué uniformidad.

**La dosis alterna casi por un factor 4 a lo largo del agujero.** Los máximos, ≈ 37 kg·m⁻²·vuelta⁻¹,
caen **entre** boquillas, donde se solapan dos huellas; los mínimos, ≈ 8,5, quedan enfrente de cada
boquilla y en los extremos. Es la consecuencia directa de un solape del 30 % entre huellas contiguas,
no un defecto del modelo. Si interesara uniformar, la palanca sería la separación entre boquillas, no
el caudal.

**INF_INT apenas contribuye al agujero.** Aporta el **4,93 %** de la masa depositada frente al ~19 %
de cada boquilla del ramal interior, y sólo en una banda de 20 mm en Z 890–912. De su propio caudal,
únicamente el **25,9 %** alcanza el agujero: su eje corta el cono en Z 873 mm, por debajo de la cara
inferior, y sólo los rayos con elevación superior a 38,7° entran. Si su función prevista es mojar la
cara inferior y el chaflán, está cumpliéndola; si se esperaba que contribuyera al agujero, no lo hace.

### 6.2 Un efecto de la conicidad que el diseño no recogió

El reparto de boquillas se dimensionó con una distancia a la pared de 143,3 mm para todas. Con la
conicidad, esa distancia va de **144,4 mm en INT_1 a 150,8 mm en INT_5**, un 5,2 % más, y las huellas
crecen de 134,8 a 139,3 mm de abajo arriba. El solape resulta ser del 29,8 al 32,1 %, algo mayor que
el 28,66 % nominal del cálculo.

## 7. Sensibilidad a los supuestos

Siete variantes, cada una cambiando **un** parámetro (`03_RESULTADOS/F4/F4_S3_sensibilidades.csv`):

| Variante | Dosis media | Diferencia | CV | Área seca |
|---|---|---|---|---|
| Base (50°, D32 354 µm, 2° fuera del plano, absorbe) | 18,809 | — | 0,340 | 0,00 % |
| Abanico 40° | 18,704 | −0,56 % | 0,241 | **0,98 %** |
| Abanico 55° | 18,634 | −0,93 % | 0,335 | 0,00 % |
| Gotas finas, D32 177 µm | 18,871 | +0,33 % | 0,361 | 0,00 % |
| Gotas gruesas, D32 584 µm | 18,771 | −0,20 % | 0,338 | 0,00 % |
| Fuera del plano 5° | 18,811 | **+0,01 %** | 0,340 | 0,00 % |
| Pared que rebota | 18,981 | +0,91 % | 0,341 | 0,00 % |

**El rango total de la dosis media entre las siete variantes es del 1,86 %.** El resultado de mojado
no depende de forma apreciable de ninguno de los supuestos que hubo que hacer por falta de datos.

Dos consecuencias merecen destacarse:

**El supuesto más débil del modelo resulta ser irrelevante para el indicador principal.** El ángulo
del abanico fuera de su plano —el único parámetro sin ningún dato de respaldo— reparte la masa en
acimut, y la dosis por vuelta integra sobre el acimut. Pasar de 2° a 5° mueve la dosis media un
**+0,01 %**. Sigue afectando al flujo instantáneo φ, que es lo que importaría para erosión o para un
modelo de película, pero no al mojado.

**El diseño tiene margen por arriba y no por abajo.** A 55° no cambia nada, pero a 40° aparece un
0,98 % de área seca y la cobertura cae al 97,06 %: las huellas se acortan de 138 a ~110 mm, desaparece
el solape y se abren huecos en los extremos. Como la ficha del fabricante da 45° a 20 psi frente a 50°
a 40 psi, **conviene asegurar la presión en la boquilla**: si cayera apreciablemente por debajo de la
de referencia, empezarían a aparecer bandas secas.

## 8. Límites del trabajo

Están detallados en `QUE_FALTA_PARA_VALIDAR.md`. En resumen:

1. **El modelo no está validado experimentalmente.** No se ha hecho ningún ensayo. Todo lo anterior
   son verificaciones internas —conservación, convergencia, coherencia entre dos cálculos
   independientes—, que comprueban que el modelo resuelve bien lo que se le pidió resolver, no que lo
   que se le pidió corresponda a la realidad.
2. **La lámina sin romper.** A 143 mm de la boquilla el abanico real es en parte una lámina líquida
   continua, y el modelo lagrangiano la representa como gotas dispersas desde el orificio. Es el
   límite físico más serio y ninguna de las verificaciones hechas lo toca.
3. **Régimen de salpicadura.** El número de Weber en el impacto es de 2177 de media y hasta 6655,
   claramente por encima del umbral de salpicadura. Ni la absorción total ni el rebote puro son
   exactos; se informa la cota de absorción y se declara.
4. **La distribución de tamaños de gota es una hipótesis**, no un dato del fabricante. El estudio de
   sensibilidad muestra que importa poco para la dosis, pero sí para la velocidad de impacto.
5. **El sentido de la conicidad** (diámetro menor abajo) es un supuesto de coherencia con el reparto
   de boquillas del equipo, pendiente de confirmar con la ficha del rodamiento.
6. **Turbulencia sin barrer**: todo se hizo con k-ε; no se probó otro modelo.
7. **No hay película superficial.** El escurrimiento del agua ya depositada no se modela.

## 9. Coste computacional

En un i7-10700F con 12 hilos y 12 GB asignados a WSL: la malla de trabajo se genera en 87 s y cada
caso de seis boquillas tarda **15 minutos** con 4 rangos MPI. La aceleración en paralelo satura en
**1,8×** (el problema está limitado por ancho de banda de memoria), de modo que usar más de 4 rangos
no aporta. El trabajo completo —diez corridas más el estudio de malla— ocupó unas 3,5 horas de cálculo.

## 10. Figuras y datos

| Figura | Qué muestra |
|---|---|
| `04_FIGURAS/F3_geometria/F3_dominio_y_cobertura.png` | El dominio, los seis abanicos y la cobertura geométrica |
| `04_FIGURAS/F2_piloto/F2_verificacion_huella.png` | Verificación del abanico contra la predicción analítica |
| `04_FIGURAS/F2_piloto/F2_masa_en_vuelo.png` | El criterio que decidió el solver |
| `04_FIGURAS/F4/F4_dosis_y_cobertura.png` | Dosis por vuelta, curva de cobertura y reparto por boquilla |
| `04_FIGURAS/F4/F4_S3_sensibilidades.png` | Las siete sensibilidades |
| `04_FIGURAS/F5/F5_nube_de_gotas_3D.png` | Los seis abanicos dentro del agujero |
| `04_FIGURAS/F5/F5_mapa_desarrollado.png` | De la huella instantánea a la dosis por vuelta |

Datos en `03_RESULTADOS/`, geometría en `01_GEOMETRIA/`, diccionarios y logs en `02_CASOS/`, scripts
en `scripts/`, protocolo de ensayo en `05_ENSAYO/`.

## 11. Trazabilidad

Cada decisión del modelo está en la ficha de F2 con la evidencia numérica que la respalda. Los
informes de fase son:

- `06_REGISTRO_ENTORNO/INFORME_F1_ENTORNO.md` — entorno y verificación de herramientas
- `03_RESULTADOS/F2_piloto/INFORME_F2_PILOTO.md` — elección de solver, inyección y modelo de pared
- `01_GEOMETRIA/INFORME_F3_GEOMETRIA.md` — dominio y control de calidad geométrico
- `03_RESULTADOS/F4/INFORME_F4_SIMULACION.md` — simulaciones, estudio de malla y sensibilidades
- `03_RESULTADOS/F5/INFORME_F5_CIERRE.md` — cierre

Todas las tablas de inyección son reproducibles: cada archivo lleva en su cabecera el comando exacto
que lo generó.
