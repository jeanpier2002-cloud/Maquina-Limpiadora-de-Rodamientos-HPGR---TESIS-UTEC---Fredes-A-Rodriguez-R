# Comprobaciones de los topes de retención (03/11/2026)

Scripts de solo lectura con los que se midió la unión de los topes en el CAD y se revisó el barrido (HPGR D-083). Se corren con freecadcmd, salvo `dif_audit.py`, que usa Python.

| Script | Qué mide |
|---|---|
| `aud_revb.py` | Compara las piezas de MES-400, 800 y 900 entre V10, V17B y V18C |
| `aud_tope.py`, `aud_tope2.py` | Huella real del tope de 60° sobre el ala y piezas vecinas |
| `aud_tope3.py` | Secciones y prueba de las cartelas interiores contra todo el CAD |
| `aud_tope4.py` | Qué sostiene el tope de 190° |
| `aud_tope5.py` | Si cabe la chapa de 16 mm bajo cada tope |
| `aud_tope6.py` | Qué ocupa r 630–715, z 805–885 (partes que giran) |
| `aud_bujes.py` | A quién pertenece cada buje del bloqueo (explica un falso choque del barrido) |
| `dif_audit.py` | Diferencia de solapes entre la auditoría de V18B y la de V18D |
| `lista_mesa.py` | Objetos visibles de la V18D por grupo |

`secc_topes.png` y `secc_190.png` son los cortes de trabajo. Las figuras limpias están en `05_ENTREGABLES_TESIS/defensa_P3/figuras_guia/`.
