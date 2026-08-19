import json, os
from collections import defaultdict, Counter

files = [
    r"C:\Users\ma130\Downloads\94381641.json",
    r"C:\Users\ma130\Downloads\94324507.json",
    r"C:\Users\ma130\Downloads\94074550.json",
    r"C:\Users\ma130\Downloads\94100037.json",
]

def analyze_full_match(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        replay = json.load(f)
    
    info = replay.get("info", {})
    teams = info.get("TeamNames", ["Player 0", "Player 1"])
    ep_id = info.get("EpisodeId", os.path.basename(filepath))
    steps = replay["steps"]
    
    print(f"\n{'='*70}")
    print(f"EPISODE {ep_id}: {teams[0]} vs {teams[1]}")
    print(f"{'='*70}")
    
    final_obs = steps[-1]
    score_p0 = final_obs[0]["observation"]["farms"][0]["money"]
    score_p1 = final_obs[1]["observation"]["farms"][1]["money"]
    print(f"Final Scores: {teams[0]} = {score_p0:.0f} | {teams[1]} = {score_p1:.0f}")
    
    for p_idx in [0, 1]:
        p_name = teams[p_idx]
        print(f"\n--- [PLAYER {p_idx}: {p_name}] ---")
        
        # Track market actions
        market_counts = defaultdict(lambda: defaultdict(int))
        hires_per_day = defaultdict(int)
        animal_buys = defaultdict(int)
        seed_buys = defaultdict(int)
        land_buys_timeline = []
        money_timeline = {}
        
        # Farmer actions
        farmer_actions = Counter()
        
        for step_idx, step in enumerate(steps):
            if step_idx == 0: continue
            day = step_idx // 24
            hour = step_idx % 24
            
            p_step = step[p_idx]
            act = p_step.get("action", {})
            obs = p_step.get("observation", {})
            
            if obs:
                m = obs.get("farms", [{}, {}])[p_idx].get("money")
                if m is not None and (hour == 23 or step_idx == len(steps)-1):
                    money_timeline[day] = m
            
            # Market ops
            for order in act.get("market", []):
                op = order[0]
                item = order[1] if len(order) > 1 else "?"
                n = order[2] if len(order) > 2 else 1
                market_counts[op][item] += n
                if op == "HIRE":
                    hires_per_day[day] += 1
                elif op == "BUY_ANIMAL":
                    animal_buys[item] += n
                elif op == "BUY_SEED":
                    seed_buys[item] += n
                elif op == "BUY_LAND":
                    land_buys_timeline.append((day, hour, step_idx))
            
            fa = act.get("farmer", ["PASS"])
            if isinstance(fa, list) and fa:
                farmer_actions[fa[0]] += 1
        
        # Final farm status
        final_farm = steps[-1][p_idx]["observation"]["farms"][p_idx]
        tiles = final_farm.get("tiles", [])
        quads = final_farm.get("unlocked_quadrants", [])
        
        placed_animals = []
        plants = []
        for row in tiles:
            for t in row:
                if isinstance(t, dict):
                    if t.get("animal"):
                        placed_animals.append(t.get("animal"))
                    elif t.get("kind") == "PLANT":
                        plants.append(t.get("crop"))
        
        print(f"  Final Money: {money_timeline.get(29, 0):.0f}")
        print(f"  Land Unlocked: {quads} (Bought at steps: {land_buys_timeline})")
        print(f"  Animals on Farm: {dict(Counter(placed_animals))}")
        print(f"  Plants on Farm: {dict(Counter(plants))}")
        print(f"  Total Animals Bought: {dict(animal_buys)}")
        print(f"  Total Seeds Bought: {dict(seed_buys)}")
        print(f"  Total Sells: {dict(market_counts.get('SELL', {}))}")
        print(f"  Total Products Bought: {dict(market_counts.get('BUY_PRODUCT', {}))}")
        
        # Print money milestones
        milestones = [0, 4, 8, 12, 16, 20, 24, 28, 29]
        m_str = " | ".join([f"D{d}:{money_timeline.get(d, 0):.0f}" for d in milestones if d in money_timeline])
        print(f"  Money Milestones: {m_str}")
        
        # Hires summary
        h_early = sum(hires_per_day[d] for d in range(5))
        h_mid = sum(hires_per_day[d] for d in range(5, 15))
        h_late = sum(hires_per_day[d] for d in range(15, 30))
        print(f"  Hires: Days 0-4={h_early} | Days 5-14={h_mid} | Days 15-29={h_late} | Peak/day={max(hires_per_day.values()) if hires_per_day else 0}")

for f in files:
    if os.path.exists(f):
        analyze_full_match(f)
    else:
        print(f"File not found: {f}")
