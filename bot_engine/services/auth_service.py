"""
NOVA_CORE — Auth Service
Gestión de suscripciones, validación de tokens y acceso restringido.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from bot_engine.config import BASE_DIR
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.auth")

DB_PATH = BASE_DIR / "data" / "nova_users.db"
TOKEN_ACTUAL = "NOVA-MAYO-26"  # Esto se podría mover a una variable de entorno

def init_db():
    """Inicializa la base de datos de usuarios si no existe."""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            token_mes TEXT,
            has_access INTEGER DEFAULT 0,
            last_login TEXT
        )
    ''')
    # Tabla de configuración global
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # Token por defecto inicial
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('token_actual', 'NOVA-MAYO-26')")
    conn.commit()
    conn.close()
    logger.info("Base de datos de usuarios y config inicializada.")

def get_current_token() -> str:
    """Obtiene el token válido actual de la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'token_actual'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "NOVA-MAYO-26"

def set_current_token(new_token: str):
    """Actualiza el token válido para todos los nuevos logins."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE config SET value = ? WHERE key = 'token_actual'", (new_token,))
    conn.commit()
    conn.close()
    logger.info(f"Token mensual actualizado a: {new_token}")

def check_access(user_id: int) -> bool:
    """Verifica si el usuario tiene acceso activo y el token correcto."""
    token_actual = get_current_token()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT has_access, token_mes FROM users WHERE user_id = ?", 
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            has_access, token_mes = result
            return has_access == 1 and token_mes == token_actual
        return False
    except Exception as e:
        logger.error(f"Error comprobando acceso para {user_id}: {e}")
        return False

def grant_access(user_id: int, username: str, token: str) -> bool:
    """Valida el token y otorga acceso al usuario."""
    token_actual = get_current_token().strip().upper()
    token_usuario = token.strip().upper()
    
    logger.info(f"Intento de login: User {user_id} con token '{token_usuario[:4]}...'")
    
    if token_usuario != token_actual:
        logger.warning(f"Token inválido: Se esperaba {token_actual[:4]}... pero se recibió {token_usuario[:4]}...")
        return False
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO users (user_id, username, token_mes, has_access, last_login)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                token_mes = excluded.token_mes,
                has_access = 1,
                last_login = excluded.last_login
        ''', (user_id, username, token_actual, now))
        conn.commit()
        conn.close()
        logger.info(f"✅ Acceso concedido a {username} ({user_id})")
        return True
    except Exception as e:
        logger.error(f"Error otorgando acceso a {user_id}: {e}")
        return False

# Inicializar al importar
init_db()
