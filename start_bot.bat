@echo off
setlocal
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

:LOOP
echo [%date% %time%] Iniciando Nova DJ Bot...
REM Usamos el ejecutable directo del venv para evitar problemas de ExecutionPolicy en PowerShell
".venv\Scripts\python.exe" -m bot_engine.main
echo [%date% %time%] El bot se cerro con codigo %errorlevel%. Reiniciando en 5 segundos...
timeout /t 5
goto LOOP

