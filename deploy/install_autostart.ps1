# install_autostart.ps1
# Registra Nova Promo Hub como tarea de Windows (requiere admin)

$taskName   = "NovaPromoHub"
$pythonPath = "C:\Users\Usuario\.gemini\antigravity\scratch\NOVA_CORE\.venv\Scripts\python.exe"
$scriptArg  = "-m bot_engine.main"
$workDir    = "C:\Users\Usuario\.gemini\antigravity\scratch\NOVA_CORE"
$logFile    = "$workDir\logs\autostart.log"

# Eliminar tarea si ya existe
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Crear acción
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptArg `
    -WorkingDirectory $workDir

# Disparador: al iniciar el sistema (con 30s de retraso para que la red esté lista)
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = "PT30S"

# Configuración avanzada
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 99 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Principal: usuario actual, nivel más alto
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Registrar
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Nova Download Engine - Bot de Telegram para Nova Club" `
    -Force

if ($?) {
    Write-Host ""
    Write-Host "  ✓ Tarea '$taskName' registrada correctamente" -ForegroundColor Green
    Write-Host "  ✓ Se iniciará automáticamente al encender el PC" -ForegroundColor Green
    Write-Host "  ✓ Se reiniciará solo si se cae (hasta 99 veces)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Iniciar ahora:" -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $taskName
    Write-Host "  ✓ Bot iniciado!" -ForegroundColor Green
} else {
    Write-Host "  ✗ Error al registrar la tarea" -ForegroundColor Red
}
