from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

# Constants
SELL_BATCH_SIZE = 5
HIRE_MONEY_THRESHOLD = 500

def _step_toward(fx, fy, tx, ty):
    if fx > tx: return "WEST"
    if fx < tx: return "EAST"
    if fy > ty: return "NORTH"
    if fy < ty: return "SOUTH"
    return None

def _get_best_crop(market_prices):
    """Returns the crop that currently has the highest market price."""
    best_crop = "MELON"
    best_price = 0
    for crop in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
        price = market_prices.get(crop, 0)
        if price > best_price:
            best_price = price
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
            if target:
                step = _step_toward(wx, wy, target[0], target[1])
                if step: action = [step]
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
                step = _step_toward(wx, wy, target[0], target[1])
                if step: action = [step]
    else:
        target = _find_target_tile(farm, board_size, has_any_seed, claimed_targets, worker_pos)
        if target:
            step = _step_toward(wx, wy, target[0], target[1])
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
            if price > 30: 
                amount_to_sell = min(count, SELL_BATCH_SIZE)
                market.append(["SELL", item, amount_to_sell])
                
    # 2. Labor Expansion
    if farm["money"] > HIRE_MONEY_THRESHOLD and farm.get("hires_today", 0) == 0:
        market.append(["HIRE"])
        
    # 3. Crop Diversification
    best_crop = _get_best_crop(market_prices)
    seed_cost = CROPS[best_crop]["seed"]
    
    if seeds.get(best_crop, 0) < 5 and farm["money"] >= seed_cost * 5:
        market.append(["BUY_SEED", best_crop, 5])
        
    # 4. Generate actions for farmer and hands
    claimed_targets = set()
    
    farmer_action = _worker_logic(farm["farmer"], farm, board_size, seeds, day, claimed_targets)
    
    hands_actions = []
    for hand_pos in farm.get("hands", []):
        hands_actions.append(_worker_logic(hand_pos, farm, board_size, seeds, day, claimed_targets))
        
    return {"farmer": farmer_action, "hands": hands_actions, "market": market[:10]}
