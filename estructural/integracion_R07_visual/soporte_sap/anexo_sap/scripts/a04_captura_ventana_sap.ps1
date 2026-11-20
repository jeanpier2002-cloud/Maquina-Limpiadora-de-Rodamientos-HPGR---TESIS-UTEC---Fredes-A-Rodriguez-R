# Anexo SAP del soporte superior, paso 4: captura automatica de la ventana de SAP2000 (PrintWindow) con el modelo abierto por la API,
# analizado y disenado. Sirve para la vista del modelo y, si SAP la muestra al disenar, la de razones D/C. Las vistas que piden menus
# (deformada, modos, diagramas) se sacan a mano con GUIA_CAPTURAS_SAP.md.
# Uso: powershell -STA -File a04_captura_ventana_sap.ps1 -Modelo K0_O10R_MARCO_SOLO
param([string]$Modelo = "K0_O10R_MARCO_SOLO")
$ErrorActionPreference = "Stop"
$S = "C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap"
$out = "$S\anexo_sap\capturas_sap"; New-Item -ItemType Directory -Force -Path $out | Out-Null
$dst = "$S\anexo_sap\modelos\CAPTURA_" + $Modelo + "_" + (Get-Date -Format "HHmmss"); New-Item -ItemType Directory -Force -Path $dst | Out-Null
$sdb = "$dst\$Modelo.sdb"; Copy-Item "$S\modelos_cabina\$Modelo.sdb" $sdb -Force
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public static class Ventana {
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint f);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
function Captura($nombre) {
  $p = Get-Process SAP2000 | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
  $h = $p.MainWindowHandle; [void][Ventana]::ShowWindow($h, 3); Start-Sleep -Seconds 3
  $r = New-Object Ventana+RECT; [void][Ventana]::GetWindowRect($h, [ref]$r)
  $bmp = New-Object System.Drawing.Bitmap ($r.R - $r.L), ($r.B - $r.T); $g = [System.Drawing.Graphics]::FromImage($bmp)
  $dc = $g.GetHdc(); [void][Ventana]::PrintWindow($h, $dc, 2); $g.ReleaseHdc($dc); $g.Dispose()
  $f = "$out\$nombre.png"; $bmp.Save($f, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose(); Write-Output "captura $f"
}
$prog = "C:\Program Files\Computers and Structures\SAP2000 27"
Add-Type -Path (Join-Path $prog "SAP2000v1.dll")
$sap = (New-Object SAP2000v1.Helper).CreateObject((Join-Path $prog "SAP2000.exe")); [void]$sap.ApplicationStart([SAP2000v1.eUnits]::kN_mm_C, $true, "")
$m = $sap.SapModel
try {
  [void]$m.File.OpenFile($sdb); [void]$m.SetPresentUnits([SAP2000v1.eUnits]::kN_mm_C)
  [void]$m.View.RefreshView(0, $false); Captura ($Modelo + "_01_modelo")
  [void]$m.Analyze.RunAnalysis(); [void]$m.View.RefreshView(0, $false); Captura ($Modelo + "_02_analizado")
  [void]$m.DesignSteel.SetCode("AISC 360-16")
  foreach ($c in @("U1", "U2", "U3_AXP", "U3_AXN", "U3_AYP", "U3_AYN")) { [void]$m.DesignSteel.SetComboStrength($c, $true) }
  [void]$m.DesignSteel.StartDesign(); [void]$m.View.RefreshView(0, $false); Captura ($Modelo + "_03_diseno")
} finally { [void]$sap.ApplicationExit($false) }
