# Revision del CAD R07 V18D (SOLIDWORKS 2024 por API): segunda opinion con la deteccion de interferencias de SW
# sobre los ensambles de las revisiones nuevas de los planos. Copia de rv02 (que no se modifica) con otra lista de ensambles. Solo lectura: abre y cierra sin guardar.
# Coincidencias (contactos) no cuentan como interferencia; si cuentan las interferencias entre cuerpos de una misma pieza
# multicuerpo (cada subconjunto del STEP es una pieza multicuerpo).
# Salida: revision_cad_v11/resultados/rv08b_interferencias_sw_v18d.csv (ensamble; componente 1; componente 2; volumen en mm3).
$ErrorActionPreference = "Stop"
$R07 = "C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
$redist = "C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\api\redist"
$refs = @("$redist\SolidWorks.Interop.sldworks.dll", "$redist\SolidWorks.Interop.swconst.dll")
foreach ($r in $refs) { [void][Reflection.Assembly]::LoadFrom($r) }
$cs = @"
using System;
using System.IO;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;
public static class InterfSW
{
    public static string Revisar(string[] asms, string csv)
    {
        SldWorks sw = (SldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"));
        sw.Visible = false;
        StringBuilder sb = new StringBuilder();
        sb.AppendLine("ensamble;componente_1;componente_2;volumen_mm3");
        foreach (string a in asms)
        {
            int e = 0, w = 0;
            ModelDoc2 m = sw.OpenDoc6(a, (int)swDocumentTypes_e.swDocASSEMBLY, (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref e, ref w);
            if (m == null) { sb.AppendLine(Path.GetFileName(a) + ";NO ABRE;" + e + ";"); continue; }
            AssemblyDoc ad = (AssemblyDoc)m;
            ad.ResolveAllLightWeightComponents(false);
            InterferenceDetectionMgr im = ad.InterferenceDetectionManager;
            im.TreatCoincidenceAsInterference = false;
            im.TreatSubAssembliesAsComponents = false;
            im.IncludeMultibodyPartInterferences = true;
            im.MakeInterferingPartsTransparent = false;
            im.CreateFastenersFolder = false;
            im.IgnoreHiddenBodies = true;
            im.ShowIgnoredInterferences = false;
            im.UseTransform = false;
            int n = im.GetInterferenceCount();
            object[] ints = (object[])im.GetInterferences();
            if (ints != null)
                foreach (object o in ints)
                {
                    IInterference it = (IInterference)o;
                    object[] cs = (object[])it.Components;
                    string c1 = cs != null && cs.Length > 0 ? ((Component2)cs[0]).Name2 : "";
                    string c2 = cs != null && cs.Length > 1 ? ((Component2)cs[1]).Name2 : c1;
                    sb.AppendLine(Path.GetFileName(a) + ";" + c1 + ";" + c2 + ";" + (it.Volume * 1e9).ToString("F1"));
                }
            sb.AppendLine(Path.GetFileName(a) + ";TOTAL;" + n + ";");
            im.Done();
            sw.CloseDoc(m.GetTitle());
        }
        File.WriteAllText(csv, sb.ToString(), Encoding.UTF8);
        sw.ExitApp();
        return sb.ToString();
    }
}
"@
Add-Type -TypeDefinition $cs -ReferencedAssemblies $refs
$P = "$R07\planos"
$asms = @("$P\mesa\revB\MES-000_MESA_CONJUNTO.SLDASM", "$P\centrador_empujador\revC\MES-520_CENTRADOR_EMPUJADOR.SLDASM",
          "$P\soporte_pivote\revB\MES-521_SOPORTE_SOLDADO_PIVOTE.SLDASM", "$P\tope_retencion\revB\MES-400_TOPE_RETENCION.SLDASM",
          "$P\tope_retencion\mes410\MES-410_TOPE_190.SLDASM", "$P\pedestal\revB\MES-900_PEDESTAL.SLDASM", "$P\traslado\revB\MES-800_TRASLADO.SLDASM")
[InterfSW]::Revisar($asms, "$R07\revision_cad_v11\resultados\rv08b_interferencias_sw_v18d.csv")
