import json
from collections import Counter

with open("./replays/episode-94374312-replay.json", "r", encoding="utf-8") as f:
    replay = json.load(f)

teams = replay.get("info", {}).get("TeamNames", ["P0", "P1"])
our_idx = 1 if ("llRX" in teams[1] or "James" in teams[1]) else 0
opp_idx = 1 - our_idx

our_sells = Counter()
opp_sells = Counter()

for step in replay["steps"]:
    for ord in step[our_idx].get("action", {}).get("market", []):
        if ord[0] == "SELL":
            our_sells[ord[1]] += ord[2] if len(ord) > 2 else 1
    for ord in step[opp_idx].get("action", {}).get("market", []):
        if ord[0] == "SELL":
            opp_sells[ord[1]] += ord[2] if len(ord) > 2 else 1

print("Our Total Sells:", our_sells)
print("Opp Total Sells:", opp_sells)
