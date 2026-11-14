#!/usr/bin/env python3
"""
CORRIDA 4 · T0 · Existencia y SHA-256 de las entradas que usa esta tanda (solo lectura; no copia datos pesados).
Salida: 01_ENTRADA/HASHES_ENTRADAS.csv (ruta, existe, bytes, sha256, uso). Los .dpm no se hashean (GB): se anota tamano.
Uso: python -I -B r4_t0_entradas.py
"""
import csv
import hashlib
import os
import sys

B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
C3 = "D:/CFD_Redosado/CORRIDA_3_O7C2"
K3 = C3 + "/03_FLUENT/resultados/KPI/R3_02_03_AB/R3_02_03_AB_"
G = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_ANSYS_COMPLETO/06_RESULTADOS"
PJ = "D:/CFD_Redosado/Diseño actual/PAQUETE_JEAN_O7C2_v2_2026-10-25"
MG = "D:/CFD_Redosado/CORRIDA_1_13a21oct/METRICA_GRASA"

E = [
    (B4 + "/00_ADMIN/CRITERIO_PREREGISTRADO.md", "preregistro (hash verificado en T0)"),
    (C3 + "/03_FLUENT/resultados/T10_tiempo_lavado.csv", "T1 aceptacion"),
    (K3 + "od_bandas_10mm.csv", "T1/T4 OD"), (K3 + "od_bandas_2mm.csv", "T1/T4 OD 2 mm"),
    (K3 + "cara_inf_bandas_10mm.csv", "T1/T4 cara inf"), (K3 + "cara_inf_bandas_2mm.csv", "T1/T4 cara inf 2 mm"),
    (K3 + "zonas.csv", "T1 Z1/Z2/Z3"), (K3 + "resumen.csv", "T1"), (K3 + "od_indicadores.csv", "T1"),
    (K3 + "cara_inf_indicadores.csv", "T1"), (K3 + "od_mapa10mm.npz", "T4 lectura por celdas"),
    (K3 + "cara_inf_mapa10mm.npz", "T4 lectura por celdas"),
    (G + "/G8/comparacion/C3/G7_sup_bandas_10mm.csv", "T1 cara superior Caso 3 (reproduce T10)"),
    (G + "/G8/comparacion/C3/G7_sup_bandas_2mm.csv", "T1 cara superior 2 mm"),
    (G + "/G8/comparacion/C3/G7_sup_mapa10mm.npz", "T4 cara superior celdas"),
    (G + "/G7/G7_agujero_bandas_10mm.csv", "T1 agujero base (reproduce T10)"),
    (G + "/G7/G7_agujero_bandas_2mm.csv", "T1 agujero 2 mm"),
    (G + "/G7/G7_agujero_mapa10mm.npz", "T4 agujero celdas"),
    (C3 + "/03_FLUENT/scripts/kit/boquillas_O7_C2.json", "T2 boquillas"),
    (C3 + "/01_ENTRADA/boquillas_O7_C2_LAT1m4.json", "T2 Caso 2 (LAT_1 -4 grados)"),
    (C3 + "/03_FLUENT/scripts/kit/rayos_r05.py", "T2 metodo de rayos"),
    (C3 + "/03_FLUENT/scripts/kit/gen_abanico.py", "T2 abanico"),
    (C3 + "/03_FLUENT/scripts/kit/r3_gen_inyecciones.py", "T2 abanico O7+C2"),
    ("D:/Explosionado tesis II/R06.3_o7_c2/explosionado/_trabajo/rodamiento_step/SKF_bearing_241_900_ECAK30F_W33_2.stp",
     "T2/T3 geometria cavidad"),
    (MG + "/04_ENTREGA/U7_FICHA_CRITERIO_GRASA_v3.md", "criterio grasa"),
    (MG + "/04_ENTREGA/U9_UMBRAL_ANALOGICO.md", "tau0"),
    (MG + "/04_ENTREGA/U7_anclas_conversion.csv", "M6"),
    (PJ + "/03_CONTEXTO/R07_resultados_pendientes.md", "T5 L2 / T7"),
    (PJ + "/04_ANALISIS_PRESION_Y_BOMBA_O7C2.md", "T7 bomba"),
    (PJ + "/03_CONTEXTO/C8_red_hidraulica_24_boquillas.out.txt", "T7 caudal"),
    (PJ + "/03_CONTEXTO/DECISIONES_EXTRACTO.md", "D-058"),
    (B4 + "/01_ENTRADA/thesis_Cyriac_texto_utf8.txt", "T5 ley de temperatura"),
    ("D:/CFD03_run/G6/G6_ESUP_base_v2/sup.dpm", "T6 (no se hashea: GB)"),
    (C3 + "/03_FLUENT/casos/R3_02_caso2/cara_inf.dpm", "T6 (no se hashea: GB)"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


filas = []
for p, uso in E:
    ok = os.path.exists(p)
    n = os.path.getsize(p) if ok else ""
    hs = (sha(p) if not p.endswith(".dpm") else "no_hasheado_GB") if ok else ""
    filas.append([p, "si" if ok else "NO", n, hs, uso])
    print("%-3s %12s %s" % ("ok" if ok else "NO", n, p), file=sys.stdout)
with open(B4 + "/01_ENTRADA/HASHES_ENTRADAS.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ruta", "existe", "bytes", "sha256", "uso"])
    w.writerows(filas)
