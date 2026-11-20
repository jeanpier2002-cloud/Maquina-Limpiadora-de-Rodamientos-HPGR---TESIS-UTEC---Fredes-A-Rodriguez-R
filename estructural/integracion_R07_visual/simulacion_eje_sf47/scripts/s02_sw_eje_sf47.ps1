# Lanza la simulación del eje del SF47 en SOLIDWORKS Simulation (ver s02_sw_eje_sf47.cs). Ejecutar con: powershell -STA -File s02_sw_eje_sf47.ps1
# Deja SOLIDWORKS abierto con el modelo y los estudios para mostrarlos. Solo crea archivos nuevos.
param([double]$HMax = 1.5, [double]$HMin = 0.15)
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$redist = "C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\api\redist"
$dlls = @("SolidWorks.Interop.sldworks.dll", "SolidWorks.Interop.swconst.dll", "SolidWorks.Interop.cosworks.dll") | ForEach-Object { Join-Path $redist $_ }
$cs = Get-Content (Join-Path $d "scripts\s02_sw_eje_sf47.cs") -Raw -Encoding UTF8
Add-Type -TypeDefinition $cs -ReferencedAssemblies $dlls
[ResolutorSw]::Registrar($redist)
$sal = Join-Path $d "resultados"; New-Item -ItemType Directory -Force -Path $sal | Out-Null
$mod = Join-Path $d "modelo"; New-Item -ItemType Directory -Force -Path $mod | Out-Null
$prt = Join-Path $mod ("EJE_SF47_D25_SW_" + (Get-Date -Format "HHmmss") + ".SLDPRT")
$r = [SwEjeSf47]::Ejecutar((Join-Path $d "geometria\EJE_SF47_D25.step"), $prt, $sal, $HMax, $HMin)
Write-Output "fin"
