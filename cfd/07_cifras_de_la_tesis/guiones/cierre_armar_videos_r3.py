"""CFD03: arma los MP4 a partir de los cuadros PNG exportados por Fluent (figuras_fluent_cfd03.py).
Usa el ffmpeg 6.1 que trae SOLIDWORKS Flow Simulation (codificador mpeg4, sin instalar nada).
Uso: python armar_videos.py
"""
import os, subprocess, sys
from PIL import Image
from pathlib import Path

FF = r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS Flow Simulation\binCFW\ffmpeg.exe"
BASE = Path("D:/CFD_Redosado/CIERRE_CFD_TESIS/video_final/figuras_fluent")
OUT = Path("D:/CFD_Redosado/CIERRE_CFD_TESIS/video_final/videos"); OUT.mkdir(exist_ok=True)
NOMBRE = {"cb_od": "CasoBase_OD_y_cara_inferior", "c2_od": "Caso2_OD_LAT1_inclinada", "pad": "Verificacion_PAD",
          "cb_int": "CasoBase_lanza_INF_INT", "cb_sup": "CasoBase_cara_superior", "c3_sup": "Caso3_cara_superior",
          "f5": "CasoBase_agujero_lanza", "r3_od": "DisenoFinal_24boq_OD_y_cara_inferior"}

def armar(frames, salida, fps, n_usar=None, pausa_final_s=0.0):
    fr = sorted(frames.glob("f_*.png"))
    if not fr:
        print("sin cuadros:", frames); return
    if n_usar: fr = fr[:n_usar]
    fr = fr + [fr[-1]] * int(round(pausa_final_s * fps))
    # este ffmpeg no trae decodificador PNG: se envian los cuadros como RGB crudo por tuberia
    W, H = 1920, 1080
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-framerate", str(fps), "-i", "-", "-vf", "format=yuv420p", "-c:v", "mpeg4", "-q:v", "2", str(salida)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in fr:
        pr.stdin.write(Image.open(f).convert("RGB").resize((W, H)).tobytes())
    pr.stdin.close()
    if pr.wait() != 0: raise RuntimeError("ffmpeg fallo")
    print("->", salida, f"{salida.stat().st_size/1e6:.1f} MB, {len(fr)} cuadros a {fps} fps")

for caso, nom in NOMBRE.items():
    if len(sys.argv) > 1 and caso not in sys.argv[1:]: continue
    d = BASE / caso
    # spray: cuadros cada 0,5 ms de tiempo de residencia. Las gotas llegan al OD y a la cara superior en < 12 ms
    # (24 cuadros); bajo el aro (INF_INT) tardan mas y se usan los 48 cuadros (24 ms)
    armar(d / "frames_spray", OUT / f"V1_{nom}_avance_del_spray.mp4", fps=6, n_usar=48 if caso in ("cb_int", "r3_od") else 24,
          pausa_final_s=2.5)
    armar(d / "frames_orbita", OUT / f"V2_{nom}_orbita_3D.mp4", fps=15)
