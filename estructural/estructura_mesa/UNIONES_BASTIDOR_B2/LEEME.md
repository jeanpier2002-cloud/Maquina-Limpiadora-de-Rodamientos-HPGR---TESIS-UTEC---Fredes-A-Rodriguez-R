# UNIONES_BASTIDOR_B2: uniones soldadas del bastidor N3 (02/11/2026)

**Qué es:** el diseño de las 10 uniones a momento de la mesa N3 (M01–M07, W6X9 A36). Responde a la observación 3.2 del asesor a la P2.

**Estado:** cálculo EJECUTADO y diseño CANDIDATO; HPGR D-076 confirmada por el usuario (02/11). No apto para fabricación.

| Archivo | Contenido |
|---|---|
| `CALCULO_UNIONES_BASTIDOR_B2.md` | Informe: detalle, cargas, resultados y abiertos |
| `scripts/b2_uniones_calculos.py` | Cálculo de las uniones; usa la parrilla de Vlasov de `../SAP_ANEXO_N3_V573/scripts/p23_vlasov_continuidad_alas.py` |
| `resultados/CALCULO_UNIONES_B2.json` | Salida del cálculo (se regenera con el script) |

**Relación con otros archivos:**
- p23 vive en el anexo SAP porque extiende sus modelos (p14/p22) con la continuidad de alas.
- Sus salidas están en `../SAP_ANEXO_N3_V573/resultados/v573/continuidad_alas_b2/`.
