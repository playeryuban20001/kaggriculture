import json
from collections import Counter

with open("./replays/episode-94374312-replay.json", "r", encoding="utf-8") as f:
    replay = json.load(f)

teams = replay.get("info", {}).get("TeamNames", ["P0", "P1"])
our_idx = 1 if ("llRX" in teams[1] or "James" in teams[1]) else 0
opp_idx = 1 - our_idx

final = replay["steps"][-1]
opp_tiles = final[opp_idx]["observation"]["farms"][opp_idx]["tiles"]
opp_animals = [t.get("animal") for row in opp_tiles for t in row if isinstance(t, dict) and t.get("animal")]
print("Opponent final animals:", Counter(opp_animals))
print("Opponent final hands:", len(final[opp_idx]["observation"]["farms"][opp_idx].get("hands", [])))
print("Our final hands:", len(final[our_idx]["observation"]["farms"][our_idx].get("hands", [])))

# Check why our cows weren't producing: fed_today? yield_units?
our_tiles = final[our_idx]["observation"]["farms"][our_idx]["tiles"]
our_anim_status = [(t.get("animal"), t.get("fed_today"), t.get("cared_today"), t.get("yield_units")) for row in our_tiles for t in row if isinstance(t, dict) and t.get("animal")]
print("\nOur animal status at end:", our_anim_status[:5])

# Check opponent market orders
opp_market_ops = Counter()
for step in replay["steps"]:
    for ord in step[opp_idx].get("action", {}).get("market", []):
        opp_market_ops[ord[0]] += 1
print("\nOpponent Market Ops:", opp_market_ops)
