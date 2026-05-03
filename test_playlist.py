import urllib.request
import re

url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8")
tracks = re.findall(r'"uri":"spotify:track:([a-zA-Z0-9]+)"', html)
print(f"Encontrados {len(tracks)} tracks")
print(list(set(tracks))[:5])
