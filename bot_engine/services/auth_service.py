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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            token_mes TEXT,
            has_access INTEGER DEFAULT 0,
            last_login TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Base de datos de usuarios inicializada.")

def check_access(user_id: int) -> bool:
    """Verifica si el usuario tiene acceso activo y el token correcto."""
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
            return has_access == 1 and token_mes == TOKEN_ACTUAL
        return False
    except Exception as e:
        logger.error(f"Error comprobando acceso para {user_id}: {e}")
        return False

def grant_access(user_id: int, username: str, token: str) -> bool:
    """Valida el token y otorga acceso al usuario."""
    if token != TOKEN_ACTUAL:
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
        ''', (user_id, username, token, now))
        conn.commit()
        conn.close()
        logger.info(f"Acceso concedido a {username} ({user_id})")
        return True
    except Exception as e:
        logger.error(f"Error otorgando acceso a {user_id}: {e}")
        return False

# Inicializar al importar
init_db()
