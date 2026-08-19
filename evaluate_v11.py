import sys
sys.path.append(r"G:\po\kaggriculture")
sys.path.append(r"G:\po\benchmark_agents")
from kaggle_environments import make

import kaggriculture_v11_apex
import kaggriculture_v10_ai_farmer
import kaggriculture_v5_agent
import ledger_lena
import rancher_rita

def run_match(agent_a, agent_b, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([agent_a.agent, agent_b.agent])
    s_a = steps[-1][0].observation["farms"][0]["money"]
    s_b = steps[-1][1].observation["farms"][1]["money"]
    return s_a, s_b

print("="*75)
print("BENCHMARKING V11 APEX DOMINATOR")
print("="*75)

opponents = {
    "vs 164k Ledger Lena": ledger_lena,
    "vs Tier 5 Rancher Rita": rancher_rita,
    "vs Our V10 AI Farmer": kaggriculture_v10_ai_farmer,
    "vs Our V5 Calmracer": kaggriculture_v5_agent,
}

for name, opp in opponents.items():
    print(f"\n>>> Running {name} across 3 seeds ...")
    scores_v11, scores_opp = [], []
    for s in [42, 100, 2026]:
        sv11, sopp = run_match(kaggriculture_v11_apex, opp, s)
        scores_v11.append(sv11)
        scores_opp.append(sopp)
        res = "WIN" if sv11 > sopp else "LOSS"
        print(f"  Seed {s:4d}: V11={sv11:8.0f} | Opp={sopp:8.0f} [{res}]")
    avg_v11 = sum(scores_v11)/len(scores_v11)
    avg_opp = sum(scores_opp)/len(scores_opp)
    print(f"  --> Average: V11 = {avg_v11:8.0f} | Opp = {avg_opp:8.0f}")
