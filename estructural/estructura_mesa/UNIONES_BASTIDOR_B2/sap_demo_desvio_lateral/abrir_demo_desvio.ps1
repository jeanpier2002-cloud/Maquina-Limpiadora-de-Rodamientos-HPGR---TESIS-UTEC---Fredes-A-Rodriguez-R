# Deja SAP2000 ABIERTO con una COPIA del modelo de la mesa (V573_RP_RIG_LOCK) a la que se le agrega el caso de desvio lateral de una rueda.
# Sirve para mostrar al asesor: (1) que el modelo original no tenia esa carga; (2) como se ve el caso en SAP.
# El modelo original no se modifica. Esta copia solo vale para el traslado: el pasador de bloqueo esta retirado.
# Condiciones iguales a las de b2_uniones_calculos.py (caso DESVIO_13_M): S = 6,51 kN en la rueda del nudo 13, en el contacto con el riel,
# con su par; la reacciona la rueda del otro riel (nudo 2); las cadenas retienen Y en los nudos 6 y 17.
# SAP modela torsion de Saint-Venant sin alabeo: la tension de ala oficial sale de la parrilla con alabeo (CALCULO_UNIONES_BASTIDOR_B2.md).
$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$orig = Join-Path $aqui "..\..\SAP_ANEXO_N3_V573\modelos\V573_RP_RIG_LOCK_092304\V573_RP_RIG_LOCK.sdb"
$dst = Join-Path $aqui "modelo"; New-Item -ItemType Directory -Force -Path $dst | Out-Null
$sdb = Join-Path $dst "N3_TRASLADO_DESVIO_LATERAL.sdb"
Copy-Item $orig $sdb -Force
$prog = "C:\Program Files\Computers and Structures\SAP2000 27"
$dll = Join-Path $prog "SAP2000v1.dll"
Add-Type -Path $dll
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public static class VentanaSAP {
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint f);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
$cs = @"
using System;
using System.Text;
using SAP2000v1;
public static class DemoDesvio
{
    static void Rest(cSapModel m, string j, bool u1, bool u2, bool u3)
    {
        bool[] r = new bool[] { u1, u2, u3, false, false, false };
        m.PointObj.SetRestraint(j, ref r, eItemType.Objects);
    }
    public static string Armar(cSapModel m)
    {
        StringBuilder sb = new StringBuilder();
        m.SetPresentUnits(eUnits.kN_mm_C);
        // Apoyos del traslado: ruedas solo verticales; la rueda opuesta toma X; las cadenas toman Y; sin pasador.
        foreach (string w in new string[] { "5", "13", "16" }) Rest(m, w, false, false, true);
        Rest(m, "2", true, false, true);
        Rest(m, "6", false, true, false);
        Rest(m, "17", false, true, false);
        Rest(m, "LOCK", false, false, false);
        m.LoadPatterns.Add("DESVIO_13_M", eLoadPatternType.Other, 0, true);
        double[] v = new double[] { -6.51, 0, 0, 0, 2864.9, 0 };   // kN, kN*mm: F1 y M2 = z*F1, con z = 290 - 730,07 mm
        m.PointObj.SetLoadForce("13", "DESVIO_13_M", ref v, true, "Global", eItemType.Objects);
        m.RespCombo.Add("ULS_DESVIO_13_M", 0);
        eCNameType t = eCNameType.LoadCase;
        string[] c = new string[] { "LC_G_FRAME", "G_K2M_RET", "G_BEARING" };
        foreach (string k in c) { t = eCNameType.LoadCase; m.RespCombo.SetCaseList("ULS_DESVIO_13_M", ref t, k, 1.35); }
        t = eCNameType.LoadCase; m.RespCombo.SetCaseList("ULS_DESVIO_13_M", ref t, "DESVIO_13_M", 1.0);
        sb.AppendLine("armado");
        return sb.ToString();
    }
    public static string Fuerzas(cSapModel m, string[] barras)
    {
        StringBuilder sb = new StringBuilder("barra;estacion_mm;P_kN;V2_kN;V3_kN;T_kNmm;M2_kNmm;M3_kNmm\n");
        m.Results.Setup.DeselectAllCasesAndCombosForOutput();
        m.Results.Setup.SetComboSelectedForOutput("ULS_DESVIO_13_M", true);
        foreach (string b in barras)
        {
            int n = 0; string[] ob = null, el = null, lc = null, st = null; double[] os = null, es = null, sn = null, p = null, v2 = null, v3 = null, tt = null, m2 = null, m3 = null;
            m.Results.FrameForce(b, eItemTypeElm.ObjectElm, ref n, ref ob, ref os, ref el, ref es, ref lc, ref st, ref sn, ref p, ref v2, ref v3, ref tt, ref m2, ref m3);
            for (int i = 0; i < n; i++)
                sb.AppendFormat(System.Globalization.CultureInfo.InvariantCulture, "{0};{1:F1};{2:F3};{3:F3};{4:F3};{5:F1};{6:F1};{7:F1}\n", b, os[i], p[i], v2[i], v3[i], tt[i], m2[i], m3[i]);
        }
        sb.Append("REACCIONES\nnudo;F1_kN;F2_kN;F3_kN\n");
        foreach (string j in new string[] { "2", "5", "13", "16", "6", "17" })
        {
            int n = 0; string[] ob = null, el = null, lc = null, st = null; double[] sn = null, f1 = null, f2 = null, f3 = null, m1 = null, m2 = null, m3 = null;
            m.Results.JointReact(j, eItemTypeElm.ObjectElm, ref n, ref ob, ref el, ref lc, ref st, ref sn, ref f1, ref f2, ref f3, ref m1, ref m2, ref m3);
            for (int i = 0; i < n; i++)
                sb.AppendFormat(System.Globalization.CultureInfo.InvariantCulture, "{0};{1:F3};{2:F3};{3:F3}\n", j, f1[i], f2[i], f3[i]);
        }
        return sb.ToString();
    }
}
"@
$ns = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\netstandard.dll"
Add-Type -TypeDefinition $cs -ReferencedAssemblies @($dll, $ns, "System.Core", "System.Linq")
$helper = New-Object SAP2000v1.Helper
$sap = $helper.CreateObject((Join-Path $prog "SAP2000.exe"))
[void]$sap.ApplicationStart([SAP2000v1.eUnits]::kN_mm_C, $true, "")
$m = $sap.SapModel
Write-Output ("OpenFile=" + $m.File.OpenFile($sdb))
Write-Output ([DemoDesvio]::Armar($m))
Write-Output ("Guardar=" + $m.File.Save($sdb))
Write-Output ("RunAnalysis=" + $m.Analyze.RunAnalysis())
$r = [DemoDesvio]::Fuerzas($m, [string[]]("7","8","9","14","17","6","10"))
[System.IO.File]::WriteAllText((Join-Path $aqui "RESULTADOS_DESVIO_13_M.csv"), $r)
Write-Output ("Guardar=" + $m.File.Save($sdb))
[void]$m.View.RefreshView(0, $false)
Start-Sleep -Seconds 4
$p = Get-Process SAP2000 | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
$h = $p.MainWindowHandle
$rc = New-Object VentanaSAP+RECT; [void][VentanaSAP]::GetWindowRect($h, [ref]$rc)
$bmp = New-Object System.Drawing.Bitmap ($rc.R - $rc.L), ($rc.B - $rc.T); $g = [System.Drawing.Graphics]::FromImage($bmp)
$dc = $g.GetHdc(); [void][VentanaSAP]::PrintWindow($h, $dc, 2); $g.ReleaseHdc($dc); $g.Dispose()
$bmp.Save((Join-Path $aqui "captura_sap_demo.png"), [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
Write-Output "SAP queda abierto: $sdb"
