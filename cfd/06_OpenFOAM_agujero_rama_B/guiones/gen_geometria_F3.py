# =============================================================================
#  F3 - Dominio de aire del agujero del rodamiento (R05)
#
#  Produce, en METROS, para snappyHexMesh:
#     anillo_rodamiento.stl  el aro interior del rodamiento: su superficie interna
#                            es la pared conica que hay que mojar
#     lanza.stl              lanza, coplas y cuerpos de boquilla, como obstaculos
#  y un informe de control de calidad.
#
#  Cotas (mm, sistema global R05):
#     agujero conico 1:30, Ø900 en z=890 -> Ø917,167 en z=1405   (B = 515)
#     eje del rodamiento = eje z = vertical (Calculos_aspersion.md, seccion 1.2)
#  El sentido de la conicidad es un SUPUESTO declarado: se toma el diametro menor
#  abajo, que es lo coherente con el reparto de boquillas del equipo
#  (b_i = 2 * 143,3 * tan 25 = 133,64 mm  y  primera boquilla en 890 + b_i/2 = 956,82).
# =============================================================================
import csv
import math

import FreeCAD
import Part
import Mesh
import MeshPart
from FreeCAD import Vector

# ----------------------------------------------------------------- parametros
Z_INF, Z_SUP = 890.0, 1405.0          # caras del rodamiento
R_INF = 450.0                          # radio del agujero en Z_INF  (Ø900)
CONICIDAD = 1.0 / 30.0                 # diametral
R_SUP = R_INF + (Z_SUP - Z_INF) * CONICIDAD / 2.0
R_ANILLO_EXT = 760.0                   # radio exterior ficticio del aro.
# Tiene que superar la SEMIDIAGONAL de la caja (500*sqrt(2) = 707,1 mm), o las
# esquinas de la caja entre z=890 y 1405 quedarian como aire y el dominio
# tendria un 5,3 % de volumen que no existe.

# caja del dominio (fondo de malla de blockMesh)
CAJA_XY = 500.0
CAJA_Z0, CAJA_Z1 = 790.0, 1445.0
# 790: 18 mm por debajo del codo de pie (808,18). 1445: 4 mm antes del codo del
# cuello (1448,79), que asi queda fuera y no hay que cortarlo.

PIEZAS_LANZA = [
    "SIM_CODO_LANZA_PIE_90", "SIM_CODO_LANZA_PIE_25", "SIM_TUBO_LANZA_PIE_DN25",
    "SIM_TAPA_LANZA_PIE", "SIM_COPLA_22_INF_INT", "SIM_BOQUILLA_22_INF_INT",
    "SIM_TUBO_LANZA_VERTICAL_DN25",
    "SIM_COPLA_17_INT_1", "SIM_BOQUILLA_17_INT_1",
    "SIM_COPLA_18_INT_2", "SIM_BOQUILLA_18_INT_2",
    "SIM_COPLA_19_INT_3", "SIM_BOQUILLA_19_INT_3",
    "SIM_COPLA_20_INT_4", "SIM_BOQUILLA_20_INT_4",
    "SIM_COPLA_21_INT_5", "SIM_BOQUILLA_21_INT_5",
]

MM_A_M = FreeCAD.Matrix()
MM_A_M.scale(1e-3, 1e-3, 1e-3)

qa = []


def anota(clave, valor, unidad="", nota=""):
    qa.append([clave, valor, unidad, nota])
    print("  %-42s %-22s %-8s %s" % (clave, valor, unidad, nota))


def exportar(shape, nombre, deflexion_mm=0.4, angular=0.02):
    """malla la forma en mm y escala LA MALLA a metros, luego escribe el STL.

    No se escala el solido con transformGeometry: falla sobre los toros de los
    codos (Convert_TorusToBSplineSurface). Escalar la malla son solo puntos.
    AngularDeflection 0,02 rad da ~314 segmentos por vuelta: en el agujero de
    R450 eso deja una flecha de cuerda de 0,02 mm. Con el valor por omision
    (0,5 rad) el cono habria salido como un prisma de 13 lados.
    """
    m = MeshPart.meshFromShape(Shape=shape,
                               LinearDeflection=deflexion_mm,
                               AngularDeflection=angular,
                               Relative=False)
    m.transform(MM_A_M)
    m.write(nombre)
    return m, shape


print("=" * 78)
print(" F3 - construccion del dominio de aire del agujero")
print("=" * 78)

doc = FreeCAD.openDocument("R05_copia.FCStd")

# ------------------------------------------------------------------ 1. el aro
print("\n1. Aro del rodamiento (su cara interior es la pared a mojar)")
altura = Z_SUP - Z_INF
cono = Part.makeCone(R_INF, R_SUP, altura, Vector(0, 0, Z_INF), Vector(0, 0, 1))
cil = Part.makeCylinder(R_ANILLO_EXT, altura, Vector(0, 0, Z_INF), Vector(0, 0, 1))
anillo = cil.cut(cono)

anota("radio del agujero en z=890", "%.4f" % R_INF, "mm", "Ø900 nominal SKF 241/900")
anota("radio del agujero en z=1405", "%.4f" % R_SUP, "mm", "Ø%.3f" % (2 * R_SUP))
anota("conicidad diametral", "1:30", "", "incremento de diametro %.4f mm" % (2 * (R_SUP - R_INF)))
anota("aro: solido valido", str(anillo.isValid()), "", "")
anota("aro: cerrado", str(anillo.isClosed()), "", "")
anota("aro: numero de solidos", str(len(anillo.Solids)), "", "")

# volumen del hueco conico, analitico y por CAD
v_cono_cad = cono.Volume
v_cono_ana = math.pi * altura / 3.0 * (R_INF ** 2 + R_INF * R_SUP + R_SUP ** 2)
anota("volumen del agujero (CAD)", "%.6f" % (v_cono_cad * 1e-9), "m3", "")
anota("volumen del agujero (analitico)", "%.6f" % (v_cono_ana * 1e-9), "m3",
      "diferencia %.3e" % abs(v_cono_cad - v_cono_ana))

# area lateral del agujero: se contrasta con el calculo del equipo (1,47001 m2)
gen = math.hypot(altura, R_SUP - R_INF)
area_lat = math.pi * (R_INF + R_SUP) * gen
anota("area de la pared del agujero", "%.6f" % (area_lat * 1e-6), "m2",
      "equipo (pi*dm*B): 1,47001 m2")

# ---------------------------------------------------------------- 2. la lanza
print("\n2. Lanza, coplas y cuerpos de boquilla")
formas = []
faltan = []
for n in PIEZAS_LANZA:
    o = doc.getObject(n)
    if o is None or not hasattr(o, "Shape") or o.Shape.isNull():
        faltan.append(n)
        continue
    formas.append(o.Shape)
if faltan:
    anota("PIEZAS QUE FALTAN", ", ".join(faltan), "", "!!")
lanza = formas[0]
for s in formas[1:]:
    lanza = lanza.fuse(s)
lanza = lanza.removeSplitter()
anota("lanza: piezas fusionadas", str(len(formas)), "", "")
anota("lanza: solido valido", str(lanza.isValid()), "", "")
anota("lanza: cerrado", str(lanza.isClosed()), "", "")
anota("lanza: numero de solidos", str(len(lanza.Solids)), "", "1 = todo conectado")
anota("lanza: volumen", "%.9f" % (lanza.Volume * 1e-9), "m3", "")
bb = lanza.BoundBox
anota("lanza: caja envolvente z", "%.2f .. %.2f" % (bb.ZMin, bb.ZMax), "mm",
      "la caja del dominio va de %.0f a %.0f" % (CAJA_Z0, CAJA_Z1))

# se recorta la lanza 5 mm por encima de la caja, para que el STL quede acotado
# y snappyHexMesh la corte limpiamente en el contorno superior
caja_corte = Part.makeBox(2 * CAJA_XY + 200, 2 * CAJA_XY + 200, (CAJA_Z1 + 5) - (CAJA_Z0 - 5),
                          Vector(-CAJA_XY - 100, -CAJA_XY - 100, CAJA_Z0 - 5))
lanza_cortada = lanza.common(caja_corte)
anota("lanza recortada: volumen", "%.9f" % (lanza_cortada.Volume * 1e-9), "m3",
      "se corto %.1f %% (el tubo sale por arriba)" %
      (100 * (1 - lanza_cortada.Volume / lanza.Volume)))

# ------------------------------------------------- 3. volumen de aire del caso
print("\n3. Volumen de aire del dominio")
caja = Part.makeBox(2 * CAJA_XY, 2 * CAJA_XY, CAJA_Z1 - CAJA_Z0,
                    Vector(-CAJA_XY, -CAJA_XY, CAJA_Z0))
aire = caja.cut(anillo).cut(lanza)
anota("caja del dominio", "%.0f x %.0f x %.0f" % (2 * CAJA_XY, 2 * CAJA_XY, CAJA_Z1 - CAJA_Z0),
      "mm", "volumen %.6f m3" % (caja.Volume * 1e-9))
anota("aire: volumen total", "%.6f" % (aire.Volume * 1e-9), "m3", "")
anota("aire: solido valido", str(aire.isValid()), "", "")
anota("aire: numero de solidos", str(len(aire.Solids)), "", "1 = region conectada")

# contraste analitico del volumen de aire
v_ext_inf = (2 * CAJA_XY) ** 2 * (Z_INF - CAJA_Z0)
v_ext_sup = (2 * CAJA_XY) ** 2 * (CAJA_Z1 - Z_SUP)
v_ana = v_cono_ana + v_ext_inf + v_ext_sup - lanza_cortada.Volume
anota("aire: volumen analitico", "%.6f" % (v_ana * 1e-9), "m3",
      "cono + 2 extensiones - lanza")
anota("aire: diferencia CAD vs analitico", "%.3e" % abs(aire.Volume - v_ana), "mm3",
      "relativa %.3e" % (abs(aire.Volume - v_ana) / v_ana))

# ------------------------------------------------------------- 4. exportar STL
print("\n4. Exportacion a STL en metros")
# El aro se exporta SEPARADO EN REGIONES: asi snappyHexMesh crea un patch por
# superficie y la deposicion se puede medir solo en la pared conica, que es la
# unica superficie objetivo que el usuario confirmo.
caras = {"pared_agujero": [], "cara_inf_rodamiento": [], "cara_sup_rodamiento": [],
         "cilindro_exterior_ficticio": []}
# Se clasifica por TIPO DE SUPERFICIE. No sirve el centroide: el de una cara
# cilindrica o conica completa cae sobre el eje, y el cilindro exterior acababa
# contado como pared del agujero (3,93 m2 en vez de 1,47 m2).
for f in anillo.Faces:
    tipo = type(f.Surface).__name__
    c = f.CenterOfMass
    if tipo == "Plane":
        if abs(c.z - Z_INF) < 1e-6:
            caras["cara_inf_rodamiento"].append(f)
        elif abs(c.z - Z_SUP) < 1e-6:
            caras["cara_sup_rodamiento"].append(f)
        else:
            anota("cara plana inesperada", "z=%.3f" % c.z, "mm", "!!")
    elif tipo == "Cylinder":
        caras["cilindro_exterior_ficticio"].append(f)
    elif tipo == "Cone":
        caras["pared_agujero"].append(f)
    else:
        anota("cara de tipo inesperado", tipo, "", "!!")
for nom, fs in caras.items():
    if not fs:
        anota("region %s" % nom, "SIN CARAS", "", "!!")
        continue
    comp = Part.Compound(fs)
    area = sum(f.Area for f in fs)
    if nom == "cilindro_exterior_ficticio":
        anota("region %s" % nom, "no se exporta", "",
              "queda fuera de la caja del dominio (R=%.0f mm)" % R_ANILLO_EXT)
        continue
    mm = MeshPart.meshFromShape(Shape=comp, LinearDeflection=0.4,
                                AngularDeflection=0.02, Relative=False)
    mm.transform(MM_A_M)
    mm.write(nom + ".stl")
    anota("%s.stl: triangulos" % nom, str(mm.CountFacets), "", "")
    anota("%s.stl: area" % nom, "%.6f" % (area * 1e-6), "m2",
          "malla %.6f m2, error %.4f %%" % (mm.Area, 100 * abs(mm.Area - area * 1e-6) / (area * 1e-6)))

m_anillo, sh_anillo = exportar(anillo, "anillo_rodamiento.stl", 0.4, 0.02)
m_lanza, sh_lanza = exportar(lanza_cortada, "lanza.stl", 0.4, 0.15)
for nombre, m, sh in (("anillo_rodamiento.stl", m_anillo, sh_anillo),
                      ("lanza.stl", m_lanza, sh_lanza)):
    anota("%s: triangulos" % nombre, str(m.CountFacets), "", "")
    anota("%s: cerrado" % nombre, str(m.isSolid()), "", "")
    b = m.BoundBox
    anota("%s: caja (m)" % nombre,
          "x %.4f..%.4f  y %.4f..%.4f  z %.4f..%.4f" % (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax),
          "m", "")
    anota("%s: error de volumen malla vs CAD" % nombre,
          "%.4f" % (100 * abs(m.Volume - sh.Volume * 1e-9) / (sh.Volume * 1e-9)), "%",
          "por la teselacion de las superficies curvas")

# ------------------------------------------- 5. boquillas en el sistema global
print("\n5. Boquillas del ramal interior, en el sistema global")
boquillas = [
    ("INT_1", "BOQUILLA_17", 306.70, 956.822, (0.0, 1.0, 0.0)),
    ("INT_2", "BOQUILLA_18", 306.70, 1052.162, (0.0, 1.0, 0.0)),
    ("INT_3", "BOQUILLA_19", 306.70, 1147.502, (0.0, 1.0, 0.0)),
    ("INT_4", "BOQUILLA_20", 306.70, 1242.842, (0.0, 1.0, 0.0)),
    ("INT_5", "BOQUILLA_21", 306.70, 1338.182, (0.0, 1.0, 0.0)),
    ("INF_INT", "BOQUILLA_22", 400.00, 850.000, (0.0, 0.9063077870366499, 0.42261826174069944)),
]
filas = []
for tag, pieza, y_punta, z_punta, eje in boquillas:
    a = Vector(*eje)
    punta = Vector(0.0, y_punta, z_punta)
    orif = punta - a * 4.5                       # el vertice del abanico, 4,5 mm detras
    # donde corta el eje a la pared conica  (r(z) = R_INF + (z-Z_INF)/60)
    t, corte = None, None
    for i in range(1, 400001):
        tt = i * 0.005
        p = punta + a * tt
        r = math.hypot(p.x, p.y)
        rw = R_INF + (p.z - Z_INF) * CONICIDAD / 2.0
        if r >= rw:
            t, corte = tt, p
            break
    if corte is None:
        filas.append([tag, pieza, 0.0, y_punta, z_punta, orif.y, orif.z,
                      eje[0], eje[1], eje[2], "", "", "", "NO CORTA LA PARED"])
        print("  %-8s el eje NO corta la pared conica dentro de 2 m" % tag)
        continue
    dentro = "si" if Z_INF <= corte.z <= Z_SUP else "NO (fuera del agujero)"
    filas.append([tag, pieza, 0.0, y_punta, z_punta, "%.3f" % orif.y, "%.3f" % orif.z,
                  eje[0], eje[1], eje[2], "%.3f" % t, "%.3f" % corte.z,
                  "%.3f" % math.hypot(corte.x, corte.y), dentro])
    print("  %-8s punta (0; %7.2f; %8.3f)  ->  impacto del eje en z=%8.3f, r=%7.3f, a %6.2f mm   %s"
          % (tag, y_punta, z_punta, corte.z, math.hypot(corte.x, corte.y), t, dentro))

with open("boquillas_globales.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tag", "pieza", "punta_x_mm", "punta_y_mm", "punta_z_mm",
                "orificio_y_mm", "orificio_z_mm", "eje_x", "eje_y", "eje_z",
                "distancia_a_pared_mm", "z_impacto_mm", "r_impacto_mm", "impacta_en_el_agujero"])
    w.writerows(filas)

with open("QA_geometria.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["magnitud", "valor", "unidad", "nota"])
    w.writerows(qa)
print("\nescritos: anillo_rodamiento.stl, lanza.stl, boquillas_globales.csv, QA_geometria.csv")

# ============================================ 6. cobertura geometrica del abanico
# Se recorre el abanico de 50 grados rayo a rayo y se busca donde corta la pared
# conica. Da, sin CFD, que tramo de la cota Z alcanza cada boquilla y que parte
# de su abanico se pierde fuera del agujero.
print("\n6. Cobertura geometrica de cada abanico (50 grados, plano radial-vertical)")
SEMI = math.radians(25.0)
N_RAYOS = 2001
cob = []
for tag, pieza, y_punta, z_punta, eje in boquillas:
    a = Vector(*eje)
    # base del abanico: el plano es el radial-vertical, normal (1,0,0)
    n = Vector(1.0, 0.0, 0.0)
    e_fuera = (n - a * n.dot(a)); e_fuera.normalize()
    e_ancho = e_fuera.cross(a); e_ancho.normalize()     # dentro del abanico
    punta = Vector(0.0, y_punta, z_punta)
    zs, alcanza = [], 0
    for i in range(N_RAYOS):
        al = -SEMI + 2 * SEMI * i / (N_RAYOS - 1.0)
        d = a + e_ancho * math.tan(al)
        d.normalize()
        # interseccion con el cono r = R_INF + (z-Z_INF)/60, por avance fino
        t, pc = None, None
        paso = 0.25
        for k in range(1, 12001):
            tt = k * paso
            p = punta + d * tt
            if math.hypot(p.x, p.y) >= R_INF + (p.z - Z_INF) * CONICIDAD / 2.0:
                t, pc = tt, p
                break
        if pc is None:
            continue
        if Z_INF <= pc.z <= Z_SUP:
            alcanza += 1
            zs.append(pc.z)
    frac = 100.0 * alcanza / N_RAYOS
    if zs:
        cob.append([tag, "%.3f" % min(zs), "%.3f" % max(zs), "%.3f" % (max(zs) - min(zs)),
                    "%.2f" % frac])
        print("  %-8s cubre Z de %8.3f a %8.3f mm  (largo %7.3f mm)  |  %6.2f %% del abanico entra en el agujero"
              % (tag, min(zs), max(zs), max(zs) - min(zs), frac))
    else:
        cob.append([tag, "", "", "", "0.00"])
        print("  %-8s NO alcanza el agujero" % tag)

with open("cobertura_geometrica.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tag", "z_min_mm", "z_max_mm", "largo_huella_mm", "porcentaje_del_abanico_en_el_agujero"])
    w.writerows(cob)

# solape entre boquillas contiguas del ramal interior
print("\n  solape entre boquillas contiguas del ramal interior:")
ints = [c for c in cob if c[0].startswith("INT")]
for i in range(len(ints) - 1):
    z1max = float(ints[i][2]); z2min = float(ints[i + 1][1])
    sol = z1max - z2min
    largo = float(ints[i][3])
    print("    %s / %s : solape %7.3f mm = %5.2f %% de la huella"
          % (ints[i][0], ints[i + 1][0], sol, 100 * sol / largo))

# que fraccion de la cota Z del agujero queda cubierta por el conjunto
cubiertos = []
for c in cob:
    if c[1]:
        cubiertos.append((float(c[1]), float(c[2])))
cubiertos.sort()
union, fin = 0.0, None
ini = None
for z0, z1 in cubiertos:
    if ini is None:
        ini, fin = z0, z1
    elif z0 <= fin:
        fin = max(fin, z1)
    else:
        union += fin - ini
        ini, fin = z0, z1
if ini is not None:
    union += fin - ini
print("\n  cota Z del agujero cubierta por el conjunto: %.3f de %.0f mm = %.2f %%"
      % (union, Z_SUP - Z_INF, 100 * union / (Z_SUP - Z_INF)))
print("  (cobertura GEOMETRICA de los ejes del abanico; no es el resultado del CFD)")
