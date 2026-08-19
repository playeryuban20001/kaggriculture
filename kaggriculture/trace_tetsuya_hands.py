import json

with open(r"C:\Users\ma130\Downloads\94381641.json", "r", encoding="utf-8") as f:
    replay = json.load(f)

print("Tetsuya Hand 0 actions on Day 0:")
for i in range(24):
    act = replay["steps"][i][0].get("action", {})
    hands = act.get("hands", [])
    if hands:
        print(f"Step {i:2d} | Hands: {hands}")
