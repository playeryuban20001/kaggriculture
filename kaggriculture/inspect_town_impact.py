import sys
sys.path.append(r"G:\po\kaggriculture")
from kaggle_environments import make

# Run a match and observe town shops unlocked and price movements across 30 days
env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": 42})
import kaggriculture_v9_evolved
steps = env.run([kaggriculture_v9_evolved.agent, kaggriculture_v9_evolved.agent])

print("Town Shops & Price Evolution over 30 Days:")
for i in range(0, len(steps), 72): # Every 3 days
    obs = steps[i][0].observation
    day = i // 24
    shops = obs.get("town", {}).get("unlocked_shops", [])
    prices = obs.get("market", {}).get("prices", {})
    inv = obs.get("market", {}).get("inventory", {})
    print(f"\nDay {day:2d} | Unlocked Shops ({len(shops)}): {shops}")
    print(f"       Prices: MILK={prices.get('MILK')} | WOOL={prices.get('WOOL')} | STRAWBERRY={prices.get('STRAWBERRY')} | WHEAT={prices.get('WHEAT')} | FERT={prices.get('FERTILIZER')}")
    print(f"       Supply: MILK={inv.get('MILK')} | WOOL={inv.get('WOOL')} | STRAWBERRY={inv.get('STRAWBERRY')} | WHEAT={inv.get('WHEAT')}")
