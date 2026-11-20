# -*- coding: utf-8 -*-
"""Arma el ZIP liviano para Jean con el estudio del brazo de la U (sin los resultados .CWR de SOLIDWORKS, que pesan ~1,2 GB).
No modifica ni borra nada de la carpeta: solo lee y escribe el ZIP nuevo. Ejecutar con el Python del usuario (usa PIL y pypdfium2)."""
import hashlib
import io
import site
import sys
import zipfile
from pathlib import Path

sys.path.append(site.getusersitepackages())
from PIL import Image
import pypdfium2 as pdfium

sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).resolve().parents[1]
HO = D.parents[2]
R07 = D.parent
SAL = R07 / "PARA_JEAN_U_CHORROS_SOLIDWORKS_2026-11-10.zip"
RAIZ = "U_CHORROS_SOLIDWORKS/"

entradas = []   # (ruta en el zip, bytes o Path)
entradas.append(("LEEME_JEAN.md", D / "LEEME_JEAN.md"))
entradas.append(("LEEME.md", D / "LEEME.md"))
for f in ("BRAZO_SIN_PLACA_SW_043142.SLDPRT", "BRAZO_CON_PLACA_SW_043845.SLDPRT"):
    entradas.append(("modelo/" + f, D / "modelo" / f))
for f in sorted((D / "geometria").iterdir()):
    entradas.append(("geometria/" + f.name, f))
for f in ("salida_malla_5mm.txt", "salida_malla_3mm.txt"):
    entradas.append(("registros/" + f, D / "resultados" / f))
for f in sorted((D / "scripts").iterdir()):
    if f.suffix in (".py", ".cs", ".ps1") and f.name != "s04_zip_para_jean.py":
        entradas.append(("scripts/" + f.name, f))
entradas.append(("scripts/s04_zip_para_jean.py", D / "scripts" / "s04_zip_para_jean.py"))
for f in ("scripts/r07_reaccion_chorros_U.py", "resultados/REACCION_CHORROS_U.json"):
    entradas.append(("calculo_a_mano/" + Path(f).name, R07 / f))
entradas.append(("calculo_a_mano/chorros_U.png", HO / "05_ENTREGABLES_TESIS/memoria_explicada_asesor_semana13/images/figuras/chorros_U.png"))

# Imágenes: las de los estudios vigentes (malla de 5 mm y malla fina _h3), recomprimidas a JPEG de calidad 85
imgs = 0
for f in sorted((D / "resultados").glob("*.jpg")):
    im = Image.open(f).convert("RGB")
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85, optimize=True)
    entradas.append(("imagenes/" + f.name, b.getvalue()))
    imgs += 1

# Páginas de la memoria con la sección 7 (índices 24 a 30 del PDF, base 0)
src = pdfium.PdfDocument(str(HO / "05_ENTREGABLES_TESIS/memoria_explicada_asesor_semana13/Memoria_explicada_y_guion_semana13.pdf"))
nuevo = pdfium.PdfDocument.new()
nuevo.import_pages(src, list(range(24, 31)))
b = io.BytesIO()
nuevo.save(b)
entradas.append(("Memoria_seccion7_chorros_U.pdf", b.getvalue()))

with zipfile.ZipFile(SAL, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for nombre, x in entradas:
        datos = x if isinstance(x, (bytes, bytearray)) else Path(x).read_bytes()
        z.writestr(RAIZ + nombre, datos)

# Verificación: abrir, probar CRC y comparar con los originales
with zipfile.ZipFile(SAL) as z:
    malo = z.testzip()
    nombres = z.namelist()
    distintos = 0
    for nombre, x in entradas:
        if not isinstance(x, (bytes, bytearray)):
            if hashlib.sha256(z.read(RAIZ + nombre)).digest() != hashlib.sha256(Path(x).read_bytes()).digest():
                distintos += 1
h = hashlib.sha256(SAL.read_bytes()).hexdigest()
print("ZIP:", SAL)
print("archivos: %d (imágenes %d) | %.1f MB | testzip: %s | distintos del original: %d" % (len(nombres), imgs, SAL.stat().st_size / 1e6, malo or "OK", distintos))
print("SHA-256:", h)
print("ruta más larga dentro del ZIP:", max(len(n) for n in nombres))
