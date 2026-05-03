"""
NOVA_CORE — Playlist Extractor
Extrae todos los tracks de una playlist (YouTube, Spotify, SoundCloud)
y devuelve una lista de queries/URLs listas para ser enviadas al downloader.
"""

import re
import yt_dlp
import json
import urllib.request
from typing import List

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.playlist")

# Patrones
SPOTIFY_PLAYLIST_PATTERN = re.compile(r"https?://open\.spotify\.com/(intl-[a-z]{2}/)?playlist/([A-Za-z0-9]+)")
SPOTIFY_ALBUM_PATTERN = re.compile(r"https?://open\.spotify\.com/(intl-[a-z]{2}/)?album/([A-Za-z0-9]+)")
YT_PLAYLIST_PATTERN = re.compile(r"list=([a-zA-Z0-9_-]+)")
SOUNDCLOUD_PLAYLIST_PATTERN = re.compile(r"https?://soundcloud\.com/[^/]+/sets/[^/]+")

def _extract_spotify_via_embed(entity_id: str, entity_type: str = "playlist") -> List[str]:
    """Extrae tracks de Spotify parseando el JSON del embed widget público."""
    url = f"https://open.spotify.com/embed/{entity_type}/{entity_id}"
    logger.info(f"Scraping Spotify Embed: {url}")
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if not match:
            logger.error("No se encontró __NEXT_DATA__ en la página embed de Spotify.")
            return []
            
        data = json.loads(match.group(1))
        entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
        tracks = entity.get('trackList', [])
        
        queries = []
        for t in tracks:
            title = t.get('title', '')
            artist = t.get('subtitle', '')
            if title:
                queries.append(f"ytsearch1:{title} {artist} audio")
                
        logger.info(f"Extraídos {len(queries)} tracks vía Spotify Embed")
        return queries
        
    except Exception as e:
        logger.error(f"Error scraping Spotify Embed: {e}")
        return []

def _extract_spotify_playlist(playlist_id: str) -> List[str]:
    return _extract_spotify_via_embed(playlist_id, "playlist")

def _extract_spotify_album(album_id: str) -> List[str]:
    return _extract_spotify_via_embed(album_id, "album")


def _extract_ytdlp_flat(url: str) -> List[str]:
    """Usa yt-dlp flat-playlist para YouTube o SoundCloud."""
    opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "entries" in info:
                urls = [entry.get("url") for entry in info["entries"] if entry.get("url")]
                # Si la URL sacada no es absoluta, a veces YT_DLP devuelve solo el ID de YT
                urls = [f"https://www.youtube.com/watch?v={u}" if len(u) == 11 and not u.startswith("http") else u for u in urls]
                logger.info(f"Extraídos {len(urls)} tracks vía yt-dlp")
                return urls
            else:
                return [url]
    except Exception as e:
        logger.error(f"Error extrayendo playlist con yt-dlp: {e}")
        return [url]


def is_playlist(url: str) -> bool:
    """Detecta si la URL es una playlist/album."""
    if SPOTIFY_PLAYLIST_PATTERN.search(url): return True
    if SPOTIFY_ALBUM_PATTERN.search(url): return True
    if "youtube.com" in url and "list=" in url: return True
    if SOUNDCLOUD_PLAYLIST_PATTERN.search(url): return True
    return False


def extract_playlist(url: str) -> List[str]:
    """
    Toma una URL y devuelve una lista de strings.
    Si es un track normal, devuelve [url].
    Si es una playlist, devuelve la lista de todas las URLs (o queries de ytsearch).
    """
    logger.info(f"Analizando URL para extracción: {url}")
    
    # Spotify Playlist
    sp_pl_match = SPOTIFY_PLAYLIST_PATTERN.search(url)
    if sp_pl_match:
        return _extract_spotify_playlist(sp_pl_match.group(2))
        
    # Spotify Album
    sp_al_match = SPOTIFY_ALBUM_PATTERN.search(url)
    if sp_al_match:
        return _extract_spotify_album(sp_al_match.group(2))
        
    # YouTube / SoundCloud Playlist
    if ("youtube.com" in url and "list=" in url) or SOUNDCLOUD_PLAYLIST_PATTERN.search(url):
        return _extract_ytdlp_flat(url)
        
    # Fallback (Single track)
    return [url]
