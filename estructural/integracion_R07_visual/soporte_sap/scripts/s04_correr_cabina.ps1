# Soporte superior (R07 V17B): ¿basta la cabina sola? Corre los casos del modelo de cascaras SoporteCabinaSAP.cs en SAP2000 v27.
# Uso: powershell -STA -File s04_correr_cabina.ps1 [-Solo C0_15,H1_15]
param([string]$Solo = "")
$ErrorActionPreference = "Stop"
$B = "C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap"
$dll = "C:\Program Files\Computers and Structures\SAP2000 27\SAP2000v1.dll"
$ns = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\netstandard.dll"
Add-Type -Path $dll
Add-Type -TypeDefinition (Get-Content "$B\scripts\SoporteCabinaSAP.cs" -Raw -Encoding UTF8) -ReferencedAssemblies @($dll, $ns, "System.Core", "System.Linq")
$V = "vigas=TUBE:160:80:5;planta=1"
$casos = [ordered]@{
  "K0_O10R_MARCO_SOLO"          = "t=0;postes=TUBE:100:100:5;bases=emp;celosia=1;$V"
  "K1_CABINA_SOLA_T15"          = "t=1.5;nl=1"
  "K2_CABINA_SOLA_T30"          = "t=3;nl=1"
  "K3_VIGAS_SOBRE_MUROS_T15"    = "t=1.5;$V"
  "K4_VIGAS_SOBRE_MUROS_T30"    = "t=3;$V"
  # chapa como diafragma (diaf=1): postes articulados, sin celosia en los muros
  "K5_DIAF_POSTES100_ART"       = "t=1.5;diaf=1;postes=TUBE:100:100:5;bases=art;$V"
  "K6_K5_UNIONES_FLEXIBLES"     = "t=1.5;diaf=1;postes=TUBE:100:100:5;bases=art;f12=0.1;$V"
  "K7_DIAF_POSTES80_ART"        = "t=1.5;diaf=1;postes=TUBE:80:80:4;bases=art;$V"
  "K8_K7_UNIONES_FLEXIBLES"     = "t=1.5;diaf=1;postes=TUBE:80:80:4;bases=art;f12=0.1;$V"
  "K9_DIAF_VIGAS_SOBRE_MUROS"   = "t=1.5;diaf=1;$V"
  "K10_DIAF_O10_COMPLETO"       = "t=1.5;diaf=1;postes=TUBE:100:100:5;bases=emp;celosia=1;$V"
  "K11_DIAF_POSTES100_ART_F03"  = "t=1.5;diaf=1;postes=TUBE:100:100:5;bases=art;f12=0.3;$V"
  # repeticiones con 60 modos de pandeo, para hallar el primer factor positivo
  "K12_K7_PANDEO60"             = "t=1.5;diaf=1;postes=TUBE:80:80:4;bases=art;npand=60;$V"
  "K13_K9_PANDEO60"             = "t=1.5;diaf=1;npand=60;$V"
  # K1 y K2 con S1 no lineal no convergieron (K1 detenido a los 5 min en el 38 % de S1): se corren lineales
  "K14_CABINA_SOLA_T15_LINEAL"  = "t=1.5"
  "K15_CABINA_SOLA_T30_LINEAL"  = "t=3"
  # 03/11, pregunta del usuario («¿no es muy grande o muy ancho?»): postes dentro de la cabina, junto a la mesa (x = +-1150)
  "K16_ANGOSTO_X1150_MISMOS"    = "t=0;xc=1150;postes=TUBE:100:100:5;bases=emp;celosia=1;$V"
  "K17_ANGOSTO_X1150_LIVIANO"   = "t=0;xc=1150;postes=TUBE:80:80:4;bases=emp;celosia=1;vigas=TUBE:120:60:4;planta=1"
  "K18_ANGOSTO_X1150_ART"       = "t=0;xc=1150;postes=TUBE:80:80:4;bases=art;celosia=1;vigas=TUBE:120:60:4;planta=1"
  "K19_MUROS_LIVIANO_EMP"       = "t=0;postes=TUBE:80:80:4;bases=emp;celosia=1;vigas=TUBE:150:100:4;planta=1"
  # 03/11, el usuario: «hay que cambiar eso, me pueden observar por sobrediseño»: barrido de perfiles delgados (bases empotradas,
  # celosia y planta), en los muros (x 2020) y dentro de la cabina (x 1200, libra las placas de los pedestales del riel)
  "K20_M_60x3_150x50x3"         = "t=0;postes=TUBE:60:60:3;bases=emp;celosia=1;vigas=TUBE:150:50:3;planta=1"
  "K21_M_75x3_150x50x3"         = "t=0;postes=TUBE:75:75:3;bases=emp;celosia=1;vigas=TUBE:150:50:3;planta=1"
  "K22_M_60x3_120x60x4"         = "t=0;postes=TUBE:60:60:3;bases=emp;celosia=1;vigas=TUBE:120:60:4;planta=1"
  "K23_M_75x3_120x60x4"         = "t=0;postes=TUBE:75:75:3;bases=emp;celosia=1;vigas=TUBE:120:60:4;planta=1"
  "K24_M_80x4_120x60x4"         = "t=0;postes=TUBE:80:80:4;bases=emp;celosia=1;vigas=TUBE:120:60:4;planta=1"
  "K25_D_50x3_100x50x3"         = "t=0;xc=1200;postes=TUBE:50:50:3;bases=emp;celosia=1;vigas=TUBE:100:50:3;planta=1"
  "K26_D_60x3_100x50x3"         = "t=0;xc=1200;postes=TUBE:60:60:3;bases=emp;celosia=1;vigas=TUBE:100:50:3;planta=1"
  "K27_D_75x3_100x50x3"         = "t=0;xc=1200;postes=TUBE:75:75:3;bases=emp;celosia=1;vigas=TUBE:100:50:3;planta=1"
  "K28_D_60x3_120x60x4"         = "t=0;xc=1200;postes=TUBE:60:60:3;bases=emp;celosia=1;vigas=TUBE:120:60:4;planta=1"
  "K29_D_75x3_120x60x4"         = "t=0;xc=1200;postes=TUBE:75:75:3;bases=emp;celosia=1;vigas=TUBE:120:60:4;planta=1"
  # vigas anchas (100 mm) para subir el modo lateral de 23-24 Hz de K21/K23/K24; y arriostramiento mas liviano
  "K30_M_75x3_150x100x4"        = "t=0;postes=TUBE:75:75:3;bases=emp;celosia=1;vigas=TUBE:150:100:4;planta=1"
  "K31_M_75x3_150x100x3"        = "t=0;postes=TUBE:75:75:3;bases=emp;celosia=1;vigas=TUBE:150:100:3;planta=1"
  "K32_M_80x4_150x100x3"        = "t=0;postes=TUBE:80:80:4;bases=emp;celosia=1;vigas=TUBE:150:100:3;planta=1"
  "K33_M_80x4_150x100x4_L30"    = "t=0;postes=TUBE:80:80:4;bases=emp;celosia=1;vigas=TUBE:150:100:4;planta=1;lac=ANGLE:30:30:3"
  # K32 (D-080) con sismo E.030-2018: Z 0,45 (zona 4), U 1,0 (C), C 2,5 (T 0,27 s < TP), S 1,05 (S2) [HIPOTESIS de suelo], R 4 (acero
  # ordinario, tabla 7): V/P = 0,45 x 1,0 x 2,5 x 1,05 / 4 = 0,295
  "K34_K32_SISMO_E030"          = "t=0;postes=TUBE:80:80:4;bases=emp;celosia=1;vigas=TUBE:150:100:3;planta=1;sismo=0.2953"
}
$sel = if ($Solo) { $Solo.Split(",") } else { $casos.Keys }
foreach ($c in $sel) {
  $t0 = Get-Date
  Write-Host "=== $c : $($casos[$c])"
  try { [void][SoporteCabinaSAP]::Correr($c, "$B\modelos_cabina", "$B\resultados_cabina", $casos[$c]) }
  catch { Write-Host "ERROR $c : $($_.Exception.Message)"; Get-Process SAP2000 -ErrorAction SilentlyContinue | Stop-Process -Force }
  Write-Host ("    {0:N0} s" -f ((Get-Date) - $t0).TotalSeconds)
}
