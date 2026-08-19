"""
Kaggriculture V6 Agent - "Master Calmracer Blueprint"
Architecture:
1. Multi-tier Animal Herd: 9 Cow + 5 Sheep (14 Pastures)
2. Dual-Engine Cash Crop Integration: Wheat self-sufficiency + Strawberry / Melon cash crops
3. Multi-Role Labor Allocation:
   - Dedicated Animal Caretakers (1 worker / 2 animals)
   - Dynamic Crop Farmers (Plant, Water daily, Harvest mature crops)
   - Centralized Builder / Expansion Manager
4. Pure Profit Fertilizer Collect & Sell (zero arbitrage costs)
5. Dynamic Liquidity & Emergency Food Fallback
"""

def agent(obs):
    p    = obs["player"]
    step = obs.get("step", 0)
    day  = step // 24
    hour = step % 24
    farm = obs["farms"][p]
    shed = obs["private"]["shed"]
    prices = obs["market"]["prices"]
    seeds  = obs["private"].get("seeds", {})

    farmer_pos = tuple(farm["farmer"])
    hands   = [tuple(h) for h in farm.get("hands", [])]
    workers = [farmer_pos] + hands

    market_orders = []

    # ─── 1. Farm State Scanner ────────────────────────────────────────────────
    coops_empty, animals, empty_tiles, weeds = [], [], [], []
    wheat_tiles, fruit_tiles = [], []

    for y, row in enumerate(farm.get("tiles", [])):
        for x, tile in enumerate(row):
            if tile is None:
                empty_tiles.append((x, y))
            elif isinstance(tile, dict):
                kind = tile.get("kind")
                if kind in ("COOP", "PASTURE"):
                    if tile.get("animal") is not None:
                        animals.append((x, y, tile))
                    else:
                        coops_empty.append((x, y))
                elif kind == "WEED":
                    weeds.append((x, y))
                elif kind == "PLANT":
                    crop = tile.get("crop", "")
                    if crop == "WHEAT":
                        wheat_tiles.append((x, y, tile))
                    else:
                        fruit_tiles.append((x, y, tile))

    num_animals    = len(animals)
    total_pastures = num_animals + len(coops_empty)
    cows_on_farm   = sum(1 for _, _, t in animals if t.get("animal") == "COW")
    sheep_on_farm  = sum(1 for _, _, t in animals if t.get("animal") == "SHEEP")
    total_cows     = cows_on_farm + shed.get("COW", 0)
    total_sheep    = sheep_on_farm + shed.get("SHEEP", 0)

    TARGET_PASTURES = 14
    TARGET_COWS     = 9
    TARGET_SHEEP    = 5

    def dist(x1, y1, x2=4, y2=4):
        return abs(x1 - x2) + abs(y1 - y2)

    def move_towards(cx, cy, tx, ty):
        if cx < tx: return "EAST"
        if cx > tx: return "WEST"
        if cy < ty: return "SOUTH"
        if cy > ty: return "NORTH"
        return "PASS"

    SHED_TILES = [(4,4), (5,4), (4,5), (5,5)]

    # Sort tiles by distance to center shed
    empty_tiles.sort(key=lambda pos: dist(pos[0], pos[1]))
    weeds.sort(      key=lambda pos: dist(pos[0], pos[1]))
    coops_empty.sort(key=lambda pos: dist(pos[0], pos[1]))
    animals.sort(    key=lambda a:   dist(a[0], a[1]))
    wheat_tiles.sort(key=lambda a:   dist(a[0], a[1]))
    fruit_tiles.sort(key=lambda a:   dist(a[0], a[1]))

    # ─── 2. Market Orders ─────────────────────────────────────────────────────
    quads = len(farm.get("unlocked_quadrants", []))

    # A. Land Expansion (Buy Quad 2 when Quad 1 filled, Quad 3 around day 8+)
    if quads < 3 and len(empty_tiles) <= 2 and farm["money"] > 2500 and step < 500:
        market_orders.append(["BUY_LAND"])

    # B. Work Force Scaling (Max 12 workers)
    if day < 4:
        target_hands = min(2, num_animals)
    elif day < 8:
        target_hands = min(6, (num_animals // 2) + 2)
    elif day < 12:
        target_hands = min(9, (num_animals // 2) + 4)
    else:
        target_hands = min(12, (num_animals // 2) + 5)

    hands_to_hire = target_hands - len(hands)
    if hands_to_hire > 0 and farm["money"] > 300:
        for _ in range(min(hands_to_hire, 10)):
            market_orders.append(["HIRE"])

    # C. Livestock Purchases
    if step < 550 and coops_empty:
        if total_cows < TARGET_COWS and shed.get("COW", 0) == 0 and farm["money"] >= 2500:
            market_orders.append(["BUY_ANIMAL", "COW", 1])
        elif total_cows >= 4 and total_sheep < TARGET_SHEEP and shed.get("SHEEP", 0) == 0 and farm["money"] >= 2000:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])

    # D. Seed Purchases (Wheat for feed/profit, Strawberry & Melon for high cash)
    if day < 16 and farm["money"] > 1500:
        # Wheat seeds (Maintain a steady planting supply)
        if seeds.get("WHEAT", 0) < 6 and (len(wheat_tiles) + seeds.get("WHEAT", 0)) < 15:
            market_orders.append(["BUY_SEED", "WHEAT", 4])
        # Cash crops (Strawberries & Melons)
        if day >= 4 and seeds.get("STRAWBERRY", 0) < 4 and farm["money"] > 3000:
            market_orders.append(["BUY_SEED", "STRAWBERRY", 3])
        if day >= 6 and seeds.get("MELON", 0) < 3 and farm["money"] > 3500:
            market_orders.append(["BUY_SEED", "MELON", 2])

    # E. Sales Execution (Smart Price Floor + Liquidation)
    # Fertilizer: 100% collect-and-sell
    fert = shed.get("FERTILIZER", 0)
    if fert > 0:
        market_orders.append(["SELL", "FERTILIZER", fert])

    # Animal products & Cash crops
    sell_thresholds = {
        "MILK": 140, "WOOL": 140, "EGG": 20,
        "STRAWBERRY": 80, "MELON": 80, "CARROT": 25, "TOMATO": 30
    }
    for product, floor in sell_thresholds.items():
        count = shed.get(product, 0)
        if count > 0 and (prices.get(product, 0) >= floor or day >= 28):
            market_orders.append(["SELL", product, count])

    # Wheat: Keep 10 units for immediate animal feed buffer, sell the rest
    wheat_shed = shed.get("WHEAT", 0)
    wheat_reserve = max(num_animals * 2, 6)
    if wheat_shed > wheat_reserve:
        market_orders.append(["SELL", "WHEAT", wheat_shed - wheat_reserve])

    # ─── 3. Worker Action Planner ─────────────────────────────────────────────
    worker_actions = []

    def handle_animal_care(wx, wy, inv, animal_list):
        """Standardized caretaking for an assigned list of animals."""
        for tx, ty, tile in animal_list:
            fed        = tile.get("fed_today", False)
            cared      = tile.get("cared_today", False)
            fert_avail = tile.get("fertilizer_available", False)
            yield_u    = tile.get("yield_units", 0)

            # Need wheat to feed?
            if not fed and inv.get("WHEAT", 0) == 0:
                if shed.get("WHEAT", 0) > 0:
                    if (wx, wy) in SHED_TILES:
                        return ["PICKUP", "WHEAT", 3]
                    else:
                        ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                        return [move_towards(wx, wy, ns[0], ns[1])]
                else:
                    # Emergency fallback: buy wheat from market
                    market_orders.append(["BUY_PRODUCT", "WHEAT", 3])
                    return ["PASS"]

            if not fed or fert_avail or yield_u > 0 or not cared:
                if (wx, wy) == (tx, ty):
                    if not fed and inv.get("WHEAT", 0) > 0:
                        return ["FEED"]
                    elif fert_avail:
                        return ["COLLECT_FERTILIZER"]
                    elif yield_u > 0:
                        return ["HARVEST"]
                    elif not cared:
                        return ["CARE"]
                else:
                    return [move_towards(wx, wy, tx, ty)]
        return None

    def handle_crop_work(wx, wy):
        """Tend crops: Water daily, harvest mature crops."""
        # 1. Water unwatered plants
        for tx, ty, tile in wheat_tiles + fruit_tiles:
            if not tile.get("watered_today", False):
                if (wx, wy) == (tx, ty):
                    return ["WATER"]
                else:
                    return [move_towards(wx, wy, tx, ty)]
        # 2. Harvest ready plants
        for tx, ty, tile in wheat_tiles + fruit_tiles:
            if tile.get("yield_units", 0) > 0:
                if (wx, wy) == (tx, ty):
                    return ["HARVEST"]
                else:
                    return [move_towards(wx, wy, tx, ty)]
        return None

    for i, (wx, wy) in enumerate(workers):
        inv = obs["private"]["inventories"][i]

        # ── WORKER 0: General Contractor (Builder, Animal Placer, Planter) ───
        if i == 0:
            action = None

            # P1: Place animals in empty pastures
            for anim in ("COW", "SHEEP"):
                if inv.get(anim, 0) > 0 and coops_empty:
                    tx, ty = coops_empty[0]
                    action = ["PLACE", anim, 1] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                    break

            # P2: Fetch animal from shed
            if action is None:
                for anim in ("COW", "SHEEP"):
                    if shed.get(anim, 0) > 0 and coops_empty:
                        if (wx, wy) in SHED_TILES:
                            action = ["PICKUP", anim, 1]
                        else:
                            ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                            action = [move_towards(wx, wy, ns[0], ns[1])]
                        break

            # P3: If alone, farmer must care for placed animals
            if action is None and len(hands) == 0:
                action = handle_animal_care(wx, wy, inv, animals)

            # P4: Build pastures up to TARGET_PASTURES
            if action is None and total_pastures < TARGET_PASTURES and empty_tiles:
                tx, ty = empty_tiles[0]
                action = ["BUILD_PASTURE"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P5: Dig weeds
            if action is None and weeds:
                tx, ty = weeds[0]
                action = ["DIG"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P6: Plant Crops (Wheat first, then Strawberry, then Melon)
            if action is None and empty_tiles and day < 20:
                for crop in ("WHEAT", "STRAWBERRY", "MELON"):
                    if seeds.get(crop, 0) > 0:
                        tx, ty = empty_tiles[0]
                        action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

            # P7: Water and harvest crops
            if action is None:
                action = handle_crop_work(wx, wy)

            worker_actions.append(action if action else ["PASS"])
            continue

        # ── WORKERS 1+: Caretakers & Field Farmers ───────────────────────────
        hand_idx = i - 1
        my_animals = animals[hand_idx * 2 : hand_idx * 2 + 2]

        action = None
        if my_animals:
            action = handle_animal_care(wx, wy, inv, my_animals)

        # If not assigned animals or finished animal tasks, work the crop fields!
        if action is None:
            # Plant seeds if any empty tiles remain
            if empty_tiles and day < 20:
                for crop in ("WHEAT", "STRAWBERRY", "MELON"):
                    if seeds.get(crop, 0) > 0:
                        tx, ty = empty_tiles[0]
                        action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break
            if action is None:
                action = handle_crop_work(wx, wy)

        worker_actions.append(action if action else ["PASS"])

    return {
        "farmer": worker_actions[0] if worker_actions else ["PASS"],
        "hands":  worker_actions[1:] if len(worker_actions) > 1 else [],
        "market": market_orders[:10],
    }
