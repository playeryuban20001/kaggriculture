import requests, json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json"
}

url = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"

# Let's test with our own submission ID first (55612375) to see the exact payload format
payloads = [
    {"submissionId": 55612375},
    {"submission_id": 55612375},
    {"teamId": 16623716, "competitionId": 83707},
    {"teamId": 16623716},
]

for p in payloads:
    r = requests.post(url, json=p, headers=headers)
    print(f"Payload {p} -> {r.status_code} | {r.text[:120]}")
