# Síntesis metodológica de los papers y qué se aplica a nuestro CFD

Fecha: 19/09/2026. Hecha leyendo el resumen y las secciones de método de cada archivo (no los ocho completos). Todos los papers revisados (ya retirados de la carpeta de trabajo) son de **modelos sustitutos con aprendizaje automático (ML) sobre resultados de CFD**. Ninguno trata el spray Euler–Lagrange, la deposición ni la película, que es lo que pide `untitled (2).md` para la simulación misma. Por eso sirven para la **«Etapa posterior»** de ese documento (reducir el número de simulaciones) y para dos buenas prácticas de verificación, no para elegir el modelo físico del spray.

## Qué aporta cada paper

| Archivo | Tema | Uso en nuestro trabajo |
|---|---|---|
| `ml_spray_c_f.md` (Ganti y Khare, 2020) | Chorros multifásicos: diseño de experimentos (DoE) → simulaciones de referencia → descomposición POD → regresión de proceso gaussiano (GP) → error en condiciones no usadas | **Plantilla del flujo de sustituto**: DoE sobre números adimensionales, GP, error frente a casos de prueba. Solo tras validar el CFD |
| `energies-13-04565-v2.md` (Ganti et al., 2020) | Igual, chorro en flujo cruzado turbulento con LES | Confirma el flujo. Dato útil: aceptan ≈ 15 % de error a cambio de una aceleración de ~65× y advierten que más puntos de entrenamiento mejoran cada vez menos. Su criterio de cierre es el error en puntos de prueba, no en los de entrenamiento |
| `2507.07034v2.md` (Vaillant et al., 2025) | CNN sustituta para matrices de chorros, 83–100 simulaciones | **Estudio de malla en tres niveles** (0,2 / 1,2 / 3,0 M celdas; independencia a 1,2 M con RMSE 0,07) hecho **en un solo caso representativo** y reutilizado para todo el conjunto. Reparto entrenamiento/validación. 83–100 simulaciones es demasiado para nosotros |
| `2402.10641v1.md` (Salavatidezfouli et al., 2024) | Chorro pulsado sobre superficie cóncava; FFT-ANN y POD-LSTM | Precedente de malla modesta para un chorro sobre una superficie curva (4·10⁵ a 1,5·10⁶ celdas, estructurada). El resto (Nusselt, pulsos) no aplica |
| `1906.02382v2.md` (Sun et al., 2019) | Red neuronal con física (PINN) sin datos de simulación | Solo dos ideas: verificar contra OpenFOAM con estudio de malla y propagar incertidumbre de una entrada con muestreo Monte Carlo (500 muestras) **sobre el sustituto**, no sobre el CFD. La PINN no es para un primer proyecto |
| `2206.06817v3.md` (Jeon et al., 2022) | Aprendizaje por transferencia con residuales para acelerar CFD largos | No aplica ahora; el CFD ni siquiera existe |
| `2109.15203v1.md` (Schmidt et al., 2021) | Turbulencia con red neuronal en chorros con evaporación súbita | No aplica (evaporación, atomización interna) |
| `2008.06731v1.md` (Renganathan et al., 2020) | DNN + GP para diseño aerodinámico | Solo la idea de DNN como media previa de un GP; no aplica |

## Qué se adopta (con las herramientas que hay)

1. **Estudio de malla en un solo caso representativo** y reuso de esa densidad en las variantes (2507). Encaja con nuestro equipo.
2. **Separar el error de entrenamiento del de prueba** y fijar antes de simular el error aceptable para el sustituto (Ganti: ~15 %), medido en casos no usados.
3. **Sustituto sobre indicadores, no sobre campos completos.** Ganti hace POD del campo entero; para nosotros basta un GP (scikit-learn, en Windows) sobre 3–5 indicadores por caso (cobertura, uniformidad, dosis media, masa perdida). Cuesta mucho menos y se interpreta.
4. **Presupuesto de casos realista:** 15–30 simulaciones, no 100. Con 2–4 parámetros (distancia, inclinación, ángulo de abanico, presión) basta un muestreo de hipercubo latino (Latin hypercube).
5. **Incertidumbre de lo que no conocemos** (tamaño de gota, ángulo real): se propaga sobre el sustituto una vez validado.

## Qué no se adopta

- PINN, POD-LSTM, redes convolucionales, evaporación súbita y LES: exceden el alcance y el hardware, y no responden a la pregunta física.
- Cualquier cifra de rendimiento de estos papers (65×, 2 %, 0,6 %) como meta nuestra: son de otros sistemas.

## Vacío de literatura

Para elegir y justificar el modelo del spray (inyección de gotas, interacción con la pared, película) **no hay entre los revisados un paper adecuado**. `untitled (2).md` habla de «literatura revisada sobre sistemas multi-boquilla y mojado superficial», pero esos documentos no se aportaron. Hace falta que el usuario los aporte o que el chat de ejecución busque 2–3 (Euler–Lagrange con deposición y splash, película delgada, cobertura de spray-arms). Hasta entonces la referencia técnica de esos submodelos son los tutoriales de OpenFOAM.
