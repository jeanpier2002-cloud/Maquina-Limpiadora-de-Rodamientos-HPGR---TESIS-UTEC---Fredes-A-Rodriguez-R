# CFD del sistema de aspersión

Simulación del mojado con fase discreta (DPM) en ANSYS Fluent 2026 R1 (licencia Student) y en OpenFOAM v2606.

| Carpeta | Qué es | Dónde está en el informe |
|---|---|---|
| `01_caso_puente_agujero_F5/` | El mismo caso del agujero en Fluent y en OpenFOAM. Diferencia de −0,27 % en la dosis media | Anexo 6, caso puente |
| `02_configuracion_base_22/` | Configuración base de 22 boquillas: casos por superficie, verificación (mallas, Δt, dominio, parcelas), variantes del diámetro exterior y guiones | 7.2.2.2–7.2.2.4; Anexo 6 |
| `03_configuracion_propuesta_24/` | Configuración propuesta de 24 boquillas (Corrida 3): journals, entradas, KPI, tablas T7, T9 y T10, y figuras | 7.2.2.5 |
| `04_alcance_del_lavado/` | Tiempo de lavado t₉₅, sombras de la cara inferior, acceso al interior del rodamiento armado y masa de grasa | 7.2.2.6; Anexo 6, §6.5–6.6 |
| `05_VOF_impacto_local/` | VOF (`interFoam`) del impacto de una lámina sobre el diámetro exterior | Anexo 6, §6.7 |
| `06_OpenFOAM_agujero_rama_B/` | Caso del agujero en OpenFOAM (`kinematicParcelFoam`), anterior al cambio a Fluent | Anexo 6 |
| `C3_TOLERANCIAS_COPLAS/` | Cribado geométrico por rayos: efecto de las tolerancias de las coplas (±2 mm, ±1°) sobre la aspersión del aro. No es CFD | Anexo 6, tabla A6.1 |
| `07_cifras_de_la_tesis/` | Guiones y tablas que generan las cifras del capítulo VII | Cap. VII |
| `guiones_comunes/` | Generación de mallas e inyecciones, y posproceso de KPI | — |
| `videos/` | Videos de las trayectorias usados en la sustentación | — |

**No incluido, por tamaño:** los casos de Fluent (`.cas.h5`, `.dat.h5`), las mallas (`.msh`), los impactos exportados (`.dpm` y tablas crudas de cientos de MB), los directorios de tiempo de OpenFOAM y los registros pesados. Las transcripciones de más de 2 MB están comprimidas (`.txt.gz`).
