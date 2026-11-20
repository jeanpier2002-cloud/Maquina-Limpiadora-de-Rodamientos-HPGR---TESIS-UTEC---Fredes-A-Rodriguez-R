// Brazo A de la U de aspersión (ASP-220, R07 V15B) en SOLIDWORKS Simulation 2024: reacción de los chorros y golpe accidental,
// sin y con la placa diagonal que sugirió el asesor (10/11/2026).
// Geometría: STEP del conjunto soldado (tubos huecos DN50 y DN40 Sch 10S, codo reductor, coplas, pie DN15, bloque B-MEC) en
// coordenadas del STEP: x a lo largo del transversal desde la cara de la brida, y vertical (arriba), z fuera del plano de la U.
// Unión entre piezas: contacto pegado (soldadura continua idealizada). Apoyo: cara de la brida empotrada (abulonada al cubo).
// Cargas (cargas_brazo_A.csv): cada chorro como carga remota distribuida en las caras de su copla o bloque, ubicada en el vértice
// de la boquilla; golpe de 1 000 N a Z1400 en el eje del brazo, sobre la superficie exterior del tubo DN40.
// Material 316L [HIPÓTESIS de B1]: E 193 GPa, nu 0,30, fluencia 153 MPa a 62 °C, rotura 485 MPa.
// Solo crea archivos nuevos. Deja SOLIDWORKS abierto.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.cosworks;

public static class ResolutorSwU
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

public static class SwBrazoU
{
    static string logPath = null;
    static StringBuilder log = new StringBuilder();
    static void L(string s) { log.AppendLine(s); Console.WriteLine(s); if (logPath != null) File.AppendAllText(logPath, s + System.Environment.NewLine); }
    static string F(double x) { return x.ToString("0.####", CultureInfo.InvariantCulture); }

    class Carga { public string nombre; public double x, y, z, fx, fy, fz; }

    public static string Ejecutar(string carpeta, string variantes, double hmax, double hmin)
    {
        log.Clear();
        string res = Path.Combine(carpeta, "resultados"); Directory.CreateDirectory(res);
        string mod = Path.Combine(carpeta, "modelo"); Directory.CreateDirectory(mod);
        logPath = Path.Combine(res, "sw_log_" + DateTime.Now.ToString("HHmmss") + ".txt");
        try
        {
            List<Carga> cargas = new List<Carga>();
            foreach (string ln in File.ReadAllLines(Path.Combine(carpeta, "geometria", "cargas_brazo_A.csv")))
            {
                string[] c = ln.Split(';');
                if (c[0] == "nombre") continue;
                Carga k = new Carga(); k.nombre = c[0];
                k.x = D(c[1]); k.y = D(c[2]); k.z = D(c[3]); k.fx = D(c[4]); k.fy = D(c[5]); k.fz = D(c[6]);
                cargas.Add(k);
            }
            SldWorks sw = (SldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"));
            sw.Visible = true;
            L("SolidWorks " + sw.RevisionNumber() + " | documento activo: " + (sw.ActiveDoc == null ? "ninguno" : ((ModelDoc2)sw.ActiveDoc).GetTitle()));
            object ao = sw.GetAddInObject("SldWorks.Simulation");
            for (int intento = 0; ao == null && intento < 3; intento++)
            {
                L("complemento Simulation no disponible; LoadAddIn=" + sw.LoadAddIn(@"C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\Simulation\cosworks.dll"));
                System.Threading.Thread.Sleep(8000);
                ao = sw.GetAddInObject("SldWorks.Simulation");
            }
            if (ao == null) { L("ERROR: sin el complemento Simulation"); return log.ToString(); }
            CosmosWorks cw = ((CwAddincallback)ao).CosmosWorks;
            foreach (string v in variantes.Split(','))
                Variante(sw, cw, v, Path.Combine(carpeta, "geometria", "BRAZO_" + v + "_V15B.step"),
                         Path.Combine(mod, "BRAZO_" + v + "_SW_" + DateTime.Now.ToString("HHmmss") + ".SLDPRT"), res, cargas, hmax, hmin);
        }
        catch (Exception ex) { L("EXCEPCION: " + ex); }
        return log.ToString();
    }

    static string Suf(double h) { return Math.Abs(h - 5.0) < 1e-9 ? "" : "_h" + F(h).Replace(".", "p"); }
    static double D(string s) { return double.Parse(s, CultureInfo.InvariantCulture); }
    static double[] Caja(Body2 b) { double[] c = (double[])b.GetBodyBox(); for (int i = 0; i < 6; i++) c[i] *= 1000; return c; }

    static void Variante(SldWorks sw, CosmosWorks cw, string v, string step, string prt, string res, List<Carga> cargas, double hmax, double hmin)
    {
        L("##### VARIANTE " + v + ": " + step);
        int err = 0, e2 = 0, w2 = 0;
        object[] abiertos = (object[])sw.GetDocuments();
        if (abiertos != null)
            foreach (object o in abiertos)
            {
                string tit = ((ModelDoc2)o).GetTitle();
                if (tit.StartsWith("BRAZO_" + v)) { sw.CloseDoc(tit); L("cerrado el documento anterior " + tit); }
            }
        ImportStepData imp = (ImportStepData)sw.GetImportFileData(step);
        ModelDoc2 doc = (ModelDoc2)sw.LoadFile4(step, "r", imp, ref err);
        if (doc == null) { L("ERROR LoadFile4 " + err); return; }
        L("guardado " + doc.Extension.SaveAs3(prt, 0, 1, null, null, ref e2, ref w2) + ": " + prt);
        object[] cuerpos = (object[])((PartDoc)doc).GetBodies2((int)swBodyType_e.swSolidBody, false);
        L("cuerpos: " + cuerpos.Length);
        Body2 brida = null, tubo40 = null, tubo50 = null, codo = null, placa = null;
        foreach (object o in cuerpos)
        {
            Body2 b = (Body2)o; double[] c = Caja(b);
            double vol = ((double[])b.GetMassProperties(7950.0))[3] * 1e9;
            if (c[3] < 20.6 && c[4] - c[1] > 160) brida = b;
            else if (Math.Abs(vol - 283506) < 500) tubo40 = b;
            else if (Math.Abs(vol - 259775) < 500) tubo50 = b;
            else if (Math.Abs(vol - 53533) < 300) codo = b;
            else if (Math.Abs(vol - 36225) < 300) placa = b;
        }
        L("brida " + (brida != null) + ", tubo DN50 " + (tubo50 != null) + ", codo " + (codo != null) + ", tubo DN40 " + (tubo40 != null) + ", placa " + (placa != null));
        Face2 caraBrida = null;
        foreach (object o in (object[])brida.GetFaces())
        {
            Face2 f = (Face2)o; double[] c = (double[])f.GetBox();
            if (((Surface)f.GetSurface()).IsPlane() && Math.Abs(c[0] * 1000) < 0.01 && Math.Abs(c[3] * 1000) < 0.01) caraBrida = f;
        }
        List<object> ext40 = new List<object>();
        foreach (object o in (object[])tubo40.GetFaces())
        {
            Surface s = (Surface)((Face2)o).GetSurface();
            if (s.IsCylinder() && Math.Abs(((double[])s.CylinderParams)[6] * 1000 - 24.15) < 0.05) ext40.Add(o);
        }
        L("cara de la brida " + (caraBrida != null) + "; caras exteriores del DN40: " + ext40.Count);
        if (caraBrida == null) return;

        // Cuerpo que recibe cada chorro: el más cercano al vértice de la boquilla (distancia a su caja)
        Dictionary<string, Body2> porCarga = new Dictionary<string, Body2>();
        foreach (Carga k in cargas)
        {
            if (!k.nombre.StartsWith("CHORRO")) continue;
            Body2 mejor = null; double dmin = 1e9;
            foreach (object o in cuerpos)
            {
                Body2 b = (Body2)o; double[] c = Caja(b);
                if (b == tubo40 || b == tubo50 || b == brida || b == codo || b == placa) continue;
                double dx = Math.Max(Math.Max(c[0] - k.x, 0), k.x - c[3]), dy = Math.Max(Math.Max(c[1] - k.y, 0), k.y - c[4]), dz = Math.Max(Math.Max(c[2] - k.z, 0), k.z - c[5]);
                double dd = Math.Sqrt(dx * dx + dy * dy + dz * dz);
                if (dd < dmin) { dmin = dd; mejor = b; }
            }
            porCarga[k.nombre] = mejor;
            double[] cb = Caja(mejor);
            L("  " + k.nombre + " -> cuerpo con caja x " + F(cb[0]) + ".." + F(cb[3]) + ", y " + F(cb[1]) + ".." + F(cb[4]) + " (a " + F(dmin) + " mm)");
        }

        CWStudyManager sm = cw.ActiveDoc.StudyManager;
        string[] estudios = { "CHORROS", "CHORROS_X2", "ACC_FUERA_PLANO", "ACC_EN_PLANO" };
        foreach (string est in estudios)
        {
            L("=== " + v + " / " + est);
            CWStudy st = sm.CreateNewStudy3(est, (int)swsAnalysisStudyType_e.swsAnalysisStudyTypeStatic, 0, out err);
            CWSolidComponent comp = st.SolidManager.GetComponentAt(0, out err);
            for (int i = 0; i < comp.SolidBodyCount; i++)
            {
                CWSolidBody sb = comp.GetSolidBodyAt(i, out err);
                CWMaterial mat = sb.GetDefaultMaterial();
                mat.MaterialUnits = 0; mat.MaterialName = "AISI 316L a 62 C (hipotesis)";
                mat.SetPropertyByName("EX", 1.93e11, 0); mat.SetPropertyByName("NUXY", 0.30, 0); mat.SetPropertyByName("DENS", 7950.0, 0);
                mat.SetPropertyByName("SIGYLD", 1.53e8, 0); mat.SetPropertyByName("SIGXT", 4.85e8, 0);
                sb.SetSolidBodyMaterial(mat);
            }
            st.ContactManager.SetGlobalContact((int)swsContactType_e.swsContactTypeBonded, 0);
            CWLoadsAndRestraintsManager lbc = st.LoadsAndRestraintsManager;
            lbc.AddRestraint((int)swsRestraintType_e.swsRestraintTypeFixed, new object[] { caraBrida }, null, out err);
            L("empotramiento en la cara de la brida err=" + err);
            double sx = 0, sy = 0, sz = 0;
            foreach (Carga k in cargas)
            {
                double fac;
                object[] caras;
                if (k.nombre.StartsWith("CHORRO") && (est == "CHORROS" || est == "CHORROS_X2"))
                { fac = est == "CHORROS_X2" ? 2.0 : 1.0; caras = (object[])porCarga[k.nombre].GetFaces(); }
                else if (k.nombre == est) { fac = 1.0; caras = ext40.ToArray(); }
                else continue;
                CWRemoteLoad rl = lbc.AddRemoteLoad((int)swsRemoteLoadType_e.swsRemoteLoadType_DirectLoad, caras, 0, k.x, k.y, k.z, out err);
                if (rl == null) { L("  AddRemoteLoad " + k.nombre + " err=" + err); continue; }
                rl.RemoteLoadBeginEdit();
                rl.ConnectionType = (int)swsRemoteLoadConnectionType_e.swsRemoteLoadConnectionType_Distributed;
                rl.ForceUnit = 0; rl.MomentUnit = 0;
                rl.SetForceOrTranslationValues2(true, true, fac * k.fx, true, fac * k.fy, true, fac * k.fz);
                rl.SetMomentOrRotationValues2(false, false, 0, false, 0, false, 0);
                int ee = rl.RemoteLoadEndEdit();
                if (ee != 0) L("  RemoteLoadEndEdit " + k.nombre + " = " + ee);
                sx += fac * k.fx; sy += fac * k.fy; sz += fac * k.fz;
            }
            L("carga aplicada: (" + F(sx) + "; " + F(sy) + "; " + F(sz) + ") N");

            CWMesh mesh = st.Mesh;
            mesh.MesherType = (int)swsMesherType_e.swsMesherTypeAlternateCB;
            mesh.Quality = (int)swsMeshQuality_e.swsMeshQualityHigh;
            mesh.Unit = (int)swsLinearUnit_e.swsLinearUnitMillimeters;
            mesh.MaxElementSize = hmax; mesh.MinElementSize = hmin; mesh.MinElementsInCircle = 8; mesh.GrowthRatio = 1.4;
            int em = st.CreateMesh((int)swsLinearUnit_e.swsLinearUnitMillimeters, hmax, hmin);
            L("CreateMesh(" + F(hmax) + "/" + F(hmin) + ") err=" + em + " | nodos " + mesh.NodeCount + ", elementos " + mesh.ElementCount);
            if (em != 0) { doc.Save3(1, ref e2, ref w2); return; }
            DateTime t0 = DateTime.Now;
            int ea = st.RunAnalysis();
            L("RunAnalysis err=" + ea + " (" + F((DateTime.Now - t0).TotalSeconds) + " s)");
            doc.Save3(1, ref e2, ref w2);
            if (ea != 0) continue;

            CWResults r = st.Results;
            nodos = null;
            double[] mm = AD(r.GetMinMaxStress(9, 0, 1, null, 3, out err));
            if (mm != null && mm.Length >= 4)
            {
                double x, y, z; mesh.GetNodeLocation((int)mm[2], out x, out y, out z);
                L("von Mises máx global " + F(mm[3]) + " MPa en (" + F(x * 1000) + "; " + F(y * 1000) + "; " + F(z * 1000) + ")");
            }
            Maximo(r, mesh, "tubo DN50", tubo50);
            Maximo(r, mesh, "codo", codo);
            Maximo(r, mesh, "tubo DN40", tubo40);
            Maximo(r, mesh, "brida", brida);
            if (placa != null) Maximo(r, mesh, "placa", placa);
            Sonda(r, mesh, tubo50, 0, 150.0, 6.0, "sonda DN50 en x = 150 (lejos de uniones)");
            Sonda(r, mesh, tubo40, 1, -200.0, 6.0, "sonda DN40 en y = -200 (lejos de uniones)");
            double[] ur = AD(r.GetMinMaxDisplacement(3, 1, null, 0, out err));
            if (ur != null && ur.Length >= 4) L("desplazamiento resultante máx " + F(ur[3]) + " mm");
            double dmax = 0;
            foreach (string kk in porCarga.Keys)
            {
                double[] u = AD(r.GetDisplacementForEntities(3, 1, null, (object[])porCarga[kk].GetFaces(), 0, out err));
                for (int i = 0; u != null && i + 1 < u.Length; i += 2) dmax = Math.Max(dmax, u[i + 1]);
            }
            L("desplazamiento máx de coplas y bloque (boquillas) " + F(dmax) + " mm");
            double[] rf = AD(r.GetReactionForcesAndMoments(1, null, 0, out err));
            if (rf != null) L("reacciones (N, N·m): " + string.Join("; ", Array.ConvertAll(rf, F)));

            CWPlot pv = r.CreatePlot((int)swsPlotResultTypes_e.swsResultStress, 9, 3, false, out err);
            if (pv != null)
            {
                pv.SetPlotTitle("Von Mises (MPa) - " + v + " - " + est);
                pv.ShowDeformedPlot(false, 0, 1.0, true);
                pv.ActivatePlot();
                Foto(doc, Path.Combine(res, "VM_" + v + "_" + est + Suf(hmax) + ".jpg"), false);
                Foto(doc, Path.Combine(res, "VM_" + v + "_" + est + Suf(hmax) + "_codo.jpg"), true);
            }
            CWPlot pd = r.CreatePlot((int)swsPlotResultTypes_e.swsResultDisplacementOrAmplitude, 3, 3, false, out err);
            if (pd != null)
            {
                pd.SetPlotTitle("Desplazamiento (mm) - " + v + " - " + est);
                pd.ShowDeformedPlot(true, 0, 0.0, true);
                pd.ActivatePlot();
                Foto(doc, Path.Combine(res, "DESPL_" + v + "_" + est + Suf(hmax) + ".jpg"), false);
            }
            if (pv != null) pv.ActivatePlot();
            doc.Save3(1, ref e2, ref w2);
        }
    }

    static void Maximo(CWResults r, CWMesh mesh, string etiqueta, Body2 b)
    {
        if (b == null) return;
        int err;
        double[] v = AD(r.GetStressForEntities3(true, 9, 1, null, (object[])b.GetFaces(), 3, 0, 0, false, out err));
        double m = -1; int n = -1;
        for (int i = 0; v != null && i + 1 < v.Length; i += 2) if (v[i + 1] > m) { m = v[i + 1]; n = (int)v[i]; }
        if (n < 0) { L(etiqueta + ": sin valores (err " + err + ")"); return; }
        double x, y, z; mesh.GetNodeLocation(n, out x, out y, out z);
        L(etiqueta + ": von Mises máx " + F(m) + " MPa en (" + F(x * 1000) + "; " + F(y * 1000) + "; " + F(z * 1000) + ")");
    }

    static Dictionary<int, double[]> nodos = null;
    static CWMesh mallaNodos = null;
    static void CargarNodos(CWMesh mesh)
    {
        if (nodos != null && mallaNodos == mesh) return;
        nodos = new Dictionary<int, double[]>(); mallaNodos = mesh;
        double[] a = AD(mesh.GetNodes());
        int n = mesh.NodeCount;
        if (a == null) { L("GetNodes: sin datos"); return; }
        int paso = a.Length == 4 * n ? 4 : (a.Length == 3 * n ? 3 : 0);
        L("GetNodes: " + a.Length + " valores para " + n + " nodos (paso " + paso + "); primeros: " + F(a[0]) + ", " + F(a[1]) + ", " + F(a[2]) + ", " + F(a[3]));
        for (int i = 0; paso > 0 && i + paso - 1 < a.Length; i += paso)
        {
            int id = paso == 4 ? (int)a[i] : i / 3 + 1;
            int o = paso == 4 ? 1 : 0;
            nodos[id] = new double[] { a[i + o], a[i + o + 1], a[i + o + 2] };
        }
    }

    static void Sonda(CWResults r, CWMesh mesh, Body2 b, int eje, double centro, double tol, string etiqueta)
    {
        int err;
        CargarNodos(mesh);
        double[] v = AD(r.GetStressForEntities3(true, 9, 1, null, (object[])b.GetFaces(), 3, 0, 0, false, out err));
        double m = -1; int nn = 0;
        for (int i = 0; v != null && i + 1 < v.Length; i += 2)
        {
            double[] q;
            if (!nodos.TryGetValue((int)v[i], out q)) continue;
            double x = q[0], y = q[1];
            double c = (eje == 0 ? x : y) * 1000;
            if (Math.Abs(c - centro) <= tol) { nn++; if (v[i + 1] > m) m = v[i + 1]; }
        }
        L(etiqueta + ": von Mises máx " + F(m) + " MPa (" + nn + " nodos)");
    }

    static void Foto(ModelDoc2 doc, string ruta, bool zoom)
    {
        doc.ShowNamedView2("*Front", (int)swStandardViews_e.swFrontView);
        doc.ViewZoomtofit2();
        if (zoom) doc.ViewZoomTo2(0.40, -0.30, -0.06, 0.66, 0.06, 0.06);
        doc.GraphicsRedraw2();
        int e = 0, w = 0;
        L("imagen " + Path.GetFileName(ruta) + ": " + doc.Extension.SaveAs3(ruta, 0, 1, null, null, ref e, ref w));
    }

    static double[] AD(object o)
    {
        if (o == null) return null;
        double[] d = o as double[];
        if (d != null) return d;
        Array a = o as Array;
        if (a == null) return null;
        double[] r = new double[a.Length];
        for (int i = 0; i < a.Length; i++) r[i] = Convert.ToDouble(a.GetValue(i), CultureInfo.InvariantCulture);
        return r;
    }
}
