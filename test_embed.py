import urllib.request, re, json
url = 'https://open.spotify.com/embed/playlist/37i9dQZF1DWSpF87bP6JSF'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    # print(html) # Uncomment to see the raw HTML
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not match:
        match = re.search(r'<script id="resource" type="application/json">(.*?)</script>', html)
    if match:
        data = json.loads(match.group(1))
        # Intentar navegar el JSON
        print("Encontrado JSON embebido.")
    else:
        print("No script data found in embed")
except Exception as e:
    print('Error:', e)
