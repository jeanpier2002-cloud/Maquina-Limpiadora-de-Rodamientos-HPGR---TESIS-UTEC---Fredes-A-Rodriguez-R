---
work_name: V5.2_ASPERSION_AUDIT_AND_HANDOFF_I01
status: PENDIENTE_DATOS_DE_ENTRADA
handoff_target: Claude
language: es
do_not_claim:
  - SISTEMA_VALIDADO
  - BOMBA_SELECCIONADA
  - DISENO_FINAL
  - LISTO_PARA_FABRICAR
---

# Handoff para Claude - sistema de aspersión HPGR V5.2

## Instrucción corta para Claude

Empieza por `START_HERE_CLAUDE.md`, `SOURCE_PRECEDENCE.md` y `RIGHTS_AND_SHARING.md`. Continúa el dimensionamiento únicamente desde los archivos compartidos en el paquete; una ruta `C:\...` es solo un localizador de trazabilidad y no significa que puedas abrir la fuente. Conserva el estado `PENDIENTE_DATOS_DE_ENTRADA` hasta recibir catálogo real de boquillas, fluido/SDS, simultaneidad, secuencia, tuberías y decisión A/B/C. No selecciones bomba ni conviertas antecedentes de 4–6 bar, 19.8/24 L/min, 80 L o 16 L/ciclo en requisitos.

## Reglas de evidencia

- Para identidad y dimensiones del rodamiento exacto gobierna la ficha SKF `241/900 ECAK30/W33`; no sustituirla por el `24088` ni por la variante sellada `241/900-2CS5...`.
- Para arquitectura gobierna V5.2 → V5.1 → V5. Los documentos Layout B, manifold U y lanza axial son `SUPERSEDED_ARQUITECTURA`.
- El manual FAG/Schaeffler de daños se cita como edición **2004**, no 2015.
- Las páginas son páginas físicas del PDF. No mezclar con la numeración impresa.
- La bibliografía análoga aporta tendencias, riesgos y diseño experimental; no convierte sus cifras en datos de entrada.
- Un catálogo oficial de la boquilla que finalmente se estudie y una curva real de bomba prevalecen sobre ejemplos genéricos.
- Si dos fuentes discrepan, registra el conflicto; no promedies ni elijas silenciosamente.

## Alerta de confidencialidad

El manual ENDURON/Weir no forma parte del paquete. Su página PDF 1 lo declara confidencial y prohíbe copiarlo o divulgarlo sin autorización escrita. No solicites, reproduzcas ni reconstruyas contenido protegido. Si el propietario confirma permiso, úsalo solo para restricciones de la máquina específica RPS16 170/180 y conserva la cita por página.

## Contexto estructurado

```yaml
project: V5.2_ASPERSION_AUDIT_AND_HANDOFF_I01
current_status: PENDIENTE_DATOS_DE_ENTRADA
mechanical_architecture:
  bearing: fixed
  bearing_model: SKF 241/900 ECAK30/W33
  bearing_geometry_mm: {ID: 900, OD: 1420, B: 515}
  monorail: {physical: true, nominal_radius_mm: 1300, nominal_z_mm: 2050}
  trolley_count: 1
  positioning: [theta, R, Z, beta]
  active_head: Head_A
  head_A_geometry_only: {side_nozzles: 4, top_nozzles: 4, standoff_mm: 150}
  bearing_or_platform_rotation: false
  axial_lance_active: false
  superseded_architecture: [Layout_B, mobile_U_manifold, active_axial_lance]
hydraulic_architecture_selected: false
candidate_scenarios: [A_once_through, B_batch_recirculation, C_recirculated_wash_once_through_rinse]
critical_contradiction: "480 L/ciclo de paso único vs carga 80 L/reposición 16 L sin retorno/filtración definidos"
required_next_file: CALCULO_SISTEMA_ASPERSION_V5_2_I01.xlsx
high_priority_missing_inputs: 25
source_manifest: SOURCE_MANIFEST.csv
rights_gate: RIGHTS_AND_SHARING.md
```

## Qué está confirmado

- [x] Rodamiento fijo y geometría base 900/1420/515 mm; masa aproximada 3032 kg.
- [x] Monorriel 360°, un trolley y posicionamiento `theta/R/Z/beta`.
- [x] Head A como cabezal físico vigente; standoff geométrico 150 mm.
- [x] Drenaje/sumidero existen como geometría heredada.
- [x] Los originales permanecen sin cambios.

## Qué cálculos ya existían

- [x] Sensibilidad paramétrica de velocidad, caudal y potencia por orificio.
- [x] Ejemplo de bomba 19.8 L/min, 4 bar, H≈56 m y P≈0.40 kW.
- [x] Ejemplo extremo 24 L/min a 6 bar.
- [x] Huella plana y solape paramétricos.
- [x] Cobertura geométrica V5.1 y ventana visual de activación.
- [x] Balance aritmético 24 L/min×20 min=480 L.

## Qué fue corregido o reclasificado

- [x] Todos los valores anteriores quedaron como `SUPUESTO_DE_ESCENARIO`, `INCOMPLETO` o `DOCUMENTADO`, nunca como selección.
- [x] Se separó número instalado de número simultáneo.
- [x] Se eliminó la equivalencia incorrecta entre volumen bombeado y tamaño de tanque recirculado.
- [x] Se documentó que 80 L/16 L solo es posible con una recirculación aún no diseñada.
- [x] La lanza axial, el manifold U y Layout B quedaron rotulados como arquitectura superseded; no son equipo vigente.

## Bloqueos actuales

- [!] Catálogo Q-P/patrón de boquilla no disponible.
- [!] Fluido, temperatura, viscosidad y compatibilidad química no definidos.
- [!] Arquitectura A/B/C no aprobada.
- [!] Simultaneidad y duración por etapa no aprobadas.
- [!] Tuberías, mangueras, accesorios, elevaciones y pérdida de filtro sin medir.
- [!] Curva de bomba, NPSH y eficiencia no disponibles.
- [!] Retorno, purga, filtración, sedimentos y drenaje sin dimensionar.
- [!] Criterio de atomización y fin de lavado sin ensayo.

## Orden recomendado

1. [ ] Reunir SDS del fluido y aprobación de compatibilidad.
2. [ ] Obtener 2–4 catálogos oficiales candidatos con curvas Q-P y tamaño de gota/patrón.
3. [ ] Aprobar escenario A, B o C.
4. [ ] Completar `01_ENTRADAS`, `02_ETAPAS_CICLO` y `03_BOQUILLAS` en el XLSX.
5. [ ] Definir simultaneidad en `04_SIMULTANEIDAD`.
6. [ ] Medir rutas CAD y completar tuberías/accesorios.
7. [ ] Revisar TDH y construir curva del sistema.
8. [ ] Comparar curvas reales de bomba; no escoger por potencia nominal sola.
9. [ ] Dimensionar tanque/sump/drenaje con el escenario aprobado.
10. [ ] Ejecutar piloto Nivel I y Nivel II; actualizar cobertura, niebla y criterio de limpieza.

## Decisiones que requieren aprobación del equipo

- arquitectura A/B/C;
- fluido y temperatura;
- zonas que operan simultáneamente;
- cualquier propuesta futura de reintroducir una lanza axial, que exige una nueva decisión mecánica explícita y no forma parte de esta base;
- criterio de limpieza y límite de niebla;
- política ambiental de retorno, purga y descarga.

## Resultados que deben volver al CAD

- diámetros y rutas reales de mangueras/tuberías;
- tamaño y masa de bomba/filtro/manifold/tanque;
- ubicación de válvulas e instrumentos;
- envolvente de mantenimiento;
- radios mínimos de manguera y esfuerzos sobre trolley;
- nivel útil del sump y diámetros de drenaje.

## Resultados para la tesis

- arquitectura elegida y justificación;
- curva Q-H del sistema y punto de bomba;
- balance por etapa y por ciclo;
- consumo, retorno, purga y efluente;
- cobertura experimental, uniformidad/CV y atomización;
- límites, supuestos y trazabilidad bibliográfica.

## Formato de respuesta esperado de Claude

Antes de calcular, devuelve primero una tabla de `conflictos`, `datos críticos faltantes`, `fuentes realmente adjuntas` y `fuentes solo referenciadas`. Por cada cálculo devuelve: `ID`, `fórmula`, `entradas con unidad`, `source_id + página/celda`, `resultado`, `unidad`, `estado`, `sensibilidad` y `bloqueos`. Si falta un dato, no lo inventes: agrégalo a `15_DATOS_FALTANTES` y deja el resultado pendiente.
