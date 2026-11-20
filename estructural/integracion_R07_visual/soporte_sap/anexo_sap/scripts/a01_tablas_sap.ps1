# Anexo SAP del soporte superior, paso 1: exporta tablas ORIGINALES de SAP2000 v27 (Database Tables, con su fila de unidades)
# de un modelo de soporte_sap/modelos_cabina, como se hizo con la mesa (SAP_ANEXO_N3_V573/scripts/p19a). Trabaja sobre una COPIA del
# .sdb: la abre, la analiza y la disena (AISC 360-16) y exporta las tablas a CSV.
# Uso: powershell -STA -File a01_tablas_sap.ps1 -Modelo K0_O10R_MARCO_SOLO
param([string]$Modelo = "K0_O10R_MARCO_SOLO")
$ErrorActionPreference = "Stop"
$S = "C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap"
$A = "$S\anexo_sap"
# carpeta nueva por corrida: abrir una copia sobre resultados viejos dejaba a SAP esperando un dialogo oculto
$dst = "$A\modelos\" + $Modelo + "_" + (Get-Date -Format "HHmmss"); New-Item -ItemType Directory -Force -Path $dst | Out-Null
$sdb = "$dst\$Modelo.sdb"
Copy-Item "$S\modelos_cabina\$Modelo.sdb" $sdb -Force
$out = "$A\tablas_sap\" + $Modelo + "_api"; New-Item -ItemType Directory -Force -Path $out | Out-Null
$prog = "C:\Program Files\Computers and Structures\SAP2000 27"
Add-Type -Path (Join-Path $prog "SAP2000v1.dll")
$sap = (New-Object SAP2000v1.Helper).CreateObject((Join-Path $prog "SAP2000.exe")); [void]$sap.ApplicationStart([SAP2000v1.eUnits]::N_mm_C, $false, "")
$m = $sap.SapModel
trap { Write-Output ("ERROR: " + $_); [void]$sap.ApplicationExit($false); break }
Write-Output ("OpenFile=" + $m.File.OpenFile($sdb)); [void]$m.SetPresentUnits([SAP2000v1.eUnits]::N_mm_C)
Write-Output ("RunAnalysis=" + $m.Analyze.RunAnalysis())
[void]$m.DesignSteel.SetCode("AISC 360-16")
foreach ($c in @("U1", "U2", "U3_AXP", "U3_AXN", "U3_AYP", "U3_AYN")) { [void]$m.DesignSteel.SetComboStrength($c, $true) }
Write-Output ("StartDesign=" + $m.DesignSteel.StartDesign())
# el Save va al final: guardar antes de exportar dejaba vacias las tablas de resultados
# casos y combinaciones que se muestran en las tablas de resultados
# todas las combinaciones y todos los casos del modelo (incluye las de sismo si existen)
[int]$nk = 0; [string[]]$combos = $null; [void]$m.RespCombo.GetNameList([ref]$nk, [ref]$combos)
$lc = @(); foreach ($tipo in [Enum]::GetValues([SAP2000v1.eLoadCaseType])) { [int]$k = 0; [string[]]$nn = $null; try { [void]$m.LoadCases.GetNameList([ref]$k, [ref]$nn, $tipo); if ($k -gt 0) { $lc += $nn } } catch {} }
$casos = [string[]]@($lc | Select-Object -Unique)
[int]$np0 = 0; [string[]]$pats = $null; [void]$m.LoadPatterns.GetNameList([ref]$np0, [ref]$pats)
Write-Output ("seleccion: combos " + $m.DatabaseTables.SetLoadCombinationsSelectedForDisplay([ref]$combos) + ", casos " +
    $m.DatabaseTables.SetLoadCasesSelectedForDisplay([ref]$casos) + ", patrones " + $m.DatabaseTables.SetLoadPatternsSelectedForDisplay([ref]$pats))
$quiero = @("Program Control", "Joint Coordinates", "Connectivity - Frame", "Frame Section Assignments", "Frame Section Properties 01 - General",
    "Frame Release Assignments 1 - General", "Joint Restraint Assignments", "Joint Constraint Assignments", "Constraint Definitions - Body",
    "Material Properties 02 - Basic Mechanical Properties", "Mass Source", "Load Pattern Definitions", "Joint Loads - Force",
    "Load Case Definitions", "Combination Definitions", "Joint Displacements", "Joint Reactions", "Base Reactions", "Element Forces - Frames",
    "Modal Periods And Frequencies", "Modal Participating Mass Ratios", "Buckling Factors", "Steel Design 1 - Summary Data - AISC 360-16",
    "Preferences - Steel Design - AISC 360-16")
[int]$nt = 0; [string[]]$tk = $null; [string[]]$tn = $null; [int[]]$it = $null; [bool[]]$ie = $null
[void]$m.DatabaseTables.GetAllTables([ref]$nt, [ref]$tk, [ref]$tn, [ref]$it, [ref]$ie)
$hechas = New-Object System.Collections.Generic.List[string]; $hechas.Add("tabla;archivo;registros")
for ($i = 0; $i -lt $nt; $i++) {
    if ($quiero -notcontains $tk[$i]) { continue }
    $arch = Join-Path $out (($tk[$i] -replace '[^A-Za-z0-9]+', '_').Trim('_') + ".csv")
    # GetTableForDisplayArray: la exportacion directa a CSV devolvia vacias las tablas de resultados
    [string[]]$fk = $null; [int]$tv = 0; [string[]]$campos = $null; [int]$nr = 0; [string[]]$dat = $null
    [void]$m.DatabaseTables.GetTableForDisplayArray($tk[$i], [ref]$fk, "", [ref]$tv, [ref]$campos, [ref]$nr, [ref]$dat)
    $lin = New-Object System.Collections.Generic.List[string]; $lin.Add(($campos -join ";"))
    $nc = $campos.Count
    for ($k = 0; $k -lt $nr; $k++) { $lin.Add(($dat[($k * $nc)..($k * $nc + $nc - 1)] -join ";")) }
    $lin | Set-Content $arch -Encoding UTF8
    $hechas.Add($tk[$i] + ";" + (Split-Path $arch -Leaf) + ";" + $nr)
}
$hechas | Set-Content (Join-Path $out "_TABLAS.csv") -Encoding UTF8
Write-Output ("tablas exportadas: " + ($hechas.Count - 1) + " en " + $out)
[void]$m.File.Save($sdb)
[void]$sap.ApplicationExit($false)
