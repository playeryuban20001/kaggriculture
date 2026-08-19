import sys
sys.path.append(r"G:\po\kaggriculture")
from kaggle_environments import make
import kaggriculture_v12_preemptive_apex as v12
import kaggriculture_v11_apex as v11
import kaggriculture_v10_ai_farmer as v10

def run_match(a1, a2, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([a1.agent, a2.agent])
    s1 = steps[-1][0].observation["farms"][0]["money"]
    s2 = steps[-1][1].observation["farms"][1]["money"]
    return s1, s2

print("=== V12 (2-Step Preemptive Engine) vs V11 (Old Front-Runner) ===")
for s in range(5):
    s1, s2 = run_match(v12, v11, 100 + s)
    res = "WIN" if s1 > s2 else "LOSS"
    print(f"Seed {100+s}: V12 = {s1:8.0f} | V11 = {s2:8.0f} [{res}]")

print("\n=== V12 (2-Step Preemptive Engine) vs V10 (AI Adaptive Farmer) ===")
for s in range(5):
    s1, s2 = run_match(v12, v10, 200 + s)
    res = "WIN" if s1 > s2 else "LOSS"
    print(f"Seed {200+s}: V12 = {s1:8.0f} | V10 = {s2:8.0f} [{res}]")
