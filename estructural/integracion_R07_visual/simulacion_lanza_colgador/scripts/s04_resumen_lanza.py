# -*- coding: utf-8 -*-
"""Resume el registro de SOLIDWORKS del modelo lanza–colgador (sw_log_*.txt) y lo compara con los controles a mano (controles.json).
Uso: python s04_resumen_lanza.py <sw_log.txt>. Escribe resultados/RESUMEN_SW_LANZA.json y muestra una tabla."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
B = Path(__file__).resolve().parents[1]
log = Path(sys.argv[1])
ctrl = json.load(open(B / "geometria/controles.json", encoding="utf-8"))
SY = 153.0
est, res = None, {}
for ln in log.read_text(encoding="utf-8").splitlines():
    m = re.match(r"=== (\S+)", ln)
    if m:
        est = m.group(1); res[est] = {"grupos": {}}; continue
    if est is None:
        continue
    r = res[est]
    if m := re.match(r"CreateMesh.*nodos (\d+), elementos (\d+)", ln):
        r["nodos"], r["elementos"] = int(m.group(1)), int(m.group(2))
    elif m := re.match(r"RunAnalysis err=(\d+) \(([\d.]+) s\)", ln):
        r["run_err"], r["run_s"] = int(m.group(1)), float(m.group(2))
    elif m := re.match(r"von Mises máx global ([\d.eE+-]+) MPa en \(([^)]*)\)", ln):
        r["vm_max_global"] = float(m.group(1)); r["vm_max_global_pos_sw"] = m.group(2)
    elif m := re.match(r"sonda LANZA.*von Mises máx ([\d.eE+-]+) MPa", ln):
        r["sonda_lanza_Z1450"] = float(m.group(1))
    elif m := re.match(r"sonda TRANSVERSAL.*von Mises máx ([\d.eE+-]+) MPa", ln):
        r["sonda_transversal_x240"] = float(m.group(1))
    elif m := re.match(r"desplazamiento máx de las coplas.* ([\d.eE+-]+) mm", ln):
        r["despl_boquillas_mm"] = float(m.group(1))
    elif m := re.match(r"desplazamiento máx del pie.* ([\d.eE+-]+) mm", ln):
        r["despl_pie_mm"] = float(m.group(1))
    elif m := re.match(r"desplazamiento máx del racor.* ([\d.eE+-]+) mm", ln):
        r["despl_racor_mm"] = float(m.group(1))
    elif m := re.match(r"UY medio del pie.*: ([\d.eE+-]+) mm", ln):
        r["UY_pie_gravedad_mm"] = float(m.group(1))
    elif m := re.match(r"(\S+): von Mises máx ([\d.eE+-]+) MPa en \(([^)]*)\)", ln):
        r["grupos"][m.group(1)] = {"MPa": float(m.group(2)), "pos_sw": m.group(3), "fraccion_fluencia": round(float(m.group(2)) / SY, 3)}

comparacion = {}
for est, r in res.items():
    for clave, k_sw in (("lanza_Z1450_" + est, "sonda_lanza_Z1450"), ("transversal_x240_" + est, "sonda_transversal_x240")):
        if clave in ctrl and k_sw in r:
            mano = ctrl[clave]["von_Mises_MPa"]
            comparacion[clave] = {"a_mano_MPa": mano, "SW_MPa": r[k_sw], "diferencia_pct": round(100 * (r[k_sw] - mano) / mano, 1)}
out = {"log": log.name, "fluencia_MPa": SY, "estudios": res, "controles": comparacion}
json.dump(out, open(B / "resultados/RESUMEN_SW_LANZA.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

grupos = ["LANZA", "CARRO", "VARILLA_", "COLGADOR_", "PUENTE_INF", "PUENTE_SUP", "ABRAZADERA|BRAZO_ABRAZADERA", "CUBO", "TRANSVERSAL",
          "BRIDA_", "EJE", "CUELLO_|CODO_LANZA_SUP|RACOR", "COPLA_", "PIE_"]
print("von Mises máx por grupo (MPa)")
print("grupo".ljust(30) + "".join(e[:11].rjust(12) for e in res))
for g in grupos:
    print(g[:29].ljust(30) + "".join(("%.2f" % res[e]["grupos"][g]["MPa"] if g in res[e]["grupos"] else "-").rjust(12) for e in res))
for k in ("despl_boquillas_mm", "despl_pie_mm", "despl_racor_mm", "nodos", "run_s"):
    print(k.ljust(30) + "".join(str(res[e].get(k, "-")).rjust(12) for e in res))
print("controles:", json.dumps(comparacion, ensure_ascii=False, indent=1))
