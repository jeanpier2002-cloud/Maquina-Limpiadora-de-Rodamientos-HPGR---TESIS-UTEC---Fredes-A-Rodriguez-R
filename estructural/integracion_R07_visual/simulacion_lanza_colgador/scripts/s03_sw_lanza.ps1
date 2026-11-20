# Lanza la simulación de la lanza, el mástil y el tambor en SOLIDWORKS (s03_sw_lanza.cs). Ejecutar con: powershell -STA -File s03_sw_lanza.ps1
param([string]$Estudios = "CHORROS,GIRO,PESO,SERVICIO,GOLPE_LANZA_RADIAL,GOLPE_LANZA_TANG,MANGUERA_100N,U_GOLPE_FUERA_PLANO,U_GOLPE_EN_PLANO",
      [double]$HMax = 6.0, [double]$HMin = 1.2)
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$redist = "C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\api\redist"
$dlls = @("SolidWorks.Interop.sldworks.dll", "SolidWorks.Interop.swconst.dll", "SolidWorks.Interop.cosworks.dll") | ForEach-Object { Join-Path $redist $_ }
Add-Type -TypeDefinition (Get-Content (Join-Path $d "scripts\s03_sw_lanza.cs") -Raw -Encoding UTF8) -ReferencedAssemblies $dlls
[ResolutorSwLanza]::Registrar($redist)
$r = [SwLanza]::Ejecutar($d, $Estudios, $HMax, $HMin)
Write-Output "fin"
