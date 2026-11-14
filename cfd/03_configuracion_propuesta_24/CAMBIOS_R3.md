# CAMBIOS_R3 — qué se copió y qué se cambió respecto de cada original (CORRIDA 3, 25-26/10/2026)

Regla: los originales (kit de Ismael, Corrida 2, CFD03) no se tocan; se copian a `03_FLUENT/scripts/` y se editan las copias.

| Copia | Original | Cambio |
|---|---|---|
| `scripts/r3_run_fluent.py` | `CORRIDA_2/.../v3_run_fluent.py` (= `run_fluent.py` del kit) | ninguno |
| `scripts/r3_cola_fluent.py` | `v3_cola_fluent.py` | BASE = CORRIDA_3; log `cola_r3.log`; etapa `fluent_R3`; **añadido**: control de disco ≥ 20 GB, reintento único con salidas movidas a `_fallo1/`, tercera columna de la cola = aceptación previa requerida (si R3_02 no pasa, corre `<caso>_humo`) |
| `scripts/r3_procesar_auto.py` | `v3_procesar_auto.py` | rutas CORRIDA_3; ventana 25–50 ms (humos: 0–100·Δt); **añadido**: escribe `resultados/<caso>_aceptacion.txt` (pasos, Error/FATAL, 8 muestras, balance < 1 %) |
| `scripts/r3_lanzar_noche.ps1` | `v3_lanzar_noche.ps1` | rutas; parámetro `-Cola`; lanza también `r3_mantener_despierto.ps1`. Corregido el 25/10 21:15: `$cola`/`$Cola` son la misma variable en PowerShell (el primer post-proceso del humo recibió una ruta rota; se relanzó a mano) |
| `scripts/r3_mantener_despierto.ps1` | `v3_mantener_despierto.ps1` | ninguno |
| `scripts/post_cfd03/r3_procesar_caso.py` | `v3_procesar_caso.py` | solo `RAIZ` = CORRIDA_3/03_FLUENT |
| `scripts/post_cfd03/{dpm2csv,lector_impactos,post_kpi}.py` | Corrida 2 (= CFD03) | ninguno |
| `scripts/kit/r3_gen_inyecciones.py` | `gen_inyecciones_o7c2.py` del kit | solo la ruta de `gen_abanico.py` (copiado junto al script; SHA-256 F681707B… idéntico). Reproduce byte a byte los 7 `.dpm` del kit (T2) |
| `scripts/kit/r3_post.py` | `post_o7c2.py` del kit | modos S9 y A+B explícito; ventana de INF_INT 0,070–0,100 s; máscaras elegibles; las 7 inyecciones en ambas superficies; añade zonas Z1–Z3, OD bajo/alto y franja sin depósito |
| `scripts/kit/{combinar_kpi,reparto_zonas,rayos_r05,dpm2csv,lector_impactos,tabla_a_dpm,gen_abanico,k1_rayos,post_kpi,procesar_caso,post_o7c2}.py`, `boquillas_O7_C2.json`, `K1_O7C2_mascaras.npz` | kit | ninguno |
| `casos/<caso>/<caso>.jou` | `G3_A_O7_O4.jou` del kit | solo rutas, malla (leída en `D:/CFD03_run/mallas`), Δt, nº de pasos, tablas `.dpm` y, en R3_03, nombres `_A`→`_B`. Diff completo en `03_FLUENT/logs/diff_journals_kit.txt` (generado antes de la corrección siguiente) |
| ídem — **corrección 25/10 21:25** | `G3_A_O7_O4.jou` del kit | **una línea en blanco más** en el primer `/report/dpm-sample` (8 en vez de 7): con 7 inyecciones el kit no cerraba la lista de inyecciones, leía las zonas como inyecciones y Fluent no escribía ninguna muestra (humo R3_00, intento 1). `r3_corregir_dpm_sample.py`; `r3_preparar_casos.py` la incluye. No es una orden TUI nueva: es la misma respuesta por defecto que en la base |

Scripts nuevos (sin original): `r3_t0_verificar.py`, `r3_t2_inyecciones.py`, `r3_t3_mascaras.py`, `r3_t3_fidelidad_cociente.py`, `r3_preparar_casos.py`, `r3_destino.py`, y los de comparación, figuras y PDF que se añadan (cada uno documenta en su cabecera qué hace).
