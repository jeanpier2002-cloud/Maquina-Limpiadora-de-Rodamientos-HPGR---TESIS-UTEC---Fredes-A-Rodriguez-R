"""G0 - Verifica que PyFluent (venv TesisII_CFD) arranca Fluent 2026 R1 Student y lo cierra sin procesos huerfanos.
Requisito verificado en CFD02: redirigir MPLCONFIGDIR antes de importar ansys.fluent.core.
Uso: <venv>/python g0_pyfluent.py D:/CFD03_run/G0
"""
import os
import sys
import time
from pathlib import Path

cwd = sys.argv[1] if len(sys.argv) > 1 else "D:/CFD03_run/G0"
os.environ["MPLCONFIGDIR"] = str(Path(cwd) / ".mplconfig")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
import ansys.fluent.core as pyfluent  # noqa: E402

t0 = time.time()
print("ansys-fluent-core", pyfluent.__version__, flush=True)
solver = pyfluent.launch_fluent(precision="double", processor_count=4, mode="solver",
                                ui_mode="hidden_gui", start_timeout=240, cwd=cwd)
try:
    print("Fluent:", solver.get_fluent_version(), f"(arranque {time.time() - t0:.1f} s)", flush=True)
finally:
    solver.exit()
print(f"cerrado; total {time.time() - t0:.1f} s", flush=True)
