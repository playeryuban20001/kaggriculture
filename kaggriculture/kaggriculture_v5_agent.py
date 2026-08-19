"""
Kaggriculture V5 Agent - "Calmracer Blueprint" (Fixed)
Phases:
  1 (Day 0-7):  Bootstrap — farmer alone builds pastures, buys+places cows, feeds them
  2 (Day 7-20): Scale     — hire workers proportional to animals, buy sheep mix, plant crops
  3 (Day 20+):  Harvest   — no new investment, squeeze every dollar
"""

def agent(obs):
    p    = obs["player"]
    step = obs.get("step", 0)
    day  = step // 24
    farm = obs["farms"][p]
    shed = obs["private"]["shed"]
    prices = obs["market"]["prices"]
    seeds  = obs["private"].get("seeds", {})

    farmer_pos = tuple(farm["farmer"])
    hands   = [tuple(h) for h in farm.get("hands", [])]
    workers = [farmer_pos] + hands

    market_orders = []

    # ─── Tile Scanner ─────────────────────────────────────────────────────────
    coops_empty, animals, empty_tiles, weeds, wheat_tiles, crop_tiles = [], [], [], [], [], []

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
                    if tile.get("crop") == "WHEAT":
                        wheat_tiles.append((x, y, tile))
                    elif tile.get("crop") in ("STRAWBERRY", "MELON", "CARROT"):
                        crop_tiles.append((x, y, tile))

    num_animals    = len(animals)
    total_pastures = num_animals + len(coops_empty)
    total_cows     = sum(1 for _, _, t in animals if t.get("animal") == "COW") + shed.get("COW", 0)
    total_sheep    = sum(1 for _, _, t in animals if t.get("animal") == "SHEEP") + shed.get("SHEEP", 0)

    TARGET_PASTURES = 14
    TARGET_COWS     = 10
    TARGET_SHEEP    = 4

    def dist(x1, y1, x2=4, y2=4):
        return abs(x1 - x2) + abs(y1 - y2)

    def move_towards(cx, cy, tx, ty):
        if cx < tx: return "EAST"
        if cx > tx: return "WEST"
        if cy < ty: return "SOUTH"
        if cy > ty: return "NORTH"
        return "PASS"

    SHED_TILES = [(4,4),(5,4),(4,5),(5,5)]

    # Sort by distance to shed for optimal pathing
    empty_tiles.sort(key=lambda pos: dist(pos[0], pos[1]))
    weeds.sort(      key=lambda pos: dist(pos[0], pos[1]))
    coops_empty.sort(key=lambda pos: dist(pos[0], pos[1]))
    animals.sort(    key=lambda a:   dist(a[0], a[1]))

    # ─── Market: Land Expansion ───────────────────────────────────────────────
    quads = len(farm.get("unlocked_quadrants", []))
    if quads < 3 and not empty_tiles and not weeds and farm["money"] > 4000 and step < 480:
        market_orders.append(["BUY_LAND"])

    # ─── Market: Hire Workers ─────────────────────────────────────────────────
    # Phase 1: no hands until we have animals producing
    # Phase 2: 1 hand per 2 animals
    if num_animals == 0 or day < 5:
        target_hands = 0
    elif day < 8:
        target_hands = min(4, num_animals // 2 + 1)
    elif day < 12:
        target_hands = min(8, num_animals // 2 + 1)
    else:
        target_hands = min(12, num_animals // 2 + 1)

    diff = target_hands - len(hands)
    if diff > 0 and farm["money"] > 400:
        for _ in range(min(diff, 10)):
            market_orders.append(["HIRE"])

    # ─── Market: Buy Animals ──────────────────────────────────────────────────
    if step < 540 and coops_empty:
        if total_cows < TARGET_COWS and shed.get("COW", 0) == 0 and farm["money"] >= 2500:
            market_orders.append(["BUY_ANIMAL", "COW", 1])
        elif total_cows >= 6 and total_sheep < TARGET_SHEEP and shed.get("SHEEP", 0) == 0 and farm["money"] >= 2000:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])

    # ─── Market: Buy Seeds ────────────────────────────────────────────────────
    # Only after first cow placed (income flowing) and we have buffer above 3000
    if num_animals >= 1 or farm["money"] > 4000:
        if day < 15 and seeds.get("WHEAT", 0) < 10 and farm["money"] > 3500:
            market_orders.append(["BUY_SEED", "WHEAT", 5])
        if day >= 8 and day < 18:
            if seeds.get("STRAWBERRY", 0) < 5 and farm["money"] > 6000:
                market_orders.append(["BUY_SEED", "STRAWBERRY", 5])
            if seeds.get("MELON", 0) < 3 and farm["money"] > 6000:
                market_orders.append(["BUY_SEED", "MELON", 3])

    # ─── Market: Sell Products ────────────────────────────────────────────────
    # Fertilizer: always sell immediately (pure profit)
    fert = shed.get("FERTILIZER", 0)
    if fert > 0:
        market_orders.append(["SELL", "FERTILIZER", fert])

    # Animal products: hold if price crashed
    for product, floor in [("MILK", 150), ("WOOL", 150), ("EGG", 20)]:
        count = shed.get(product, 0)
        if count > 0 and (prices.get(product, 0) >= floor or day >= 28):
            market_orders.append(["SELL", product, count])

    # Crops: always sell
    for product in ["STRAWBERRY", "MELON", "CARROT", "TOMATO"]:
        count = shed.get(product, 0)
        if count > 0:
            market_orders.append(["SELL", product, count])

    # Wheat: keep 3-day feeding reserve, sell excess
    wheat_shed = shed.get("WHEAT", 0)
    reserve = max(num_animals * 3, 3)
    if wheat_shed > reserve:
        market_orders.append(["SELL", "WHEAT", wheat_shed - reserve])

    # ─── Worker Action Planner ────────────────────────────────────────────────
    worker_actions = []

    def do_animal_care(wx, wy, inv, tile_list):
        """Try to feed/care/harvest/collect from a list of animal tiles. Returns action or None."""
        for tx, ty, tile in tile_list:
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

    for i, (wx, wy) in enumerate(workers):
        inv = obs["private"]["inventories"][i]

        # ── WORKER 0: Builder / Caretaker-of-all (until hands are hired) ──────
        if i == 0:
            action = None

            # P1: Place animal from inventory
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

            # P3: Feed/care ALL animals (farmer must tend all until hands hired)
            if action is None:
                action = do_animal_care(wx, wy, inv, animals)

            # P4: Build pasture (only when all animals tended)
            if action is None and total_pastures < TARGET_PASTURES and empty_tiles:
                tx, ty = empty_tiles[0]
                action = ["BUILD_PASTURE"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P5: Remove weeds
            if action is None and weeds:
                tx, ty = weeds[0]
                action = ["DIG"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P6: Water wheat (must water on planting day!)
            if action is None:
                for tx, ty, tile in wheat_tiles:
                    if not tile.get("watered_today", False):
                        action = ["WATER"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

            # P7: Harvest wheat
            if action is None:
                for tx, ty, tile in wheat_tiles:
                    if tile.get("yield_units", 0) > 0:
                        action = ["HARVEST"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

            # P8: Plant wheat
            if action is None and empty_tiles and seeds.get("WHEAT", 0) > 0 and day < 18:
                tx, ty = empty_tiles[0]
                action = ["PLANT", "WHEAT"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

            # P9: Water/harvest high-value crops
            if action is None:
                for tx, ty, tile in crop_tiles:
                    if not tile.get("watered_today", False):
                        action = ["WATER"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break
                    elif tile.get("yield_units", 0) > 0:
                        action = ["HARVEST"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

            worker_actions.append(action if action else ["PASS"])
            continue

        # ── WORKERS 1+: Animal Caretakers (2 animals each) ────────────────────
        hand_idx   = i - 1
        my_animals = animals[hand_idx * 2: hand_idx * 2 + 2]
        action     = do_animal_care(wx, wy, inv, my_animals)

        if action is None:
            # Idle: help water crops
            for tx, ty, tile in wheat_tiles + crop_tiles:
                if not tile.get("watered_today", False):
                    action = ["WATER"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                    break

        worker_actions.append(action if action else ["PASS"])

    return {
        "farmer": worker_actions[0] if worker_actions else ["PASS"],
        "hands":  worker_actions[1:] if len(worker_actions) > 1 else [],
        "market": market_orders[:10],
    }
