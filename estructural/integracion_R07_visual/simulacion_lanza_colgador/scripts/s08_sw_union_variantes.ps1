# Variantes de refuerzo de la unión W5 en SOLIDWORKS (s08_sw_union_variantes.cs). Ejecutar con: powershell -STA -ExecutionPolicy Bypass -File s08_sw_union_variantes.ps1
param([string]$Variantes = "BASE,S40,S80,CART,LENG", [string]$Estudios = "FUERA:1,FUERA:0.6,EN:1")
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$redist = "C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\api\redist"
$dlls = @("SolidWorks.Interop.sldworks.dll", "SolidWorks.Interop.swconst.dll", "SolidWorks.Interop.cosworks.dll") | ForEach-Object { Join-Path $redist $_ }
Add-Type -TypeDefinition (Get-Content (Join-Path $d "scripts\s08_sw_union_variantes.cs") -Raw -Encoding UTF8) -ReferencedAssemblies $dlls
[ResolutorSwVariantes]::Registrar($redist)
$r = [SwVariantes]::Ejecutar($d, $Variantes, $Estudios)
Write-Output $r
