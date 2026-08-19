from kaggle_environments import make
import kaggriculture_v4_agent
import kaggriculture_v3_agent
import sys
sys.path.append(r"G:\po\kaggriculture")

def run_match(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": seed})
    steps = env.run([kaggriculture_v4_agent.agent, kaggriculture_v3_agent.agent])
    final_obs = steps[-1][0].observation
    reward1 = final_obs["farms"][0]["money"]
    reward2 = final_obs["farms"][1]["money"]
    return reward1, reward2

def evaluate():
    results = []
    print("Starting evaluation of 10 independent episodes (V4 vs V3)...")
    for i in range(10):
        # We use a fixed set of seeds for reproducibility
        seed = 42 + i
        r1, r2 = run_match(seed)
        results.append((r1, r2))
        print(f"Episode {i+1:02d}/10 | V4 (Agent 1): {r1:7.1f} | V3 (Agent 2): {r2:7.1f}")
    
    return results

def print_summary(results):
    avg_v4 = sum(r[0] for r in results) / len(results)
    avg_v3 = sum(r[1] for r in results) / len(results)
    
    print("=" * 40)
    print(" EVALUATION SUMMARY (V4 vs V3)")
    print("=" * 40)
    print(f"Agent 1 (V4): {avg_v4:7.1f} avg score")
    print(f"Agent 2 (V3): {avg_v3:7.1f} avg score")
    
    wins_v4 = sum(1 for r in results if r[0] > r[1])
    wins_v3 = sum(1 for r in results if r[1] > r[0])
    ties = len(results) - wins_v4 - wins_v3
    
    print(f"Win Rate V4: {wins_v4/len(results)*100:.1f}%")
    print(f"Win Rate V3: {wins_v3/len(results)*100:.1f}%")
    print(f"Ties: {ties}")

if __name__ == "__main__":
    results = evaluate()
    print_summary(results)
