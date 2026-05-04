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
    
    # Tabla gigs_finanzas (El Tracker Nativo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gigs_finanzas (
            gig_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sala_nombre TEXT,
            fecha_bolo TEXT,
            cache FLOAT,
            estado TEXT DEFAULT 'PENDIENTE',
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Tabla blacklist_promotores (El Radar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklist_promotores (
            sala_nombre TEXT PRIMARY KEY,
            reportes_negativos INTEGER DEFAULT 0
        )
    ''')

    # Token por defecto inicial
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('token_actual', 'NOVA-MAYO-26')")
    conn.commit()
    conn.close()
    logger.info("Base de datos de usuarios, finanzas y blacklist inicializada.")

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

def add_gig(user_id: int, sala: str, fecha: str, cache: float):
    """Registra un nuevo bolo en las finanzas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO gigs_finanzas (user_id, sala_nombre, fecha_bolo, cache) VALUES (?, ?, ?, ?)",
        (user_id, sala, fecha, cache)
    )
    conn.commit()
    conn.close()

def get_user_finances(user_id: int) -> dict:
    """Calcula el total pagado y pendiente para un usuario."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT estado, SUM(cache) FROM gigs_finanzas WHERE user_id = ? GROUP BY estado",
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    
    finanzas = {"PENDIENTE": 0.0, "PAGADO": 0.0}
    for estado, total in results:
        finanzas[estado] = total
    return finanzas

def check_radar(sala: str) -> int:
    """Verifica si una sala tiene reportes negativos en el Radar."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT reportes_negativos FROM blacklist_promotores WHERE sala_nombre LIKE ?", (f"%{sala}%",))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

# Inicializar al importar
init_db()
