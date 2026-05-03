@echo off
REM Wrapper para arrancar Nova bot desde el Programador de Tareas
REM Cambia el directorio de trabajo antes de lanzar Python

cd /d "C:\Users\Usuario\.gemini\antigravity\scratch\NOVA_CORE"
"C:\Users\Usuario\.gemini\antigravity\scratch\NOVA_CORE\.venv\Scripts\python.exe" -m bot_engine.main
