@echo off
title Nova Promo Hub
cd /d "C:\Users\Usuario\.gemini\antigravity\scratch\NOVA_CORE"

:inicio
echo.
echo  ==========================================
echo   Nova Promo Hub - Auto Restart
echo   %DATE% %TIME%
echo  ==========================================
echo.
".venv\Scripts\python.exe" -m bot_engine.main
echo.
echo  [!] El bot se detuvo. Reiniciando en 5 segundos...
timeout /t 5 /nobreak
goto inicio
