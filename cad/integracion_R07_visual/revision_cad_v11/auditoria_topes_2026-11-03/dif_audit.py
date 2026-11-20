import json
R = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\resultados"
a = json.load(open(R + r"\rv07_resumen_v18b.json", encoding="utf-8"))
b = json.load(open(R + r"\rv08_resumen_v18d.json", encoding="utf-8"))
print(str(b["solapes_detalle"][0])[:200])


def pares(d):
    return {tuple(sorted((x[0], x[1]))): x[2] for x in d["solapes_detalle"]}


A, B = pares(a), pares(b)
print(len(A), len(B))
print("solo en V18B:")
for k in sorted(set(A) - set(B)):
    print("  ", k, A[k])
print("solo en V18D:")
for k in sorted(set(B) - set(A)):
    print("  ", k, B[k])
