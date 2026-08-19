"""
Comprehensive Evaluation Matrix for Kaggriculture Agents
Benchmarks V5, V9, V10 against the Official Reference Benchmark Ladder (Tiers 1-7)
"""

import sys, time
sys.path.append(r"G:\po\kaggriculture")
sys.path.append(r"G:\po\benchmark_agents")

from kaggle_environments import make

# Import our agents
import kaggriculture_v5_agent
import kaggriculture_v9_evolved
import kaggriculture_v10_ai_farmer

# Import benchmark opponents
import wheat_walter
import rotation_rosa
import melon_mateo
import rancher_rita
import ledger_lena

OUR_AGENTS = {
    "V5 (Calmracer Herd)": kaggriculture_v5_agent.agent,
    "V9 (Evolved Master)": kaggriculture_v9_evolved.agent,
    "V10 (AI Adaptive Farmer)": kaggriculture_v10_ai_farmer.agent,
}

OPPONENTS = {
    "Tier 1 (Wheat Walter)": wheat_walter.agent,
    "Tier 2 (Rotation Rosa)": rotation_rosa.agent,
    "Tier 4 (Melon Mateo)": melon_mateo.agent,
    "Tier 5 (Rancher Rita)": rancher_rita.agent,
    "Tier 7 (164k Ledger Lena)": ledger_lena.agent,
}

SEEDS = [42, 100, 2026]

def run_match(agent_a, agent_b, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([agent_a, agent_b])
    s_a = steps[-1][0].observation["farms"][0]["money"]
    s_b = steps[-1][1].observation["farms"][1]["money"]
    return s_a, s_b

print("="*80)
print("STARTING COMPREHENSIVE BENCHMARK EVALUATION MATRIX")
print("="*80)

results = {}

for a_name, a_fn in OUR_AGENTS.items():
    print(f"\n>>> Evaluating {a_name} ...")
    results[a_name] = {}
    for opp_name, opp_fn in OPPONENTS.items():
        scores_a, scores_b = [], []
        wins = 0
        for s in SEEDS:
            sa, sb = run_match(a_fn, opp_fn, s)
            scores_a.append(sa)
            scores_b.append(sb)
            if sa > sb:
                wins += 1
        avg_a = sum(scores_a) / len(scores_a)
        avg_b = sum(scores_b) / len(scores_b)
        win_rate = (wins / len(SEEDS)) * 100
        results[a_name][opp_name] = (avg_a, avg_b, win_rate, min(scores_a), max(scores_a))
        print(f"  vs {opp_name:24s} | Us: {avg_a:8.0f} | Opp: {avg_b:8.0f} | WinRate: {win_rate:5.1f}% | Min: {min(scores_a):6.0f} | Max: {max(scores_a):6.0f}")

print("\n" + "="*80)
print("SUMMARY TABLE")
print("="*80)
print(f"{'Agent':26s} | {'vs Tier 1':14s} | {'vs Tier 2':14s} | {'vs Tier 4':14s} | {'vs Tier 5':14s} | {'vs 164k Lena':14s}")
print("-"*105)
for a_name, opp_data in results.items():
    row = [f"{a_name:26s}"]
    for opp_name in OPPONENTS.keys():
        avg_a, _, wr, _, _ = opp_data[opp_name]
        row.append(f"{avg_a:6.0f} ({wr:3.0f}%)")
    print(" | ".join(row))
