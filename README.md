# Máquina para el lavado de rodamientos HPGR de gran tamaño

Repositorio de la tesis *Diseño de una máquina para la limpieza de rodamientos de gran tamaño en equipos de rodillos de alta presión (HPGR) en entornos mineros*.
Universidad de Ingeniería y Tecnología (UTEC), Ingeniería Mecánica, Proyecto Final de Ingeniería Mecánica II (ME5007), 2026.

- **Autores:**
  - Ismael Enrique Rodríguez Rojas: soporte, mesa, centradores, traslado y estructura.
  - Jean Piere Fredes Arapa: aspersión, red hidráulica y CFD.
- **Asesor:** Helard Henry Alvarez Sánchez.

## Contenido

| Carpeta | Contenido | Responsable |
|---|---|---|
| [`informe/`](informe/) | Informe final (P3) en PDF y su fuente LaTeX | Ambos |
| [`cfd/`](cfd/) | Casos de ANSYS Fluent y OpenFOAM: journals, inyecciones, transcripciones, guiones de posproceso, tablas de resultados y videos | Jean |
| [`hidraulica/`](hidraulica/) | Guiones y resultados de las redes de 19, 22 y 24 boquillas, y esquema hidráulico | Jean |
| [`estructural/`](estructural/) | SAP2000, CalculiX, uniones soldadas y libro mecánico del soporte | Ismael |
| [`cad/`](cad/) | Planos y modelos CAD | Ismael |
| [`gestion/`](gestion/) | Diagrama de Gantt, presupuesto, actas y registro de decisiones | Ismael |

Las rutas de la Tabla A6.1 del informe (Anexo 6) remiten a estas carpetas.

## Alcance y estado

- El diseño está **verificado por simulación y cálculo**: mallas, paso de tiempo, dominio, balances y caso puente entre programas.
- **No está validado con ensayos.**
- El modelo de mojado mide cuánto líquido llega a cada superficie, no la remoción de grasa.
- Se publica lo esencial para reproducir los resultados. No se suben los casos de Fluent (`.cas.h5`/`.dat.h5`) ni los impactos exportados (`.dpm`, tablas crudas), que ocupan del orden de 100 GB.
- No se incluyen catálogos ni fichas de terceros: se citan en el informe.
- La empresa de remanufactura que aportó información para la tesis no se nombra.
- El uso de asistentes de inteligencia artificial está declarado en la Sección 5.1 y en el Anexo 6 del informe.

## Licencia

Todos los derechos reservados por los autores. Puede citarse como trabajo académico.
