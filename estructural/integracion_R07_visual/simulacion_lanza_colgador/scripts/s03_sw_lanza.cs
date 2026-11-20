// Lanza, carro, mástil, tambor (cubo distribuidor) y transversal central (R07 V18D) en SOLIDWORKS Simulation 2024 (12/11/2026).
// Pregunta del asesor: ¿se forman momentos importantes en el «cuello» que une la lanza con el tambor cuando el rotor gira?
// Geometría: LANZA_COLGADOR_V18D.step (s01), marco SW = (−x, z, y) del CAD, Y vertical. Unión entre piezas: contacto pegado
// (soldaduras y uniones abulonadas idealizadas; el carro pegado a las varillas representa los bujes y el émbolo de bloqueo).
// Apoyo: eje del rotor empotrado en Z2840 (centro del rodamiento inferior; el par de rodamientos del cartucho da empotramiento).
// Cargas (cargas.csv de s02): cargas remotas distribuidas en el cuerpo indicado y ubicadas en el punto de aplicación real;
// giro como fuerza centrífuga y aceleración angular sobre el eje del rotor; peso como gravedad.
// Material 316L [HIPÓTESIS de B1, la misma del estudio de la U]: E 193 GPa, nu 0,30, fluencia 153 MPa a 62 °C, rotura 485 MPa.
// Solo crea archivos nuevos (modelo y resultados). Deja SOLIDWORKS abierto.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.cosworks;

public static class ResolutorSwLanza
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

public static class SwLanza
{
    static string logPath = null;
    static void L(string s) { Console.WriteLine(s); if (logPath != null) File.AppendAllText(logPath, s + System.Environment.NewLine); }
    static string F(double x) { return x.ToString("0.####", CultureInfo.InvariantCulture); }
    static double D(string s) { return double.Parse(s, CultureInfo.InvariantCulture); }

    class Carga { public string nombre, estudios, cuerpo; public double x, y, z, fx, fy, fz; }
    class Ref { public string nombre; public double vol, cx, cy, cz; }

    const double OMEGA = 2 * Math.PI * 1.7 / 60.0;   // rad/s (1,7 rpm)
    const double ALFA = OMEGA / 1.0;                  // rad/s², rampa de 1 s [HIPÓTESIS]

    public static string Ejecutar(string carpeta, string estudios, double hmax, double hmin)
    {
        string res = Path.Combine(carpeta, "resultados"); Directory.CreateDirectory(res);
        string mod = Path.Combine(carpeta, "modelo"); Directory.CreateDirectory(mod);
        string sello = DateTime.Now.ToString("HHmmss");
        logPath = Path.Combine(res, "sw_log_" + sello + ".txt");
        try
        {
            List<Carga> cargas = new List<Carga>();
            foreach (string ln in File.ReadAllLines(Path.Combine(carpeta, "geometria", "cargas.csv")))
            {
                string[] c = ln.Split(';');
                if (c[0] == "nombre") continue;
                Carga k = new Carga(); k.nombre = c[0]; k.estudios = c[1]; k.cuerpo = c[2];
                k.x = D(c[3]); k.y = D(c[4]); k.z = D(c[5]); k.fx = D(c[6]); k.fy = D(c[7]); k.fz = D(c[8]);
                cargas.Add(k);
            }
            List<Ref> refs = new List<Ref>();
            foreach (string ln in File.ReadAllLines(Path.Combine(carpeta, "geometria", "cuerpos.csv")))
            {
                string[] c = ln.Split(';');
                if (c[0] == "nombre") continue;
                Ref r = new Ref(); r.nombre = c[0]; r.vol = D(c[1]); r.cx = D(c[2]); r.cy = D(c[3]); r.cz = D(c[4]);
                refs.Add(r);
            }
            SldWorks sw = (SldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"));
            sw.Visible = true;
            L("SolidWorks " + sw.RevisionNumber() + " | malla " + F(hmax) + "/" + F(hmin) + " mm | estudios: " + estudios);
            object ao = sw.GetAddInObject("SldWorks.Simulation");
            for (int intento = 0; ao == null && intento < 3; intento++)
            {
                L("complemento Simulation no disponible; LoadAddIn=" + sw.LoadAddIn(@"C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\Simulation\cosworks.dll"));
                System.Threading.Thread.Sleep(8000);
                ao = sw.GetAddInObject("SldWorks.Simulation");
            }
            if (ao == null) { L("ERROR: sin el complemento Simulation"); return "error"; }
            CosmosWorks cw = ((CwAddincallback)ao).CosmosWorks;
            Modelo(sw, cw, carpeta, Path.Combine(mod, "LANZA_COLGADOR_SW_" + sello + ".SLDPRT"), res, cargas, refs, estudios, hmax, hmin);
        }
        catch (Exception ex) { L("EXCEPCION: " + ex); }
        return "fin";
    }

    static string Suf(double h) { return Math.Abs(h - 6.0) < 1e-9 ? "" : "_h" + F(h).Replace(".", "p"); }

    static void Modelo(SldWorks sw, CosmosWorks cw, string carpeta, string prt, string res, List<Carga> cargas, List<Ref> refs,
                       string estudios, double hmax, double hmin)
    {
        string step = Path.Combine(carpeta, "geometria", "LANZA_COLGADOR_V18D.step");
        int err = 0, e2 = 0, w2 = 0;
        object[] abiertos = (object[])sw.GetDocuments();
        if (abiertos != null)
            foreach (object o in abiertos)
            {
                string tit = ((ModelDoc2)o).GetTitle();
                if (tit.StartsWith("LANZA_COLGADOR")) { sw.CloseDoc(tit); L("cerrado el documento anterior " + tit); }
            }
        ImportStepData imp = (ImportStepData)sw.GetImportFileData(step);
        ModelDoc2 doc = (ModelDoc2)sw.LoadFile4(step, "r", imp, ref err);
        if (doc == null) { L("ERROR LoadFile4 " + err); return; }
        L("guardado " + doc.Extension.SaveAs3(prt, 0, 1, null, null, ref e2, ref w2) + ": " + prt);
        object[] cuerpos = (object[])((PartDoc)doc).GetBodies2((int)swBodyType_e.swSolidBody, false);
        L("cuerpos: " + cuerpos.Length + " (esperados " + refs.Count + ")");

        // Identificar cada cuerpo por su centro de masa y volumen
        Dictionary<string, Body2> cu = new Dictionary<string, Body2>();
        foreach (object o in cuerpos)
        {
            Body2 b = (Body2)o;
            double[] mp = (double[])b.GetMassProperties(7950.0);
            double vol = mp[3] * 1e9, x = mp[0] * 1000, y = mp[1] * 1000, z = mp[2] * 1000;
            Ref mejor = null; double dmin = 1e9;
            foreach (Ref r in refs)
            {
                double d = Math.Sqrt((r.cx - x) * (r.cx - x) + (r.cy - y) * (r.cy - y) + (r.cz - z) * (r.cz - z)) + 1000 * Math.Abs(vol - r.vol) / r.vol;
                if (d < dmin) { dmin = d; mejor = r; }
            }
            if (mejor != null && dmin < 5 && !cu.ContainsKey(mejor.nombre)) cu[mejor.nombre] = b;
            else L("  cuerpo sin identificar: vol " + F(vol) + " centro (" + F(x) + "; " + F(y) + "; " + F(z) + ") dmin " + F(dmin));
        }
        L("identificados " + cu.Count + " de " + refs.Count);
        if (cu.Count != refs.Count) return;

        Face2 caraEmp = null, caraBridaA = null, cilEje = null;
        foreach (object o in (object[])cu["EJE"].GetFaces())
        {
            Face2 f = (Face2)o; Surface s = (Surface)f.GetSurface(); double[] c = (double[])f.GetBox();
            if (s.IsPlane() && Math.Abs(c[1] * 1000 - 2840) < 0.01 && Math.Abs(c[4] * 1000 - 2840) < 0.01) caraEmp = f;
            if (s.IsCylinder() && Math.Abs(((double[])s.CylinderParams)[6] * 1000 - 57.15) < 0.05) cilEje = f;
        }
        foreach (object o in (object[])cu["BRIDA_A"].GetFaces())
        {
            Face2 f = (Face2)o; Surface s = (Surface)f.GetSurface(); double[] c = (double[])f.GetBox();
            if (s.IsPlane() && Math.Abs(c[0] * 1000 + 299.25) < 0.01 && Math.Abs(c[3] * 1000 + 299.25) < 0.01) caraBridaA = f;
        }
        L("cara de empotramiento " + (caraEmp != null) + "; cara exterior de la brida A " + (caraBridaA != null) + "; cilindro del eje " + (cilEje != null));
        if (caraEmp == null || caraBridaA == null || cilEje == null) return;

        string[] grupos = { "LANZA", "CARRO", "VARILLA_", "COLGADOR_", "PUENTE_INF", "PUENTE_SUP", "PLACA_BLOQUEO", "ABRAZADERA|BRAZO_ABRAZADERA",
                            "CUBO", "TRANSVERSAL", "BRIDA_", "EJE", "CUELLO_|CODO_LANZA_SUP|RACOR", "COPLA_", "PIE_" };
        CWStudyManager sm = cw.ActiveDoc.StudyManager;
        foreach (string est in estudios.Split(','))
        {
            L("=== " + est);
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
            lbc.AddRestraint((int)swsRestraintType_e.swsRestraintTypeFixed, new object[] { caraEmp }, null, out err);
            L("empotramiento del eje en Z2840 err=" + err);

            double sx = 0, sy = 0, sz = 0;
            foreach (Carga k in cargas)
            {
                if (Array.IndexOf(k.estudios.Split('|'), est) < 0) continue;
                object[] caras = k.cuerpo == "BRIDA_A" ? new object[] { caraBridaA } : (object[])cu[k.cuerpo].GetFaces();
                CWRemoteLoad rl = lbc.AddRemoteLoad((int)swsRemoteLoadType_e.swsRemoteLoadType_DirectLoad, caras, 0, k.x, k.y, k.z, out err);
                if (rl == null) { L("  AddRemoteLoad " + k.nombre + " err=" + err); continue; }
                rl.RemoteLoadBeginEdit();
                rl.ConnectionType = (int)swsRemoteLoadConnectionType_e.swsRemoteLoadConnectionType_Distributed;
                rl.ForceUnit = 0; rl.MomentUnit = 0;
                rl.SetForceOrTranslationValues2(true, true, k.fx, true, k.fy, true, k.fz);
                rl.SetMomentOrRotationValues2(false, false, 0, false, 0, false, 0);
                int ee = rl.RemoteLoadEndEdit();
                L("  " + k.nombre + " en " + k.cuerpo + " (" + caras.Length + " caras) punto (" + F(k.x) + "; " + F(k.y) + "; " + F(k.z) + ") F ("
                  + F(k.fx) + "; " + F(k.fy) + "; " + F(k.fz) + ") N" + (ee != 0 ? " EndEdit=" + ee : ""));
                sx += k.fx; sy += k.fy; sz += k.fz;
            }
            L("cargas remotas aplicadas: (" + F(sx) + "; " + F(sy) + "; " + F(sz) + ") N");
            if (est == "GIRO" || est == "SERVICIO")
            {
                CWCentriFugalForce cf = lbc.AddCentrifugalForce(cilEje, out err);
                if (cf == null) L("  AddCentrifugalForce err=" + err);
                else
                {
                    cf.CFForceBeginEdit(); cf.Unit = 0; cf.AngularVelocity = OMEGA; cf.AngularAcceleration = ALFA;
                    L("  giro: omega " + F(OMEGA) + " rad/s, alfa " + F(ALFA) + " rad/s2 (EndEdit=" + cf.CFForceEndEdit() + ")");
                }
            }
            CWGravity gr = null;
            if (est == "PESO" || est == "SERVICIO")
            {
                gr = lbc.AddGravity(caraEmp, out err);
                if (gr == null) L("  AddGravity err=" + err);
                else
                {
                    // La normal de la cara de empotramiento apunta hacia +Y (arriba): con +9,81 la gravedad quedó hacia arriba (corrida
                    // 015836, UY del pie +0,039 mm) y el indicador de inversión no tuvo efecto. Se usa el valor negativo.
                    gr.GravityBeginEdit(); gr.Unit = 0; gr.SetGravitationalAcclerationValues(0, 0, -9.81);
                    int eg = gr.GravityEndEdit();
                    if (eg != 0)
                    {
                        gr.GravityBeginEdit(); gr.SetGravitationalAcclerationValues(0, 0, 9.81); gr.ReverseDirectionNormalToPlane2 = true;
                        L("  valor negativo rechazado (" + eg + "); se usa 9,81 con inversión (EndEdit=" + gr.GravityEndEdit() + ")");
                    }
                    else L("  gravedad -9,81 m/s2 normal a la cara de empotramiento (EndEdit=0)");
                }
            }

            CWMesh mesh = st.Mesh;
            mesh.MesherType = (int)swsMesherType_e.swsMesherTypeAlternateCB;
            mesh.Quality = (int)swsMeshQuality_e.swsMeshQualityHigh;
            mesh.Unit = (int)swsLinearUnit_e.swsLinearUnitMillimeters;
            mesh.MaxElementSize = hmax; mesh.MinElementSize = hmin; mesh.MinElementsInCircle = 8; mesh.GrowthRatio = 1.4;
            DateTime t0 = DateTime.Now;
            int em = st.CreateMesh((int)swsLinearUnit_e.swsLinearUnitMillimeters, hmax, hmin);
            L("CreateMesh(" + F(hmax) + "/" + F(hmin) + ") err=" + em + " | nodos " + mesh.NodeCount + ", elementos " + mesh.ElementCount + " (" + F((DateTime.Now - t0).TotalSeconds) + " s)");
            if (em != 0) { doc.Save3(1, ref e2, ref w2); return; }
            t0 = DateTime.Now;
            int ea = st.RunAnalysis();
            L("RunAnalysis err=" + ea + " (" + F((DateTime.Now - t0).TotalSeconds) + " s)");
            if (ea != 0) { doc.Save3(1, ref e2, ref w2); continue; }
            CWResults r = st.Results;

            if (gr != null)
            {
                double uy = Media(AD(r.GetDisplacementForEntities(1, 1, null, (object[])cu["PIE_CODO_90"].GetFaces(), 0, out err)));
                L("UY medio del pie de la lanza con gravedad: " + F(uy) + " mm" + (est == "PESO" && uy > 0 ? "  ADVERTENCIA: la gravedad quedó hacia arriba" : ""));
            }
            doc.Save3(1, ref e2, ref w2);

            nodos = null;
            double[] mm = AD(r.GetMinMaxStress(9, 0, 1, null, 3, out err));
            if (mm != null && mm.Length >= 4) L("von Mises máx global " + F(mm[3]) + " MPa en " + Pos(mesh, (int)mm[2]));
            foreach (string g in grupos)
            {
                List<object> caras = new List<object>();
                foreach (KeyValuePair<string, Body2> kv in cu)
                    foreach (string pre in g.Split('|'))
                        if (pre.EndsWith("_") ? kv.Key.StartsWith(pre) : kv.Key == pre) { caras.AddRange((object[])kv.Value.GetFaces()); break; }
                Maximo(r, mesh, g, caras.ToArray());
            }
            Sonda(r, mesh, cu["LANZA"], 1, 1450.0, 6.0, "sonda LANZA en Z1450 (entre el carro y la boquilla más alta)");
            Sonda(r, mesh, cu["TRANSVERSAL"], 0, -240.0, 6.0, "sonda TRANSVERSAL en x = +240 del CAD (entre el tambor y la brida A)");
            double[] ur = AD(r.GetMinMaxDisplacement(3, 1, null, 0, out err));
            if (ur != null && ur.Length >= 4) L("desplazamiento resultante máx " + F(ur[3]) + " mm en " + Pos(mesh, (int)ur[2]));
            double dcop = 0;
            foreach (string kk in cu.Keys)
                if (kk.StartsWith("COPLA_")) dcop = Math.Max(dcop, Maxi(AD(r.GetDisplacementForEntities(3, 1, null, (object[])cu[kk].GetFaces(), 0, out err))));
            L("desplazamiento máx de las coplas (boquillas de la lanza) " + F(dcop) + " mm");
            L("desplazamiento máx del pie de la lanza " + F(Maxi(AD(r.GetDisplacementForEntities(3, 1, null, (object[])cu["PIE_CODO_90"].GetFaces(), 0, out err)))) + " mm");
            L("desplazamiento máx del racor de la manguera " + F(Maxi(AD(r.GetDisplacementForEntities(3, 1, null, (object[])cu["RACOR"].GetFaces(), 0, out err)))) + " mm");

            CWPlot pv = r.CreatePlot((int)swsPlotResultTypes_e.swsResultStress, 9, 3, false, out err);
            if (pv != null)
            {
                pv.SetPlotTitle("Von Mises (MPa) - " + est);
                pv.ShowDeformedPlot(false, 0, 1.0, true);
                pv.ActivatePlot();
                Foto(doc, Path.Combine(res, "VM_" + est + Suf(hmax) + ".jpg"), "*Front", null);
                Foto(doc, Path.Combine(res, "VM_" + est + Suf(hmax) + "_lanza.jpg"), "*Front", new double[] { -0.34, 0.78, -0.2, 0.34, 1.92, 0.6 });
                Foto(doc, Path.Combine(res, "VM_" + est + Suf(hmax) + "_tambor.jpg"), "*Front", new double[] { -0.44, 1.45, -0.25, 0.44, 1.95, 0.6 });
                Foto(doc, Path.Combine(res, "VM_" + est + Suf(hmax) + "_iso.jpg"), "*Isometric", null);
            }
            CWPlot pd = r.CreatePlot((int)swsPlotResultTypes_e.swsResultDisplacementOrAmplitude, 3, 3, false, out err);
            if (pd != null)
            {
                pd.SetPlotTitle("Desplazamiento (mm) - " + est);
                pd.ShowDeformedPlot(true, 0, 0.0, true);
                pd.ActivatePlot();
                Foto(doc, Path.Combine(res, "DESPL_" + est + Suf(hmax) + ".jpg"), "*Right", null);
            }
            if (pv != null) pv.ActivatePlot();
            doc.Save3(1, ref e2, ref w2);
        }
    }

    static string Pos(CWMesh mesh, int n)
    {
        double x, y, z; mesh.GetNodeLocation(n, out x, out y, out z);
        return "(" + F(x * 1000) + "; " + F(y * 1000) + "; " + F(z * 1000) + ") SW";
    }

    static double Media(double[] u) { double s = 0; int n = 0; for (int i = 0; u != null && i + 1 < u.Length; i += 2) { s += u[i + 1]; n++; } return n > 0 ? s / n : double.NaN; }
    static double Maxi(double[] u) { double m = 0; for (int i = 0; u != null && i + 1 < u.Length; i += 2) m = Math.Max(m, u[i + 1]); return m; }

    static void Maximo(CWResults r, CWMesh mesh, string etiqueta, object[] caras)
    {
        if (caras.Length == 0) { L(etiqueta + ": sin caras"); return; }
        int err;
        double[] v = AD(r.GetStressForEntities3(true, 9, 1, null, caras, 3, 0, 0, false, out err));
        double m = -1; int n = -1;
        for (int i = 0; v != null && i + 1 < v.Length; i += 2) if (v[i + 1] > m) { m = v[i + 1]; n = (int)v[i]; }
        if (n < 0) { L(etiqueta + ": sin valores (err " + err + ")"); return; }
        L(etiqueta + ": von Mises máx " + F(m) + " MPa en " + Pos(mesh, n));
    }

    static Dictionary<int, double[]> nodos = null;
    static void CargarNodos(CWMesh mesh)
    {
        if (nodos != null) return;
        nodos = new Dictionary<int, double[]>();
        double[] a = AD(mesh.GetNodes());
        int n = mesh.NodeCount;
        if (a == null) { L("GetNodes: sin datos"); return; }
        int paso = a.Length == 4 * n ? 4 : (a.Length == 3 * n ? 3 : 0);
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
            double c = q[eje] * 1000;
            if (Math.Abs(c - centro) <= tol) { nn++; if (v[i + 1] > m) m = v[i + 1]; }
        }
        L(etiqueta + ": von Mises máx " + F(m) + " MPa (" + nn + " nodos)");
    }

    static void Foto(ModelDoc2 doc, string ruta, string vista, double[] zoom)
    {
        int idv = vista == "*Front" ? (int)swStandardViews_e.swFrontView : vista == "*Right" ? (int)swStandardViews_e.swRightView : (int)swStandardViews_e.swIsometricView;
        doc.ShowNamedView2(vista, idv);
        doc.ViewZoomtofit2();
        if (zoom != null) doc.ViewZoomTo2(zoom[0], zoom[1], zoom[2], zoom[3], zoom[4], zoom[5]);
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
