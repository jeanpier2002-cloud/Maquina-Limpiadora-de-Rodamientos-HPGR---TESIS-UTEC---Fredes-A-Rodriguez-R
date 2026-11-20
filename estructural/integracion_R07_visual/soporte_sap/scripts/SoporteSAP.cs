// Soporte superior del rotor y del motorreductor (R07): modelo parametrico de SAP2000 v27 por API (N, mm).
// Geometria del CAD R07 V11 (soporte R04: 4 columnas, celosia en X por costado, 2 vigas, cartucho) y cargas de R03
// (MEMORIA_CIERRE_R03.md 6.3-6.4; RESULTADOS_CALCULOS_R03.json). El cartucho, la mensula y el motor se modelan como cuerpo
// rigido apoyado en las vigas en x = +-230 (placa base de 460 mm). Bases articuladas. Diseno AISC 360-16 (LRFD).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using SAP2000v1;

public static class SoporteSAP
{
    static cSapModel m;
    static CultureInfo IC = CultureInfo.InvariantCulture;
    static StringBuilder log = new StringBuilder();
    static void L(string s) { log.AppendLine(s); Console.WriteLine(s); }
    static string F(double v) { return v.ToString("0.######", IC); }

    static string Barra(double x1, double y1, double z1, double x2, double y2, double z2, string prop, string nombre)
    {
        string n = "";
        int r = m.FrameObj.AddByCoord(x1, y1, z1, x2, y2, z2, ref n, prop, nombre, "Global");
        if (r != 0) L("AddByCoord fallo " + nombre);
        return n;
    }

    static void Rotula(string n, bool inicio, bool fin)
    {
        bool[] ii = { false, false, false, false, inicio, inicio };
        bool[] jj = { false, false, false, fin, fin, fin };
        double[] a = new double[6], b = new double[6];
        m.FrameObj.SetReleases(n, ref ii, ref jj, ref a, ref b);
    }

    static string Punto(double x, double y, double z, string nombre)
    {
        string n = "";
        m.PointObj.AddCartesian(x, y, z, ref n, nombre, "Global", false, 0);
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

    // secciones: "TUBE:h:b:t", "ANGLE:b:b:t", "PIPE:d:t"
    static void Seccion(string nombre, string def)
    {
        string[] p = def.Split(':');
        double a = double.Parse(p[1], IC), b = p.Length > 2 ? double.Parse(p[2], IC) : 0, c = p.Length > 3 ? double.Parse(p[3], IC) : 0;
        if (p[0] == "TUBE") m.PropFrame.SetTube(nombre, "A36", a, b, c, c, -1, "", "");
        else if (p[0] == "ANGLE") m.PropFrame.SetAngle(nombre, "A36", a, b, c, c, -1, "", "");
        else if (p[0] == "PIPE") m.PropFrame.SetPipe(nombre, "A36", a, b, -1, "", "");
    }

    public static string Correr(string caso, string dirModelos, string dirRes, double xc, double yc, string col, string viga, string lac,
                                double zViga, bool visible, bool empotrar, double cartela, string cartSec, bool planta)
    {
        log.Clear();
        string prog = @"C:\Program Files\Computers and Structures\SAP2000 27";
        cHelper h = new Helper();
        cOAPI sap = h.CreateObject(Path.Combine(prog, "SAP2000.exe"));
        sap.ApplicationStart(eUnits.N_mm_C, visible, "");
        m = sap.SapModel;
        m.InitializeNewModel(eUnits.N_mm_C);
        m.File.NewBlank();
        // material A36 (hipotesis del proyecto), peso 7850 kg/m3
        m.PropMaterial.SetMaterial("A36", eMatType.Steel, -1, "", "");
        m.PropMaterial.SetMPIsotropic("A36", 200000, 0.3, 1.17e-5, 0);
        m.PropMaterial.SetWeightAndMass("A36", 1, 7.6982e-5, 0);
        m.PropMaterial.SetOSteel_1("A36", 250, 400, 275, 440, 1, 1, 0.02, 0.1, 0.2, -0.1, 0);
        Seccion("COL", col); Seccion("VIGA", viga); Seccion("LAC", lac); if (cartela > 0) Seccion("CART", cartSec);

        double z1 = 150, z2 = 1470, z3 = 2690;
        var cols = new List<string>();
        var vigas = new List<string>();
        var lacs = new List<string>();
        foreach (double sx in new[] { -1.0, 1.0 })
            foreach (double sy in new[] { -1.0, 1.0 })
            {
                double x = sx * xc, y = sy * yc;
                double[] zs = cartela > 0 && zViga - cartela > z3 + 1 ? new[] { 0, z1, z2, z3, zViga - cartela, zViga }
                            : cartela > 0 ? new[] { 0, z1, z2, zViga - cartela, z3, zViga } : new[] { 0, z1, z2, z3, zViga };
                Array.Sort(zs);
                for (int i = 0; i < zs.Length - 1; i++) cols.Add(Barra(x, y, zs[i], x, y, zs[i + 1], "COL", ""));
            }
        // celosia en X por costado: 2 paneles (z1-z2, z2-z3) y travesano en z2; diagonales partidas en el cruce
        foreach (double sx in new[] { -1.0, 1.0 })
        {
            double x = sx * xc;
            foreach (double[] pz in new[] { new[] { z1, z2 }, new[] { z2, z3 } })
            {
                double zm = (pz[0] + pz[1]) / 2;
                string a1 = Barra(x, -yc, pz[0], x, 0, zm, "LAC", ""); Rotula(a1, true, false);
                string a2 = Barra(x, 0, zm, x, yc, pz[1], "LAC", ""); Rotula(a2, false, true);
                string b1 = Barra(x, yc, pz[0], x, 0, zm, "LAC", ""); Rotula(b1, true, false);
                string b2 = Barra(x, 0, zm, x, -yc, pz[1], "LAC", ""); Rotula(b2, false, true);
                lacs.AddRange(new[] { a1, a2, b1, b2 });
            }
            string t = Barra(x, -yc, z2, x, yc, z2, "LAC", ""); Rotula(t, true, true); lacs.Add(t);
        }
        // vigas con nudos en x = -230, 0, +230 (apoyo del cartucho) y, si hay cartelas, en x = +-(xc - cartela)
        foreach (double sy in new[] { -1.0, 1.0 })
        {
            double y = sy * yc;
            double[] xs = cartela > 0 ? new[] { -xc, -xc + cartela, -230, 0, 230, xc - cartela, xc } : new[] { -xc, -230, 0, 230, xc };
            for (int i = 0; i < xs.Length - 1; i++) vigas.Add(Barra(xs[i], y, zViga, xs[i + 1], y, zViga, "VIGA", ""));
        }
        // cartelas a 45 grados en el plano de cada portico (nudo viga-poste), articuladas en sus extremos
        if (cartela > 0)
        {
            foreach (double sx in new[] { -1.0, 1.0 })
                foreach (double sy in new[] { -1.0, 1.0 })
                {
                    double x = sx * xc, y = sy * yc;
                    // nudo intermedio en el poste a zViga - cartela
                    string c = Barra(x, y, zViga - cartela, x - sx * cartela, y, zViga, "CART", ""); Rotula(c, true, true);
                }
        }
        // arriostramiento en planta entre las dos vigas (X en cada tramo lateral al cartucho), articulado
        if (planta)
            foreach (double[] t in new[] { new[] { -xc, -230.0 }, new[] { 230.0, xc } })
            {
                string d1 = Barra(t[0], -yc, zViga, t[1], yc, zViga, "LAC", ""); Rotula(d1, true, true);
                string d2 = Barra(t[0], yc, zViga, t[1], -yc, zViga, "LAC", ""); Rotula(d2, true, true);
            }
        // bases articuladas o empotradas
        foreach (double sx in new[] { -1.0, 1.0 })
            foreach (double sy in new[] { -1.0, 1.0 })
            {
                string b = Punto(sx * xc, sy * yc, 0, "");
                bool[] rr = empotrar ? new[] { true, true, true, true, true, true } : new[] { true, true, true, false, false, false };
                m.PointObj.SetRestraint(b, ref rr, eItemType.Objects);
            }
        // cuerpo rigido: cartucho, mensula y motor, apoyado en las vigas en x = +-230
        bool[] todo = { true, true, true, true, true, true };
        m.ConstraintDef.SetBody("CARTUCHO", ref todo, "Global");
        var cuerpo = new List<string>();
        foreach (double sx in new[] { -230.0, 230.0 })
            foreach (double sy in new[] { -yc, yc })
            { cuerpo.Add(Punto(sx, sy, zViga, "")); }
        string LB = Punto(0, 0, 2850, "COJ_INF"), UB = Punto(0, 0, 3450, "COJ_SUP"), CG = Punto(0, 0, 3100, "CART_CG"),
               BR = Punto(570, 0, 3150, "MENSULA_CG"), MO = Punto(800, 0, 3280, "MOTOR_CG"), PO = Punto(700, 0, 3150, "POLEA_MOTRIZ"),
               PC = Punto(0, 0, 3150, "POLEA_CONDUCIDA");
        cuerpo.AddRange(new[] { LB, UB, CG, BR, MO, PO, PC });
        foreach (string p in cuerpo) { string cn = "CARTUCHO"; m.PointObj.SetConstraint(p, ref cn, eItemType.Objects, true); }

        // patrones de carga
        m.LoadPatterns.Add("BELT", eLoadPatternType.Other, 0, true);
        m.LoadPatterns.Add("TORQ", eLoadPatternType.Other, 0, true);
        foreach (string a in new[] { "AXP", "AXN", "AYP", "AYN" }) m.LoadPatterns.Add(a, eLoadPatternType.Other, 0, true);
        // DEAD: peso propio + cartucho y apoyos (volumen CAD x 7850: 23,234 L -> 1 789 N) + mensula y tornapuntas (5,347 L -> 412 N)
        //       + motorreductor SF47 con brida 21 kg + polea y cubo ~10 kg (304 N) + rotor 180 kg (1 766 N) en el cojinete inferior
        Carga(CG, "DEAD", 0, 0, -1789, 0, 0, 0);
        Carga(BR, "DEAD", 0, 0, -412, 0, 0, 0);
        Carga(MO, "DEAD", 0, 0, -304, 0, 0, 0);
        Carga(LB, "DEAD", 0, 0, -1766, 0, 0, 0);
        // BELT: envolvente radial 2T0 + Ft = 1 071 N (T = 60 N m, T0 = 300 N); tira de la polea conducida hacia el motor (+x)
        //       y del motor hacia el eje (-x): fuerzas internas al cuerpo rigido (se incluyen para el diseno local futuro)
        Carga(PC, "BELT", 1071, 0, 0, 0, 0, 0);
        Carga(PO, "BELT", -1071, 0, 0, 0, 0, 0);
        // TORQ: par del rotor bloqueado (limitador a 60 N m en el rotor, D-062) reaccionado por la estructura
        Carga(CG, "TORQ", 0, 0, 0, 0, 0, 60000);
        // accidental: 1 000 N horizontal a z 1400 sobre la U, trasladado al cojinete inferior (z 2850) con su momento,
        // mas el peso excentrico 1 766 N x 50 mm en el mismo sentido
        double Fa = 1000, brazo = 2850 - 1400, Mexc = 1766 * 50;
        Carga(LB, "AXP", Fa, 0, 0, 0, -(Fa * brazo + Mexc), 0);
        Carga(LB, "AXN", -Fa, 0, 0, 0, (Fa * brazo + Mexc), 0);
        Carga(LB, "AYP", 0, Fa, 0, (Fa * brazo + Mexc), 0, 0);
        Carga(LB, "AYN", 0, -Fa, 0, -(Fa * brazo + Mexc), 0, 0);

        // casos de analisis lineales para cada patron (NewBlank solo trae DEAD y MODAL)
        foreach (string a in new[] { "BELT", "TORQ", "AXP", "AXN", "AYP", "AYN" })
        {
            m.LoadCases.StaticLinear.SetCase(a);
            string[] lt = { "Load" }; string[] ln = { a }; double[] sf = { 1 };
            m.LoadCases.StaticLinear.SetLoads(a, 1, ref lt, ref ln, ref sf);
        }
        // combinaciones (AISC/ASCE 7 LRFD; accidental como extraordinaria con factor 1,0)
        Combo("U1", "DEAD", 1.4);
        Combo("U2", "DEAD", 1.2, "BELT", 1.6, "TORQ", 1.6);
        foreach (string a in new[] { "AXP", "AXN", "AYP", "AYN" }) Combo("U3_" + a, "DEAD", 1.2, "BELT", 1.0, "TORQ", 1.0, a, 1.0);
        Combo("S1", "DEAD", 1.0, "BELT", 1.0, "TORQ", 1.0);
        foreach (string a in new[] { "AXP", "AXN", "AYP", "AYN" }) Combo("S2_" + a, "DEAD", 1.0, "BELT", 1.0, "TORQ", 1.0, a, 1.0);
        // masa: elementos + cargas DEAD
        string[] mp = { "DEAD" }; double[] ms = { 1 };
        m.SourceMass.SetMassSource("MASA", true, false, true, true, 1, ref mp, ref ms);
        m.LoadCases.ModalEigen.SetNumberModes("MODAL", 12, 1);

        Directory.CreateDirectory(dirModelos); Directory.CreateDirectory(dirRes);
        string sdb = Path.Combine(dirModelos, caso + ".sdb");
        m.File.Save(sdb);
        int ra = m.Analyze.RunAnalysis();
        L("analisis " + ra);

        var J = new StringBuilder();
        J.Append("{\"caso\":\"" + caso + "\",\"empotrado\":" + (empotrar ? "true" : "false") + ",\"cartela\":" + F(cartela) + ",\"cartSec\":\"" + cartSec + "\",\"planta\":" + (planta ? "true" : "false") + ",\"xc\":" + F(xc) + ",\"yc\":" + F(yc) + ",\"zViga\":" + F(zViga) +
                 ",\"col\":\"" + col + "\",\"viga\":\"" + viga + "\",\"lac\":\"" + lac + "\"");
        // barras: coordenadas, seccion y masa
        int nf = 0; string[] fn = null;
        m.FrameObj.GetNameList(ref nf, ref fn);
        double masa = 0;
        J.Append(",\"barras\":[");
        for (int i = 0; i < nf; i++)
        {
            string p1 = "", p2 = ""; m.FrameObj.GetPoints(fn[i], ref p1, ref p2);
            double x1 = 0, y1 = 0, z1c = 0, x2 = 0, y2 = 0, z2c = 0;
            m.PointObj.GetCoordCartesian(p1, ref x1, ref y1, ref z1c, "Global");
            m.PointObj.GetCoordCartesian(p2, ref x2, ref y2, ref z2c, "Global");
            string prop = "", sAuto = ""; m.FrameObj.GetSection(fn[i], ref prop, ref sAuto);
            double A = 0, As2 = 0, As3 = 0, Tq = 0, I22 = 0, I33 = 0, S22 = 0, S33 = 0, Z22 = 0, Z33 = 0, R22 = 0, R33 = 0;
            m.PropFrame.GetSectProps(prop, ref A, ref As2, ref As3, ref Tq, ref I22, ref I33, ref S22, ref S33, ref Z22, ref Z33, ref R22, ref R33);
            double Lg = Math.Sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1) + (z2c - z1c) * (z2c - z1c));
            masa += A * Lg * 7.85e-6;
            J.Append((i > 0 ? "," : "") + "{\"n\":\"" + fn[i] + "\",\"p1\":\"" + p1 + "\",\"p2\":\"" + p2 + "\",\"sec\":\"" + prop + "\",\"c\":[" +
                     F(x1) + "," + F(y1) + "," + F(z1c) + "," + F(x2) + "," + F(y2) + "," + F(z2c) + "],\"A\":" + F(A) + "}");
        }
        J.Append("],\"masa_kg\":" + F(masa));
        L("masa de barras kg " + masa.ToString("F1", IC));

        // desplazamientos de todos los nudos por combinacion de servicio y por modo
        int np = 0; string[] pn = null; m.PointObj.GetNameList(ref np, ref pn);
        J.Append(",\"nudos\":{");
        for (int i = 0; i < np; i++)
        {
            double x = 0, y = 0, z = 0; m.PointObj.GetCoordCartesian(pn[i], ref x, ref y, ref z, "Global");
            J.Append((i > 0 ? "," : "") + "\"" + pn[i] + "\":[" + F(x) + "," + F(y) + "," + F(z) + "]");
        }
        J.Append("}");
        var salidas = new List<string> { "S1", "S2_AXP", "S2_AXN", "S2_AYP", "S2_AYN", "U2", "U3_AXP", "U3_AYP" };
        J.Append(",\"despl\":{");
        bool primero = true;
        foreach (string c in salidas)
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            m.Results.Setup.SetComboSelectedForOutput(c, true);
            J.Append((primero ? "" : ",") + "\"" + c + "\":{"); primero = false;
            for (int i = 0; i < np; i++)
            {
                int n = 0; string[] o = null, e = null, lc = null, st = null; double[] sn = null, u1 = null, u2 = null, u3 = null, r1 = null, r2 = null, r3 = null;
                m.Results.JointDispl(pn[i], eItemTypeElm.ObjectElm, ref n, ref o, ref e, ref lc, ref st, ref sn, ref u1, ref u2, ref u3, ref r1, ref r2, ref r3);
                if (n > 0) J.Append((i > 0 ? "," : "") + "\"" + pn[i] + "\":[" + F(u1[0]) + "," + F(u2[0]) + "," + F(u3[0]) + "," + F(r1[0]) + "," + F(r2[0]) + "," + F(r3[0]) + "]");
            }
            J.Append("}");
        }
        J.Append("}");
        // modos
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            m.Results.Setup.SetCaseSelectedForOutput("MODAL", true);
            int n = 0; string[] lc = null, st = null; double[] sn = null, per = null, fr = null, cf = null, ev = null;
            m.Results.ModalPeriod(ref n, ref lc, ref st, ref sn, ref per, ref fr, ref cf, ref ev);
            J.Append(",\"frecuencias_Hz\":[");
            for (int i = 0; i < n; i++) J.Append((i > 0 ? "," : "") + F(fr[i]));
            J.Append("]");
            L("f1..f3 Hz " + (n > 2 ? fr[0].ToString("F2", IC) + " " + fr[1].ToString("F2", IC) + " " + fr[2].ToString("F2", IC) : "?"));
            J.Append(",\"modos\":[");
            for (int k = 0; k < Math.Min(4, n); k++)
            {
                J.Append((k > 0 ? "," : "") + "{");
                for (int i = 0; i < np; i++)
                {
                    int nn = 0; string[] o = null, e = null, lc2 = null, st2 = null; double[] sn2 = null, u1 = null, u2 = null, u3 = null, r1 = null, r2 = null, r3 = null;
                    m.Results.JointDispl(pn[i], eItemTypeElm.ObjectElm, ref nn, ref o, ref e, ref lc2, ref st2, ref sn2, ref u1, ref u2, ref u3, ref r1, ref r2, ref r3);
                    for (int q = 0; q < nn; q++)
                        if (Math.Abs(sn2[q] - (k + 1)) < 0.01)
                            J.Append((i > 0 ? "," : "") + "\"" + pn[i] + "\":[" + F(u1[q]) + "," + F(u2[q]) + "," + F(u3[q]) + "]");
                }
                J.Append("}");
            }
            J.Append("]");
            // masa participante por modo (Ux, Uy, Uz, Rz)
            int nm = 0; string[] lcm = null, stm = null; double[] snm = null, pm = null, ux = null, uy = null, uz = null, sux = null, suy = null, suz = null,
                rx = null, ry = null, rz = null, srx = null, sry = null, srz = null;
            m.Results.ModalParticipatingMassRatios(ref nm, ref lcm, ref stm, ref snm, ref pm, ref ux, ref uy, ref uz, ref sux, ref suy, ref suz,
                ref rx, ref ry, ref rz, ref srx, ref sry, ref srz);
            J.Append(",\"participacion\":[");
            for (int i = 0; i < nm; i++)
                J.Append((i > 0 ? "," : "") + "[" + F(ux[i]) + "," + F(uy[i]) + "," + F(uz[i]) + "," + F(rz[i]) + "]");
            J.Append("]");
        }
        // reacciones en las bases (envolvente de las combinaciones de servicio)
        J.Append(",\"reacciones\":{");
        primero = true;
        foreach (string c in new[] { "S1", "S2_AXP", "S2_AXN", "S2_AYP", "S2_AYN", "U2", "U3_AXP", "U3_AXN", "U3_AYP", "U3_AYN" })
        {
            m.Results.Setup.DeselectAllCasesAndCombosForOutput();
            m.Results.Setup.SetComboSelectedForOutput(c, true);
            int n = 0; string[] o = null, e = null, lc = null, st = null; double[] sn = null, f1 = null, f2 = null, f3 = null, m1 = null, m2 = null, m3 = null;
            m.Results.JointReact("ALL", eItemTypeElm.GroupElm, ref n, ref o, ref e, ref lc, ref st, ref sn, ref f1, ref f2, ref f3, ref m1, ref m2, ref m3);
            J.Append((primero ? "" : ",") + "\"" + c + "\":["); primero = false;
            for (int i = 0; i < n; i++) J.Append((i > 0 ? "," : "") + "[\"" + o[i] + "\"," + F(f1[i]) + "," + F(f2[i]) + "," + F(f3[i]) + "]");
            J.Append("]");
        }
        J.Append("}");
        // diseno AISC 360-16
        m.DesignSteel.SetCode("AISC 360-16");
        foreach (string c in new[] { "U1", "U2", "U3_AXP", "U3_AXN", "U3_AYP", "U3_AYN" }) m.DesignSteel.SetComboStrength(c, true);
        int rd = m.DesignSteel.StartDesign();
        L("diseno " + rd);
        {
            int n = 0; string[] fr = null, cb = null, es = null, ws = null; double[] ratio = null, loc = null; int[] rtype = null;
            m.DesignSteel.GetSummaryResults("ALL", ref n, ref fr, ref ratio, ref rtype, ref loc, ref cb, ref es, ref ws, eItemType.Group);
            J.Append(",\"diseno\":[");
            double rmax = 0; string fmax = "";
            for (int i = 0; i < n; i++)
            {
                J.Append((i > 0 ? "," : "") + "[\"" + fr[i] + "\"," + F(ratio[i]) + ",\"" + cb[i] + "\",\"" + (es[i] ?? "").Replace("\"", "'") + "\"]");
                if (ratio[i] > rmax) { rmax = ratio[i]; fmax = fr[i]; }
            }
            J.Append("]");
            L("D/C max " + rmax.ToString("F3", IC) + " en " + fmax);
        }
        J.Append("}");
        File.WriteAllText(Path.Combine(dirRes, caso + ".json"), J.ToString(), new UTF8Encoding(false));
        m.File.Save(sdb);
        sap.ApplicationExit(false);
        File.WriteAllText(Path.Combine(dirRes, caso + "_log.txt"), log.ToString(), new UTF8Encoding(false));
        return log.ToString();
    }
}
