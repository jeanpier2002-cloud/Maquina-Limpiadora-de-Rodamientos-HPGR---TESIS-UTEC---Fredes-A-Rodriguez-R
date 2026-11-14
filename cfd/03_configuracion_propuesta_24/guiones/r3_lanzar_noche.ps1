# CORRIDA 3 · T5/T8 · Lanza la cola R3 (Fluent) y el post-proceso automatico como procesos independientes de la
# sesion de Claude (siguen aunque se cierre la ventana), mas el proceso que mantiene el PC despierto. Copia de
# v3_lanzar_noche.ps1 (CORRIDA 2). Uso:
#   powershell -NoProfile -File r3_lanzar_noche.ps1 [-Cola cola_r3.txt] [-Horas 22]
# Para detener sin cortar la corrida en curso: crear 03_FLUENT\PARAR (no lanza el siguiente caso).
param([string]$Cola = 'cola_r3.txt', [double]$Horas = 22)
# (PowerShell no distingue mayusculas: el proceso de la cola va en $pcola, no en $cola, para no pisar $Cola)
$FL = 'D:\CFD_Redosado\CORRIDA_3_O7C2\03_FLUENT'
$PY = (Get-Command python).Source
$n = [IO.Path]::GetFileNameWithoutExtension($Cola)
$pcola = Start-Process -FilePath $PY -ArgumentList '-I', "$FL\scripts\r3_cola_fluent.py", "$FL\$Cola" `
    -WorkingDirectory "$FL\scripts" -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput "$FL\logs\${n}_stdout.txt" -RedirectStandardError "$FL\logs\${n}_stderr.txt"
$post = Start-Process -FilePath $PY -ArgumentList '-I', "$FL\scripts\r3_procesar_auto.py", "$FL\$Cola" `
    -WorkingDirectory "$FL\scripts" -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput "$FL\logs\procesar_${n}_stdout.txt" -RedirectStandardError "$FL\logs\procesar_${n}_stderr.txt"
$desp = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', `
    "$FL\scripts\r3_mantener_despierto.ps1", '-Horas', "$Horas" -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput "$FL\logs\despierto_${n}.txt"
"{0} {1}: cola PID {2}; post-proceso PID {3}; despierto PID {4} ({5} h)" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Cola, `
    $pcola.Id, $post.Id, $desp.Id, $Horas | Tee-Object -FilePath "$FL\logs\lanzamientos.txt" -Append
