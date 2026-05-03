import urllib.request
import re
from bs4 import BeautifulSoup

url = 'https://open.spotify.com/playlist/37i9dQZF1DWSpF87bP6JSF'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
html = urllib.request.urlopen(req).read().decode('utf-8')

soup = BeautifulSoup(html, "html.parser")
print(f"Title: {soup.title.text}")

# Spotify inyecta tracks en un meta tag o en el body?
for tag in soup.find_all("meta"):
    if "music:song" in tag.get("property", "") or "track" in tag.get("content", ""):
        print(tag)

# Buscar en el json initial_state
match = re.search(r'<script id="initial-state" type="text/plain">(.*?)</script>', html)
if match:
    import base64
    import json
    data = base64.b64decode(match.group(1)).decode('utf-8')
    try:
        j = json.loads(data)
        print("Initial state JSON loaded!")
        # Buscar tracks
    except:
        pass
else:
    print("No initial-state found")
