# Lanza la simulación del brazo de la U en SOLIDWORKS (s03_sw_brazo_u.cs). Ejecutar con: powershell -STA -File s03_sw_brazo_u.ps1
param([string]$Variantes = "SIN_PLACA,CON_PLACA", [double]$HMax = 5.0, [double]$HMin = 1.0)
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$redist = "C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\api\redist"
$dlls = @("SolidWorks.Interop.sldworks.dll", "SolidWorks.Interop.swconst.dll", "SolidWorks.Interop.cosworks.dll") | ForEach-Object { Join-Path $redist $_ }
Add-Type -TypeDefinition (Get-Content (Join-Path $d "scripts\s03_sw_brazo_u.cs") -Raw -Encoding UTF8) -ReferencedAssemblies $dlls
[ResolutorSwU]::Registrar($redist)
$r = [SwBrazoU]::Ejecutar($d, $Variantes, $HMax, $HMin)
Write-Output "fin"
