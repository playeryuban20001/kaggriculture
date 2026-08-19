import sys
sys.path.append(r"G:\po\kaggriculture")
from kaggle_environments import make
import kaggriculture_v13_infinite_horizon as v13
import kaggriculture_v12_preemptive_apex as v12

def run_match(a1, a2, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([a1.agent, a2.agent])
    s1 = steps[-1][0].observation["farms"][0]["money"]
    s2 = steps[-1][1].observation["farms"][1]["money"]
    return s1, s2

print("=== V13 (Infinite Horizon) vs V12 (2-Step Horizon) ===")
for s in range(5):
    s1, s2 = run_match(v13, v12, 1000 + s)
    res = "WIN" if s1 > s2 else "LOSS" if s1 < s2 else "TIE"
    print(f"Seed {1000+s}: V13 = {s1:8.0f} | V12 = {s2:8.0f} [{res}]")
