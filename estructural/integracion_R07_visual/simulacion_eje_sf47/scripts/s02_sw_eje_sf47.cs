// Simulación estática en SOLIDWORKS Simulation 2024 (API) del eje de salida del SEW SF47 (Ø25 × 50 con chavetero).
// Geometría: s01_geometria_eje_sf47.py (FreeCAD, medidas del STEP de SEW). Z a lo largo del eje, resalte en Z = 0, punta en Z = 50,
// chavetero del lado +Y. Apoyo idealizado: cara interior del cuerpo Ø50 (Z = -30) empotrada.
// Carga: carga remota distribuida en la cara de la punta, ubicada en el eje a x = 92 mm del resalte (línea media de la correa, D-062):
//   fuerza radial -Y (pone el chavetero del lado traccionado, el peor giro) y par alrededor de Z.
// Estudios: CON_LIMITADOR (625 N; 30 N·m) y ATASCO_SIN_LIMITADOR (3 938 N; 189 N·m), de CALCULO_CARGA_RADIAL_SF47.md y D-062.
// Material: C45 normalizado [HIPÓTESIS]: E 210 GPa, nu 0,30, Sy 305 MPa, Su 580 MPa. Malla: tetraedros de 2.º orden, curvatura.
// Solo crea archivos nuevos. Deja SOLIDWORKS abierto con el modelo para mostrarlo.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.cosworks;

public static class ResolutorSw
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

public static class SwEjeSf47
{
    static StringBuilder log = new StringBuilder();
    static string logPath = null;
    static void L(string s) { log.AppendLine(s); Console.WriteLine(s); if (logPath != null) File.AppendAllText(logPath, s + System.Environment.NewLine); }
    static string F(double x) { return x.ToString("0.####", System.Globalization.CultureInfo.InvariantCulture); }
    static double[] Caja(Face2 f) { return (double[])f.GetBox(); }   // m

    public static string Ejecutar(string step, string prt, string salida, double hmax, double hmin)
    {
        log.Clear();
        logPath = Path.Combine(salida, "sw_log_" + DateTime.Now.ToString("HHmmss") + ".txt");
        try
        {
            SldWorks sw = (SldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"));
            sw.Visible = true;
            Correr(sw, step, prt, salida, hmax, hmin);
        }
        catch (Exception ex) { L("EXCEPCION: " + ex); }
        return log.ToString();
    }

    static void Correr(SldWorks sw, string step, string prt, string salida, double hmax, double hmin)
    {
        L("SolidWorks " + sw.RevisionNumber());
        L("LoadAddIn=" + sw.LoadAddIn(@"C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\Simulation\cosworks.dll"));
        CwAddincallback cb = (CwAddincallback)sw.GetAddInObject("SldWorks.Simulation");
        CosmosWorks cw = cb.CosmosWorks;

        ImportStepData imp = (ImportStepData)sw.GetImportFileData(step);
        int err = 0;
        ModelDoc2 doc = (ModelDoc2)sw.LoadFile4(step, "r", imp, ref err);
        if (doc == null) { L("ERROR LoadFile4 " + err); return; }
        int e2 = 0, w2 = 0;
        L("guardado: " + doc.Extension.SaveAs3(prt, 0, 1, null, null, ref e2, ref w2) + " (" + e2 + "/" + w2 + ") " + prt);
        PartDoc part = (PartDoc)doc;
        object[] bodies = (object[])part.GetBodies2((int)swBodyType_e.swSolidBody, false);
        Body2 b = (Body2)bodies[0];
        double[] mp = (double[])b.GetMassProperties(7850.0);
        L("cuerpos " + bodies.Length + "; volumen " + F(mp[3] * 1e9) + " mm3; caras " + b.GetFaceCount());

        // Clasificar caras por geometría (mm)
        Face2 fijo = null, punta = null;
        List<object> filete = new List<object>(), chavetero = new List<object>(), cil25 = new List<object>();
        foreach (object o in (object[])b.GetFaces())
        {
            Face2 f = (Face2)o; double[] c = Caja(f); Surface s = (Surface)f.GetSurface();
            double z1 = c[2] * 1000, z2 = c[5] * 1000, y1 = c[1] * 1000, y2 = c[4] * 1000;
            if (s.IsPlane() && Math.Abs(z1 + 30) < 0.01 && Math.Abs(z2 + 30) < 0.01) fijo = f;
            else if (s.IsPlane() && Math.Abs(z1 - 50) < 0.01 && Math.Abs(z2 - 50) < 0.01) punta = f;
            else if (y1 > 8.0 && z1 > 4.9 && z2 < 45.1) chavetero.Add(f);
            else if (!s.IsPlane() && !s.IsCylinder() && z1 > -0.05 && z2 < 1.05) filete.Add(f);
            else if (s.IsCylinder() && Math.Abs(((double[])s.CylinderParams)[6] * 1000 - 12.5) < 0.01) cil25.Add(f);
        }
        L("caras: fija " + (fijo != null) + ", punta " + (punta != null) + ", filete " + filete.Count + ", chavetero " + chavetero.Count + ", cilindro Ø25 " + cil25.Count);
        if (fijo == null || punta == null) return;

        string[] nombres = { "CON_LIMITADOR", "ATASCO_SIN_LIMITADOR" };
        double[] fr = { 625.0, 3938.0 };
        double[] tq = { 30.0, 189.0 };
        CWModelDoc cwDoc = cw.ActiveDoc;
        CWStudyManager sm = cwDoc.StudyManager;
        for (int k = 0; k < nombres.Length; k++)
        {
            L("=== " + nombres[k] + ": F_R " + F(fr[k]) + " N a 92 mm del resalte; T " + F(tq[k]) + " N·m");
            CWStudy st = sm.CreateNewStudy3(nombres[k], (int)swsAnalysisStudyType_e.swsAnalysisStudyTypeStatic, 0, out err);
            L("CreateNewStudy3 err=" + err);
            CWSolidManager solm = st.SolidManager;
            CWSolidComponent comp = solm.GetComponentAt(0, out err);
            CWSolidBody sb = comp.GetSolidBodyAt(0, out err);
            CWMaterial mat = sb.GetDefaultMaterial();
            mat.MaterialUnits = 0;
            mat.MaterialName = "C45 normalizado (hipotesis)";
            mat.SetPropertyByName("EX", 2.1e11, 0);
            mat.SetPropertyByName("NUXY", 0.30, 0);
            mat.SetPropertyByName("DENS", 7850.0, 0);
            mat.SetPropertyByName("SIGYLD", 3.05e8, 0);
            mat.SetPropertyByName("SIGXT", 5.8e8, 0);
            L("material: " + sb.SetSolidBodyMaterial(mat));

            CWLoadsAndRestraintsManager lbc = st.LoadsAndRestraintsManager;
            lbc.AddRestraint((int)swsRestraintType_e.swsRestraintTypeFixed, new object[] { fijo }, null, out err);
            L("empotramiento err=" + err);
            CWRemoteLoad rl = lbc.AddRemoteLoad((int)swsRemoteLoadType_e.swsRemoteLoadType_DirectLoad, new object[] { punta }, 0, 0.0, 0.0, 92.0, out err);
            L("AddRemoteLoad err=" + err);
            rl.RemoteLoadBeginEdit();
            rl.ConnectionType = (int)swsRemoteLoadConnectionType_e.swsRemoteLoadConnectionType_Distributed;
            rl.ForceUnit = 0; rl.MomentUnit = 0;
            rl.SetForceOrTranslationValues2(true, true, 0.0, true, -fr[k], true, 0.0);
            rl.SetMomentOrRotationValues2(true, true, 0.0, true, 0.0, true, tq[k]);
            L("RemoteLoadEndEdit=" + rl.RemoteLoadEndEdit());

            CWMesh mesh = st.Mesh;
            mesh.MesherType = (int)swsMesherType_e.swsMesherTypeAlternateCB;
            mesh.Quality = (int)swsMeshQuality_e.swsMeshQualityHigh;
            mesh.Unit = (int)swsLinearUnit_e.swsLinearUnitMillimeters;
            mesh.MaxElementSize = hmax;
            mesh.MinElementSize = hmin;
            mesh.MinElementsInCircle = 12;
            mesh.GrowthRatio = 1.3;
            int em = st.CreateMesh((int)swsLinearUnit_e.swsLinearUnitMillimeters, hmax, hmin);
            L("CreateMesh(" + F(hmax) + "/" + F(hmin) + " mm) err=" + em + " | nodos " + mesh.NodeCount + ", elementos " + mesh.ElementCount + " | max " + F(mesh.MaxElementSize) + ", min " + F(mesh.MinElementSize));
            if (em != 0) return;
            DateTime t0 = DateTime.Now;
            int ea = st.RunAnalysis();
            L("RunAnalysis err=" + ea + " (" + F((DateTime.Now - t0).TotalSeconds) + " s)");
            doc.Save3(1, ref e2, ref w2);
            if (ea != 0) return;

            CWResults res = st.Results;
            double[] mm = AD(res.GetMinMaxStress(9, 0, 1, null, 3, out err));
            if (mm != null && mm.Length >= 4)
            {
                double x, y, z; mesh.GetNodeLocation((int)mm[2], out x, out y, out z);
                L("von Mises global: min " + F(mm[1]) + ", max " + F(mm[3]) + " MPa en el nodo " + (int)mm[2] + " (" + F(x * 1000) + "; " + F(y * 1000) + "; " + F(z * 1000) + ") mm");
            }
            Maximo(res, mesh, "filete del resalte r 1", filete);
            Maximo(res, mesh, "chavetero (paredes, fondo y extremos)", chavetero);
            Maximo(res, mesh, "superficie del Ø25", cil25);
            // Tensión axial SZ en la generatriz inferior (lado sin chavetero, comprimido), lejos de entalles: control frente a M/W
            object sz = res.GetStressForEntities3(true, 2, 1, null, cil25.ToArray(), 3, 0, 0, false, out err);
            double[] v = AD(sz);
            StringBuilder sb2 = new StringBuilder("z_mm;SZ_MPa\n");
            for (int i = 0; v != null && i + 1 < v.Length; i += 2)
            {
                double x, y, z; mesh.GetNodeLocation((int)v[i], out x, out y, out z);
                if (Math.Abs(x) < 1.5e-3 && y < -0.0124) sb2.Append(F(z * 1000) + ";" + F(v[i + 1]) + "\n");
            }
            File.WriteAllText(Path.Combine(salida, "SZ_generatriz_inferior_" + nombres[k] + ".csv"), sb2.ToString());
            double[] ur = AD(res.GetMinMaxDisplacement(3, 1, null, 0, out err));
            if (ur != null && ur.Length >= 4) L("desplazamiento resultante máx " + F(ur[3]) + " mm (unidad 0)");

            // Gráficos: von Mises sin deformar y desplazamiento deformado
            CWPlot pv = res.CreatePlot((int)swsPlotResultTypes_e.swsResultStress, 9, 3, false, out err);
            if (pv != null)
            {
                pv.SetPlotTitle("Von Mises (MPa) - " + nombres[k]);
                pv.ShowDeformedPlot(false, 0, 1.0, true);
                pv.ActivatePlot();
                Foto(doc, Path.Combine(salida, "VM_" + nombres[k] + "_iso.jpg"), false);
                Foto(doc, Path.Combine(salida, "VM_" + nombres[k] + "_zoom_resalte.jpg"), true);
            }
            else L("CreatePlot VM err=" + err);
            CWPlot pd = res.CreatePlot((int)swsPlotResultTypes_e.swsResultDisplacementOrAmplitude, 3, 0, false, out err);
            if (pd != null)
            {
                pd.SetPlotTitle("Desplazamiento resultante (mm) - " + nombres[k]);
                pd.ShowDeformedPlot(true, 0, 0.0, true);
                pd.ActivatePlot();
                Foto(doc, Path.Combine(salida, "DESPL_" + nombres[k] + "_iso.jpg"), false);
            }
            else L("CreatePlot desplazamiento err=" + err);
            if (pv != null) pv.ActivatePlot();
            doc.Save3(1, ref e2, ref w2);
        }
        // Dejar activo el estudio con limitador y su gráfico de von Mises
        L("modelo guardado: " + prt);
    }

    static void Maximo(CWResults res, CWMesh mesh, string etiqueta, List<object> caras)
    {
        if (caras.Count == 0) { L(etiqueta + ": sin caras"); return; }
        int err;
        double[] v = AD(res.GetStressForEntities3(true, 9, 1, null, caras.ToArray(), 3, 0, 0, false, out err));
        double m = -1; int n = -1;
        for (int i = 0; v != null && i + 1 < v.Length; i += 2) if (v[i + 1] > m) { m = v[i + 1]; n = (int)v[i]; }
        if (n < 0) { L(etiqueta + ": sin valores (err " + err + ")"); return; }
        double x, y, z; mesh.GetNodeLocation(n, out x, out y, out z);
        L(etiqueta + ": von Mises máx " + F(m) + " MPa en (" + F(x * 1000) + "; " + F(y * 1000) + "; " + F(z * 1000) + ") mm");
    }

    static void Foto(ModelDoc2 doc, string ruta, bool zoom)
    {
        doc.ShowNamedView2("*Isometric", (int)swStandardViews_e.swIsometricView);
        doc.ViewZoomtofit2();
        if (zoom) doc.ViewZoomTo2(-0.016, -0.004, -0.008, 0.016, 0.016, 0.016);
        doc.GraphicsRedraw2();
        int e = 0, w = 0;
        bool ok = doc.Extension.SaveAs3(ruta, 0, 1, null, null, ref e, ref w);
        L("imagen " + Path.GetFileName(ruta) + ": " + ok + " (" + e + "/" + w + ")");
    }

    static double[] AD(object o)
    {
        if (o == null) return null;
        double[] d = o as double[];
        if (d != null) return d;
        Array a = o as Array;
        if (a == null) return null;
        double[] r = new double[a.Length];
        for (int i = 0; i < a.Length; i++) r[i] = Convert.ToDouble(a.GetValue(i), System.Globalization.CultureInfo.InvariantCulture);
        return r;
    }
}
