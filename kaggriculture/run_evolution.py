"""
Kaggriculture Strategy Parameter Auto-Tuner & Evolutionary Optimizer
Uses Guided Random Mutation Hill-Climbing to optimize strategy weights over simulated seasons.
"""

import sys, random, copy, time
sys.path.append(r"G:\po\kaggriculture")

from kaggle_environments import make
import kaggriculture_v5_agent

PARAM_BOUNDS = {
    "TARGET_COWS": (6, 12),
    "TARGET_SHEEP": (2, 8),
    "TARGET_PASTURES": (12, 18),
    "DAY_BUY_QUAD2": (5, 8),
    "DAY_BUY_QUAD3": (7, 12),
    "QUAD2_MONEY": (800, 1800),
    "QUAD3_MONEY": (1500, 3000),
    "MAX_HANDS_EARLY": (1, 4),
    "MAX_HANDS_MID": (4, 8),
    "MAX_HANDS_LATE": (8, 12),
    "WHEAT_TARGET": (6, 20),
    "CROP_STOP_DAY": (12, 20),
    "MILK_FLOOR": (100, 170),
    "WOOL_FLOOR": (100, 170),
    "WHEAT_RESERVE_MULT": (1, 4),
    "LIQUIDATION_DAY": (26, 29),
}

DEFAULT_PARAMS = {
    "TARGET_COWS": 10,
    "TARGET_SHEEP": 4,
    "TARGET_PASTURES": 14,
    "DAY_BUY_QUAD2": 6,
    "DAY_BUY_QUAD3": 9,
    "QUAD2_MONEY": 1000,
    "QUAD3_MONEY": 2000,
    "MAX_HANDS_EARLY": 2,
    "MAX_HANDS_MID": 6,
    "MAX_HANDS_LATE": 12,
    "WHEAT_TARGET": 10,
    "CROP_STOP_DAY": 16,
    "MILK_FLOOR": 140,
    "WOOL_FLOOR": 140,
    "WHEAT_RESERVE_MULT": 2,
    "LIQUIDATION_DAY": 28,
}

from auto_optimizer import make_parametric_agent

TEST_SEEDS = [111, 222, 333, 444, 555]

def evaluate_params(candidate_params, seeds=TEST_SEEDS):
    cand_agent = make_parametric_agent(candidate_params)
    scores = []
    wins = 0
    for s in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": s})
        steps = env.run([cand_agent, kaggriculture_v5_agent.agent])
        score_cand = steps[-1][0].observation["farms"][0]["money"]
        score_opp  = steps[-1][1].observation["farms"][1]["money"]
        scores.append(score_cand)
        if score_cand > score_opp:
            wins += 1
    avg_score = sum(scores) / len(scores)
    return avg_score, wins, scores

def mutate(params):
    child = copy.deepcopy(params)
    # Pick 1-3 keys to mutate
    k_to_mutate = random.sample(list(PARAM_BOUNDS.keys()), k=random.randint(1, 3))
    for k in k_to_mutate:
        low, high = PARAM_BOUNDS[k]
        if isinstance(low, int):
            delta = random.choice([-2, -1, 1, 2])
            new_v = child[k] + delta
            if "MONEY" in k:
                delta = random.choice([-200, -100, 100, 200])
                new_v = child[k] + delta
            child[k] = max(low, min(high, new_v))
    return child

def run_evolution(generations=25):
    current_best = copy.deepcopy(DEFAULT_PARAMS)
    best_score, best_wins, _ = evaluate_params(current_best)
    print(f"[Gen 00/BASE] Best Avg: {best_score:.0f} | Wins: {best_wins}/5")
    
    for g in range(1, generations + 1):
        candidate = mutate(current_best)
        score, wins, _ = evaluate_params(candidate)
        
        # Fitness function: average score (with small bonus for wins)
        fitness_cand = score + wins * 2000
        fitness_best = best_score + best_wins * 2000
        
        if fitness_cand > fitness_best:
            print(f"[Gen {g:02d} - IMPROVED!] New Best Avg: {score:.0f} (+{score - best_score:+.0f}) | Wins: {wins}/5")
            current_best = copy.deepcopy(candidate)
            best_score = score
            best_wins = wins
        else:
            print(f"[Gen {g:02d}] Trial Avg: {score:.0f} (Best: {best_score:.0f})")
            
    print("\n" + "="*60)
    print(f"OPTIMIZATION FINISHED! Global Best Average Score: {best_score:.0f} ({best_wins}/5 wins)")
    print("Optimal Parameter Dictionary:")
    import pprint
    pprint.pprint(current_best)
    return current_best

if __name__ == "__main__":
    run_evolution(20)
