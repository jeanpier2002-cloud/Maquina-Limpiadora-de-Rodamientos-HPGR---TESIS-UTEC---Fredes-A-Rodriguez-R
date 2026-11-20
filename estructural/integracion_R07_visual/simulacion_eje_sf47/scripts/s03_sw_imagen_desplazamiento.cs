// Se conecta al SOLIDWORKS abierto (modelo del eje del SF47 ya analizado) y rehace el gráfico de desplazamiento en mm.
// El primer intento salió en otra unidad: aquí se prueba cada código de unidad y se elige el que da el máximo en mm (0,0358).
// No vuelve a analizar. Solo crea gráficos e imágenes nuevas.
using System;
using System.IO;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
using SolidWorks.Interop.cosworks;

public static class ResolutorSw3
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

public static class SwImagenDespl
{
    public static string Ejecutar(string salida)
    {
        System.Text.StringBuilder log = new System.Text.StringBuilder();
        try
        {
            SldWorks sw = (SldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"));
            ModelDoc2 doc = (ModelDoc2)sw.ActiveDoc;
            if (doc == null) { log.AppendLine("sin documento activo: es otra instancia; se cierra"); try { sw.ExitApp(); } catch (Exception) { } return log.ToString(); }
            log.AppendLine("documento: " + doc.GetTitle());
            CosmosWorks cw = ((CwAddincallback)sw.GetAddInObject("SldWorks.Simulation")).CosmosWorks;
            CWStudyManager sm = cw.ActiveDoc.StudyManager;
            int err;
            for (int i = 0; i < sm.StudyCount; i++)
            {
                sm.ActiveStudy = i;
                CWStudy st = sm.GetStudy(i);
                CWResults res = st.Results;
                log.AppendLine("estudio " + st.Name);
                int elegido = -1;
                for (int u = 0; u <= 10 && elegido < 0; u++)
                {
                    CWPlot p = res.CreatePlot((int)swsPlotResultTypes_e.swsResultDisplacementOrAmplitude, 3, u, false, out err);
                    if (p == null) { log.AppendLine("  unidad " + u + ": err " + err); continue; }
                    string nombre; p.GetPlotName(out nombre);
                    object mm = p.GetMinMaxResultValues(out err);
                    Array a = mm as Array;
                    string txt = "";
                    double mx = double.NaN;
                    if (a != null) { foreach (object o in a) txt += Convert.ToString(o, System.Globalization.CultureInfo.InvariantCulture) + " "; if (a.Length >= 4) mx = Convert.ToDouble(a.GetValue(3)); else if (a.Length >= 2) mx = Convert.ToDouble(a.GetValue(1)); }
                    log.AppendLine("  unidad " + u + ": " + nombre + " -> " + txt);
                    if (!double.IsNaN(mx) && mx > 0.01 && mx < 1.0) { elegido = u; p.SetPlotTitle("Desplazamiento resultante (mm) - " + st.Name); p.ShowDeformedPlot(true, 0, 0.0, true); p.ActivatePlot();
                        doc.ShowNamedView2("*Isometric", (int)swStandardViews_e.swIsometricView); doc.ViewZoomtofit2(); doc.GraphicsRedraw2();
                        int e = 0, w = 0; string ruta = Path.Combine(salida, "DESPL_" + st.Name + "_iso_mm.jpg");
                        log.AppendLine("  imagen " + Path.GetFileName(ruta) + ": " + doc.Extension.SaveAs3(ruta, 0, 1, null, null, ref e, ref w)); }
                    else res.DeletePlot(nombre);
                }
                log.AppendLine("  unidad mm = " + elegido);
            }
            // dejar activo el estudio con limitador y su von Mises
            sm.ActiveStudy = 0;
            CWResults r0 = sm.GetStudy(0).Results;
            foreach (object n in (object[])r0.GetPlotNames()) { string s = n.ToString(); if (s.StartsWith("Tensiones")) { r0.ActivatePlot(s); log.AppendLine("activo: " + s); break; } }
            doc.ShowNamedView2("*Isometric", (int)swStandardViews_e.swIsometricView); doc.ViewZoomtofit2();
            int e2 = 0, w2 = 0; doc.Save3(1, ref e2, ref w2);
        }
        catch (Exception ex) { log.AppendLine("EXCEPCION: " + ex); }
        return log.ToString();
    }
}
