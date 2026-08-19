import sys
sys.path.append(r"G:\po\kaggriculture")
sys.path.append(r"G:\po\benchmark_agents")
from kaggle_environments import make
import ledger_lena
import kaggriculture_v5_agent
import kaggriculture_v10_ai_farmer

def run_match(agent_a, agent_b, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([agent_a.agent, agent_b.agent])
    r1 = steps[-1][0].observation["farms"][0]["money"]
    r2 = steps[-1][1].observation["farms"][1]["money"]
    return r1, r2

print("=== Evaluating 164k Top Meta (Ledger Lena) vs V5 across 5 episodes ===")
for i in range(5):
    r1, r2 = run_match(ledger_lena, kaggriculture_v5_agent, 1000 + i)
    win = "WIN" if r1 > r2 else "LOSS"
    print(f"Ep {i+1:02d}: Lena={r1:8.0f}  V5={r2:8.0f}  [{win}]")
