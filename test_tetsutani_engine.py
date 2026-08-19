import sys
sys.path.append(r"G:\po\kaggriculture")
sys.path.append(r"G:\po\tetsutani_agent")
sys.path.append(r"G:\po\benchmark_agents")
from kaggle_environments import make

import tetsutani_agent.main as tetsu
import ledger_lena
import kaggriculture_v11_apex

def run_match(agent_a, agent_b, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([agent_a.agent, agent_b.agent])
    s_a = steps[-1][0].observation["farms"][0]["money"]
    s_b = steps[-1][1].observation["farms"][1]["money"]
    return s_a, s_b

print("=== Benchmarking Tetsutani 2-Step Preemptive Engine vs 164k Lena (10 seeds) ===")
wins, losses = 0, 0
scores_tetsu, scores_lena = [], []

for s in range(10):
    st, sl = run_match(tetsu, ledger_lena, 5000 + s)
    scores_tetsu.append(st)
    scores_lena.append(sl)
    if st > sl:
        wins += 1
        res = "WIN"
    else:
        losses += 1
        res = "LOSS"
    print(f"Match {s+1:02d} (Seed {5000+s}): Tetsutani = {st:8.0f} | Lena = {sl:8.0f} [{res}]")

print(f"\nResult: Tetsutani {wins}W - {losses}L vs Lena")
print(f"Avg Score: Tetsutani = {sum(scores_tetsu)/10:.0f} | Lena = {sum(scores_lena)/10:.0f}")
