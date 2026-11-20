# Rehace la imagen de desplazamiento en mm sobre el SOLIDWORKS abierto (ver s03_sw_imagen_desplazamiento.cs). powershell -STA -File ...
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$redist = "C:\swdist\SOLIDWORKS_2024_sp05\SOLIDWORKS\api\redist"
$dlls = @("SolidWorks.Interop.sldworks.dll", "SolidWorks.Interop.swconst.dll", "SolidWorks.Interop.cosworks.dll") | ForEach-Object { Join-Path $redist $_ }
Add-Type -TypeDefinition (Get-Content (Join-Path $d "scripts\s03_sw_imagen_desplazamiento.cs") -Raw -Encoding UTF8) -ReferencedAssemblies $dlls
[ResolutorSw3]::Registrar($redist)
[SwImagenDespl]::Ejecutar((Join-Path $d "resultados"))
