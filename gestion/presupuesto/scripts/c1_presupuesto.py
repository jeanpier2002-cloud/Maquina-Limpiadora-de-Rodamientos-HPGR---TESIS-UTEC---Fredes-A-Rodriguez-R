# -*- coding: utf-8 -*-
"""C1 (obs. 3.8 del asesor): presupuesto completo de la maquina R07 V16B, 02/11/2026.

La P2 costeo solo los componentes comerciales (S/ 33 855) y dejo fuera la fabricacion, la cabina, el tanque, el filtro y el
tablero, que es lo que pide el asesor. Este calculo los agrega.
Metodo: estimacion de costo de clase 4 (orden de magnitud con ingenieria basica; exactitud tipica -30 % / +50 %).
  - piezas fabricadas: masa del CAD (METRADO_CAD_V16B.json) x precio del material + horas de taller (h/kg segun complejidad
    [HIPOTESIS]) x tarifa de taller (sueldo de soldador homologado en Lima x cargas sociales x gastos y utilidad [HIPOTESIS]);
  - componentes comerciales: precio publicado de fabricante o distribuidor (fuente y fecha); lo importado lleva un factor de
    importacion [HIPOTESIS];
  - lo que no tiene precio publicado: [HIPOTESIS] con rango.
Cada partida tiene un rango: con fuente 0,85-1,20; HIPOTESIS 0,70-1,50. Montos sin IGV (se informa aparte).
Salida: presupuesto/resultados/PRESUPUESTO_R07_V16B.json y 05_ENTREGABLES_TESIS/insumos_P3/tabla_presupuesto_completo.tex
"""
import json
import math
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
HO = AQUI.parents[2]
METRADO = AQUI / "resultados" / "METRADO_CAD_V16B.json"
SALIDA = AQUI / "resultados" / "PRESUPUESTO_R07_V16B.json"
TEX = HO / "05_ENTREGABLES_TESIS" / "insumos_P3" / "tabla_presupuesto_completo.tex"

# ---------------- base de precios (valor, moneda, fuente, estado) ----------------
TC = {"PEN": 1.0, "USD": 3.448, "EUR": 3.91}
FUENTE_TC = {"USD": "SUNAT venta 13/10/2026 (tucambista.pe/noticias/dolares-a-soles-13-octubre-2026)",
             "EUR": "P2, base de precios (global66.com, 9/10/2026)"}
IMPORT = 1.20  # flete, seguro, agente y ad valorem de lo comprado fuera [HIPOTESIS]

P = {
    # materiales
    "acero_A36_kg": (3.16, "USD", "P2, base de precios: rango internacional 2026 1,81-3,16 US$/kg, se adopta el maximo (es.accio.com)", "FUENTE"),
    "inox_kg": (5.62, "USD", "P2, base de precios: 316L 4,52-5,62 US$/kg (mwalloys.com, mayo 2026), maximo; se aplica tambien al 304", "FUENTE"),
    "uhmw_plancha": (198.25, "EUR", "P2, base de precios: plancha 2013 x 1003 x 8 mm (klefinghaus.de)", "FUENTE"),
    # mano de obra de taller
    "sueldo_soldador_mes": (3500.0, "PEN", "Aviso de soldador homologado en SJL, Lima, 2026 (cazvid.com)", "FUENTE"),
    # comerciales
    "bomba_CRN15_3": (2647.06 * 1.4, "EUR", "CR 10-06 con motor EUR 2647,06 (P2, sparepartsnow.de) x 1,4 por 316 y tamaño 15 [HIPOTESIS]; sin precio publicado de la CRN 15-3 (lenntech: a pedido)", "HIPOTESIS"),
    "motorreductor_SF47": (1500.0, "USD", "S37 con freno US$ 1226,14 (P2, mrosupply.com); el SF47 es un tamaño mayor [HIPOTESIS]", "HIPOTESIS"),
    "roba_slip_T1": (350.0, "USD", "Sin precio publicado [HIPOTESIS]", "HIPOTESIS"),
    "transmision_HTD": (250.0, "USD", "2 poleas HTD 8M con bujes y correa [HIPOTESIS]", "HIPOTESIS"),
    "union_rotativa": (476.0, "USD", "Deublin 555-000-001 (P2, allworldmachinery.com)", "FUENTE"),
    "boquilla_veejet": (16.26, "USD", "VeeJet 50 grados inox, 1/4 in (P2, northstarhotsy.com); la de 3/8 se cotiza a pedido", "FUENTE"),
    "rueda_SPKVS200K": (450.0, "USD", "Sin precio publicado de la SPKVS 200K; la P2 uso la LE-ALST 200K-14 (US$ 220), otro producto [HIPOTESIS]", "HIPOTESIS"),
    "riel_kg": (3.16, "USD", "P2: precio del acero A36 por kg; riel A45 de 22,1 kg/m (ArcelorMittal)", "FUENTE"),
    "clip_gantrex_par": (40.0, "USD", "Gantrex BG10/BJ, par [HIPOTESIS]", "HIPOTESIS"),
    "anclaje_M16_A4": (6.0, "USD", "Varilla roscada M16 A4-70 de 220 mm con tuerca y arandela [HIPOTESIS]", "HIPOTESIS"),
    "adhesivo_500ml": (35.0, "EUR", "Hilti HIT-RE 500 V4 500 ml: EUR 23,50 en reventa (ebay.de); se adopta 35 por compra en distribuidor [HIPOTESIS]", "HIPOTESIS"),
    "grout_bolsa": (100.0, "PEN", "Grout sin retraccion, bolsa de 25 kg [HIPOTESIS]", "HIPOTESIS"),
    "traslado_D071": (1664.0, "USD", "CALCULO_V14_TRASLADO_CADENA.md §5: cadena Tyma 30,66 EUR/m y partidas [HIP]", "MIXTO"),
    "rodamiento_110": (150.0, "USD", "Rodamiento de 110 mm del cartucho [HIPOTESIS; seleccion pendiente, P1-32]", "HIPOTESIS"),
    "filtro_ES2": (2208.45, "USD", "Carcasa de filtro de bolsa inox 2 in NPT, 90 gpm, 150 psi (Grainger, punchout.acklandsgrainger.com)", "FUENTE"),
    "colador_Y_2in": (150.0, "USD", "Colador en Y 2 in CF8M malla 40 [HIPOTESIS]", "HIPOTESIS"),
    "valvula_3vias_2in": (800.0, "USD", "Bola de 3 vias 2 in con actuador de 24 V [HIPOTESIS]", "HIPOTESIS"),
    "valvulas_menores": (600.0, "USD", "Retencion 2 in, bola 2 in, aislamiento y venteo de la lanza, purgas [HIPOTESIS]", "HIPOTESIS"),
    "resistencia_12kW": (1200.0, "PEN", "Resistencia de inmersion de 12 kW fabricada en Lima [HIPOTESIS]", "HIPOTESIS"),
    "FTL31": (189.88, "EUR", "Liquiphant FTL31 (RS Components, de.rs-online.com)", "FUENTE"),
    "TM131": (350.0, "EUR", "Sonda de temperatura TM131 [HIPOTESIS]", "HIPOTESIS"),
    "PMP21": (450.0, "EUR", "Transmisor de presion PMP21 [HIPOTESIS]", "HIPOTESIS"),
    "LT_nivel": (600.0, "USD", "Transmisor de nivel del tanque 1 [HIPOTESIS]", "HIPOTESIS"),
    "manometro": (80.0, "USD", "WIKA 233.50 [HIPOTESIS]", "HIPOTESIS"),
    "DDA": (1079.17, "EUR", "Grundfos DDA 7.5-16 (hellopro.fr, listado descontinuado: referencia)", "FUENTE"),
    "rittal_AE": (900.0, "USD", "Rittal AE 1260.500 IP66 [HIPOTESIS: sin precio publicado de lista]", "HIPOTESIS"),
    "cpu_1214C": (745.0, "USD", "Siemens 6ES7214-1AG40-0XB0 (Steiner Electric, distribuidor)", "FUENTE"),
    "ktp700": (886.10 / 1.19, "EUR", "Siemens KTP700 Basic 6AV2123-2GB03-0AX0: EUR 886 con IVA (buerklin.com)", "FUENTE"),
    "atv320": (922.48, "USD", "Schneider ATV320U55N4C (standardelectricsupply.com)", "FUENTE"),
    "cfw300": (200.0, "USD", "WEG CFW300 0,37 kW 400 V [HIPOTESIS a partir de GBP 134 en inverterdrive.com]", "HIPOTESIS"),
    "aparamenta": (1500.0, "USD", "Seccionador, interruptores, guardamotores, contactores, rele de seguridad, fuente 24 V, borneras [HIPOTESIS]", "HIPOTESIS"),
    "emergencia": (60.0, "USD", "Pulsador de emergencia Schneider XALK [HIPOTESIS]", "HIPOTESIS"),
    "cableado": (800.0, "USD", "Cables de fuerza y control, prensaestopas [HIPOTESIS]", "HIPOTESIS"),
    "bandeja_m": (25.0, "USD", "Bandeja portacables de 200 mm, por metro [HIPOTESIS]", "HIPOTESIS"),
    "motor_puerta": (1226.14, "USD", "Motorreductor con freno para la puerta: S37 (P2, mrosupply.com)", "FUENTE"),
    "extractor_niebla": (1500.0, "USD", "Ventilador en linea de 600-900 m3/h y eliminador de niebla [HIPOTESIS]", "HIPOTESIS"),
    "luminaria_IP65": (80.0, "USD", "Luminaria IP65 de 1200 mm [HIPOTESIS]", "HIPOTESIS"),
    "menores_cabina": (300.0, "USD", "Sello EPDM, cepillos, mirilla de policarbonato, persiana [HIPOTESIS]", "HIPOTESIS"),
    "lana_mineral_m3": (150.0, "USD", "Lana mineral con forro, por m3 [HIPOTESIS]", "HIPOTESIS"),
    "bomba_hidrostal": (1000.0, "USD", "Hidrostal A02Q-S (fabricada en Peru) [HIPOTESIS]", "HIPOTESIS"),
    "drenaje_menores": (650.0, "USD", "Desviadora motorizada, flotador, IBC de 1000 L, tuberia DN100 [HIPOTESIS]", "HIPOTESIS"),
    "detergente_balde": (525.29, "USD", "Zep 36342, balde de 56,7 kg (P2)", "FUENTE"),
    "inhibidor_bidon": (300.0, "USD", "Inhibidor multimetal, bidon de 60 L [HIPOTESIS]", "HIPOTESIS"),
    "obra_civil": (8500.0, "PEN", "Pozo de bombeo (S/ 2 500), piso humedo con pendiente, colector y bordillos (S/ 6 000) [HIPOTESIS]", "HIPOTESIS"),
}

# horas de taller por kg segun complejidad [HIPOTESIS] y tarifa de taller
HKG = {"estructura": 0.15, "mecanizado": 0.40, "precision": 0.60, "inox_chapa": 0.25, "inox_tuberia": 0.35}
CARGAS, GASTOS = 1.50, 2.00  # cargas sociales (CTS, gratificaciones, EsSalud, vacaciones) y gastos generales + utilidad [HIPOTESIS]


def pen(clave, cant=1.0):
    v, mon, _, _ = P[clave]
    return v * TC[mon] * cant


def main():
    M = json.loads(METRADO.read_text(encoding="utf-8"))["piezas"]

    def vol(f):
        return sum(p["volumen_cm3"] for p in M if f(p))

    def kg(f, rho=7.85):
        return vol(f) * rho / 1000.0

    tarifa = P["sueldo_soldador_mes"][0] / (26 * 8) * CARGAS * GASTOS   # S/ por hora
    lineas = []

    def fab(partida, desc, masa, material, cplx, nota):
        mat = masa * pen("acero_A36_kg" if material == "A36" else "inox_kg")
        mo = masa * HKG[cplx] * tarifa
        lineas.append({"partida": partida, "descripcion": desc, "cantidad": round(masa, 1), "unidad": "kg",
                       "material_PEN": round(mat), "mano_obra_PEN": round(mo), "total_PEN": round(mat + mo),
                       "fuente": nota + "; mano de obra %.2f h/kg x S/ %.1f/h [HIPOTESIS]" % (HKG[cplx], tarifa),
                       "estado": "MIXTO", "importado": False})

    def com(partida, desc, clave, cant, unidad="u", importado=True, nota=""):
        v, mon, fuente, estado = P[clave]
        tot = pen(clave, cant) * (IMPORT if importado else 1.0)
        lineas.append({"partida": partida, "descripcion": desc, "cantidad": cant, "unidad": unidad,
                       "precio_unitario": "%s %.2f" % (mon, v), "total_PEN": round(tot),
                       "fuente": fuente + (" x %.2f de importacion [HIPOTESIS]" % IMPORT if importado else "") + (("; " + nota) if nota else ""),
                       "estado": estado, "importado": importado})

    g, n = (lambda grupo: (lambda p: p["grupo"] == grupo)), (lambda pref: (lambda p: p["pieza"].startswith(pref)))

    # ---------------- A. Mesa, centrado y traslado ----------------
    A = "A. Mesa, centrado y traslado"
    fab(A, "Bastidor N3 W6X9 con uniones soldadas (HPGR-MES-100)", kg(g("R07_V16_BASTIDOR_UNIONES")), "A36", "estructura", "CAD V16B, grupo R07_V16_BASTIDOR_UNIONES")
    m_mesa = kg(lambda p: p["grupo"] == "G00_CONTEXTO_MESA_R05" and not p["pieza"].startswith(("CTX_WHEEL", "CTX_PAD_0", "CTX_WEB_STIFF")))
    m_mesa += kg(lambda p: p["pieza"].startswith("CTX_PAD_") and not p["pieza"].endswith("LINER"))
    m_mesa += kg(g("R07_V12_CORRECCIONES")) + kg(n("R06_PATA_RECEPTOR"))
    fab(A, "Apoyos, horquillas y ejes de rueda, topes, manillar y bloqueo LOAD", m_mesa, "A36", "mecanizado",
        "CAD V16B: PAD (base y tapa), FORK, AXLE, topes, manillar, bloqueo y patas de receptores")
    fab(A, "Centradores K2-M (3), con ajustes H7/g6", kg(g("G_R061_K2M")) + kg(g("R07_V13_AMARRE_U2_Y_RUEDAS")), "A36", "precision",
        "CAD V16B, grupos G_R061_K2M y R07_V13 (rodillos polimericos tratados como acero: cota alta)")
    com(A, "Plancha UHMW-PE de 8 mm para los PAD", "uhmw_plancha", 1)
    com(A, "Ruedas Blickle SPKVS 200K", "rueda_SPKVS200K", 4)
    m_riel = 2 * 6.54 * 22.1
    com(A, "Rieles A45 (2 x 6,54 m)", "riel_kg", round(m_riel, 1), "kg", importado=False)
    com(A, "Clips Gantrex BG10/BJ", "clip_gantrex_par", 24, "par")
    m_ped = 24 * (0.300 * 0.280 * 0.020 + 0.250 * 0.280 * 0.020) * 7930 + 24 * 0.165 * 17.8
    fab(A, "Pedestales del riel en inox 304 (24; HPGR D-073)", m_ped, "inox", "inox_chapa",
        "D-073: placa base 300x280x20, placa superior 250x280x20 y SHS 120x5 de 165 mm")
    com(A, "Anclajes M16 A4-70 (96)", "anclaje_M16_A4", 96)
    com(A, "Adhesivo HIT-RE 500 V4, cartuchos de 500 ml (96 anclajes, ~12 ml c/u)", "adhesivo_500ml", 3)
    com(A, "Grout sin retraccion (24 x 0,3 x 0,28 x 0,03 m)", "grout_bolsa", 3, "bolsa", importado=False)
    com(A, "Traslado por doble cadena con volante (HPGR D-071)", "traslado_D071", 1)

    # ---------------- B. Aspersion y accionamiento del rotor ----------------
    B = "B. Aspersion y accionamiento"
    comerciales_rotor = ("POLEA_CONDUCIDA", "UNION_ROTATIVA", "BOQUILLA", "VALVULA_", "PURGA_", "MANETA", "CADENA_PORTA",
                         "MANGUERA", "RACOR", "R07_V15_PERNOS", "R07_V15_ARANDELAS", "R07_V15_TUERCAS", "R07_V15_EMPAQUET", "R063")
    rotor = lambda p: (p["grupo"].startswith(("A0_", "A1_", "A2_", "A3_", "A4_", "A6_", "A7_", "A8_")) or p["grupo"] in ("R07_V15_U_BRIDAS", "B_MEC_316L_CANDIDATO")) \
        and not p["pieza"].startswith(comerciales_rotor)
    fab(B, "Rotor: eje, cubo, U con bridas, lanza, red, mastil y carro (316L)", kg(rotor, 7.95), "inox", "inox_tuberia",
        "CAD V16B, grupos A0-A8, R07_V15_U_BRIDAS y B-MEC sin los comerciales")
    com(B, "Boquillas VeeJet 3/8 (24)", "boquilla_veejet", 24)
    com(B, "Union rotativa 1-1/2 in", "union_rotativa", 1)
    com(B, "Motorreductor SEW SF47R17DRN63MS4 con brida", "motorreductor_SF47", 1)
    com(B, "Limitador Mayr ROBA-slip hub T1", "roba_slip_T1", 1)
    com(B, "Transmision HTD 8M 2:1", "transmision_HTD", 1)
    com(B, "Rodamientos del cartucho (110 mm)", "rodamiento_110", 2)
    com(B, "Manguera de 1 in, cadena portamangueras, valvulas y purgas de la lanza", "valvulas_menores", 1)
    sop = kg(g("R07_V12_SOPORTE_MARCO_CABINA")) + kg(g("G06_SOPORTE_COMPACTO")) \
        + kg(lambda p: p["grupo"] == "G07_APOYOS_ACCIONAMIENTO_FIJOS" and not p["pieza"].startswith(("R04_POLEA", "R04_CORREA"))) \
        + kg(lambda p: p["pieza"].startswith(("R07_V9_BANCADA", "R07_V9_MENSULA", "R07_V9_GUARDA"))) + kg(g("R07_V7_SF47_BANCADA"))
    fab(B, "Soporte superior (HPGR D-065), cartucho, alojamientos, mensula y guarda", sop, "A36", "estructura",
        "CAD V16B: R07_V12_SOPORTE_MARCO_CABINA, G06, G07 sin polea ni correa, bancada, mensula y guarda")

    # ---------------- C. Hidraulica y filtrado ----------------
    C = "C. Hidraulica y filtrado"
    com(C, "Bomba Grundfos CRN 15-3 en 316 con motor de 3 kW", "bomba_CRN15_3", 1)
    com(C, "Filtro de bolsa Pentair ES2 316L", "filtro_ES2", 1)
    com(C, "Colador en Y de 2 in", "colador_Y_2in", 1)
    com(C, "Valvula de 3 vias de 2 in con actuador (lavado / enjuague)", "valvula_3vias_2in", 1)
    com(C, "Retencion, bola de impulsion, bypass y purgas", "valvulas_menores", 1)
    fab(C, "Tuberia fija 316L (impulsion DN50 de 9,5 m, drenaje 2 in, purga)", 9.5 * 4.0 + 6.0 * 4.0 + 1.2 * 4.0, "inox", "inox_tuberia",
        "Largos: linea de 9,5 m (INFORME_BLOQUES_G_H), drenaje 2 in de ~6 m y purga de 1,2 m [HIPOTESIS]; DN50 Sch 10S 4,0 kg/m")
    fab(C, "Pedestal de la bomba y postes de apoyo", kg(n("R07_B_PEDESTAL")) + kg(n("R07_B_POSTE")), "A36", "estructura", "CAD V16B")
    com(C, "Transmisor de presion PMP21", "PMP21", 1)
    com(C, "Manometro WIKA 233.50", "manometro", 1)

    # ---------------- D. Tanques, calentamiento y dosificacion ----------------
    D = "D. Tanques y calentamiento"
    m_t1 = kg(n("R07_V9_TANQUE_CUERPO"), 7.93) + kg(g("R07_E_TANQUE"), 7.93)
    fab(D, "Tanque 1 de 600 L en inox 304 con tabique, tapas, cesto, separador y tubuladuras", m_t1, "inox", "inox_chapa",
        "CAD V16B: R07_V9_TANQUE_CUERPO y grupo R07_E_TANQUE")
    m_t2 = kg(n("R07_V9_TANQUE_ENJUAGUE"), 7.93) + kg(lambda p: p["pieza"].startswith(("R07_G_TAPA", "R07_G_PATA")), 7.93)
    fab(D, "Tanque de enjuague de 204 L en inox 304", m_t2, "inox", "inox_chapa", "CAD V16B: R07_V9_TANQUE_ENJUAGUE, tapa y patas")
    com(D, "Aislamiento de lana mineral de 50 mm con forro", "lana_mineral_m3", round(vol(n("R07_V9_AISLAMIENTO")) / 1e6, 3), "m3", importado=False)
    com(D, "Resistencias de inmersion de 12 kW (3)", "resistencia_12kW", 3, importado=False)
    com(D, "Interruptores de nivel FTL31 (3)", "FTL31", 3)
    com(D, "Sonda de temperatura TM131", "TM131", 1)
    com(D, "Transmisor de nivel del tanque 1", "LT_nivel", 1)
    com(D, "Dosificadoras Grundfos DDA (detergente e inhibidor)", "DDA", 2)
    com(D, "Detergente inicial (balde de 56,7 kg)", "detergente_balde", 1)
    com(D, "Inhibidor inicial (bidon de 60 L)", "inhibidor_bidon", 1)

    # ---------------- E. Cabina hermetica ----------------
    E = "E. Cabina hermetica"
    area = sum(p["caja_mm"][0] * p["caja_mm"][2] / 1e6 if p["caja_mm"][1] <= 100.5 else
               (p["caja_mm"][1] * p["caja_mm"][2] / 1e6 if p["caja_mm"][0] <= 100.5 else p["caja_mm"][0] * p["caja_mm"][1] / 1e6)
               for p in M if p["grupo"] == "G00_CONTEXTO_CABINA_R05" and p["pieza"].startswith("CTX_CABIN"))
    m_pan = area * 1.5e-3 * 7930 * 1.20
    fab(E, "Paneles de inox 304 de 1,5 mm (%.1f m2, +20 %% de juntas y refuerzos)" % area, m_pan, "inox", "inox_chapa",
        "Area de los muros y el techo de CTX_CABIN (CAD); espesor y +20 %% [HIPOTESIS]")
    m_puerta = 2.24 * 1.515 * 2e-3 * 7930 + 9.0 * 2.3 + 2 * 3.23 * 5.5 + 2.6 * 19.0
    fab(E, "Puerta de guillotina: hoja (piel de 2 mm y marco), guias y dintel", m_puerta, "inox", "inox_chapa",
        "INFORME_BLOQUES_G_H: piel de 2 mm y marco 40x40; guias en U y dintel en cajon [HIPOTESIS de seccion]")
    com(E, "Motorreductor de la puerta con freno y contrapeso", "motor_puerta", 1)
    com(E, "Extractor y eliminador de niebla", "extractor_niebla", 1)
    com(E, "Luminarias IP65 (2)", "luminaria_IP65", 2)
    com(E, "Sellos EPDM, cepillos, mirilla y persiana", "menores_cabina", 1)

    # ---------------- F. Drenaje ----------------
    F = "F. Drenaje"
    com(F, "Bomba de drenaje Hidrostal A02Q-S", "bomba_hidrostal", 1, importado=False)
    com(F, "Desviadora, flotador, IBC de 1000 L y tuberia DN100", "drenaje_menores", 1, importado=False)

    # ---------------- G. Tablero y control ----------------
    G = "G. Tablero electrico y control"
    com(G, "Gabinete Rittal AE 1260.500 IP66", "rittal_AE", 1)
    com(G, "PLC Siemens S7-1200 CPU 1214C", "cpu_1214C", 1)
    com(G, "HMI Siemens KTP700 Basic", "ktp700", 1)
    com(G, "Variador de la bomba ATV320U55N4C", "atv320", 1)
    com(G, "Variador del rotor WEG CFW300", "cfw300", 1)
    com(G, "Aparamenta, protecciones, rele de seguridad y fuente", "aparamenta", 1)
    com(G, "Pulsadores de emergencia (2)", "emergencia", 2)
    com(G, "Cables y prensaestopas", "cableado", 1)
    com(G, "Bandejas portacables (~6,5 m)", "bandeja_m", 6.5, "m")
    fab(G, "Soportes del tablero y mensulas de bandeja", kg(lambda p: p["pieza"].startswith(("R07_C_SOPORTE", "R07_C_MENSULA"))), "A36", "estructura", "CAD V16B")

    # ---------------- H. Obra civil, montaje y puesta en marcha ----------------
    H = "H. Obra civil, montaje y puesta en marcha"
    com(H, "Obra civil: pozo de bombeo, piso humedo, colector y bordillos", "obra_civil", 1, importado=False)
    lineas.append({"partida": H, "descripcion": "Montaje mecanico y electrico, pruebas y puesta en marcha (2 tecnicos x 15 dias)",
                   "cantidad": 2 * 15 * 8, "unidad": "h", "total_PEN": round(2 * 15 * 8 * tarifa),
                   "fuente": "Tarifa de taller S/ %.1f/h [HIPOTESIS de duracion]" % tarifa, "estado": "HIPOTESIS", "importado": False})

    # ---------------- totales y rangos ----------------
    for l in lineas:
        lo, hi = (0.85, 1.20) if l["estado"] == "FUENTE" else (0.70, 1.50)
        l["min_PEN"], l["max_PEN"] = round(l["total_PEN"] * lo), round(l["total_PEN"] * hi)
    partidas = {}
    for l in lineas:
        q = partidas.setdefault(l["partida"], {"total_PEN": 0, "min_PEN": 0, "max_PEN": 0})
        for k in ("total_PEN", "min_PEN", "max_PEN"):
            q[k] += l[k]
    sub = sum(q["total_PEN"] for q in partidas.values())
    ing = round(0.05 * sub)
    cont = round(0.15 * (sub + ing))
    total = sub + ing + cont
    rng_lo = sum(q["min_PEN"] for q in partidas.values()) + ing + cont
    rng_hi = sum(q["max_PEN"] for q in partidas.values()) + ing + cont
    fuente_pct = sum(l["total_PEN"] for l in lineas if l["estado"] == "FUENTE") / sub
    fabricado = sum(l["total_PEN"] for l in lineas if "mano_obra_PEN" in l)
    mo = sum(l.get("mano_obra_PEN", 0) for l in lineas)

    # evaluacion economica (misma formula de la P2: VAN = -I + A n f Cm)
    A_fac = (1 - 1.10 ** -5) / 0.10
    Cm = 885.0
    feq = {n_: round(100 * total / (A_fac * n_ * Cm)) for n_ in (4, 12, 24, 48)}
    # HPGR D-077: beneficio requerido por rodamiento para recuperar la inversion en 5 anos al 10 %: B* = I / (A n)
    breq = {n_: [round(rng_lo / (A_fac * n_)), round(total / (A_fac * n_)), round(rng_hi / (A_fac * n_))] for n_ in (4, 12, 24, 48)}

    res = {"estado": "EJECUTADO (calculo); estimacion de clase 4; precios de referencia y HIPOTESIS; sin IGV",
           "tipo_cambio": {k: [TC[k], FUENTE_TC[k]] for k in FUENTE_TC}, "factor_importacion": IMPORT,
           "tarifa_taller_PEN_h": round(tarifa, 1), "horas_por_kg": HKG, "cargas_sociales": CARGAS, "gastos_utilidad": GASTOS,
           "partidas": partidas, "subtotal_PEN": sub, "ingenieria_gestion_5pct_PEN": ing, "contingencia_15pct_PEN": cont,
           "total_sin_IGV_PEN": total, "rango_PEN": [rng_lo, rng_hi], "IGV_18pct_PEN": round(0.18 * total),
           "fraccion_con_fuente": round(fuente_pct, 3), "fabricado_PEN": fabricado, "mano_obra_taller_PEN": mo,
           "P2_total_PEN": 33855, "fraccion_equilibrio_pct_n_4_12_24_48": feq,
           "beneficio_requerido_PEN_por_rodamiento_min_base_max": breq, "factor_anualidad_5a_10pct": round(A_fac, 3),
           "precios": {k: {"valor": v[0], "moneda": v[1], "fuente": v[2], "estado": v[3]} for k, v in P.items()},
           "lineas": lineas}
    SALIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    # tabla LaTeX para la tesis (por partida)
    def f(x):
        s = "{:,.0f}".format(x).replace(",", "\\,")
        return s
    filas = []
    for k, q in partidas.items():
        filas.append("%s & %s & %s--%s\\\\" % (k[3:], f(q["total_PEN"]), f(q["min_PEN"]), f(q["max_PEN"])))
    tex = ("% Generado por presupuesto/scripts/c1_presupuesto.py (02/11/2026). No editar a mano.\n"
           "\\begin{table}[htbp]\n\\centering\\small\\singlespacing\n"
           "\\caption{Presupuesto de inversi\\'on de la m\\'aquina por partida (estimaci\\'on de clase 4, sin IGV)}\n"
           "\\label{tab:presupuesto-completo}\n\\begin{tabular}{@{}lrr@{}}\n\\toprule\n"
           "\\textbf{Partida} & \\textbf{Base (S/)} & \\textbf{Rango (S/)}\\\\\n\\midrule\n" + "\n".join(filas) + "\n\\midrule\n"
           "Subtotal & %s & \\\\\nIngenier\\'ia de fabricaci\\'on y gesti\\'on (5\\,\\%%) & %s & \\\\\nContingencia (15\\,\\%%) & %s & \\\\\n"
           "\\textbf{Total sin IGV} & \\textbf{%s} & %s--%s\\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
           % (f(sub), f(ing), f(cont), f(total), f(rng_lo), f(rng_hi)))
    TEX.write_text(tex, encoding="utf-8")
    filas_b = "\n".join("%d & %s & %s--%s & %s\\\\" % (n_, f(b[1]), f(b[0]), f(b[2]), f(Cm)) for n_, b in breq.items())
    TEX.with_name("tabla_beneficio_requerido.tex").write_text(
        "% Generado por presupuesto/scripts/c1_presupuesto.py (HPGR D-077). No editar a mano.\n"
        "\\begin{table}[htbp]\n\\centering\\small\\singlespacing\n"
        "\\caption{Beneficio por rodamiento necesario para recuperar la inversi\\'on en cinco a\\~nos al 10\\,\\%% anual}\n"
        "\\label{tab:beneficio-requerido}\n\\begin{tabular}{@{}rrrr@{}}\n\\toprule\n"
        "\\textbf{Rodamientos por a\\~no} & \\textbf{Base (S/)} & \\textbf{Rango (S/)} & \\textbf{Mano de obra manual hoy (S/)}\\\\\n\\midrule\n"
        + filas_b + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n", encoding="utf-8")

    print("tarifa de taller S/ %.1f/h" % tarifa)
    for k, q in partidas.items():
        print("%-46s %9s  (%s - %s)" % (k, f(q["total_PEN"]).replace("\\,", " "), q["min_PEN"], q["max_PEN"]))
    print("subtotal %d | ingenieria %d | contingencia %d | TOTAL %d (rango %d - %d) | IGV %d" % (sub, ing, cont, total, rng_lo, rng_hi, round(0.18 * total)))
    print("con fuente %.0f %% | fabricado %d (mano de obra %d) | P2 33 855 | f* (n=4,12,24,48) = %s %%" % (100 * fuente_pct, fabricado, mo, feq))
    for l in lineas:
        print("  %-30s %-70s %8d %s" % (l["partida"][:30], l["descripcion"][:70], l["total_PEN"], l["estado"]))


if __name__ == "__main__":
    main()
