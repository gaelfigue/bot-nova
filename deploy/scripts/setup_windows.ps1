<#
.SYNOPSIS
    NOVA_CORE — Script de Setup para Windows (Ryzen 5)
.DESCRIPTION
    Crea entorno virtual, instala dependencias, FFmpeg y configura .env
.NOTES
    Ejecutar desde la raíz de NOVA_CORE:
    powershell -ExecutionPolicy Bypass -File .\deploy\scripts\setup_windows.ps1
#>

$ErrorActionPreference = "Stop"

# ─── Colores ─────────────────────────────────────────────────
function Write-Step { param($msg) Write-Host "`n[NOVA] " -ForegroundColor Magenta -NoNewline; Write-Host $msg -ForegroundColor White }
function Write-OK   { param($msg) Write-Host "  [OK] " -ForegroundColor Green -NoNewline; Write-Host $msg }
function Write-Warn { param($msg) Write-Host "  [!!] " -ForegroundColor Yellow -NoNewline; Write-Host $msg }
function Write-Fail { param($msg) Write-Host "  [XX] " -ForegroundColor Red -NoNewline; Write-Host $msg }

Write-Host ""
Write-Host "  ╔════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "  ║   NOVA CORE — Setup Windows            ║" -ForegroundColor Magenta
Write-Host "  ╚════════════════════════════════════════╝" -ForegroundColor Magenta

# ─── 1. Verificar Python ────────────────────────────────────
Write-Step "Verificando Python..."
try {
    $pyVersion = python --version 2>&1
    Write-OK "Python encontrado: $pyVersion"
} catch {
    Write-Fail "Python no encontrado. Instálalo desde https://python.org"
    exit 1
}

# ─── 2. Crear entorno virtual ───────────────────────────────
Write-Step "Creando entorno virtual (.venv)..."
if (Test-Path ".venv") {
    Write-Warn "Entorno virtual ya existe, reutilizando..."
} else {
    python -m venv .venv
    Write-OK "Entorno virtual creado en .venv/"
}

# Activar entorno virtual
Write-Step "Activando entorno virtual..."
. .\.venv\Scripts\Activate.ps1
Write-OK "Entorno virtual activado"

# ─── 3. Instalar dependencias ───────────────────────────────
Write-Step "Instalando dependencias Python..."
pip install --upgrade pip | Out-Null
pip install -r bot_engine\requirements.txt
Write-OK "Dependencias instaladas correctamente"

# ─── 4. Instalar FFmpeg ─────────────────────────────────────
Write-Step "Verificando FFmpeg..."
$ffmpegPath = Get-Command ffmpeg -ErrorAction SilentlyContinue

if ($ffmpegPath) {
    $ffVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-OK "FFmpeg ya instalado: $ffVersion"
} else {
    Write-Warn "FFmpeg no encontrado. Intentando instalar..."

    # Intentar con winget primero
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Step "Instalando FFmpeg con winget..."
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
        Write-OK "FFmpeg instalado con winget"
    } else {
        # Intentar con choco
        $choco = Get-Command choco -ErrorAction SilentlyContinue
        if ($choco) {
            Write-Step "Instalando FFmpeg con Chocolatey..."
            choco install ffmpeg -y
            Write-OK "FFmpeg instalado con Chocolatey"
        } else {
            Write-Fail "No se pudo instalar FFmpeg automaticamente."
            Write-Host ""
            Write-Host "  Instala FFmpeg manualmente:" -ForegroundColor Yellow
            Write-Host "    1. Descarga de https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Gray
            Write-Host "    2. Extrae y agrega la carpeta 'bin' al PATH del sistema" -ForegroundColor Gray
            Write-Host "    3. Reinicia PowerShell y ejecuta este script de nuevo" -ForegroundColor Gray
            Write-Host ""
        }
    }
}

# ─── 5. Configurar .env ────────────────────────────────────
Write-Step "Configurando archivo .env..."
if (Test-Path ".env") {
    Write-Warn "Archivo .env ya existe, no se sobrescribe"
} else {
    Copy-Item ".env.example" ".env"
    Write-OK "Archivo .env creado desde .env.example"
    Write-Warn "IMPORTANTE: Edita .env y agrega tu TELEGRAM_TOKEN de @BotFather"
}

# ─── 6. Verificación final ─────────────────────────────────
Write-Host ""
Write-Host "  ╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║       SETUP COMPLETADO                 ║" -ForegroundColor Green
Write-Host "  ╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Pasos siguientes:" -ForegroundColor Cyan
Write-Host "    1. Edita .env y agrega tu TELEGRAM_TOKEN" -ForegroundColor White
Write-Host "    2. Activa el entorno: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "    3. Ejecuta el bot:    python -m bot_engine.main" -ForegroundColor White
Write-Host ""
