# Análisis estructural

Diseño CANDIDATO, verificado solo por simulación (sin ensayos).

| Carpeta | Qué es | Dónde está en el informe |
|---|---|---|
| `N3_R01/` | Corrida de referencia en SAP2000 24.2.0 (`.sdb`, tablas exportadas y SHA-256) | Anexo 6 |
| `N3_R05/` | Libro mecánico reproducible de la revisión 5: guion Python, libro editable, resultados JSON y modelos de la mesa | Anexo 6 |
| `integracion_R06/R06.1_centradores/resultados/k2m_v57/` | FEM local de los centradores K2-M (versiones 5.7 a 5.7.4), con el FEM de contacto del amarre en CalculiX y SOLIDWORKS (`fem_contacto_v573/`) | Anexo 6 |
| `integracion_R06/R06.1_centradores/resultados/n3_global_v571/` | Modelo global de la mesa con los centradores y con alabeo | Anexo 6 |
| `integracion_R06/00_ANALISIS_PREVIOS_2026-09-24/J2_soportes_riel_recalculo.md` | Recálculo de los soportes del riel | Anexo 6 |
| `integracion_R07_visual/soporte_sap/` | Soporte superior K32 y cabina en SAP2000: modelos `.sdb` y `.$2k`, tablas exportadas, anexo SAP y cálculo de las bases con sismo E.030 | Anexo 6 |
| `estructura_mesa/UNIONES_BASTIDOR_B2/` | Uniones soldadas del bastidor y parrilla con alabeo | Anexo 6 |
| `integracion_R07_visual/simulacion_eje_sf47/` | Eje del motorreductor de la U (SOLIDWORKS Simulation) | Anexo 6 |
| `integracion_R07_visual/simulacion_u_chorros/` | Brazo de la U cargado con la reacción de los chorros (SOLIDWORKS Simulation) | Anexo 6 |
| `integracion_R07_visual/simulacion_lanza_colgador/` | Lanza, colgador y unión W5 con sus variantes de refuerzo (SOLIDWORKS Simulation) | Anexo 6 |

Cada carpeta trae su informe (`.md`), los guiones, los modelos y los resultados resumidos (JSON y CSV).

**No incluido, por tamaño:** los resultados binarios de los solucionadores (`.CWR` de SOLIDWORKS, `.frd` y `.dat` de CalculiX, archivos de análisis de SAP2000), las tablas de datos crudos de más de 3 MB y los registros de consola. Se regeneran con los modelos y guiones publicados. La lista está en `NO_PUBLICADOS.md`.

En los guiones y registros, las rutas absolutas de la máquina de los autores aparecen como `C:\Users\<usuario>\…`.
