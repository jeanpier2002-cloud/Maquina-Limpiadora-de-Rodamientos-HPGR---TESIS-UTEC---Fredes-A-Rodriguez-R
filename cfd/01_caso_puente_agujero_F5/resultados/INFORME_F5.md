# INFORME F5 — Caso puente: interior de la rama B en ANSYS Fluent

Estado: **EJECUTADO · verificado (verificación cruzada entre solvers) · CANDIDATO**. Borrador de trabajo generado en modo autónomo el 2026-09-26; Jean debe auditarlo. **No es validación**: ambos solvers comparten la misma tabla de inyección (espesor del abanico y Rosin-Rammler SUPUESTOS) y ninguno se ha contrastado con un ensayo.

## 1. Configuración

| Elemento | Fluent (este caso) | Rama B (S2_seis, OpenFOAM v2606) |
|---|---|---|
| Solver | ANSYS Fluent 2026 R1 Student, Build 10262, 3ddp, 4 procesos | `kinematicParcelFoam` |
| Malla | Propia, hexaédrica polar estructurada (`05_SCRIPTS/malla_agujero.py --nivel base`): **512 130 celdas**, ortogonalidad mín. 0,990, AR máx. 16,4; celda en pared ≈ 5 mm radial × 6 mm en z × 0,8° | snappyHexMesh, 430 294 celdas, 4 mm en pared |
| Dominio | Cono 1:30 exacto (Z 0,890-1,405); franjas abiertas Z 0,790-0,890 y 1,405-1,445 hasta R 0,55 m; núcleo r < 0,10 m abierto (S4); lanza por celdas enmascaradas desde `lanza.stl` (S6) | Caja 1000 × 1000 × 655 mm menos el aro; lanza y núcleo mallados |
| Fase continua | Aire incompresible ρ = 0,9061 kg/m³, μ = 1,825e-5 Pa·s, k-ε estándar, gravedad −Z, p_op = 76 240 Pa | Igual (ν = 2,0141e-5 m²/s) |
| Gotas | Inertes, ρ = 982,12 kg/m³, 2 vías, sin dispersión estocástica | Igual |
| Inyección | 6 inyecciones *file* con las tablas de `gen_abanico.py` y **los mismos argumentos** que la rama B (450 parcelas por boquilla, 50°, 2° fuera del plano, RR λ = 300 µm, n = 2,5, 50-900 µm, ω×r). Σ = 0,898376 kg/s | Igual (tabla *lookup*); 22 000 parcelas/s por boquilla (S7) |
| Pared | `trap` en pared del agujero, caras del aro y lanza | `escape` en todos los patches |
| Tiempo | Transitorio 1.er orden, Δt = 5e-5 s, 10 it/paso, 700 pasos (35 ms); seguimiento no estacionario con el mismo paso | Δt = 5e-5 s, 35 ms |
| Ventana | 0,020-0,035 s (columna `flow-time` del muestreo) | Igual |
| Coste | 1 h 11 min de reloj | - |

Archivos: journal `04_CASOS/F5_puente_interior/journals/F5_base_v1.jou`; transcripción `logs/F5_base_v1_transcript.txt`; muestreo `export/*.dpm.gz` (con hash); malla y tablas con hash en `malla/`.

## 2. Checklist de citabilidad

| Punto | Resultado |
|---|---|
| Inyección efectiva | Fluent informa "Injecting 2700 particle parcels with mass 4.49188e-05 kg" por paso = 0,898376 kg/s × 5e-5 s (error < 1e-5) ✓ |
| Balance de masa en la ventana | Σ salidas (pared 0,78142 + cara inf. 0,06768 + lateral 0,04675 + superior 0,00307 kg/s) = 0,898914 kg/s vs 0,898376 inyectados → **+0,060 %** ✓ (< 1 %) |
| 3 mallas | **Pendiente (F8).** Solo malla base |
| Δt | No se estudió; se usa el Δt de la rama B |
| Dominio | Pendiente; ver supuestos S4-S6 |
| Parcelas por celda de huella | 3 418,6 (criterio ≥ 10) ✓ |

## 3. Comparación (`F5_puente.csv`)

| Indicador | Rama B S2_seis | Fluent F5_base_v1 | Diferencia | Criterio de trabajo | Cumple |
|---|---|---|---|---|---|
| ṁ depositado en el agujero (kg/s) | 0,783494 | 0,781418 | −0,26 % | - | - |
| **K2 D̄ (kg·m⁻²·vuelta⁻¹)** | 18,8086 | 18,7587 | **−0,27 %** | ≤ 5 % | SÍ |
| **K3 CV** | 0,3397 | 0,3362 | **−0,0035** | ≤ 0,03 | SÍ |
| **K4 zona seca** | 0,000 % | 0,000 % | 0 | 0 % en ambos | SÍ |
| D_min / D_max | 8,47 / 36,89 | 10,45 / 34,38 | +1,98 / −2,51 | - | - |
| **C(D_min), 1-20** | - | - | **máx. 1,33 pp** | ≤ 2 pp | SÍ |
| RMSE del perfil D(z) | - | - | 5,08 % de la media | - | - |
| K5 η (agujero) | 87,2 % | 86,98 % | - | - | - |

Reparto por boquilla (Fluent): INT_1-5 = 18,8-19,2 % cada una, INF_INT = 4,63 % (rama B: 18,8-19,1 % y 4,93 %). Tramo de INT_3: Z 1078,30-1217,50 mm (rama B: 1078,25-1217,51 mm).

Lectura: los indicadores integrales coinciden dentro del 0,3 %. Las diferencias en D_min y D_max (± 2-2,5 kg·m⁻²·vuelta⁻¹) y el RMSE del perfil del 5 % son del mismo orden que el RMSE entre mallas de la propia rama B (6,3-7,4 %), que allí se atribuyó a la resolución de rayos por banda y no a la malla (MEMORIA_CFD §5.5).

## 4. Conclusión (propuesta)

Con los criterios de trabajo de `PROMPT_MAESTRO_ANSYS.md` §4.2, el cambio de solver OpenFOAM → Fluent queda **verificado de forma cruzada** para K2, K3 y K4 en el caso interior. Esto respalda el borrador de decisión HPGR D-0xx (`00_ADMIN/D-0xx_borrador_Fluent.md`), que sigue pendiente de registro por Ismael.

## 5. Qué NO permite afirmar

- Que el agujero quede limpio (N4): el CFD mide la masa depositada con deposición perfecta (`trap`/`escape`), sin rebote ni escorrentía.
- Que D̄ o el CV sean los reales: ambos solvers usan la misma tabla de inyección con espesor de abanico y distribución de gotas SUPUESTOS. La coincidencia verifica la implementación, no la física de la boquilla (DATO EXTERNO PENDIENTE: ensayo de huella).
- Independencia de malla del caso Fluent: pendiente de F8.
