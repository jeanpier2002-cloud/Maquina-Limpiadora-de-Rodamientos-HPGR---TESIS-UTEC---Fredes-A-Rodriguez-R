# Cifras del informe que no están en `CIFRAS_CIERRE_CFD.csv`

`CIFRAS_CIERRE_CFD.csv` se generó el 11/11/2026, antes de fijar la configuración final. Dos grupos de cifras del informe salen de otros archivos del repositorio.

## 1. t95 de la cara superior (Sección 7.2.2.6 y Tabla A6.10)

| D_req (kg/m²) | 65 | 183 | 305 |
|---|---|---|---|
| Informe: SUP_2 en su posición base | 4,1 min | 10,6 min | 17,6 min |
| Filas `C_lavado_E1, Cara superior` del CSV: Caso 3 (SUP_2 desplazada 15 mm) | 2,94 min | 7,65 min | 12,94 min |

El Caso 3 se evaluó, pero no se incorporó al diseño, así que la cifra que corresponde es la de la posición base. La reproduce `cfd/04_alcance_del_lavado/03_DOSIS_TIEMPO/t95_cara_superior_posicion_base.py` a partir de las bandas de 10 mm de la configuración base (`G7_sup_bandas_10mm_posicion_base.csv`): 7, 18 y 30 vueltas, es decir, 4,12, 10,59 y 17,65 min.

## 2. Verificación de la configuración propuesta (Sección 7.2.2.5)

«Las dosis medias cambiaron como máximo un 0,63 % entre la malla base y la fina, y un 0,42 % al cambiar el número de parcelas» son los máximos entre el diámetro exterior, la cara inferior y su zona exterior Z3. Los dos corresponden a la fila `Z3: D̄` de:

- `cfd/03_configuracion_propuesta_24/resultados/T9_malla.csv`: −0,632 %;
- `cfd/03_configuracion_propuesta_24/resultados/T9_particulas.csv`: −0,416 %.

El CSV de cierre solo trae el diámetro exterior y la cara inferior completa (0,26 %), y su 0,42 % corresponde a otra comparación: el ruido entre los brazos A y B (`T9_ruido_AB.csv`).

Los balances de masa de las seis corridas, de 0,024 a 0,125 %, están en `R3_02` a `R3_07_*_aceptacion.txt`, en la misma carpeta.
