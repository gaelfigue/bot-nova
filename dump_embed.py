import urllib.request, re, json
url = 'https://open.spotify.com/embed/playlist/37i9dQZF1DWSpF87bP6JSF'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not match:
        match = re.search(r'<script id="resource" type="application/json">(.*?)</script>', html)
    
    if match:
        data = json.loads(match.group(1))
        # Find tracks in __NEXT_DATA__
        # Usually it's in props -> pageProps -> state -> data -> entity -> trackList
        print("Data keys:", data.keys())
        with open("dump.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
        print("Dumped to dump.json")
    else:
        print("No script data found in embed")
except Exception as e:
    print('Error:', e)
