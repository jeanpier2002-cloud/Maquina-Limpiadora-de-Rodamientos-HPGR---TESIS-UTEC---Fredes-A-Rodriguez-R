# Anexo SAP del soporte superior, paso 3: deja SAP2000 ABIERTO (visible) con una COPIA del modelo, ya analizado y disenado
# (AISC 360-16), para sacar las capturas de GUIA_CAPTURAS_SAP.md (como p8 del anexo de la mesa). No cierra SAP: las capturas las
# hace el usuario y luego cierra SAP sin guardar.
# Uso: powershell -STA -File a03_abrir_para_capturas.ps1 -Modelo K0_O10R_MARCO_SOLO   (o K16_ANGOSTO_X1150_MISMOS, K14_CABINA_SOLA_T15_LINEAL,
#      K13_K9_PANDEO60, K10_DIAF_O10_COMPLETO)
param([string]$Modelo = "K0_O10R_MARCO_SOLO")
$ErrorActionPreference = "Stop"
$S = "C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap"
$dst = "$S\anexo_sap\modelos\CAPTURAS_" + $Modelo + "_" + (Get-Date -Format "HHmmss"); New-Item -ItemType Directory -Force -Path $dst | Out-Null
$sdb = "$dst\$Modelo.sdb"
Copy-Item "$S\modelos_cabina\$Modelo.sdb" $sdb -Force
$prog = "C:\Program Files\Computers and Structures\SAP2000 27"
Add-Type -Path (Join-Path $prog "SAP2000v1.dll")
$sap = (New-Object SAP2000v1.Helper).CreateObject((Join-Path $prog "SAP2000.exe")); [void]$sap.ApplicationStart([SAP2000v1.eUnits]::kN_mm_C, $true, "")
$m = $sap.SapModel
Write-Output ("OpenFile=" + $m.File.OpenFile($sdb))
[void]$m.SetPresentUnits([SAP2000v1.eUnits]::kN_mm_C)
Write-Output ("RunAnalysis=" + $m.Analyze.RunAnalysis())
[int]$nf = 0; [string[]]$fn = $null; [void]$m.FrameObj.GetNameList([ref]$nf, [ref]$fn)
if ($nf -gt 0) {
    [void]$m.DesignSteel.SetCode("AISC 360-16")
    foreach ($c in @("U1", "U2", "U3_AXP", "U3_AXN", "U3_AYP", "U3_AYN")) { [void]$m.DesignSteel.SetComboStrength($c, $true) }
    Write-Output ("StartDesign=" + $m.DesignSteel.StartDesign())
}
[void]$m.View.RefreshView(0, $false)
Write-Output "SAP queda abierto con $sdb (unidades kN, mm, C). Sigue GUIA_CAPTURAS_SAP.md y cierra SAP sin guardar."
