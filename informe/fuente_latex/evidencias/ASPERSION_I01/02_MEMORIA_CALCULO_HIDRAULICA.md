---
work_name: V5.2_ASPERSION_AUDIT_AND_HANDOFF_I01
status: PENDIENTE_DATOS_DE_ENTRADA
---

# 02. Memoria de cálculo hidráulica

## 1. Arquitectura reconstruida

### Confirmado en V5.2

Rodamiento fijo → Head A móvil sobre un único trolley/monorriel → drenaje por piso/bandeja hacia sumidero heredado. Head A tiene ocho cuerpos de boquilla representativos (4 superiores y 4 laterales), pero cantidad, patrón, presión y simultaneidad siguen pendientes.

### No confirmado

No existe decisión única entre paso único, recirculación por lote o lavado recirculado con enjuague de un solo paso. La lanza axial no está activa en V5.2; el PFD la conserva únicamente como antecedente `SUPERSEDED_ARQUITECTURA`, fuera del dimensionamiento vigente.

## 2. Escenarios que deben compararse

| Escenario | Descripción | Ventaja | Bloqueo principal | Estado |
|---|---|---|---|---|
| A | Suministro de un solo paso | Simple y trazable | Alto consumo/efluente y contención completa | CANDIDATO |
| B | Recirculación por lote | Reduce reposición | Requiere tanque, retorno, filtro, purga y control de contaminación | CANDIDATO |
| C | Lavado recirculado + enjuague de un solo paso | Separa eficiencia y calidad final | Mayor complejidad y dos balances | CANDIDATO |

Ninguno fue seleccionado silenciosamente. El libro permite completar los tres.

## 3. Ecuaciones controladas

### Boquillas

`Q2 = Q1·sqrt(P2/P1)` solo es válido para el mismo orificio y fluido. El caudal simultáneo es `Qsim = ΣQi` de las boquillas activas, no de todas las instaladas.

### Etapas y balance

Paso único: `Vi = Qsim,i·ti`; `Vciclo = ΣVi`.

Recirculación: `Vtanque` se compone de inventario del circuito, mínimo operativo, sumidero, retorno pendiente, reserva, sedimentos y reposición. No se iguala automáticamente a `Q×t`.

### Cobertura

`W = 2S·tan(α/2)` es solo una huella plana ideal. Debe corregirse por curvatura, incidencia, sombra, solape, jaula y rodillos.

### Movimiento

`vt = ωR`; `tvuelta = 2π/ω`. El tiempo local requiere huella efectiva y velocidad tangencial. Los frames V5.1 no son segundos industriales.

### Tuberías

`Re = ρVD/μ`; `hf = f(L/D)V²/(2g)`; `hm = ΣK·V²/(2g)`.

### Bomba

`HTDH = Δz + ΔPboquilla/(ρg) + hf + hm + hfiltro`;
`Ph = ρgQH`; `Pmotor = Ph/(ηpηm)`.

La bomba se puede seleccionar solo con curva real Q-H, NPSH y materiales compatibles.

## 4. Riesgos y límites

- Presión alta/orificio pequeño puede incrementar niebla, rebote y riesgo de daño.
- Cobertura geométrica HIT no equivale a remoción de grasa.
- El retorno de fluido contaminado requiere filtración y criterio de purga.
- El sumidero de 58.5 L es solo una envolvente geométrica preliminar.
- La manguera anular sigue pendiente de validación dinámica.
- La lanza axial entra en conflicto con la arquitectura/piso y no se considera activa.

## 5. Condición para avanzar

Completar primero las entradas de prioridad ALTA en `DATOS_FALTANTES_ASPERSION_V5_2.csv`, especialmente fluido/SDS, catálogo Q-P, simultaneidad, etapas, rutas de tubería y arquitectura A/B/C.
