def get_shed_tiles(farm):
    return [(4, 4), (5, 4), (4, 5), (5, 5)]

def move_towards(curr_x, curr_y, target_x, target_y):
    if curr_x < target_x: return "EAST"
    if curr_x > target_x: return "WEST"
    if curr_y < target_y: return "SOUTH"
    if curr_y > target_y: return "NORTH"
    return "PASS"

def distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)

def agent(obs):
    p = obs["player"]
    step = obs.get("step", 0)
    farm = obs["farms"][p]
    shed = obs["private"]["shed"]
    
    farmer_pos = tuple(farm["farmer"])
    hands = [tuple(h) for h in farm.get("hands", [])]
    workers = [farmer_pos] + hands
    
    market_orders = []
    
    # Count animals and coops
    coops = []
    animals = []
    empty = []
    for y, row in enumerate(farm.get("tiles", [])):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and tile.get("kind") in ["COOP", "PASTURE"]:
                if tile.get("animal") is not None:
                    animals.append((x, y, tile))
                else:
                    coops.append((x, y))
            elif tile is None:
                empty.append((x, y))
                
    num_animals = len(animals)
    
    # Import Wheat
    wheat_needed = num_animals * 2
    if shed.get("WHEAT", 0) < wheat_needed and farm["money"] > 100:
        market_orders.append(["BUY_PRODUCT", "WHEAT", 1])
        
    # Expansion & Hiring
    if farm["money"] > 3500 and len(farm.get("unlocked_quadrants", [])) < 4:
        market_orders.append(["BUY_LAND"])
        
    target_hands = num_animals + 2 # one builder, rest caretakers
    if target_hands > 10: target_hands = 10
    hands_to_hire = target_hands - len(hands)
    if hands_to_hire > 0 and farm["money"] > 1000:
        for _ in range(hands_to_hire):
            market_orders.append(["HIRE"])

    # Buy Cow
    if len(coops) > 0 and shed.get("COW", 0) == 0 and farm["money"] >= 2500:
        market_orders.append(["BUY_ANIMAL", "COW", 1])
        
    # Financial Market Manipulation
    if num_animals > 0:
        if step % 2 == 0:
            market_orders.append(["BUY_PRODUCT", "FERTILIZER", 8])
        else:
            fert_count = shed.get("FERTILIZER", 0)
            if fert_count > 0:
                market_orders.append(["SELL", "FERTILIZER", fert_count])
            
    # Sell animal products
    for product in ["MILK", "EGG", "WOOL"]:
        count = shed.get(product, 0)
        if count > 0:
            market_orders.append(["SELL", product, count])
        
    worker_actions = []
    shed_tiles = get_shed_tiles(farm)
    
    for i, w_pos in enumerate(workers):
        wx, wy = w_pos
        inv = obs["private"]["inventories"][i]
            
        # 1. Builder Worker (Worker 0)
        if i == 0:
            if len(coops) > 0:
                # We have an empty pasture, try to get a cow and place it
                if inv.get("COW", 0) > 0:
                    # Place cow
                    target = coops[0]
                    if (wx, wy) == target:
                        worker_actions.append(["PLACE", "COW", 1])
                    else:
                        worker_actions.append([move_towards(wx, wy, target[0], target[1])])
                else:
                    # Go get cow from shed
                    if shed.get("COW", 0) > 0:
                        if (wx, wy) in shed_tiles:
                            worker_actions.append(["PICKUP", "COW", 1])
                        else:
                            target = min(shed_tiles, key=lambda s: distance(wx, wy, s[0], s[1]))
                            worker_actions.append([move_towards(wx, wy, target[0], target[1])])
                    else:
                        worker_actions.append(["PASS"])
            elif len(empty) > 0:
                # Build pasture
                target = empty[0]
                if (wx, wy) == target:
                    worker_actions.append(["BUILD_PASTURE"])
                else:
                    worker_actions.append([move_towards(wx, wy, target[0], target[1])])
            else:
                worker_actions.append(["PASS"])
            continue
            
        # 3. Animal Caretakers (Worker 1+)
        animal_idx = i - 1
        if animal_idx < len(animals):
            target_animal = animals[animal_idx]
            tx, ty, tile_data = target_animal
            
            if not tile_data.get("fed_today", False) and inv.get("WHEAT", 0) == 0:
                # Need wheat
                if shed.get("WHEAT", 0) > 0:
                    if (wx, wy) in shed_tiles:
                        worker_actions.append(["PICKUP", "WHEAT", 1])
                    else:
                        target = min(shed_tiles, key=lambda s: distance(wx, wy, s[0], s[1]))
                        worker_actions.append([move_towards(wx, wy, target[0], target[1])])
                else:
                    worker_actions.append(["PASS"])
                continue
                
            # Go to animal
            if (wx, wy) == (tx, ty):
                if not tile_data.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                    worker_actions.append(["FEED"])
                elif tile_data.get("fertilizer_available", False):
                    worker_actions.append(["COLLECT_FERTILIZER"])
                elif tile_data.get("yield_units", 0) > 0:
                    worker_actions.append(["HARVEST"])
                elif not tile_data.get("cared_today", False):
                    worker_actions.append(["CARE"])
                else:
                    worker_actions.append(["PASS"])
            else:
                worker_actions.append([move_towards(wx, wy, tx, ty)])
        else:
            worker_actions.append(["PASS"])

    farmer_action = worker_actions[0] if len(worker_actions) > 0 else ["PASS"]
    hands_actions = worker_actions[1:] if len(worker_actions) > 1 else []
    
    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": market_orders[:10]
    }
