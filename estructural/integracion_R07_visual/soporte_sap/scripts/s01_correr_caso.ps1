# Soporte superior (R07): corre un caso del modelo parametrico de SAP2000 (SoporteSAP.cs).
# Uso: powershell -STA -File s01_correr_caso.ps1 -Caso O1_V11_ACTUAL -Xc 2170 -Yc 300 -Col TUBE:150:150:6 -Viga TUBE:200:100:6 -Lac ANGLE:50:50:5
param([string]$Caso, [double]$Xc = 2170, [double]$Yc = 300, [string]$Col = "TUBE:150:150:6", [string]$Viga = "TUBE:200:100:6",
      [string]$Lac = "ANGLE:50:50:5", [double]$ZViga = 2790, [switch]$Visible, [switch]$Empotrar, [double]$Cartela = 0, [string]$CartSec = "TUBE:60:60:4", [switch]$Planta)
$ErrorActionPreference = "Stop"
$B = "C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap"
$dll = "C:\Program Files\Computers and Structures\SAP2000 27\SAP2000v1.dll"
$ns = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\netstandard.dll"
Add-Type -Path $dll
Add-Type -TypeDefinition (Get-Content "$B\scripts\SoporteSAP.cs" -Raw -Encoding UTF8) -ReferencedAssemblies @($dll, $ns)
[SoporteSAP]::Correr($Caso, "$B\modelos", "$B\resultados", $Xc, $Yc, $Col, $Viga, $Lac, $ZViga, [bool]$Visible, [bool]$Empotrar, $Cartela, $CartSec, [bool]$Planta)
