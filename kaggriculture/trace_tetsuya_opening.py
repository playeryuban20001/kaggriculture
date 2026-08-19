import json

with open(r"C:\Users\ma130\Downloads\94381641.json", "r", encoding="utf-8") as f:
    replay = json.load(f)

# Player 0 is tetsuya
print("Tetsuya opening steps (Days 0-3):")
for i in range(72):
    act = replay["steps"][i][0].get("action", {})
    obs = replay["steps"][i][0].get("observation", {})
    money = obs["farms"][0]["money"]
    market = act.get("market", [])
    farmer = act.get("farmer", [])
    if market or farmer != ["PASS"]:
        print(f"Step {i:2d} (Day {i//24} Hr {i%24:2d}) | Money: {money:6.0f} | Farmer: {farmer} | Market: {market}")
