# Simulación del eje de salida del SF47 en SOLIDWORKS (10/11/2026)

**Estado.** EJECUTADO en SOLIDWORKS Simulation 2024 (licencia educativa), sobre HIPÓTESIS de material, apoyo y radios. Es una verificación por simulación, sin validación experimental. No es una decisión.

**Motivo.** El usuario pidió simular el eje conectado al motorreductor para tener los esfuerzos en forma gráfica. Antes solo estaban la comprobación de catálogo de SEW (D-062) y el cálculo a mano del diámetro mínimo (`../resultados/NOTA_EJES_SECADO_EMPUJE_2026-11-10.md`).

## Modelo

**Geometría** (`scripts/s01_geometria_eje_sf47.py`, FreeCAD). Medidas tomadas del STEP de SEW (`04_REFERENCIAS/cad_comerciales_R07/SF47R17DRN63MS4_brida160_eje25x50.stp`):
- eje Ø25 × 50 mm con chaflán de 1 mm;
- resalte a Ø29,76 en la cara de la brida;
- chavetero forma A de 8 de ancho y 4 de fondo, de 5 a 45 mm desde el resalte, para una chaveta de 8 × 7 × 40.

**[HIPÓTESIS]:**
- radio de 1 mm en el resalte (el STEP lo dibuja con canto vivo);
- radio de 0,4 mm en el fondo del chavetero (DIN 6885 da 0,16–0,25 mm, así que el pico real sería algo mayor);
- sin el agujero de centro M10;
- dentro del reductor, un cuerpo de apoyo Ø50 empotrado en Z −30, lejos del resalte.

**Cargas** (D-062 y `CALCULO_CARGA_RADIAL_SF47.md`). Se aplican como carga remota distribuida en la cara de la punta, ubicada en el eje a 92 mm del resalte (línea media de la correa). La fuerza va en −Y, lo que pone el chavetero del lado traccionado: es el peor giro.

| Estudio | Fuerza radial | Par |
|---|---|---|
| CON_LIMITADOR | 625 N | 30 N·m |
| ATASCO_SIN_LIMITADOR | 3 938 N | 189 N·m |

**Material:** C45 normalizado [HIPÓTESIS]: E 210 GPa, ν 0,30, Sy 305 MPa, Su 580 MPa.

**Malla:** curvatura combinada, tetraedros de 2.º orden, de 1,5 a 0,15 mm. Son 418 503 nodos y 296 191 elementos. Cada análisis tardó unos 25 s.

## Resultados

| | Con limitador | Atasco sin limitador |
|---|---|---|
| von Mises máximo, extremo del chavetero junto al resalte (Z 5,2) | **105 MPa** | **662 MPa** |
| von Mises en el radio del resalte | 84 MPa | 527 MPa |
| Desplazamiento máximo (punta) | 0,036 mm | 0,23 mm |
| Factor frente a la fluencia (305 MPa) | **2,9** | **0,46**: fluye |
| Factor frente a la rotura (580 MPa) | 5,5 | 0,88 |
| Fatiga, Goodman, escalando el cálculo a mano con el pico FEM | **≈ 1,8** | — |

**Control frente a la teoría.** La tensión axial en la generatriz inferior, a Z = 25, da −31,5 MPa en el FEM. Con M/W de la sección rebajada por el chavetero da −31,6 MPa:
- M = 625 × 67 N·mm;
- W = 1 325 mm³ (A 460,6 mm², centroide a −0,68 mm, I 15 652 mm⁴).

La diferencia es del 0,3 %.

**Lectura:**
- El punto crítico es **el extremo del chavetero, junto al resalte**: ahí se juntan el mayor momento (la correa a 92 mm) y la concentración del chavetero.
- El pico es 2,55 veces la tensión nominal de 41 MPa.
- La estimación a mano con K_t de libro (95 MPa) queda un 10 % por debajo. Por eso la fatiga baja de n 1,97 (a mano) a ≈ 1,8.
- **Con el limitador, el eje Ø25 cumple** con margen estático y de fatiga.
- **Sin el limitador, el atasco lo hace fluir:** el limitador es un requisito (D-062).

## Limitaciones

- La fuerza de la correa sigue sin cerrar: 625 N frente a 1 071 N [VERIFICAR]. Con 1 071 N, las tensiones suben un 71 % y el pico pasa a unos 180 MPa: factor 1,7 a fluencia y fatiga < 1,5.
- Los radios de 1 y 0,4 mm, el material del eje (SEW no lo publica) y el apoyo son hipótesis.
- Es un análisis lineal: en el atasco solo indica que se supera la fluencia, no cuánto se deforma.
- No incluye el contacto de la chaveta ni del cubo ROBA: la carga entra por la cara de la punta. El cálculo cerca de la punta no es representativo, aunque la zona crítica está a 45 mm.

## Archivos

| Carpeta | Contenido |
|---|---|
| `geometria/` | `EJE_SF47_D25.step` y `.FCStd` |
| `modelo/` | `EJE_SF47_D25_SW_033615.SLDPRT`, con los dos estudios y sus resultados |
| `resultados/` | `VM_*_iso.jpg`, `VM_*_zoom_resalte.jpg`, `DESPL_*_iso_mm.jpg`, `SZ_generatriz_inferior_*.csv`, `sw_log_033615.txt` |
| `scripts/` | `s01` (FreeCAD), `s02` (SOLIDWORKS: estudio y análisis) y `s03` (imagen de desplazamiento en mm) |

En `resultados/`, las imágenes `DESPL_*_iso.jpg` sin `_mm` salieron con otra unidad (Å). Se conservan, pero valen las `_mm`.
