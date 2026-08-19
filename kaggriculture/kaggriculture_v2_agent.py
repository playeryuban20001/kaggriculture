from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
from collections import deque

SELL_BATCH_SIZE = 10
HIRE_MONEY_THRESHOLD = 200

def _bfs_step(fx, fy, tx, ty, farm, board_size):
    if fx == tx and fy == ty:
        return None
    
    queue = deque([(fx, fy, [])])
    visited = set([(fx, fy)])
    
    while queue:
        cx, cy, path = queue.popleft()
        if cx == tx and cy == ty:
            return path[0] if path else None
            
        for dx, dy, move in [(-1, 0, "WEST"), (1, 0, "EAST"), (0, -1, "NORTH"), (0, 1, "SOUTH")]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                if (nx, ny) not in visited:
                    if farm["tiles"][ny][nx] != "LOCKED":
                        visited.add((nx, ny))
                        queue.append((nx, ny, path + [move]))
    return None

def _get_best_crop(market_prices):
    best_crop = "MELON"
    best_roi = -9999
    for crop in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
        price = market_prices.get(crop, 0)
        seed_cost = CROPS[crop]["seed"]
        max_yield_day = max(1, CROPS[crop]["max_yield_day"])
        roi = (price - seed_cost) / max_yield_day
        if roi > best_roi:
            best_roi = roi
            best_crop = crop
    return best_crop

def _find_target_tile(farm, board_size, have_seed, claimed_targets, worker_pos):
    fx, fy = worker_pos
    candidates = []
    
    for y in range(board_size):
        for x in range(board_size):
            if (x, y) in claimed_targets:
                continue
                
            tile = farm["tiles"][y][x]
            
            if tile == "LOCKED":
                continue
                
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                purpose = None
                age_ok = tile["yield_units"] > 0
                if age_ok and tile.get("planted_day") is not None:
                    purpose = "harvest"
                if not tile["watered_today"]:
                    purpose = "water" if purpose is None else purpose
                if purpose:
                    candidates.append((x, y, purpose))
            elif tile is None and have_seed:
                candidates.append((x, y, "plant"))

    if not candidates:
        return None

    priority = {"harvest": 0, "water": 1, "plant": 2}
    candidates.sort(key=lambda c: (priority[c[2]], abs(c[0] - fx) + abs(c[1] - fy)))
    
    best_target = candidates[0]
    claimed_targets.add((best_target[0], best_target[1]))
    return best_target

def _worker_logic(worker_pos, farm, board_size, seeds, day, claimed_targets):
    wx, wy = worker_pos
    tile = farm["tiles"][wy][wx]
    action = ["PASS"]
    
    has_any_seed = any(v > 0 for v in seeds.values())
    
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        age = day - tile.get("planted_day", day)
        crop_data = CROPS[tile["crop"]]
        if age >= crop_data["max_yield_day"] and tile["yield_units"] > 0:
            action = ["HARVEST"]
        elif not tile["watered_today"]:
            action = ["WATER"]
        else:
            target = _find_target_tile(farm, board_size, has_any_seed, claimed_targets, worker_pos)
            step = _bfs_step(wx, wy, target[0], target[1], farm, board_size) if target else "NO_TARGET"
            print(f"Worker {wx},{wy} -> target={target}, step={step}")
            if target and step and step != "NO_TARGET": action = [step]
    elif tile is None:
        planted = False
        for crop, count in seeds.items():
            if count > 0:
                action = ["PLANT", crop]
                seeds[crop] -= 1 
                planted = True
                break
        if not planted:
            target = _find_target_tile(farm, board_size, has_any_seed, claimed_targets, worker_pos)
            if target:
                step = _bfs_step(wx, wy, target[0], target[1], farm, board_size)
                if step: action = [step]
    else:
        target = _find_target_tile(farm, board_size, has_any_seed, claimed_targets, worker_pos)
        if target:
            step = _bfs_step(wx, wy, target[0], target[1], farm, board_size)
            if step: action = [step]
            
    return action

def agent(obs):
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    private = obs.get("private", {}) or {}
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    board_size = len(farm["tiles"])
    day = obs.get("day", 0)
    
    seeds = dict(private.get("seeds", {})) 
    shed = private.get("shed", {})
    market_prices = (obs.get("market", {}) or {}).get("prices", {})
    
    market = []
    
    # 1. Smart Batch Selling
    for item, count in shed.items():
        if count > 0:
            price = market_prices.get(item, 0)
            is_profitable = price > CROPS[item]["seed"] + 10 if item in CROPS else False
            if item in CROPS and (is_profitable or day >= 25): 
                amount_to_sell = count if day >= 25 else min(count, SELL_BATCH_SIZE)
                market.append(["SELL", item, amount_to_sell])
            elif item not in CROPS and price > 10: 
                amount_to_sell = min(count, SELL_BATCH_SIZE)
                market.append(["SELL", item, amount_to_sell])
                
    # 2. Dynamic Land Expansion
    unlocked = farm.get("unlocked_quadrants", [])
    num_unlocked = len(unlocked)
    # Disabled land buying: In a 30-day game, 1000/2000 land cost is impossible to recoup
    # We will just maximize workers on the starting 5x5 quadrant
        
    # 3. Swarm Labor Scaling
    max_hires = 5 # Maximize workers on the base 5x5 quadrant
    if day < 20 and farm["money"] > HIRE_MONEY_THRESHOLD and len(farm.get("hands", [])) < max_hires:
        market.append(["HIRE"])
        
    # 4. Crop Diversification with ROI
    best_crop = _get_best_crop(market_prices)
    seed_cost = CROPS[best_crop]["seed"]
    
    target_seeds = num_unlocked * 5
    if day < 20 and seeds.get(best_crop, 0) < target_seeds and farm["money"] >= seed_cost * target_seeds:
        market.append(["BUY_SEED", best_crop, target_seeds])
        
    # 5. Generate actions for farmer and hands
    claimed_targets = set()
    
    farmer_action = _worker_logic(farm["farmer"], farm, board_size, seeds, day, claimed_targets)
    
    hands_actions = []
    for hand_pos in farm.get("hands", []):
        hands_actions.append(_worker_logic(hand_pos, farm, board_size, seeds, day, claimed_targets))
        
    return {"farmer": farmer_action, "hands": hands_actions, "market": market[:10]}
