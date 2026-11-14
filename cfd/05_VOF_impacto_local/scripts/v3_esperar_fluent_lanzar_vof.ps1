# CORRIDA 2 · Espera a que termine la cola de Fluent (F1-F6) y entonces lanza el VOF en WSL por carriles.
# Regla de Jean: Fluent y WSL no corren a la vez. Condicion de arranque: el proceso de la cola de Fluent
# (PID dado) ya no existe y no hay procesos fl2610/cx2610/fl_mpi2610; luego espera 2 min mas.
# Uso: powershell -NoProfile -File v3_esperar_fluent_lanzar_vof.ps1 -PidCola 928
param([int]$PidCola = 928)
$VOF = 'D:\CFD_Redosado\CORRIDA_2_desde24oct\02_VOF_v3'
$LOG = "$VOF\logs\lanzador_vof.log"
New-Item -ItemType Directory -Force "$VOF\logs" | Out-Null
function Log($m) { "{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m | Out-File -FilePath $LOG -Append -Encoding utf8 }
Log "esperando a la cola de Fluent (PID $PidCola)"
while ($true) {
    $cola = Get-Process -Id $PidCola -ErrorAction SilentlyContinue
    $fl = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(fl2610|cx2610|fl_mpi2610)$' }
    if (-not $cola -and -not $fl) { break }
    Start-Sleep -Seconds 60
}
Log "Fluent terminado; espero 120 s"
Start-Sleep -Seconds 120
$S = '/mnt/d/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/scripts/v3_cola_vof.sh'
$carriles = [ordered]@{
    'A' = @('e1:N5_Co0.5_lam:1:0', 'e1od:OD_N5_Co0.5:1:0', 'e1od:OD_N10_Co0.5:1:0', 'e1od:OD_N10_Co0.5_g0_-9.81_0:1:0',
            'e1od:OD_N10_Co0.5_g0_9.81_0:1:0', 'e1od:OD_N10_Co0.5_completo:1:0', 'e1od:OD_N10_Co0.5_g-9.81_0_0_completo:1:0')
    'B' = @('e1od:OD_N20_Co0.5:2:0', 'e1od:OD_N20_Co0.5_g0_-9.81_0:2:0')
    'C' = @('e1od:OD_N20_Co1:2:0', 'e1od:OD_N20_Co0.25:2:0')
    'D' = @('e1od:OD_N40_Co0.5:4:16200')
}
foreach ($c in $carriles.Keys) {
    $args_ = @('-d', 'Ubuntu', '--cd', '/home/piermoto', '-e', 'bash', $S, 'lanzar', $c) + $carriles[$c]
    $out = & wsl.exe @args_ 2>&1
    Log ("carril {0}: {1}" -f $c, ($out -join ' '))
    Start-Sleep -Seconds 5
}
Log "carriles lanzados"
