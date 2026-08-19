"""
Kaggriculture V7 Agent - "Tetsuya Master Class"
Exact Replication of Leaderboard #1 (tetsuya):
1. Day 0 Blitzkrieg: 5 Hires + Cow/Sheep buys + Wheat seeds + Strawberry seeds
2. Immediate Coordinated Deployment:
   - Builders/Herders: Pickup animals -> Build pasture -> Place -> Feed -> Care
   - Planters: Move to empty tiles -> Plant Wheat/Strawberry -> Water SAME DAY
3. Daily Multi-Agent Rhythm:
   - Morning: Pickup wheat from shed -> Feed animals -> Collect Fertilizer -> Care -> Harvest
   - Noon: Water crops -> Harvest mature plants -> Plant new seeds on empty tiles
   - Evening: Return to shed / DROP inventory -> 100% Sell Fertilizer -> Sell Milk/Wool/Crops
4. Precision Land Expansion: Day 7 (Quad 2, $1000), Day 9 (Quad 3, $2000)
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
    coops_empty, pastures_empty = [], []
    animals, empty_tiles, weeds = [], [], []
    wheat_tiles, fruit_tiles = [], []

    for y, row in enumerate(farm.get("tiles", [])):
        for x, tile in enumerate(row):
            if tile is None:
                empty_tiles.append((x, y))
            elif isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "COOP":
                    if tile.get("animal") is not None:
                        animals.append((x, y, tile))
                    else:
                        coops_empty.append((x, y))
                elif kind == "PASTURE":
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

    TARGET_COWS     = 8
    TARGET_SHEEP    = 6
    TARGET_PASTURES = 14

    def dist(x1, y1, x2=4, y2=4):
        return abs(x1 - x2) + abs(y1 - y2)

    def move_towards(cx, cy, tx, ty):
        if cx < tx: return "EAST"
        if cx > tx: return "WEST"
        if cy < ty: return "SOUTH"
        if cy > ty: return "NORTH"
        return "PASS"

    SHED_TILES = [(4,4), (5,4), (4,5), (5,5)]

    empty_tiles.sort(   key=lambda pos: dist(pos[0], pos[1]))
    weeds.sort(         key=lambda pos: dist(pos[0], pos[1]))
    pastures_empty.sort(key=lambda pos: dist(pos[0], pos[1]))
    animals.sort(       key=lambda a:   dist(a[0], a[1]))
    wheat_tiles.sort(   key=lambda a:   dist(a[0], a[1]))
    fruit_tiles.sort(   key=lambda a:   dist(a[0], a[1]))

    # ─── 2. Market Orders (Tetsuya Opening & Growth) ──────────────────────────
    quads = len(farm.get("unlocked_quadrants", []))

    # Day 0 Opening Setup
    if step == 0:
        market_orders.append(["BUY_PRODUCT", "WHEAT", 5])
        market_orders.append(["BUY_ANIMAL", "COW", 1])
        market_orders.append(["BUY_ANIMAL", "SHEEP", 1])
        market_orders.append(["BUY_SEED", "WHEAT", 6])
        for _ in range(2):
            market_orders.append(["HIRE"])

    # Precision Land Purchases (Day 7: Quad 2 $1000, Day 9: Quad 3 $2000)
    if hour == 1:
        if quads == 1 and (day >= 6 or len(empty_tiles) <= 2) and farm["money"] >= 1000:
            market_orders.append(["BUY_LAND"])
        elif quads == 2 and (day >= 8 or len(empty_tiles) <= 3) and farm["money"] >= 2000:
            market_orders.append(["BUY_LAND"])

    # Optimized Workforce Scaling (Scale with animals and farm tasks)
    if hour == 0 and step > 0:
        if num_animals == 0:
            target_hands = 0
        elif day < 4:
            target_hands = min(3, (num_animals // 2) + 1)
        elif day < 8:
            target_hands = min(6, (num_animals // 2) + 2)
        elif day < 13:
            target_hands = min(9, (num_animals // 2) + 3)
        else:
            target_hands = min(12, (num_animals // 2) + 4)

        hands_to_hire = target_hands - len(hands)
        if hands_to_hire > 0 and farm["money"] > 300:
            for _ in range(min(hands_to_hire, 10)):
                market_orders.append(["HIRE"])

    # Continuous Livestock Replenishment
    if step < 520 and len(pastures_empty) > 0 and hour <= 4:
        if total_cows < TARGET_COWS and shed.get("COW", 0) == 0 and farm["money"] >= 2600:
            market_orders.append(["BUY_ANIMAL", "COW", 1])
        elif total_cows >= 2 and total_sheep < TARGET_SHEEP and shed.get("SHEEP", 0) == 0 and farm["money"] >= 2100:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])

    # Crop Trinity Seed Supply
    if day < 18 and farm["money"] > 500 and hour <= 4:
        if seeds.get("WHEAT", 0) < 6 and (len(wheat_tiles) + seeds.get("WHEAT", 0)) < 18:
            market_orders.append(["BUY_SEED", "WHEAT", 5])
        if day >= 2 and seeds.get("STRAWBERRY", 0) < 4 and farm["money"] > 1500:
            market_orders.append(["BUY_SEED", "STRAWBERRY", 3])
        if day >= 5 and seeds.get("MELON", 0) < 2 and farm["money"] > 2500:
            market_orders.append(["BUY_SEED", "MELON", 2])

    # Market Sales (Fertilizer 100% + Product Floors)
    fert = shed.get("FERTILIZER", 0)
    if fert > 0:
        market_orders.append(["SELL", "FERTILIZER", fert])

    sell_floors = {
        "MILK": 130, "WOOL": 130, "EGG": 15,
        "STRAWBERRY": 70, "MELON": 70, "CARROT": 20, "TOMATO": 25
    }
    for prod, floor in sell_floors.items():
        count = shed.get(prod, 0)
        if count > 0 and (prices.get(prod, 0) >= floor or day >= 28):
            market_orders.append(["SELL", prod, count])

    # Wheat: retain buffer for feeding, sell surplus
    wheat_shed = shed.get("WHEAT", 0)
    wheat_reserve = max(num_animals * 2, 5)
    if wheat_shed > wheat_reserve:
        market_orders.append(["SELL", "WHEAT", wheat_shed - wheat_reserve])

    # ─── 3. Multi-Agent Action Coordination ───────────────────────────────────
    worker_actions = []

    def handle_animal_care(wx, wy, inv, my_animals):
        """Feeding, collecting fertilizer, harvesting, and caring for assigned animals."""
        for tx, ty, tile in my_animals:
            fed        = tile.get("fed_today", False)
            cared      = tile.get("cared_today", False)
            fert_avail = tile.get("fertilizer_available", False)
            yield_u    = tile.get("yield_units", 0)

            # Needs wheat?
            if not fed and inv.get("WHEAT", 0) == 0:
                if shed.get("WHEAT", 0) > 0:
                    if (wx, wy) in SHED_TILES:
                        return ["PICKUP", "WHEAT", 3]
                    else:
                        ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                        return [move_towards(wx, wy, ns[0], ns[1])]
                else:
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
        """Water unwatered crops (CRITICAL: water same day) and harvest mature crops."""
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

        # ── WORKER 0: General Contractor & Lead Herder ───────────────────────
        if i == 0:
            action = None

            # P1: Place Cow/Sheep in empty Pasture
            for anim in ("COW", "SHEEP"):
                if inv.get(anim, 0) > 0 and pastures_empty:
                    tx, ty = pastures_empty[0]
                    action = ["PLACE", anim, 1] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                    break

            # P2: Fetch Cow/Sheep from Shed
            if action is None:
                for anim in ("COW", "SHEEP"):
                    if shed.get(anim, 0) > 0 and pastures_empty:
                        if (wx, wy) in SHED_TILES:
                            action = ["PICKUP", anim, 1]
                        else:
                            ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                            action = [move_towards(wx, wy, ns[0], ns[1])]
                        break

            # P3: Care for animals if hands are few
            if action is None and len(hands) <= 2 and animals:
                action = handle_animal_care(wx, wy, inv, animals)

            # P4: Build Pasture up to target
            if action is None and total_pastures < TARGET_PASTURES and empty_tiles:
                tx, ty = empty_tiles[0]
                action = ["BUILD_PASTURE"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P5: Clear Weeds
            if action is None and weeds:
                tx, ty = weeds[0]
                action = ["DIG"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P6: Plant Crops on spare empty tiles
            if action is None and empty_tiles and day < 20:
                for crop in ("WHEAT", "STRAWBERRY", "MELON"):
                    if seeds.get(crop, 0) > 0:
                        tx, ty = empty_tiles[0]
                        action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

            # P7: Water & harvest crops
            if action is None:
                action = handle_crop_work(wx, wy)

            # P8: End of day return to shed if holding items
            if action is None and hour >= 21 and any(v > 0 for v in inv.values()):
                if (wx, wy) in SHED_TILES:
                    action = ["DROP"]
                else:
                    ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                    action = [move_towards(wx, wy, ns[0], ns[1])]

            worker_actions.append(action if action else ["PASS"])
            continue

        # ── WORKERS 1+: Caretakers & Field Farmers ───────────────────────────
        hand_idx = i - 1

        # Herders take animals; field workers (or herders after animals are done) work crops
        my_animals = animals[hand_idx * 2 : hand_idx * 2 + 2]
        action = None

        # P1: Place animal if holding one
        for anim in ("COW", "SHEEP"):
            if inv.get(anim, 0) > 0 and pastures_empty:
                tx, ty = pastures_empty[0]
                action = ["PLACE", anim, 1] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                break

        # P2: Fetch animal if shed has one and pasture is empty
        if action is None and hand_idx == 0:
            for anim in ("COW", "SHEEP"):
                if shed.get(anim, 0) > 0 and pastures_empty:
                    if (wx, wy) in SHED_TILES:
                        action = ["PICKUP", anim, 1]
                    else:
                        ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                        action = [move_towards(wx, wy, ns[0], ns[1])]
                    break

        # P3: Care for assigned animals
        if action is None and my_animals:
            action = handle_animal_care(wx, wy, inv, my_animals)

        # P4: Plant crops on empty tiles
        if action is None and empty_tiles and day < 20:
            for crop in ("WHEAT", "STRAWBERRY", "MELON"):
                if seeds.get(crop, 0) > 0:
                    tx, ty = empty_tiles[0]
                    action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                    break

        # P5: Water and harvest crops
        if action is None:
            action = handle_crop_work(wx, wy)

        # P6: End of day return to shed / DROP
        if action is None and hour >= 21 and any(v > 0 for v in inv.values()):
            if (wx, wy) in SHED_TILES:
                action = ["DROP"]
            else:
                ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                action = [move_towards(wx, wy, ns[0], ns[1])]

        worker_actions.append(action if action else ["PASS"])

    return {
        "farmer": worker_actions[0] if worker_actions else ["PASS"],
        "hands":  worker_actions[1:] if len(worker_actions) > 1 else [],
        "market": market_orders[:10],
    }
