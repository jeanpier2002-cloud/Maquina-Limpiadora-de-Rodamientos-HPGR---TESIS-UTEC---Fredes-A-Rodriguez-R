# Mantiene el PC despierto mientras este proceso viva (no cambia ninguna configuración del sistema).
# Uso:  powershell -NoProfile -File mantener_despierto.ps1 -Horas 12
# Para liberarlo: termina el proceso (o espera a que acabe el plazo). Al salir, Windows recupera su comportamiento normal.
param([double]$Horas = 12)

Add-Type -Namespace Win32 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'

# ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001) = 2147483649
[void][Win32.Power]::SetThreadExecutionState([uint32]2147483649)
$fin = (Get-Date).AddHours($Horas)
Write-Output ("[{0}] PC mantenido despierto hasta {1}" -f (Get-Date -Format 'HH:mm:ss'), $fin.ToString('HH:mm:ss'))
while ((Get-Date) -lt $fin) {
    $resta = ($fin - (Get-Date)).TotalSeconds
    Start-Sleep -Seconds ([Math]::Max(1, [Math]::Min(30, [Math]::Ceiling($resta))))
}
[void][Win32.Power]::SetThreadExecutionState([uint32]2147483648)  # ES_CONTINUOUS solo: libera la petición
Write-Output ("[{0}] Petición liberada" -f (Get-Date -Format 'HH:mm:ss'))
