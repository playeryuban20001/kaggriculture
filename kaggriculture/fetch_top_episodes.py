import requests, json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json"
}

# Try fetching episodes by teamId for tetsuya (16623716) and カワシギ (16677252)
for name, tid in [("tetsuya", 16623716), ("カワシギ", 16677252)]:
    try:
        url = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
        r = requests.post(url, json={"teamId": tid}, headers=headers, timeout=10)
        print(f"{name} ({tid}) -> Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            episodes = data.get("episodes", [])
            print(f"  Found {len(episodes)} episodes for {name}")
            for ep in episodes[:5]:
                print(f"    Ep ID: {ep.get('id')} | State: {ep.get('state')} | Type: {ep.get('type')}")
    except Exception as e:
        print(f"Error {name}: {e}")
