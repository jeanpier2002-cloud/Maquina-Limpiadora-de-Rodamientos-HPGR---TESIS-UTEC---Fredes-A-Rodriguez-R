# Red hidráulica

| Carpeta | Contenido |
|---|---|
| `red_19_caso_analitico/` | Caso analítico de 19 boquillas: libro de cálculo, memoria y matriz de trazabilidad (Anexo 3, §3.2–3.3) |
| `red_22_configuracion_base/` | `calculo_red_22.py` y `resultados_22.json`: 202,59 L/min y 52,56 m (Anexo 3, §3.4) |
| `red_24_configuracion_propuesta/` | `calculo_red_24.py` y `resultados_24.json`: 221,07 L/min y 53,39 m, con la red de 22 como control; salida C8 original, análisis de la bomba y altura con el trazado R07 (Anexo 3, §3.5) |
| `esquema/` | Esquema hidráulico HPGR-HID-001, hojas 1 y 2 |

Método: caudal proporcional a √p, Darcy–Weisbach con Swamee–Jain, pérdidas locales K = n·f_T (Crane TP-410) y aproximaciones sucesivas hasta que la boquilla más desfavorable reciba 4,00 bar.
