import urllib.request, json, re
url = 'https://open.spotify.com/playlist/37i9dQZF1DWSpF87bP6JSF'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    match = re.search(r'"accessToken":"(.*?)"', html)
    if match:
        token = match.group(1)
        print('Token found:', token[:10] + '...')
        api_url = 'https://api.spotify.com/v1/playlists/37i9dQZF1DWSpF87bP6JSF/tracks?limit=5'
        api_req = urllib.request.Request(api_url, headers={'Authorization': 'Bearer ' + token})
        data = json.loads(urllib.request.urlopen(api_req).read())
        print('Success:', len(data['items']), 'tracks')
    else:
        print('No token found')
except Exception as e:
    print('Error:', e)
