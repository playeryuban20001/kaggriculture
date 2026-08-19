import sys
sys.path.append(r"G:\po\kaggriculture")
from kaggle_environments import make
import kaggriculture_v7_agent

env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": 300})
steps = env.run([kaggriculture_v7_agent.agent, kaggriculture_v7_agent.agent])

print("Day-by-day money V7:")
for i in range(23, len(steps), 24):
    day = i // 24
    obs = steps[i][0].observation
    m = obs["farms"][0]["money"]
    tiles = obs["farms"][0]["tiles"]
    animals = [t.get("animal") for row in tiles for t in row if isinstance(t, dict) and t.get("animal")]
    print(f"Day {day:2d}: Money={m:7.0f} | Animals={animals}")

# Final state
final_farm = steps[-1][0].observation["farms"][0]
print("\nFinal Farm tiles summary:")
placed = [t.get("animal") if t.get("animal") else t.get("kind") for row in final_farm["tiles"] for t in row if isinstance(t, dict)]
from collections import Counter
print("Final structures:", Counter(placed))
print("Final Shed:", steps[-1][0].observation["private"]["shed"])
