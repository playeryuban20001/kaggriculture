import requests, json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}

url = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"

# Let's inspect what the API returns for teamId 16623716
r = requests.post(url, json={"teamId": 16623716}, headers=headers)
print("Status:", r.status_code)
print("Response text:", r.text)
