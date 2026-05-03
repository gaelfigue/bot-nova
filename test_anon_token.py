import urllib.request
import json

try:
    req = urllib.request.Request(
        "https://open.spotify.com/get_access_token?reason=transport&productType=web_player",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    resp = urllib.request.urlopen(req).read()
    data = json.loads(resp)
    token = data.get("accessToken")
    print("Token:", token[:15] + "...")
    
    # Try fetching the playlist
    playlist_id = "37i9dQZF1DWSpF87bP6JSF"
    api_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=5"
    api_req = urllib.request.Request(
        api_url, 
        headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
    )
    api_resp = urllib.request.urlopen(api_req).read()
    api_data = json.loads(api_resp)
    print("Success! Tracks:", len(api_data["items"]))
    for item in api_data["items"]:
        track = item.get("track", {})
        print("-", track.get("name"), "by", track.get("artists", [{}])[0].get("name"))
        
except Exception as e:
    print("Error:", e)
