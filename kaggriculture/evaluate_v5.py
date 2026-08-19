import sys
sys.path.append(r"G:\po\kaggriculture")
from kaggle_environments import make
import kaggriculture_v5_agent
import kaggriculture_v4_agent

def run_match(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([kaggriculture_v5_agent.agent, kaggriculture_v4_agent.agent])
    r1 = steps[-1][0].observation["farms"][0]["money"]
    r2 = steps[-1][1].observation["farms"][1]["money"]
    return r1, r2

results = []
print("Evaluating V5 vs V4 (10 episodes)...")
for i in range(10):
    r1, r2 = run_match(100 + i)
    results.append((r1, r2))
    win = "WIN" if r1 > r2 else "LOSS"
    print(f"Ep {i+1:02d}: V5={r1:8.0f}  V4={r2:8.0f}  [{win}]")

avg5 = sum(r[0] for r in results) / len(results)
avg4 = sum(r[1] for r in results) / len(results)
wins = sum(1 for r in results if r[0] > r[1])
print(f"\nV5 avg: {avg5:.0f}  |  V4 avg: {avg4:.0f}  |  V5 wins: {wins}/10")
