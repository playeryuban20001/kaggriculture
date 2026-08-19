import json

with open("./replays/episode-94374312-replay.json", "r", encoding="utf-8") as f:
    replay = json.load(f)

teams = replay.get("info", {}).get("TeamNames", ["P0", "P1"])
our_idx = 1 if ("llRX" in teams[1] or "James" in teams[1]) else 0
opp_idx = 1 - our_idx

final = replay["steps"][-1]
our_money = final[our_idx]["observation"]["farms"][our_idx]["money"]
opp_money = final[opp_idx]["observation"]["farms"][opp_idx]["money"]

print(f"=== Episode 94374312 (V5 First Public Match) ===")
print(f"Us ({teams[our_idx]}): {our_money:.0f}")
print(f"Opponent ({teams[opp_idx]}): {opp_money:.0f}")
print(f"Result: {'WIN' if our_money > opp_money else 'LOSS'}")

# Check our animals at end
tiles = final[our_idx]["observation"]["farms"][our_idx]["tiles"]
animals = [t.get("animal") for row in tiles for t in row if isinstance(t, dict) and t.get("animal")]
from collections import Counter
print(f"Our animals: {dict(Counter(animals))}")
