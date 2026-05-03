@echo off
REM =========================================================
REM  INSTALAR NOVA BOT COMO SERVICIO 24/7
REM  Ejecutar como ADMINISTRADOR (clic derecho → Ejecutar como admin)
REM =========================================================

echo.
echo  Instalando Nova Download Engine como tarea automatica...
echo.

schtasks /Delete /TN "NovaDownloadEngine" /F 2>nul

schtasks /Create /TN "NovaDownloadEngine" /XML "%~dp0nova_task.xml" /F

if %ERRORLEVEL% == 0 (
    echo.
    echo  [OK] Tarea registrada correctamente!
    echo  [OK] El bot arrancara automaticamente al encender el PC
    echo  [OK] Se reiniciara solo si se cae
    echo.
    echo  Iniciando ahora...
    schtasks /Run /TN "NovaDownloadEngine"
    echo  [OK] Bot iniciado!
) else (
    echo.
    echo  [ERROR] No se pudo registrar la tarea.
    echo  Asegurate de ejecutar este archivo como ADMINISTRADOR.
)

echo.
pause
