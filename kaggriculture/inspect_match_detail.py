import json

with open("./replays/episode-94374312-replay.json", "r", encoding="utf-8") as f:
    replay = json.load(f)

teams = replay.get("info", {}).get("TeamNames", ["P0", "P1"])
our_idx = 1 if ("llRX" in teams[1] or "James" in teams[1]) else 0
opp_idx = 1 - our_idx

final = replay["steps"][-1]
our_shed = final[our_idx]["observation"]["private"]["shed"]
opp_shed = final[opp_idx]["observation"]["private"]["shed"]

print("Our Final Shed:", our_shed)
print("Opp Final Shed:", opp_shed)

# Check money progression
for step_idx in range(0, len(replay["steps"]), 48):
    day = step_idx // 24
    our_m = replay["steps"][step_idx][our_idx]["observation"]["farms"][our_idx]["money"]
    opp_m = replay["steps"][step_idx][opp_idx]["observation"]["farms"][opp_idx]["money"]
    print(f"Day {day:2d} | Us: {our_m:8.0f} | Opp: {opp_m:8.0f}")
