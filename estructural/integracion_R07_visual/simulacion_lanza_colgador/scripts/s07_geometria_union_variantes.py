# -*- coding: utf-8 -*-
"""Variantes de refuerzo de la unión transversal–cubo (soldadura W5), para compararlas en SOLIDWORKS (12/11/2026).
Parte del submodelo de s05 (misma copia del CAD R07 V18D, mismos cordones W5) y genera cinco geometrías:
  BASE  DN50 Sch 10S (t 2,77), como s05, con la zona fina alargada a x = 170–272 para que entren las puntas de los refuerzos.
  S40   tramo central DN50 Sch 40S (t 3,91): mismo diámetro exterior 60,3; el agujero del injerto central sigue abierto.
  S80   tramo central DN50 Sch 80S (t 5,54).
  CART  Sch 10S + cartela vertical de 8 mm en el plano de la U (y = 0), soldada a la pared del cubo (R200) y sobre el tubo;
        60 mm de alto en la pared, punta a x = 266 con nariz de 6 mm × 7 mm; cordones de filete a ambos lados (HIPÓTESIS de forma).
  LENG  Sch 10S + lengüeta horizontal de 8 mm apoyada sobre el tubo, a tope contra el cubo (prolonga la placa inferior):
        semiancho 50 mm en el borde del cubo, 14 mm en la punta (x = 255); cordones como W5 debajo (HIPÓTESIS de forma).
Las dimensiones de los refuerzos son una PROPUESTA para comparar, no salen de ningún plano.
Ejecutar con freecadcmd y HPGR_COPIA_V18D. Solo crea archivos en geometria/variantes_w5/."""
import json
import os
import FreeCAD as App
import Part

COPIA = os.environ.get("HPGR_COPIA_V18D")
G = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geometria", "variantes_w5")
os.makedirs(G, exist_ok=True)
doc = App.openDocument(COPIA)
V = App.Vector
R_EXT, R_INT10, Z_EJE_TUBO, X_FIN = 30.15, 27.38, 1740.0, 200.0
X_F0, X_F1 = 170.0, 272.0            # zona de malla fina del tubo (lado A)
ESPESOR = {"BASE": 2.77, "S40": 3.91, "S80": 5.54, "CART": 2.77, "LENG": 2.77}   # ASME B36.19M, DN50


def obj(et):
    c = [o for o in doc.Objects if o.Label == et]
    if len(c) != 1:
        raise RuntimeError("etiqueta %s: %d objetos" % (et, len(c)))
    return c[0].Shape.copy()


def solido(nom, s):
    sol = [q for q in s.Solids if q.Volume > 0.5]
    if len(sol) != 1:
        raise RuntimeError("%s: %d sólidos (%s)" % (nom, len(sol), [round(q.Volume, 2) for q in s.Solids]))
    return sol[0]


def caja(x0, x1):
    return Part.makeBox(x1 - x0, 200, 200, V(x0, -100, 1640))


def prisma_yz(pts_yz, x0, x1):
    """Polígono en el plano (y, z) extruido de x0 a x1."""
    p = [V(x0, y, z) for y, z in pts_yz] + [V(x0, pts_yz[0][0], pts_yz[0][1])]
    return Part.Face(Part.makePolygon(p)).extrude(V(x1 - x0, 0, 0))


def prisma_xz(pts_xz, y0, y1):
    p = [V(x, y0, z) for x, z in pts_xz] + [V(pts_xz[0][0], y0, pts_xz[0][1])]
    return Part.Face(Part.makePolygon(p)).extrude(V(0, y1 - y0, 0))


def prisma_xy(pts_xy, z0, z1):
    p = [V(x, y, z0) for x, y in pts_xy] + [V(pts_xy[0][0], pts_xy[0][1], z0)]
    return Part.Face(Part.makePolygon(p)).extrude(V(0, 0, z1 - z0))


eje = obj("EJE_ROTOR").common(Part.makeBox(400, 400, 2840.0 - 1800, V(-200, -200, 1800)))
cubo = obj("CUBO_DISTRIBUIDOR")
transv0 = obj("R07_V15_TRANSVERSAL_CENTRO_DN50").cut(cubo)
bridas = []
for lado, s in (("A", 1), ("B", -1)):
    br = obj("R07_V15_BRIDA_%s_CENTRO" % lado)
    x0, x1 = (279.25, 296.25) if s > 0 else (-296.25, -279.25)
    anillo = Part.makeCylinder(30.75, x1 - x0, V(x0, 0, Z_EJE_TUBO), V(1, 0, 0)).cut(
        Part.makeCylinder(30.15, x1 - x0, V(x0, 0, Z_EJE_TUBO), V(1, 0, 0)))
    bridas.append(("BRIDA_" + lado, br.fuse(anillo).removeSplitter()))
tubo_lleno = Part.makeCylinder(R_EXT, 700, V(-350, 0, Z_EJE_TUBO), V(1, 0, 0))
huella = Part.makeCylinder(200.0, 200, V(0, 0, 1690), V(0, 0, 1))
W5_YZ = lambda sg: [(sg * 2.9, 1770), (sg * 12.0, 1770), (sg * 6.0, 1764), (sg * 2.9, 1764)]   # perfil de s05


def cordones_w5(transv):
    piezas = []
    for sg, nom in ((1, "POS"), (-1, "NEG")):
        w = prisma_yz(W5_YZ(sg), -205, 205).cut(tubo_lleno).cut(transv).common(huella)
        trozos = sorted([q for q in w.common(caja(-300, X_F0)).Solids if q.Volume > 1.0], key=lambda q: q.BoundBox.XMin)
        for k, q in enumerate(trozos):
            piezas.append(("W5_%s_%d" % (nom, k + 1), q))
        piezas.append(("W5_%s_FINO" % nom, w.common(caja(X_F0, X_F1))))
    return piezas


salida = {}
for var in ("BASE", "S40", "S80", "CART", "LENG"):
    t = ESPESOR[var]
    transv = transv0.copy()
    extra = []
    if var in ("S40", "S80"):
        r_in = R_EXT - t
        anillo_int = Part.makeCylinder(R_INT10, 592.5, V(-296.25, 0, Z_EJE_TUBO), V(1, 0, 0)).cut(
            Part.makeCylinder(r_in, 592.5, V(-296.25, 0, Z_EJE_TUBO), V(1, 0, 0)))
        boca = Part.makeCylinder(R_INT10, 32, V(0, 0, Z_EJE_TUBO), V(0, 0, 1))   # el injerto sigue con su agujero
        transv = transv.fuse(anillo_int).removeSplitter().cut(boca).cut(cubo)
    if var == "CART":
        cart = prisma_xz([(200, 1760), (200, 1770), (195, 1770), (195, 1830), (200, 1830), (260, 1777), (266, 1777), (266, 1760)],
                         -4.0, 4.0).cut(cubo).cut(tubo_lleno)
        extra.append(("CARTELA", solido("CARTELA", cart)))
        for sg, nom in ((1, "POS"), (-1, "NEG")):
            w = prisma_yz([(sg * 3.9, 1776), (sg * 12.6, 1767.3), (sg * 12.6, 1760), (sg * 3.9, 1760)], 200.0, 266.0)
            w = w.cut(tubo_lleno).cut(cart).cut(cubo)
            extra.append(("WR_" + nom, solido("WR_" + nom, w)))
    if var == "LENG":
        leng = prisma_xy([(180, -55), (200, -50), (255, -14), (255, 14), (200, 50), (180, 55)], 1770.0, 1778.0).cut(cubo)
        leng = solido("LENGUETA", leng)
        transv = transv.cut(leng)                       # el tubo queda aplanado 0,15 mm bajo la lengüeta, como bajo el cubo
        extra.append(("LENGUETA", leng))
        for sg, nom in ((1, "POS"), (-1, "NEG")):
            w = prisma_yz(W5_YZ(sg), 195.0, 255.0).cut(tubo_lleno).cut(transv).cut(huella)
            extra.append(("WR_" + nom, solido("WR_" + nom, w)))
    transv = solido("TRANSV", transv)
    piezas = [("EJE", eje), ("CUBO", cubo),
              ("TRANSV_CENTRO", transv.common(caja(-300, X_F0))),
              ("TRANSV_FINO", transv.common(caja(X_F0, X_F1))),
              ("TRANSV_EXT", transv.common(caja(X_F1, 300)))] + bridas + cordones_w5(transv) + extra
    piezas = [(n, solido(n, s)) for n, s in piezas]
    par, solapes = [], []
    for i in range(len(piezas)):
        for j in range(i + 1, len(piezas)):
            d = piezas[i][1].distToShape(piezas[j][1])[0]
            if d < 2.0:
                v = piezas[i][1].common(piezas[j][1]).Volume if d < 1e-6 else 0.0
                par.append([piezas[i][0], piezas[j][0], round(d, 4), round(v, 3)])
                if v > 0.5:
                    solapes.append([piezas[i][0], piezas[j][0], round(v, 2)])
    M = App.Matrix(-1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1)
    cuerpos, sol = [], []
    for nom, s in piezas:
        q = s.copy(); q.transformShape(M); b = q.BoundBox
        cuerpos.append({"nombre": nom, "vol_mm3": round(q.Volume, 1),
                        "caja_sw_mm": [round(v, 3) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)],
                        "centro_sw_mm": [round(v, 3) for v in (q.CenterOfMass.x, q.CenterOfMass.y, q.CenterOfMass.z)]})
        sol.append(q)
    Part.makeCompound(sol).exportStep(os.path.join(G, "UNION_%s.step" % var))
    with open(os.path.join(G, "cuerpos_%s.csv" % var), "w", encoding="utf-8") as f:
        f.write("nombre;vol_mm3;cx;cy;cz\n")
        for c in cuerpos:
            f.write("%s;%s;%s;%s;%s\n" % (c["nombre"], c["vol_mm3"], *c["centro_sw_mm"]))
    masa_ref = sum(c["vol_mm3"] for c in cuerpos if c["nombre"] in ("CARTELA", "LENGUETA") or c["nombre"].startswith("WR_")) * 7.95e-6
    masa_tubo = sum(c["vol_mm3"] for c in cuerpos if c["nombre"].startswith("TRANSV")) * 7.95e-6
    salida[var] = {"t_mm": t, "r_int_mm": round(R_EXT - t, 2), "cuerpos": cuerpos, "contactos_cad": par, "solapes_mm3": solapes,
                   "masa_tubo_central_kg": round(masa_tubo, 3), "masa_refuerzo_kg": round(masa_ref, 3)}
json.dump({"marco": "(X, Y, Z)_SW = (-x, z, y)_CAD; mm", "zona_fina_x_cad": [X_F0, X_F1], "variantes": salida},
          open(os.path.join(G, "geometria_variantes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(G, "resumen_s07.txt"), "w", encoding="utf-8") as f:
    for var, s in salida.items():
        f.write("%s: %d cuerpos; tubo central %.3f kg; refuerzo %.3f kg; solapes %s\n"
                % (var, len(s["cuerpos"]), s["masa_tubo_central_kg"], s["masa_refuerzo_kg"], s["solapes_mm3"]))
os._exit(0)
