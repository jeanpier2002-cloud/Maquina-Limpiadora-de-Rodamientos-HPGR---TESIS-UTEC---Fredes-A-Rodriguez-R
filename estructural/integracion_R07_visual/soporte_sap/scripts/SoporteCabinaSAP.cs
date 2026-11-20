// Soporte superior del rotor y del motorreductor (R07 V17B): ¿basta la cabina sola? Modelo parametrico de SAP2000 v27 por API (N, mm).
// Extiende SoporteSAP.cs (D-065, que no se modifica) con la cabina como cascaras: muros y techo de inox 304 en los planos medios de
// CTX_CABIN (x = +-2020, y = +-2070, techo z 2610; puerta x +-1070, z 140-1605). Cargas de R03 con el rotor real de D-075
// (231 kg, CG a 79,6 mm: CALCULO_B1_ROTOR_U_EJE_CUBO.md). El cartucho, la mensula y el motor son un cuerpo rigido.
// Opciones (texto "clave=valor;..."):
//   t        espesor de la chapa de la cabina (mm); 0 = sin cabina estructural
//   postes   seccion de los postes o "no";  bases = emp | art
//   celosia  1/0 (X L40x4 en los muros);  planta = 1/0 (X en planta entre vigas)
//   vigas    seccion de las vigas o "no" (sin vigas: el cartucho apoya en el techo)
//   f12      modificador de la rigidez a cortante de membrana de la chapa (flexibilidad de las uniones, HIPOTESIS)
//   nl       1 = caso S1 no lineal con grandes desplazamientos
//   diaf     1 = la chapa sin peso ni masa propios (los lleva el esqueleto de los paneles): solo su rigidez de diafragma
//   npand    numero de modos de pandeo (6 por defecto)
//   sismo    coeficiente sismico horizontal V/P de la E.030-2018 (estatico equivalente, Z U C S / R); 0 = sin sismo. Patrones SX y SY con
//            las masas del cuerpo (el rotor en su CG real, z 2208, con el momento respecto del cojinete inferior) y el peso propio de las
//            barras; combinaciones U4 = 1,4D + BELT + TORQ +- E y U5 = 0,7D +- E (vertical +-2/3 del horizontal, E.030 6.5), y S3 = D + BELT + TORQ + E
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using SAP2000v1;

public static class SoporteCabinaSAP
{
    static cSapModel m;
    static CultureInfo IC = CultureInfo.InvariantCulture;
    static StringBuilder log = new StringBuilder();
    static Dictionary<string, string> pts = new Dictionary<string, string>();
    static Dictionary<string, string> zona = new Dictionary<string, string>();
    static void L(string s) { log.AppendLine(s); Console.WriteLine(s); }
    static string F(double v) { return v.ToString("0.######", IC); }

    static string P(double x, double y, double z)
    {
        string k = Math.Round(x, 1).ToString(IC) + "|" + Math.Round(y, 1).ToString(IC) + "|" + Math.Round(z, 1).ToString(IC);
        string n;
        if (pts.TryGetValue(k, out n)) return n;
        n = "";
        m.PointObj.AddCartesian(x, y, z, ref n, "", "Global", true, 0);
        pts[k] = n;
        return n;
    }

    static string Barra(double x1, double y1, double z1, double x2, double y2, double z2, string prop)
    {
        string n = "";
        int r = m.FrameObj.AddByPoint(P(x1, y1, z1), P(x2, y2, z2), ref n, prop, "");
        if (r != 0) L("AddByPoint fallo " + prop);
        return n;
    }

    static void Rotula(string n, bool inicio, bool fin)
    {
        bool[] ii = { false, false, false, false, inicio, inicio };
        bool[] jj = { false, false, false, fin, fin, fin };
        double[] a = new double[6], b = new double[6];
        m.FrameObj.SetReleases(n, ref ii, ref jj, ref a, ref b);
    }

    static string Area(string z, string prop, double[] x, double[] y, double[] zz)
    {
        string[] p = new string[4];
        for (int i = 0; i < 4; i++) p[i] = P(x[i], y[i], zz[i]);
        string n = "";
        m.AreaObj.AddByPoint(4, ref p, ref n, prop, "");
        zona[n] = z;
        return n;
    }

    static void Carga(string p, string patron, double fx, double fy, double fz, double mx, double my, double mz)
    {
        double[] v = { fx, fy, fz, mx, my, mz };
        m.PointObj.SetLoadForce(p, patron, ref v, true, "Global", eItemType.Objects);
    }

    static void Combo(string n, params object[] lista)
    {
        m.RespCombo.Add(n, 0);
        for (int i = 0; i < lista.Length; i += 2)
        {
            eCNameType t = eCNameType.LoadCase;
            m.RespCombo.SetCaseList(n, ref t, (string)lista[i], (double)lista[i + 1]);
        }
    }

    static void Seccion(string nombre, string def)
    {
        string[] p = def.Split(':');
        double a = double.Parse(p[1], IC), b = p.Length > 2 ? double.Parse(p[2], IC) : 0, c = p.Length > 3 ? double.Parse(p[3], IC) : 0;
        if (p[0] == "TUBE") m.PropFrame.SetTube(nombre, "A36", a, b, c, c, -1, "", "");
        else if (p[0] == "ANGLE") m.PropFrame.SetAngle(nombre, "A36", a, b, c, c, -1, "", "");
    }

    // lineas de malla: las claves y subdivisiones iguales de largo <= dmax
    static double[] Lineas(double[] claves, double dmax)
    {
        var l = new List<double>();
        for (int i = 0; i < claves.Length - 1; i++)
        {
            int n = (int)Math.Ceiling((claves[i + 1] - claves[i]) / dmax - 1e-9);
            for (int k = 0; k < n; k++) l.Add(claves[i] + (claves[i + 1] - claves[i]) * k / n);
        }
        l.Add(claves[claves.Length - 1]);
        return l.ToArray();
    }

    static void Lineal(string caso, string[] patrones, double[] fac)
    {
        string[] lt = patrones.Select(x => "Load").ToArray();
        m.LoadCases.StaticLinear.SetCase(caso);
        m.LoadCases.StaticLinear.SetLoads(caso, patrones.Length, ref lt, ref patrones, ref fac);
    }

    public static string Correr(string caso, string dirModelos, string dirRes, string opciones)
    {
        log.Clear(); pts.Clear(); zona.Clear();
        var o = opciones.Split(';').Where(s => s.Contains("=")).ToDictionary(s => s.Split('=')[0].Trim(), s => s.Split('=')[1].Trim());
        Func<string, string, string> op = (k, d) => o.ContainsKey(k) ? o[k] : d;
        double t = double.Parse(op("t", "0"), IC), f12 = double.Parse(op("f12", "1"), IC);
        string postes = op("postes", "no"), vigas = op("vigas", "no");
        bool emp = op("bases", "art") == "emp", celosia = op("celosia", "0") == "1", planta = op("planta", "0") == "1", nl = op("nl", "0") == "1", diaf = op("diaf", "0") == "1";
        double cs = double.Parse(op("sismo", "0"), IC);
        bool cabina = t > 0, hayVigas = vigas != "no", hayPostes = postes != "no";

        string prog = @"C:\Program Files\Computers and Structures\SAP2000 27";
        cHelper h = new Helper();
        cOAPI sap = h.CreateObject(Path.Combine(prog, "SAP2000.exe"));
        sap.ApplicationStart(eUnits.N_mm_C, false, "");
        m = sap.SapModel;
        m.InitializeNewModel(eUnits.N_mm_C);
        m.File.NewBlank();
        m.PropMaterial.SetMaterial("A36", eMatType.Steel, -1, "", "");
        m.PropMaterial.SetMPIsotropic("A36", 200000, 0.3, 1.17e-5, 0);
        m.PropMaterial.SetWeightAndMass("A36", 1, 7.6982e-5, 0);
        m.PropMaterial.SetOSteel_1("A36", 250, 400, 275, 440, 1, 1, 0.02, 0.1, 0.2, -0.1, 0);
        // inox 304 (ASTM A240): E 193 GPa, nu 0,29, 8 000 kg/m3, Fy 205 MPa
        m.PropMaterial.SetMaterial("INOX304", eMatType.Steel, -1, "", "");
        m.PropMaterial.SetMPIsotropic("INOX304", 193000, 0.29, 1.73e-5, 0);
        m.PropMaterial.SetWeightAndMass("INOX304", 1, 7.8453e-5, 0);
        m.PropMaterial.SetOSteel_1("INOX304", 205, 515, 205, 515, 1, 1, 0.02, 0.1, 0.2, -0.1, 0);
        if (hayPostes) Seccion("COL", postes);
        if (hayVigas) Seccion("VIGA", vigas);
        Seccion("LAC", op("lac", "ANGLE:40:40:4"));
        Seccion("TACO", "TUBE:100:100:5");
        if (cabina) m.PropArea.SetShell_1("CHAPA", 1, true, "INOX304", 0, t, t, -1, "", "");

        // xc: postes en los muros (2020) o dentro de la cabina (solo sin cascaras: con t > 0 los muros siguen a xc)
        double xc = double.Parse(op("xc", "2020"), IC), yc = 300, zViga = 2790, zT = 2610, yM = 2070;
        double[] X = Lineas(new[] { -xc, -1070, -230, 0, 230, 1070, xc }, 150);
        double[] Y = Lineas(new[] { -yM, -yc, 0, yc, yM }, 150);
        double[] Z = Lineas(new[] { 0, 140, 1605, zT }, 150);
        double z1 = 150, z2 = 1470, z3 = 2690;

        // ---- cabina: techo y cuatro muros (frente con la puerta de guillotina) ----
        double area = 0;
        if (cabina)
        {
            for (int i = 0; i < X.Length - 1; i++)
                for (int j = 0; j < Y.Length - 1; j++)
                    Area("TECHO", "CHAPA", new[] { X[i], X[i + 1], X[i + 1], X[i] }, new[] { Y[j], Y[j], Y[j + 1], Y[j + 1] }, new[] { zT, zT, zT, zT });
            area += (2 * xc) * (2 * yM);
            foreach (double sx in new[] { -1.0, 1.0 })
                for (int j = 0; j < Y.Length - 1; j++)
                    for (int k = 0; k < Z.Length - 1; k++)
                        Area(sx < 0 ? "MURO_IZQ" : "MURO_DER", "CHAPA", new[] { sx * xc, sx * xc, sx * xc, sx * xc }, new[] { Y[j], Y[j + 1], Y[j + 1], Y[j] }, new[] { Z[k], Z[k], Z[k + 1], Z[k + 1] });
            area += 2 * (2 * yM) * zT;
            foreach (double sy in new[] { -1.0, 1.0 })
                for (int i = 0; i < X.Length - 1; i++)
                    for (int k = 0; k < Z.Length - 1; k++)
                    {
                        double xm = (X[i] + X[i + 1]) / 2, zm = (Z[k] + Z[k + 1]) / 2;
                        if (sy < 0 && Math.Abs(xm) < 1070 && zm > 140 && zm < 1605) continue;  // vano de la puerta
                        Area(sy < 0 ? "MURO_FRENTE" : "MURO_FONDO", "CHAPA", new[] { X[i], X[i + 1], X[i + 1], X[i] }, new[] { sy * yM, sy * yM, sy * yM, sy * yM }, new[] { Z[k], Z[k], Z[k + 1], Z[k + 1] });
                    }
            area += 2 * (2 * xc) * zT - 2140 * 1465;
            // diaf = 1: la chapa solo aporta rigidez (diafragma); su peso y su masa los llevan las nervaduras de los paneles
            if (f12 != 1 || diaf)
            {
                double[] mod = { 1, 1, f12, 1, 1, 1, 1, 1, diaf ? 0 : 1, diaf ? 0 : 1 };
                foreach (string a in zona.Keys) m.AreaObj.SetModifiers(a, ref mod, eItemType.Objects);
            }
            // base de los muros: apoyo continuo articulado sobre el bordillo del piso humedo (HIPOTESIS)
            bool[] art = { true, true, true, false, false, false };
            foreach (var kv in pts.ToList())
                if (Math.Abs(double.Parse(kv.Key.Split('|')[2], IC)) < 0.01) m.PointObj.SetRestraint(kv.Value, ref art, eItemType.Objects);
        }

        // ---- postes, celosias, vigas y planta ----
        var zPoste = new SortedSet<double>(new[] { 0.0, zViga });
        if (celosia) { zPoste.Add(z1); zPoste.Add(z2); zPoste.Add(z3); }
        if (cabina) foreach (double z in Z) zPoste.Add(z);
        if (hayPostes)
            foreach (double sx in new[] { -1.0, 1.0 })
                foreach (double sy in new[] { -1.0, 1.0 })
                {
                    double[] zs = zPoste.ToArray();
                    for (int i = 0; i < zs.Length - 1; i++) Barra(sx * xc, sy * yc, zs[i], sx * xc, sy * yc, zs[i + 1], "COL");
                    string b = P(sx * xc, sy * yc, 0);
                    bool[] rr = emp ? new[] { true, true, true, true, true, true } : new[] { true, true, true, false, false, false };
                    m.PointObj.SetRestraint(b, ref rr, eItemType.Objects);
                }
        else if (hayVigas && cabina)
            // sin postes: la viga apoya en el borde superior del muro con un taco SHS100x5 de z 2610 a 2790, a momento
            foreach (double sx in new[] { -1.0, 1.0 })
                foreach (double sy in new[] { -1.0, 1.0 })
                    Barra(sx * xc, sy * yc, zT, sx * xc, sy * yc, zViga, "TACO");
        if (celosia && hayPostes)
            foreach (double sx in new[] { -1.0, 1.0 })
            {
                double x = sx * xc;
                foreach (double[] pz in new[] { new[] { z1, z2 }, new[] { z2, z3 } })
                {
                    double zm = (pz[0] + pz[1]) / 2;
                    Rotula(Barra(x, -yc, pz[0], x, 0, zm, "LAC"), true, false);
                    Rotula(Barra(x, 0, zm, x, yc, pz[1], "LAC"), false, true);
                    Rotula(Barra(x, yc, pz[0], x, 0, zm, "LAC"), true, false);
                    Rotula(Barra(x, 0, zm, x, -yc, pz[1], "LAC"), false, true);
                }
                Rotula(Barra(x, -yc, z2, x, yc, z2, "LAC"), true, true);
            }
        double zApoyo = hayVigas ? zViga : zT;
        if (hayVigas)
            foreach (double sy in new[] { -1.0, 1.0 })
                for (int i = 0; i < X.Length - 1; i++) Barra(X[i], sy * yc, zViga, X[i + 1], sy * yc, zViga, "VIGA");
        if (planta && hayVigas)
            foreach (double[] tr in new[] { new[] { -xc, -230.0 }, new[] { 230.0, xc } })
            {
                Rotula(Barra(tr[0], -yc, zViga, tr[1], yc, zViga, "LAC"), true, true);
                Rotula(Barra(tr[0], yc, zViga, tr[1], -yc, zViga, "LAC"), true, true);
            }

        // ---- cuerpo rigido: cartucho, mensula y motor, apoyado en x = +-230, y = +-300 (vigas o techo) ----
        bool[] todo = { true, true, true, true, true, true };
        m.ConstraintDef.SetBody("CARTUCHO", ref todo, "Global");
        var cuerpo = new List<string>();
        foreach (double sx in new[] { -230.0, 230.0 })
            foreach (double sy in new[] { -yc, yc }) cuerpo.Add(P(sx, sy, zApoyo));
        string LB = P(0, 0, 2850), UB = P(0, 0, 3450), CG = P(0, 0, 3100), BR = P(570, 0, 3150), MO = P(800, 0, 3280), PO = P(700, 0, 3150), PC = P(0, 0, 3150);
        cuerpo.AddRange(new[] { LB, UB, CG, BR, MO, PO, PC });
        foreach (string p in cuerpo) { string cn = "CARTUCHO"; m.PointObj.SetConstraint(p, ref cn, eItemType.Objects, true); }

        m.LoadPatterns.Add("BELT", eLoadPatternType.Other, 0, true);
        m.LoadPatterns.Add("TORQ", eLoadPatternType.Other, 0, true);
        foreach (string a in new[] { "AXP", "AXN", "AYP", "AYN" }) m.LoadPatterns.Add(a, eLoadPatternType.Other, 0, true);
        // DEAD: como D-065, con el rotor real de D-075 (231,0 kg -> 2 266 N) en el cojinete inferior
        Carga(CG, "DEAD", 0, 0, -1789, 0, 0, 0);
        Carga(BR, "DEAD", 0, 0, -412, 0, 0, 0);
        Carga(MO, "DEAD", 0, 0, -304, 0, 0, 0);
        Carga(LB, "DEAD", 0, 0, -2266, 0, 0, 0);
        Carga(PC, "BELT", 1071, 0, 0, 0, 0, 0);
        Carga(PO, "BELT", -1071, 0, 0, 0, 0, 0);
        Carga(CG, "TORQ", 0, 0, 0, 0, 0, 60000);
        // accidental: 1 000 N a z 1400 llevada al cojinete inferior, mas el peso excentrico 2 266 N x 79,6 mm en el mismo sentido
        double Fa = 1000, brazo = 2850 - 1400, Mexc = 2266 * 79.6;
        Carga(LB, "AXP", Fa, 0, 0, 0, -(Fa * brazo + Mexc), 0);
        Carga(LB, "AXN", -Fa, 0, 0, 0, (Fa * brazo + Mexc), 0);
        Carga(LB, "AYP", 0, Fa, 0, (Fa * brazo + Mexc), 0, 0);
        Carga(LB, "AYN", 0, -Fa, 0, -(Fa * brazo + Mexc), 0, 0);
        foreach (string a in new[] { "BELT", "TORQ", "AXP", "AXN", "AYP", "AYN" }) Lineal(a, new[] { a }, new[] { 1.0 });
        if (cs > 0)
        {
            // E.030-2018 estatico equivalente: F = cs * peso; rotor (2 266 N) con CG en z 2208 (MASAS_ROTOR_V15B.json): su fuerza se aplica en
            // el cojinete inferior con el momento r x F, r = (0, 0, 2208 - 2850)
            double dz = 2208.0 - 2850.0;
            m.LoadPatterns.Add("SX", eLoadPatternType.Other, 0, true);
            m.LoadPatterns.Add("SY", eLoadPatternType.Other, 0, true);
            Carga(CG, "SX", cs * 1789, 0, 0, 0, 0, 0); Carga(BR, "SX", cs * 412, 0, 0, 0, 0, 0); Carga(MO, "SX", cs * 304, 0, 0, 0, 0, 0);
            Carga(LB, "SX", cs * 2266, 0, 0, 0, dz * cs * 2266, 0);
            Carga(CG, "SY", 0, cs * 1789, 0, 0, 0, 0); Carga(BR, "SY", 0, cs * 412, 0, 0, 0, 0); Carga(MO, "SY", 0, cs * 304, 0, 0, 0, 0);
            Carga(LB, "SY", 0, cs * 2266, 0, -dz * cs * 2266, 0, 0);
            int nfs = 0; string[] fns = null; m.FrameObj.GetNameList(ref nfs, ref fns);
            for (int i = 0; i < nfs; i++)
            {
                string prop = "", sAuto = ""; m.FrameObj.GetSection(fns[i], ref prop, ref sAuto);
                double A = 0, As2 = 0, As3 = 0, Tq = 0, I22 = 0, I33 = 0, S22 = 0, S33 = 0, Z22 = 0, Z33 = 0, R22 = 0, R33 = 0;
                m.PropFrame.GetSectProps(prop, ref A, ref As2, ref As3, ref Tq, ref I22, ref I33, ref S22, ref S33, ref Z22, ref Z33, ref R22, ref R33);
                double q = cs * A * 7.6982e-5;   // N/mm
                m.FrameObj.SetLoadDistributed(fns[i], "SX", 1, 4, 0, 1, q, q, "Global", true, true, eItemType.Objects);
                m.FrameObj.SetLoadDistributed(fns[i], "SY", 1, 5, 0, 1, q, q, "Global", true, true, eItemType.Objects);
            }
            Lineal("SX", new[] { "SX" }, new[] { 1.0 }); Lineal("SY", new[] { "SY" }, new[] { 1.0 });
        }
        Combo("U1", "DEAD", 1.4);
        Combo("U2", "DEAD", 1.2, "BELT", 1.6, "TORQ", 1.6);
        foreach (string a in new[] { "AXP", "AXN", "AYP", "AYN" }) Combo("U3_" + a, "DEAD", 1.2, "BELT", 1.0, "TORQ", 1.0, a, 1.0);
        Combo("S1", "DEAD", 1.0, "BELT", 1.0, "TORQ", 1.0);
        foreach (string a in new[] { "AXP", "AXN", "AYP", "AYN" }) Combo("S2_" + a, "DEAD", 1.0, "BELT", 1.0, "TORQ", 1.0, a, 1.0);
        var sism = new List<string>();
        if (cs > 0)
        {
            double v = 2.0 / 3.0 * cs;   // vertical, E.030 6.5
            foreach (string e in new[] { "SX", "SY" })
                foreach (double sg in new[] { 1.0, -1.0 })
                {
                    string k = e + (sg > 0 ? "P" : "N");
                    Combo("U4_" + k, "DEAD", 1.2 + v, "BELT", 1.0, "TORQ", 1.0, e, sg);
                    Combo("U5_" + k, "DEAD", 0.9 - v, e, sg);
                    sism.Add("U4_" + k); sism.Add("U5_" + k);
                }
            Combo("S3_SX", "DEAD", 1.0, "BELT", 1.0, "TORQ", 1.0, "SX", 1.0);
            Combo("S3_SY", "DEAD", 1.0, "BELT", 1.0, "TORQ", 1.0, "SY", 1.0);
        }
        string[] mp = { "DEAD" }; double[] ms = { 1 };
        m.SourceMass.SetMassSource("MASA", true, false, true, true, 1, ref mp, ref ms);
        m.LoadCases.ModalEigen.SetNumberModes("MODAL", 12, 1);
        // pandeo lineal con las cargas de U2 y de U3 en X e Y
        var pand = new Dictionary<string, string[]> { { "PAND_U2", new[] { "DEAD", "BELT", "TORQ" } },
            { "PAND_U3X", new[] { "DEAD", "BELT", "TORQ", "AXP" } }, { "PAND_U3Y", new[] { "DEAD", "BELT", "TORQ", "AYP" } } };
        foreach (var kv in pand)
        {
            m.LoadCases.Buckling.SetCase(kv.Key);
            string[] lt = kv.Value.Select(x => "Load").ToArray(); string[] ln = kv.Value;
            double[] sf = kv.Key == "PAND_U2" ? new[] { 1.2, 1.6, 1.6 } : new[] { 1.2, 1.0, 1.0, 1.0 };
            m.LoadCases.Buckling.SetLoads(kv.Key, ln.Length, ref lt, ref ln, ref sf);
            // SAP entrega los factores de menor valor absoluto: con chapa, los negativos (carga invertida) llenan los primeros modos
            m.LoadCases.Buckling.SetParameters(kv.Key, int.Parse(op("npand", "6")), 1e-9);
        }
        if (nl)
        {
            m.LoadCases.StaticNonlinear.SetCase("S1_NL");
            string[] lt = { "Load", "Load", "Load" }; string[] ln = { "DEAD", "BELT", "TORQ" }; double[] sf = { 1, 1, 1 };
            m.LoadCases.StaticNonlinear.SetLoads("S1_NL", 3, ref lt, ref ln, ref sf);
            m.LoadCases.StaticNonlinear.SetGeometricNonlinearity("S1_NL", 2);
        }

        Directory.CreateDirectory(dirModelos); Directory.CreateDirectory(dirRes);
        string sdb = Path.Combine(dirModelos, caso + ".sdb");
        m.File.Save(sdb);
        int ra = m.Analyze.RunAnalysis();
        L("analisis " + ra + "  areas " + zona.Count + "  nudos " + pts.Count);

        var J = new StringBuilder();
        J.Append("{\"caso\":\"" + caso + "\",\"opciones\":\"" + opciones + "\",\"t_mm\":" + F(t) + ",\"area_chapa_m2\":" + F(area / 1e6) +
                 ",\"masa_chapa_kg\":" + F(area * t * 8e-6));
        int nf = 0; string[] fn = null;
        m.FrameObj.GetNameList(ref nf, ref fn);
        double masa = 0;
        for (int i = 0; i < nf; i++)
        {
            string p1 = "", p2 = ""; m.FrameObj.GetPoints(fn[i], ref p1, ref p2);
            double x1 = 0, y1 = 0, zz1 = 0, x2 = 0, y2 = 0, zz2 = 0;
            m.PointObj.GetCoordCartesian(p1, ref x1, ref y1, ref zz1, "Global");
            m.PointObj.GetCoordCartesian(p2, ref x2, ref y2, ref zz2, "Global");
            string prop = "", sAuto = ""; m.FrameObj.GetSection(fn[i], ref prop, ref sAuto);
            double A = 0, As2 = 0, As3 = 0, Tq = 0, I22 = 0, I33 = 0, S22 = 0, S33 = 0, Z22 = 0, Z33 = 0, R22 = 0, R33 = 0;
            m.PropFrame.GetSectProps(prop, ref A, ref As2, ref As3, ref Tq, ref I22, ref I33, ref S22, ref S33, ref Z22, ref Z33, ref R22, ref R33);
            masa += A * Math.Sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1) + (zz2 - zz1) * (zz2 - zz1)) * 7.85e-6;
        }
        J.Append(",\"masa_barras_kg\":" + F(masa));
        L("barras " + masa.ToString("F1", IC) + " kg; chapa " + (area * t * 8e-6).ToString("F1", IC) + " kg");

        // coordenadas de los nudos (para separar el techo y medir flechas)
        var coord = new Dictionary<string, double[]>();
        foreach (var kv in pts) { var c = kv.Key.Split('|'); coord[kv.Value] = new[] { double.Parse(c[0], IC), double.Parse(c[1], IC), double.Parse(c[2], IC) }; }

        Func<string, string, double[]> despl = (pt, cb) =>
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            if (cb.StartsWith("S1_NL")) m.Results.Setup.SetCaseSelectedForOutput(cb, true); else m.Results.Setup.SetComboSelectedForOutput(cb, true);
            int n = 0; string[] ob = null, e = null, lc = null, st = null; double[] sn = null, u1 = null, u2 = null, u3 = null, r1 = null, r2 = null, r3 = null;
            m.Results.JointDispl(pt, eItemTypeElm.ObjectElm, ref n, ref ob, ref e, ref lc, ref st, ref sn, ref u1, ref u2, ref u3, ref r1, ref r2, ref r3);
            return n > 0 ? new[] { u1[n - 1], u2[n - 1], u3[n - 1] } : new[] { double.NaN, double.NaN, double.NaN };
        };
        // desplazamientos de los cojinetes y del apoyo del cartucho
        var combos = new List<string> { "S1", "S2_AXP", "S2_AXN", "S2_AYP", "S2_AYN" };
        if (cs > 0) { combos.Add("S3_SX"); combos.Add("S3_SY"); }
        J.Append(",\"cojinetes\":{");
        bool pr = true;
        foreach (string cb in combos)
        {
            double[] us = despl(UB, cb), ui = despl(LB, cb);
            J.Append((pr ? "" : ",") + "\"" + cb + "\":{\"sup\":[" + F(us[0]) + "," + F(us[1]) + "," + F(us[2]) + "],\"inf\":[" + F(ui[0]) + "," + F(ui[1]) + "," + F(ui[2]) + "]}");
            pr = false;
        }
        J.Append("}");
        // flecha del apoyo del cartucho en S1: centro de la viga (o del techo) menos los extremos
        {
            double[] c0 = despl(P(0, yc, zApoyo), "S1"), c1 = despl(P(0, -yc, zApoyo), "S1");
            double[] e0 = hayVigas ? despl(P(xc, yc, zViga), "S1") : new double[] { 0, 0, 0 };
            J.Append(",\"flecha_apoyo_S1_mm\":" + F(Math.Max(Math.Abs(c0[2] - e0[2]), Math.Abs(c1[2] - e0[2]))));
            if (nl) { double[] q = despl(P(0, yc, zApoyo), "S1_NL"); J.Append(",\"flecha_apoyo_S1_NL_mm\":" + F(Math.Abs(q[2]))); }
        }
        // flecha maxima del techo en S1 (todos los nudos z 2610)
        if (cabina)
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            m.Results.Setup.SetComboSelectedForOutput("S1", true);
            int n = 0; string[] ob = null, e = null, lc = null, st = null; double[] sn = null, u1 = null, u2 = null, u3 = null, r1 = null, r2 = null, r3 = null;
            m.Results.JointDispl("ALL", eItemTypeElm.GroupElm, ref n, ref ob, ref e, ref lc, ref st, ref sn, ref u1, ref u2, ref u3, ref r1, ref r2, ref r3);
            double wmax = 0, hmax = 0;
            for (int i = 0; i < n; i++)
            {
                double[] c; if (!coord.TryGetValue(ob[i], out c)) continue;
                if (Math.Abs(c[2] - zT) < 0.1) wmax = Math.Max(wmax, Math.Abs(u3[i]));
                else if (Math.Abs(c[0]) > xc - 0.1 || Math.Abs(c[1]) > yM - 0.1) hmax = Math.Max(hmax, Math.Sqrt(u1[i] * u1[i] + u2[i] * u2[i]));
            }
            J.Append(",\"techo_w_max_S1_mm\":" + F(wmax) + ",\"muro_desplome_max_S1_mm\":" + F(hmax));
        }
        // modos
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            m.Results.Setup.SetCaseSelectedForOutput("MODAL", true);
            int n = 0; string[] lc = null, st = null; double[] sn = null, per = null, fr = null, cf = null, ev = null;
            m.Results.ModalPeriod(ref n, ref lc, ref st, ref sn, ref per, ref fr, ref cf, ref ev);
            J.Append(",\"frecuencias_Hz\":[" + string.Join(",", fr.Take(n).Select(F)) + "]");
            L("f1..f3 Hz " + (n > 2 ? fr[0].ToString("F2", IC) + " " + fr[1].ToString("F2", IC) + " " + fr[2].ToString("F2", IC) : "?"));
            int nm = 0; string[] lcm = null, stm = null; double[] snm = null, pm = null, ux = null, uy = null, uz = null, sux = null, suy = null, suz = null,
                rx = null, ry = null, rz = null, srx = null, sry = null, srz = null;
            m.Results.ModalParticipatingMassRatios(ref nm, ref lcm, ref stm, ref snm, ref pm, ref ux, ref uy, ref uz, ref sux, ref suy, ref suz,
                ref rx, ref ry, ref rz, ref srx, ref sry, ref srz);
            J.Append(",\"participacion\":[");
            for (int i = 0; i < nm; i++) J.Append((i > 0 ? "," : "") + "[" + F(ux[i]) + "," + F(uy[i]) + "," + F(uz[i]) + "," + F(rz[i]) + "]");
            J.Append("]");
        }
        // pandeo lineal
        J.Append(",\"pandeo\":{");
        pr = true;
        foreach (string pc in pand.Keys)
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            m.Results.Setup.SetCaseSelectedForOutput(pc, true);
            int n = 0; string[] lc = null, st = null; double[] sn = null, fa = null;
            m.Results.BucklingFactor(ref n, ref lc, ref st, ref sn, ref fa);
            J.Append((pr ? "" : ",") + "\"" + pc + "\":[" + string.Join(",", (fa ?? new double[0]).Take(n).Select(F)) + "]"); pr = false;
            L(pc + " " + (n > 0 ? fa[0].ToString("F3", IC) : "?"));
        }
        J.Append("}");
        // tensiones de von Mises en la chapa (cara superior e inferior), maximo por zona y combinacion
        if (cabina)
        {
            J.Append(",\"chapa_vm_MPa\":{");
            pr = true;
            foreach (string cb in new[] { "S1", "S2_AXP", "S2_AYP", "S2_AXN", "S2_AYN", "U2", "U3_AXP", "U3_AXN", "U3_AYP", "U3_AYN" })
            {
                m.Results.Setup.DeselectAllCasesAndCombosForOutput();
                m.Results.Setup.SetComboSelectedForOutput(cb, true);
                int n = 0; string[] ob = null, el = null, pe = null, lc = null, st = null; double[] sn = null,
                    s11t = null, s22t = null, s12t = null, smaxt = null, smint = null, sangt = null, svmt = null,
                    s11b = null, s22b = null, s12b = null, smaxb = null, sminb = null, sangb = null, svmb = null,
                    s13 = null, s23 = null, smaxa = null, sanga = null;
                m.Results.AreaStressShell("ALL", eItemTypeElm.GroupElm, ref n, ref ob, ref el, ref pe, ref lc, ref st, ref sn,
                    ref s11t, ref s22t, ref s12t, ref smaxt, ref smint, ref sangt, ref svmt,
                    ref s11b, ref s22b, ref s12b, ref smaxb, ref sminb, ref sangb, ref svmb, ref s13, ref s23, ref smaxa, ref sanga);
                var porZona = new Dictionary<string, double>();
                for (int i = 0; i < n; i++)
                {
                    string z; if (!zona.TryGetValue(ob[i], out z)) continue;
                    double v = Math.Max(svmt[i], svmb[i]);
                    double prev; porZona[z] = porZona.TryGetValue(z, out prev) ? Math.Max(prev, v) : v;
                }
                J.Append((pr ? "" : ",") + "\"" + cb + "\":{" + string.Join(",", porZona.Select(kv => "\"" + kv.Key + "\":" + F(kv.Value))) + "}"); pr = false;
            }
            J.Append("}");
        }
        // reacciones: suma y maximo por nudo (servicio y ultimo)
        J.Append(",\"reacciones\":{");
        pr = true;
        foreach (string cb in new[] { "S1", "S2_AXP", "S2_AYP", "U2", "U3_AXP", "U3_AYP" }.Concat(sism))
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            m.Results.Setup.SetComboSelectedForOutput(cb, true);
            int n = 0; string[] ob = null, e = null, lc = null, st = null; double[] sn = null, f1 = null, f2 = null, f3 = null, m1 = null, m2 = null, m3 = null;
            m.Results.JointReact("ALL", eItemTypeElm.GroupElm, ref n, ref ob, ref e, ref lc, ref st, ref sn, ref f1, ref f2, ref f3, ref m1, ref m2, ref m3);
            double sz = 0, fzmax = 0, fzmin = 0, fh = 0, mmax = 0;
            for (int i = 0; i < n; i++)
            {
                sz += f3[i]; fzmax = Math.Max(fzmax, f3[i]); fzmin = Math.Min(fzmin, f3[i]);
                fh = Math.Max(fh, Math.Sqrt(f1[i] * f1[i] + f2[i] * f2[i])); mmax = Math.Max(mmax, Math.Sqrt(m1[i] * m1[i] + m2[i] * m2[i]));
            }
            J.Append((pr ? "" : ",") + "\"" + cb + "\":{\"suma_Fz\":" + F(sz) + ",\"Fz_max\":" + F(fzmax) + ",\"Fz_min\":" + F(fzmin) + ",\"Fh_max\":" + F(fh) + ",\"M_max\":" + F(mmax) + "}"); pr = false;
        }
        J.Append("}");
        // diseno AISC 360-16 de las barras
        if (nf > 0)
        {
            m.DesignSteel.SetCode("AISC 360-16");
            foreach (string c in new[] { "U1", "U2", "U3_AXP", "U3_AXN", "U3_AYP", "U3_AYN" }.Concat(sism)) m.DesignSteel.SetComboStrength(c, true);
            m.DesignSteel.StartDesign();
            int n = 0; string[] fr = null, cb = null, es = null, ws = null; double[] ratio = null, loc = null; int[] rtype = null;
            m.DesignSteel.GetSummaryResults("ALL", ref n, ref fr, ref ratio, ref rtype, ref loc, ref cb, ref es, ref ws, eItemType.Group);
            var porSec = new Dictionary<string, double>();
            double rmax = 0; string fmax = "", cmax = "";
            for (int i = 0; i < n; i++)
            {
                string prop = "", sAuto = ""; m.FrameObj.GetSection(fr[i], ref prop, ref sAuto);
                double prev; porSec[prop] = porSec.TryGetValue(prop, out prev) ? Math.Max(prev, ratio[i]) : ratio[i];
                if (ratio[i] > rmax) { rmax = ratio[i]; fmax = prop; cmax = cb[i]; }
            }
            J.Append(",\"DC_max\":" + F(rmax) + ",\"DC_seccion\":\"" + fmax + "\",\"DC_combo\":\"" + cmax + "\",\"DC_por_seccion\":{" +
                     string.Join(",", porSec.Select(kv => "\"" + kv.Key + "\":" + F(kv.Value))) + "}");
            L("D/C max " + rmax.ToString("F3", IC) + " en " + fmax + " " + cmax);
        }
        J.Append("}");
        File.WriteAllText(Path.Combine(dirRes, caso + ".json"), J.ToString(), new UTF8Encoding(false));
        m.File.Save(sdb);
        sap.ApplicationExit(false);
        File.WriteAllText(Path.Combine(dirRes, caso + "_log.txt"), log.ToString(), new UTF8Encoding(false));
        return log.ToString();
    }
}
