#!/usr/bin/env bash
# ══════════════════════════════════════════════════
# NOVA_CORE — Setup para Linux
# Ejecutar desde la raíz de NOVA_CORE:
#   chmod +x deploy/scripts/setup_linux.sh
#   ./deploy/scripts/setup_linux.sh
# ══════════════════════════════════════════════════

set -euo pipefail

PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step()  { echo -e "\n${PURPLE}[NOVA]${NC} $1"; }
ok()    { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "  ${YELLOW}[!!]${NC} $1"; }
fail()  { echo -e "  ${RED}[XX]${NC} $1"; }

echo ""
echo -e "${PURPLE}  ╔════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}  ║   NOVA CORE — Setup Linux              ║${NC}"
echo -e "${PURPLE}  ╚════════════════════════════════════════╝${NC}"

# ─── 1. Verificar Python ────────────────────────────────
step "Verificando Python..."
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version)
    ok "Python encontrado: $PY_VER"
else
    fail "Python3 no encontrado. Instálalo con: sudo apt install python3 python3-venv"
    exit 1
fi

# ─── 2. Instalar FFmpeg ─────────────────────────────────
step "Verificando FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    FF_VER=$(ffmpeg -version | head -n1)
    ok "FFmpeg encontrado: $FF_VER"
else
    warn "FFmpeg no encontrado, instalando..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y ffmpeg libsndfile1
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y ffmpeg libsndfile
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm ffmpeg libsndfile
    else
        fail "No se pudo instalar FFmpeg. Instálalo manualmente."
        exit 1
    fi
    ok "FFmpeg instalado"
fi

# ─── 3. Crear entorno virtual ───────────────────────────
step "Creando entorno virtual (.venv)..."
if [ -d ".venv" ]; then
    warn "Entorno virtual ya existe, reutilizando..."
else
    python3 -m venv .venv
    ok "Entorno virtual creado en .venv/"
fi

# Activar
source .venv/bin/activate
ok "Entorno virtual activado"

# ─── 4. Instalar dependencias ───────────────────────────
step "Instalando dependencias Python..."
pip install --upgrade pip > /dev/null
pip install -r bot_engine/requirements.txt
ok "Dependencias instaladas"

# ─── 5. Configurar .env ────────────────────────────────
step "Configurando .env..."
if [ -f ".env" ]; then
    warn "Archivo .env ya existe, no se sobrescribe"
else
    cp .env.example .env
    ok "Archivo .env creado desde .env.example"
    warn "IMPORTANTE: Edita .env y agrega tu TELEGRAM_TOKEN"
fi

# ─── 6. Resultado ──────────────────────────────────────
echo ""
echo -e "${GREEN}  ╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║       SETUP COMPLETADO                 ║${NC}"
echo -e "${GREEN}  ╚════════════════════════════════════════╝${NC}"
echo ""
echo "  Pasos siguientes:"
echo "    1. Edita .env y agrega tu TELEGRAM_TOKEN"
echo "    2. Activa el entorno: source .venv/bin/activate"
echo "    3. Ejecuta el bot:    python -m bot_engine.main"
echo ""
