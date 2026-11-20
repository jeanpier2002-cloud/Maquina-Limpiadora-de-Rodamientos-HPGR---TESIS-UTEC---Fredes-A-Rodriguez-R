# Submodelo de la unión transversal–cubo en SOLIDWORKS (s06_sw_union_cubo.cs). Ejecutar con: powershell -STA -File s06_sw_union_cubo.ps1
param([string]$Tamanos = "2,1,0.6", [string]$Casos = "U_GOLPE_FUERA_PLANO,U_GOLPE_EN_PLANO")
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$redist = "C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\api\redist"
$dlls = @("SolidWorks.Interop.sldworks.dll", "SolidWorks.Interop.swconst.dll", "SolidWorks.Interop.cosworks.dll") | ForEach-Object { Join-Path $redist $_ }
Add-Type -TypeDefinition (Get-Content (Join-Path $d "scripts\s06_sw_union_cubo.cs") -Raw -Encoding UTF8) -ReferencedAssemblies $dlls
[ResolutorSwUnion]::Registrar($redist)
$r = [SwUnion]::Ejecutar($d, $Tamanos, $Casos)
Write-Output $r
