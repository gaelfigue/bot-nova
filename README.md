# 🎧 NOVA_CORE — Promo Hub

Promo Hub para DJs con procesado de audio a nivel de estudio.

## ⚡ Quick Start (Local — Sin Docker)

### Requisitos
- **Python 3.11+**
- **FFmpeg** instalado y en el PATH
- **Token de Telegram** de [@BotFather](https://t.me/BotFather)

### Paso 1: Setup automático
```powershell
# Windows (PowerShell como Admin)
powershell -ExecutionPolicy Bypass -File .\deploy\scripts\setup_windows.ps1
```

```bash
# Linux
chmod +x deploy/scripts/setup_linux.sh
./deploy/scripts/setup_linux.sh
```

### Paso 2: Configurar Token
Edita el archivo `.env` y pega tu token:
```
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Paso 3: Ejecutar
```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Arrancar el bot
python -m bot_engine.main
```

---

## 🐳 Docker (Un solo comando)

```bash
# Crear .env primero
cp .env.example .env
# Editar .env con tu token

# Levantar todo
docker-compose up --build -d

# Ver logs
docker-compose logs -f nova-bot

# Parar
docker-compose down
```

---

## 🎛 Pipeline de Audio

```
URL → yt-dlp (bestaudio) → WAV lossless
  → pyloudnorm (-14 LUFS) → Peak Limit (-1.0 dBTP)
    → MP3 320kbps → mutagen (ID3 fix) → Telegram
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Target LUFS | -14.0 | Estándar streaming / DJ |
| Peak Limit | -1.0 dBTP | Anti-clipping en cabina |
| Bitrate | 320 kbps | Máxima calidad MP3 |
| Encoder | LAME (via FFmpeg) | Mejor encoder MP3 |

---

## 📂 Estructura

```
NOVA_CORE/
├── bot_engine/          # Nova Promo Hub - Bot de Telegram para Nova Club
│   ├── handlers/        # Comandos y descarga
│   ├── services/        # Nova Promo Hub: Downloader, Audio, Metadata
│   ├── utils/           # Logger
│   └── main.py          # Entry point
├── shared_assets/       # Presets, templates, branding
├── ai_modules/          # Módulos IA (futuro)
├── deploy/              # Scripts de setup
├── docker-compose.yml   # Orquestación Docker
└── .env.example         # Template de configuración
```

---

## 📋 Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Mensaje de bienvenida |
| `/help` | Ayuda y plataformas soportadas |
| `/status` | Estado del servidor |
| `[URL]` | Enviar cualquier URL para descargar |

---

*Built for Nova Club 🎧*
