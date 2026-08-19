"""
Kaggriculture V8 Master Agent - Synthesis of Top Leaderboard Strategies
(tetsuya #1 + カワシギ #2 + Calmracer Blueprint)

Core Architectural Pillars:
1. Dairy & Wool Dual-Core: 10 Cows + 4-6 Sheep in Pastures
2. Pure Fertilizer Direct Monetization: 100% collect and sell daily for free cashflow
3. Precision Land Expansion: Day 7 (NE Quad, $1000) & Day 9 (SW Quad, $2000). Never Quad 4.
4. Guaranteed Animal Life Support: Zero-cost self-feed + emergency market wheat buffer
5. Distance-Optimized Assembly Line: 1 hand per 2 animals with strict Manhattan pathing
6. Smart Price Floor & Day 28+ Full Liquidation
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
    pastures_empty, animals, empty_tiles, weeds = [], [], [], []
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
                        pastures_empty.append((x, y))
                elif kind == "WEED":
                    weeds.append((x, y))
                elif kind == "PLANT":
                    crop = tile.get("crop", "")
                    if crop == "WHEAT":
                        wheat_tiles.append((x, y, tile))
                    else:
                        fruit_tiles.append((x, y, tile))

    num_animals   = len(animals)
    cows_on_farm  = sum(1 for _, _, t in animals if t.get("animal") == "COW")
    sheep_on_farm = sum(1 for _, _, t in animals if t.get("animal") == "SHEEP")

    total_cows     = cows_on_farm + shed.get("COW", 0)
    total_sheep    = sheep_on_farm + shed.get("SHEEP", 0)
    total_pastures = (cows_on_farm + sheep_on_farm) + len(pastures_empty)

    # Strategy Targets: 10 Cows + 6 Sheep (Max 16 Pastures across 3 Quads)
    TARGET_COWS     = 10
    TARGET_SHEEP    = 6
    TARGET_PASTURES = 16

    def dist(x1, y1, x2=4, y2=4):
        return abs(x1 - x2) + abs(y1 - y2)

    def move_towards(cx, cy, tx, ty):
        if cx < tx: return "EAST"
        if cx > tx: return "WEST"
        if cy < ty: return "SOUTH"
        if cy > ty: return "NORTH"
        return "PASS"

    SHED_TILES = [(4,4), (5,4), (4,5), (5,5)]

    # Manhattan Distance sorting (closest to center shed first)
    empty_tiles.sort(   key=lambda pos: dist(pos[0], pos[1]))
    weeds.sort(         key=lambda pos: dist(pos[0], pos[1]))
    pastures_empty.sort(key=lambda pos: dist(pos[0], pos[1]))
    animals.sort(       key=lambda a:   dist(a[0], a[1]))
    wheat_tiles.sort(   key=lambda a:   dist(a[0], a[1]))
    fruit_tiles.sort(   key=lambda a:   dist(a[0], a[1]))

    # ─── 2. Market Orders (Tetsuya & Kawashigi Proven Policy) ─────────────────
    quads = len(farm.get("unlocked_quadrants", []))

    # A. Day 7 & Day 9 Precision Land Expansion
    if hour <= 2 and step < 480:
        if quads == 1 and (day >= 6 or len(empty_tiles) <= 1) and farm["money"] >= 1000:
            market_orders.append(["BUY_LAND"])
        elif quads == 2 and (day >= 8 or len(empty_tiles) <= 2) and farm["money"] >= 2000:
            market_orders.append(["BUY_LAND"])

    # B. Dynamic Labor Scaling (1 hand per 2 animals + 1 builder)
    if hour == 0 and step > 0:
        if num_animals == 0:
            target_hands = 0
        elif day < 4:
            target_hands = min(2, (num_animals // 2) + 1)
        elif day < 8:
            target_hands = min(6, (num_animals // 2) + 1)
        elif day < 12:
            target_hands = min(9, (num_animals // 2) + 1)
        else:
            target_hands = min(12, (num_animals // 2) + 1)

        hands_to_hire = target_hands - len(hands)
        if hands_to_hire > 0 and farm["money"] > 300:
            for _ in range(min(hands_to_hire, 10)):
                market_orders.append(["HIRE"])

    # C. Livestock Progression (Cows first -> Sheep hedge)
    if step < 520 and len(pastures_empty) > 0 and hour <= 4:
        if total_cows < TARGET_COWS and shed.get("COW", 0) == 0 and farm["money"] >= 2500:
            market_orders.append(["BUY_ANIMAL", "COW", 1])
        elif total_cows >= 4 and total_sheep < TARGET_SHEEP and shed.get("SHEEP", 0) == 0 and farm["money"] >= 2000:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])

    # D. Supplementary Wheat & Cash Crop Seeds
    if day < 16 and farm["money"] > 3000 and hour <= 2:
        if seeds.get("WHEAT", 0) < 5 and (len(wheat_tiles) + seeds.get("WHEAT", 0)) < 12:
            market_orders.append(["BUY_SEED", "WHEAT", 4])
        if day >= 6 and seeds.get("STRAWBERRY", 0) < 3 and farm["money"] > 5000:
            market_orders.append(["BUY_SEED", "STRAWBERRY", 3])

    # E. Pure Profit Fertilizer Monetization
    fert = shed.get("FERTILIZER", 0)
    if fert > 0:
        market_orders.append(["SELL", "FERTILIZER", fert])

    # F. Product Sales with Price Floor & Day 28+ Final Liquidation
    sell_floors = {
        "MILK": 140, "WOOL": 140, "EGG": 15,
        "STRAWBERRY": 75, "MELON": 75, "CARROT": 20, "TOMATO": 25
    }
    for prod, floor in sell_floors.items():
        count = shed.get(prod, 0)
        if count > 0 and (prices.get(prod, 0) >= floor or day >= 28):
            market_orders.append(["SELL", prod, count])

    # G. Wheat Stockpile Management
    wheat_shed = shed.get("WHEAT", 0)
    wheat_reserve = max(num_animals * 2, 4)
    if wheat_shed > wheat_reserve:
        market_orders.append(["SELL", "WHEAT", wheat_shed - wheat_reserve])

    # ─── 3. Multi-Agent Action Coordination ───────────────────────────────────
    worker_actions = []

    def handle_animal_care(wx, wy, inv, my_animals):
        """Zero-waste pipeline: feed, harvest, collect fertilizer, and care."""
        for tx, ty, tile in my_animals:
            fed        = tile.get("fed_today", False)
            cared      = tile.get("cared_today", False)
            fert_avail = tile.get("fertilizer_available", False)
            yield_u    = tile.get("yield_units", 0)

            # Check wheat for feeding
            if not fed and inv.get("WHEAT", 0) == 0:
                if shed.get("WHEAT", 0) > 0:
                    if (wx, wy) in SHED_TILES:
                        return ["PICKUP", "WHEAT", 3]
                    else:
                        ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                        return [move_towards(wx, wy, ns[0], ns[1])]
                else:
                    # Emergency safety net: buy wheat from market immediately
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
        """Water unwatered crops and harvest mature plants."""
        for tx, ty, tile in wheat_tiles + fruit_tiles:
            if not tile.get("watered_today", False):
                if (wx, wy) == (tx, ty):
                    return ["WATER"]
                else:
                    return [move_towards(wx, wy, tx, ty)]
        for tx, ty, tile in wheat_tiles + fruit_tiles:
            if tile.get("yield_units", 0) > 0:
                if (wx, wy) == (tx, ty):
                    return ["HARVEST"]
                else:
                    return [move_towards(wx, wy, tx, ty)]
        return None

    for i, (wx, wy) in enumerate(workers):
        inv = obs["private"]["inventories"][i]

        # ── WORKER 0: Lead Builder, Animal Placer, General Manager ───────────
        if i == 0:
            action = None

            # P1: Place Cow/Sheep from inventory into Pasture
            for anim in ("COW", "SHEEP"):
                if inv.get(anim, 0) > 0 and pastures_empty:
                    tx, ty = pastures_empty[0]
                    action = ["PLACE", anim, 1] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                    break

            # P2: Fetch Cow/Sheep from Shed if Pasture is waiting
            if action is None:
                for anim in ("COW", "SHEEP"):
                    if shed.get(anim, 0) > 0 and pastures_empty:
                        if (wx, wy) in SHED_TILES:
                            action = ["PICKUP", anim, 1]
                        else:
                            ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                            action = [move_towards(wx, wy, ns[0], ns[1])]
                        break

            # P3: Care for animals if alone (Day 0-3 bootstrap)
            if action is None and len(hands) == 0 and animals:
                action = handle_animal_care(wx, wy, inv, animals)

            # P4: Build Pastures up to target
            if action is None and total_pastures < TARGET_PASTURES and empty_tiles:
                tx, ty = empty_tiles[0]
                action = ["BUILD_PASTURE"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P5: Clear Weeds
            if action is None and weeds:
                tx, ty = weeds[0]
                action = ["DIG"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P6: Plant Crops on spare empty tiles
            if action is None and empty_tiles and day < 18:
                for crop in ("WHEAT", "STRAWBERRY"):
                    if seeds.get(crop, 0) > 0:
                        tx, ty = empty_tiles[0]
                        action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

            # P7: Water & Harvest crops
            if action is None:
                action = handle_crop_work(wx, wy)

            worker_actions.append(action if action else ["PASS"])
            continue

        # ── WORKERS 1+: Caretakers (2 animals each) & Field Support ──────────
        hand_idx = i - 1
        my_animals = animals[hand_idx * 2 : hand_idx * 2 + 2]
        action = None

        # P1: Tend assigned animals
        if my_animals:
            action = handle_animal_care(wx, wy, inv, my_animals)

        # P2: Help plant seeds on empty tiles
        if action is None and empty_tiles and day < 18:
            for crop in ("WHEAT", "STRAWBERRY"):
                if seeds.get(crop, 0) > 0:
                    tx, ty = empty_tiles[0]
                    action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                    break

        # P3: Help water and harvest crops
        if action is None:
            action = handle_crop_work(wx, wy)

        worker_actions.append(action if action else ["PASS"])

    return {
        "farmer": worker_actions[0] if worker_actions else ["PASS"],
        "hands":  worker_actions[1:] if len(worker_actions) > 1 else [],
        "market": market_orders[:10],
    }
