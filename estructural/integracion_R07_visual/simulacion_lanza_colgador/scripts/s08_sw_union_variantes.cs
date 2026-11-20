// Variantes de refuerzo de la unión transversal–cubo (W5) en SOLIDWORKS Simulation 2024 (12/11/2026).
// Geometrías de s07 (BASE, S40, S80, CART, LENG). Mismo apoyo, material, contacto y carga que s06: eje empotrado en Z2840,
// golpe de 1 000 N en el brazo A a Z1400 como carga remota distribuida en la cara de la brida A, contacto pegado global,
// 316L a 62 °C (hipótesis de B1). Malla global 8/1,5 mm; control de malla h en TRANSV_FINO (x = 170–272), en los cordones
// W5_*_FINO y en los cordones del refuerzo WR_*.
// Para cada estudio escribe un CSV con los nodos de la superficie de TRANSV_FINO (coordenadas SW, von Mises y las seis
// componentes, en MPa), que procesa s09. Solo crea archivos nuevos.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.cosworks;

public static class ResolutorSwVariantes
{
    static string carpeta;
    public static void Registrar(string dir)
    {
        carpeta = dir;
        AppDomain.CurrentDomain.AssemblyResolve += delegate(object s, ResolveEventArgs a)
        {
            string p = Path.Combine(carpeta, new System.Reflection.AssemblyName(a.Name).Name + ".dll");
            return File.Exists(p) ? System.Reflection.Assembly.LoadFrom(p) : null;
        };
    }
}

public static class SwVariantes
{
    static string logPath;
    static void L(string s) { Console.WriteLine(s); File.AppendAllText(logPath, s + System.Environment.NewLine); }
    static string F(double x) { return x.ToString("0.####", CultureInfo.InvariantCulture); }
    static double D(string s) { return double.Parse(s, CultureInfo.InvariantCulture); }

    public static string Ejecutar(string carpeta, string variantes, string estudios)
    {
        string res = Path.Combine(carpeta, "resultados", "union_variantes"); Directory.CreateDirectory(res);
        string sello = DateTime.Now.ToString("HHmmss");
        logPath = Path.Combine(res, "sw_variantes_log_" + sello + ".txt");
        try
        {
            Dictionary<string, double[]> cargas = new Dictionary<string, double[]>();
            foreach (string ln in File.ReadAllLines(Path.Combine(carpeta, "geometria", "cargas.csv")))
            {
                string[] c = ln.Split(';');
                if (c[0].StartsWith("U_GOLPE")) cargas[c[0]] = new double[] { D(c[3]), D(c[4]), D(c[5]), D(c[6]), D(c[7]), D(c[8]) };
            }
            SldWorks sw = (SldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"));
            sw.Visible = true;
            object ao = sw.GetAddInObject("SldWorks.Simulation");
            for (int k = 0; ao == null && k < 3; k++)
            {
                sw.LoadAddIn(@"C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\Simulation\cosworks.dll");
                System.Threading.Thread.Sleep(8000); ao = sw.GetAddInObject("SldWorks.Simulation");
            }
            if (ao == null) { L("ERROR: sin Simulation"); return "error"; }
            CosmosWorks cw = ((CwAddincallback)ao).CosmosWorks;
            L("SolidWorks " + sw.RevisionNumber() + " | variantes " + variantes + " | estudios " + estudios);

            foreach (string var in variantes.Split(','))
            {
                int err = 0, e2 = 0, w2 = 0;
                string gdir = Path.Combine(carpeta, "geometria", "variantes_w5");
                List<string[]> refs = new List<string[]>();
                foreach (string ln in File.ReadAllLines(Path.Combine(gdir, "cuerpos_" + var + ".csv")))
                    if (!ln.StartsWith("nombre")) refs.Add(ln.Split(';'));
                object[] abiertos = (object[])sw.GetDocuments();
                if (abiertos != null) foreach (object o in abiertos) { string t = ((ModelDoc2)o).GetTitle(); if (t.StartsWith("UNION_")) sw.CloseDoc(t); }
                string step = Path.Combine(gdir, "UNION_" + var + ".step");
                ModelDoc2 doc = (ModelDoc2)sw.LoadFile4(step, "r", (ImportStepData)sw.GetImportFileData(step), ref err);
                if (doc == null) { L("ERROR: no se abrió " + step + " err=" + err); continue; }
                string prt = Path.Combine(carpeta, "modelo", "UNION_W5_" + var + "_" + sello + ".SLDPRT");
                L("##### " + var + " | guardado " + doc.Extension.SaveAs3(prt, 0, 1, null, null, ref e2, ref w2) + ": " + prt);
                Dictionary<string, Body2> cu = new Dictionary<string, Body2>();
                foreach (object o in (object[])((PartDoc)doc).GetBodies2((int)swBodyType_e.swSolidBody, false))
                {
                    Body2 b = (Body2)o; double[] mp = (double[])b.GetMassProperties(7950.0);
                    double vol = mp[3] * 1e9, x = mp[0] * 1000, y = mp[1] * 1000, z = mp[2] * 1000, dmin = 1e9; string mejor = null;
                    foreach (string[] r in refs)
                    {
                        double d = Math.Sqrt(Math.Pow(D(r[2]) - x, 2) + Math.Pow(D(r[3]) - y, 2) + Math.Pow(D(r[4]) - z, 2)) + 1000 * Math.Abs(vol - D(r[1])) / D(r[1]);
                        if (d < dmin) { dmin = d; mejor = r[0]; }
                    }
                    if (dmin < 5 && !cu.ContainsKey(mejor)) cu[mejor] = b; else L("  sin identificar: vol " + F(vol) + " (" + F(x) + "; " + F(y) + "; " + F(z) + ")");
                }
                L("cuerpos identificados " + cu.Count + " de " + refs.Count);
                Face2 emp = null, brida = null;
                foreach (object o in (object[])cu["EJE"].GetFaces())
                { Face2 f = (Face2)o; double[] c = (double[])f.GetBox(); if (((Surface)f.GetSurface()).IsPlane() && Math.Abs(c[1] * 1000 - 2840) < 0.01 && Math.Abs(c[4] * 1000 - 2840) < 0.01) emp = f; }
                foreach (object o in (object[])cu["BRIDA_A"].GetFaces())
                { Face2 f = (Face2)o; double[] c = (double[])f.GetBox(); if (((Surface)f.GetSurface()).IsPlane() && Math.Abs(c[0] * 1000 + 299.25) < 0.01 && Math.Abs(c[3] * 1000 + 299.25) < 0.01) brida = f; }
                L("cara de empotramiento " + (emp != null) + "; cara de la brida A " + (brida != null));
                if (emp == null || brida == null || cu.Count != refs.Count) { L("ERROR: identificación incompleta en " + var); continue; }
                List<object> finos = new List<object>();
                foreach (string n in new string[] { "TRANSV_FINO", "W5_POS_FINO", "W5_NEG_FINO", "WR_POS", "WR_NEG" })
                    if (cu.ContainsKey(n)) finos.AddRange((object[])cu[n].GetFaces());
                object[] carasTubo = (object[])cu["TRANSV_FINO"].GetFaces();

                CWStudyManager sm = cw.ActiveDoc.StudyManager;
                foreach (string ec in estudios.Split(','))
                {
                    string[] pe = ec.Split(':');
                    string caso = pe[0] == "FUERA" ? "U_GOLPE_FUERA_PLANO" : "U_GOLPE_EN_PLANO";
                    double h = D(pe[1]);
                    string est = pe[0] + "_h" + pe[1].Replace(".", "p");
                    L("=== " + var + " " + est + " (" + caso + ", malla fina " + F(h) + " mm)");
                    CWStudy st = sm.CreateNewStudy3(est, (int)swsAnalysisStudyType_e.swsAnalysisStudyTypeStatic, 0, out err);
                    CWSolidComponent comp = st.SolidManager.GetComponentAt(0, out err);
                    for (int i = 0; i < comp.SolidBodyCount; i++)
                    {
                        CWSolidBody sb = comp.GetSolidBodyAt(i, out err); CWMaterial mat = sb.GetDefaultMaterial();
                        mat.MaterialUnits = 0; mat.MaterialName = "AISI 316L a 62 C (hipotesis)";
                        mat.SetPropertyByName("EX", 1.93e11, 0); mat.SetPropertyByName("NUXY", 0.30, 0); mat.SetPropertyByName("DENS", 7950.0, 0);
                        mat.SetPropertyByName("SIGYLD", 1.53e8, 0); mat.SetPropertyByName("SIGXT", 4.85e8, 0); sb.SetSolidBodyMaterial(mat);
                    }
                    st.ContactManager.SetGlobalContact((int)swsContactType_e.swsContactTypeBonded, 0);
                    CWLoadsAndRestraintsManager lbc = st.LoadsAndRestraintsManager;
                    lbc.AddRestraint((int)swsRestraintType_e.swsRestraintTypeFixed, new object[] { emp }, null, out err);
                    double[] q = cargas[caso];
                    CWRemoteLoad rl = lbc.AddRemoteLoad((int)swsRemoteLoadType_e.swsRemoteLoadType_DirectLoad, new object[] { brida }, 0, q[0], q[1], q[2], out err);
                    rl.RemoteLoadBeginEdit();
                    rl.ConnectionType = (int)swsRemoteLoadConnectionType_e.swsRemoteLoadConnectionType_Distributed;
                    rl.ForceUnit = 0; rl.MomentUnit = 0;
                    rl.SetForceOrTranslationValues2(true, true, q[3], true, q[4], true, q[5]);
                    rl.SetMomentOrRotationValues2(false, false, 0, false, 0, false, 0);
                    L("carga remota en (" + F(q[0]) + "; " + F(q[1]) + "; " + F(q[2]) + ") F (" + F(q[3]) + "; " + F(q[4]) + "; " + F(q[5]) + ") EndEdit=" + rl.RemoteLoadEndEdit());
                    CWMesh mesh = st.Mesh;
                    mesh.MesherType = (int)swsMesherType_e.swsMesherTypeAlternateCB;
                    mesh.Quality = (int)swsMeshQuality_e.swsMeshQualityHigh;
                    mesh.Unit = (int)swsLinearUnit_e.swsLinearUnitMillimeters;
                    mesh.MaxElementSize = 8.0; mesh.MinElementSize = 1.5; mesh.MinElementsInCircle = 8; mesh.GrowthRatio = 1.4;
                    CWMeshControl mc = mesh.ApplyMeshControl(finos.ToArray(), out err);
                    if (mc == null) L("  ApplyMeshControl err=" + err);
                    else
                    {
                        mc.MeshControlBeginEdit(); mc.Units = (int)swsLinearUnit_e.swsLinearUnitMillimeters; mc.ElementSize = h; mc.Ratio = 1.3;
                        mc.MinimumElementSizeForBlendedCurveMesher = h; mc.MinNumOfElementsPerCircleForBlendedCurveMesher = 16;
                        L("  control de malla " + F(h) + " mm en " + finos.Count + " caras (EndEdit=" + mc.MeshControlEndEdit() + ")");
                    }
                    DateTime t0 = DateTime.Now;
                    int em = st.CreateMesh((int)swsLinearUnit_e.swsLinearUnitMillimeters, 8.0, 1.5);
                    L("CreateMesh err=" + em + " | nodos " + mesh.NodeCount + ", elementos " + mesh.ElementCount + " (" + F((DateTime.Now - t0).TotalSeconds) + " s)");
                    if (em != 0) continue;
                    t0 = DateTime.Now;
                    int ea = st.RunAnalysis();
                    L("RunAnalysis err=" + ea + " (" + F((DateTime.Now - t0).TotalSeconds) + " s)");
                    doc.Save3(1, ref e2, ref w2);
                    if (ea != 0) continue;
                    CWResults r = st.Results;
                    Dictionary<int, double[]> nod = Nodos(mesh);
                    foreach (string g in new string[] { "TRANSV_FINO", "W5_POS_FINO", "W5_NEG_FINO", "WR_POS", "WR_NEG", "CARTELA", "LENGUETA", "CUBO", "TRANSV_CENTRO", "TRANSV_EXT" })
                        if (cu.ContainsKey(g)) Maximo(r, nod, g, (object[])cu[g].GetFaces());
                    // nodos de la superficie del tubo fino: von Mises y componentes (MPa)
                    Dictionary<int, double[]> val = new Dictionary<int, double[]>();
                    int[] compo = { 9, 0, 1, 2, 3, 4, 5 };
                    for (int k = 0; k < compo.Length; k++)
                    {
                        double[] v = AD(r.GetStressForEntities3(true, compo[k], 1, null, carasTubo, 3, 0, 0, false, out err));
                        for (int i = 0; v != null && i + 1 < v.Length; i += 2)
                        {
                            int id = (int)v[i]; double[] a;
                            if (!val.TryGetValue(id, out a)) { a = new double[7]; for (int j = 0; j < 7; j++) a[j] = double.NaN; val[id] = a; }
                            a[k] = v[i + 1];
                        }
                    }
                    StringBuilder sb2 = new StringBuilder("nodo;X;Y;Z;VON;SX;SY;SZ;TXY;TXZ;TYZ\n");
                    foreach (KeyValuePair<int, double[]> kv in val)
                    {
                        double[] p; if (!nod.TryGetValue(kv.Key, out p)) continue;
                        sb2.Append(kv.Key).Append(';').Append(F(p[0])).Append(';').Append(F(p[1])).Append(';').Append(F(p[2]));
                        foreach (double s in kv.Value) sb2.Append(';').Append(s.ToString("0.###", CultureInfo.InvariantCulture));
                        sb2.Append('\n');
                    }
                    string csv = Path.Combine(res, "nodos_" + var + "_" + est + ".csv");
                    File.WriteAllText(csv, sb2.ToString());
                    L("nodos de la superficie del tubo fino: " + val.Count + " -> " + Path.GetFileName(csv));
                    CWPlot pv = r.CreatePlot((int)swsPlotResultTypes_e.swsResultStress, 9, 3, false, out err);
                    if (pv != null)
                    {
                        pv.SetPlotTitle("Von Mises (MPa) - union W5 - " + var + " " + est); pv.ShowDeformedPlot(false, 0, 1.0, true); pv.ActivatePlot();
                        doc.ShowNamedView2("*Isometric", (int)swStandardViews_e.swIsometricView); doc.ViewZoomtofit2();
                        doc.ViewZoomTo2(-0.30, 1.69, -0.07, -0.16, 1.84, 0.07); doc.GraphicsRedraw2();
                        L("imagen " + doc.Extension.SaveAs3(Path.Combine(res, "VM_" + var + "_" + est + ".jpg"), 0, 1, null, null, ref e2, ref w2));
                    }
                    doc.Save3(1, ref e2, ref w2);
                }
            }
        }
        catch (Exception ex) { L("EXCEPCION: " + ex); }
        return "fin";
    }

    static Dictionary<int, double[]> Nodos(CWMesh mesh)
    {
        Dictionary<int, double[]> d = new Dictionary<int, double[]>();
        double[] a = AD(mesh.GetNodes()); int n = mesh.NodeCount;
        int paso = a.Length == 4 * n ? 4 : 3;
        for (int i = 0; i + paso - 1 < a.Length; i += paso)
        {
            int id = paso == 4 ? (int)a[i] : i / 3 + 1; int o = paso == 4 ? 1 : 0;
            d[id] = new double[] { a[i + o] * 1000, a[i + o + 1] * 1000, a[i + o + 2] * 1000 };
        }
        return d;
    }

    static void Maximo(CWResults r, Dictionary<int, double[]> nod, string et, object[] caras)
    {
        int err; double[] v = AD(r.GetStressForEntities3(true, 9, 1, null, caras, 3, 0, 0, false, out err));
        double m = -1; int n = -1;
        for (int i = 0; v != null && i + 1 < v.Length; i += 2) if (v[i + 1] > m) { m = v[i + 1]; n = (int)v[i]; }
        double[] p; string pos = nod.TryGetValue(n, out p) ? "(" + F(p[0]) + "; " + F(p[1]) + "; " + F(p[2]) + ") SW" : "?";
        L(et + ": von Mises máx " + F(m) + " MPa en " + pos);
    }

    static double[] AD(object o)
    {
        if (o == null) return null; double[] d = o as double[]; if (d != null) return d;
        Array a = o as Array; if (a == null) return null;
        double[] r = new double[a.Length]; for (int i = 0; i < a.Length; i++) r[i] = Convert.ToDouble(a.GetValue(i), CultureInfo.InvariantCulture); return r;
    }
}
