import time
import copy
import numpy as np
from kaggle_environments import make

import kaggriculture_v2_agent
import kaggriculture_v3_agent

NUM_EPISODES = 10
COPY_OBSERVATION = False

def evaluate_agents(agent1, agent2, num_episodes=10):
    env = make("kaggriculture", configuration={"episodeSteps": 720})
    
    results = {
        "agent1_scores": [],
        "agent2_scores": [],
        "agent1_times": [],
        "agent2_times": [],
        "errors": []
    }
    
    print(f"Starting evaluation of {num_episodes} independent episodes...")
    
    for i in range(num_episodes):
        def wrapped_agent1(obs):
            safe_obs = copy.deepcopy(obs) if COPY_OBSERVATION else obs
            t0 = time.perf_counter()
            act = agent1(safe_obs)
            results["agent1_times"].append(time.perf_counter() - t0)
            return act
            
        def wrapped_agent2(obs):
            safe_obs = copy.deepcopy(obs) if COPY_OBSERVATION else obs
            t0 = time.perf_counter()
            act = agent2(safe_obs)
            results["agent2_times"].append(time.perf_counter() - t0)
            return act

        steps = env.run([wrapped_agent1, wrapped_agent2])
        final_state = steps[-1]
        
        if final_state[0].status == "ERROR" or final_state[1].status == "ERROR":
            results["errors"].append((i, final_state[0].status, final_state[1].status))
            
        r1 = final_state[0].reward if final_state[0].reward is not None else 0
        r2 = final_state[1].reward if final_state[1].reward is not None else 0
        
        results["agent1_scores"].append(r1)
        results["agent2_scores"].append(r2)
        
        print(f"Episode {i+1:02d}/{num_episodes} | V3 (Agent 1): {r1:7.1f} | V2 (Agent 2): {r2:7.1f}")
        
    return results

def print_summary(results):
    a1_scores = np.array(results["agent1_scores"])
    a2_scores = np.array(results["agent2_scores"])
    
    wins = np.sum(a1_scores > a2_scores)
    losses = np.sum(a1_scores < a2_scores)
    ties = np.sum(a1_scores == a2_scores)
    
    n = len(a1_scores)
    
    print("=" * 40)
    print("📊 EVALUATION SUMMARY (V3 vs V2)")
    print("=" * 40)
    print(f"Total Episodes: {n}")
    print(f"Win/Loss/Tie: {wins}W - {losses}L - {ties}T")
    print(f"Win Rate: {(wins/n)*100:.1f}%\n")
    
    print("Agent 1 (V3 Challenger) Stats:")
    print(f"  Mean Score:   {np.mean(a1_scores):.2f}")
    
    print("\nAgent 2 (V2 Baseline) Stats:")
    print(f"  Mean Score:   {np.mean(a2_scores):.2f}")
    
    if results["errors"]:
        print(f"\n⚠️ WARNING: {len(results['errors'])} episodes ended in an ERROR state.")
    else:
        print("\n✅ No errors detected during evaluation.")

if __name__ == "__main__":
    results = evaluate_agents(kaggriculture_v3_agent.agent, kaggriculture_v2_agent.agent, num_episodes=NUM_EPISODES)
    print_summary(results)
