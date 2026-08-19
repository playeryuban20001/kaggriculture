"""
Kaggriculture V10 AI Adaptive Farmer & Dynamic Strategy
Key Innovations:
1. Macro Demand Forecaster: Analyzes active town shops to predict exact commodity price spikes
2. Dynamic Crop Selector: Calculates expected Profit Density (Net Profit / Growth Days) considering remaining season days
3. Precision Fertilizer Deployment:
   - Day 0-10: 100% Sell for max capital compounding
   - Day 11-25: Reserve fertilizer to FERTILIZE Strawberry & Melon for 2x yield burst
4. Guaranteed Livestock Life Support: Self-grown wheat feed with automated market emergency buffer
5. Day 28+ Global Liquidation
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
    town_shops = obs.get("town", {}).get("unlocked_shops", [])

    farmer_pos = tuple(farm["farmer"])
    hands   = [tuple(h) for h in farm.get("hands", [])]
    workers = [farmer_pos] + hands

    market_orders = []

    # ─── 1. Farm State Scanner ────────────────────────────────────────────────
    pastures_empty, animals, empty_tiles, weeds = [], [], [], []
    wheat_tiles, fruit_tiles = [], []
    unfertilized_cash_crops = []

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
                        # Check if high-value crop needs fertilizer
                        if crop in ("STRAWBERRY", "MELON"):
                            fert_until = tile.get("fertilized_until_day", -1)
                            if fert_until < day:
                                unfertilized_cash_crops.append((x, y, tile))

    num_animals   = len(animals)
    cows_on_farm  = sum(1 for _, _, t in animals if t.get("animal") == "COW")
    sheep_on_farm = sum(1 for _, _, t in animals if t.get("animal") == "SHEEP")

    total_cows     = cows_on_farm + shed.get("COW", 0)
    total_sheep    = sheep_on_farm + shed.get("SHEEP", 0)
    total_pastures = (cows_on_farm + sheep_on_farm) + len(pastures_empty)

    TARGET_COWS     = 10
    TARGET_SHEEP    = 4
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

    empty_tiles.sort(             key=lambda pos: dist(pos[0], pos[1]))
    weeds.sort(                   key=lambda pos: dist(pos[0], pos[1]))
    pastures_empty.sort(          key=lambda pos: dist(pos[0], pos[1]))
    animals.sort(                 key=lambda a:   dist(a[0], a[1]))
    wheat_tiles.sort(             key=lambda a:   dist(a[0], a[1]))
    fruit_tiles.sort(             key=lambda a:   dist(a[0], a[1]))
    unfertilized_cash_crops.sort( key=lambda a:   dist(a[0], a[1]))

    # ─── 2. Macro Demand & Profit Density Forecaster ──────────────────────────
    # Count shop demands
    shop_demand = {"MILK": 0, "STRAWBERRY": 0, "WOOL": 0, "WHEAT": 0, "CARROT": 0, "TOMATO": 0}
    for s in town_shops:
        if s == "PIZZA_SHOP":
            shop_demand["MILK"] += 1; shop_demand["WHEAT"] += 1; shop_demand["TOMATO"] += 1
        elif s == "SMOOTHIE_SHOP":
            shop_demand["STRAWBERRY"] += 1; shop_demand["MILK"] += 1
        elif s == "ICE_CREAM_SHOP":
            shop_demand["STRAWBERRY"] += 1; shop_demand["MILK"] += 1; shop_demand["WHEAT"] += 1
        elif s == "YARN_STORE":
            shop_demand["WOOL"] += 2
        elif s == "BRUNCH_SPOT":
            shop_demand["STRAWBERRY"] += 1; shop_demand["WHEAT"] += 1
        elif s == "BAKERY":
            shop_demand["WHEAT"] += 1
        elif s == "PET_CAFE":
            shop_demand["CARROT"] += 2
        elif s == "FARMERS_MARKET":
            shop_demand["WHEAT"] += 1; shop_demand["CARROT"] += 1; shop_demand["STRAWBERRY"] += 1

    rem_days = 29 - day

    # Calculate expected profit per crop if planted today
    crop_profits = {}

    # Wheat: growth ~3 days, feed value or sell value
    if rem_days >= 3:
        w_val = max(prices.get("WHEAT", 25), 35)
        crop_profits["WHEAT"] = (3 * w_val - 20) / 3.0
    else:
        crop_profits["WHEAT"] = -999

    # Strawberry: ongoing every 2 days
    if rem_days >= 4:
        s_val = prices.get("STRAWBERRY", 120) + (shop_demand["STRAWBERRY"] * 15)
        possible_harvests = min(8, max(1, (rem_days - 3) // 2 + 1))
        fert_mult = 2.0 if day >= 10 else 1.0
        total_rev = possible_harvests * fert_mult * s_val
        crop_profits["STRAWBERRY"] = (total_rev - 100) / float(rem_days)
    else:
        crop_profits["STRAWBERRY"] = -999

    # Melon: one-time burst, needs 6-8 days
    if rem_days >= 7:
        m_val = prices.get("MELON", 120)
        fert_units = 8 if day >= 10 else 6
        crop_profits["MELON"] = (fert_units * m_val - 200) / 7.0
    else:
        crop_profits["MELON"] = -999

    # Find best crop to plant
    best_crop = max(crop_profits, key=crop_profits.get)
    best_profit = crop_profits[best_crop]

    # ─── 3. Market Orders ─────────────────────────────────────────────────────
    quads = len(farm.get("unlocked_quadrants", []))

    # A. Precision Land Purchases
    if hour <= 2 and step < 480:
        if quads == 1 and (day >= 7 or len(empty_tiles) <= 1) and farm["money"] >= 1000:
            market_orders.append(["BUY_LAND"])
        elif quads == 2 and (day >= 11 or len(empty_tiles) <= 2) and farm["money"] >= 2000:
            market_orders.append(["BUY_LAND"])

    # B. Workforce Scaling
    if hour == 0 and step > 0:
        if num_animals == 0:
            target_hands = 0
        elif day < 4:
            target_hands = min(2, (num_animals // 2) + 1)
        elif day < 8:
            target_hands = min(6, (num_animals // 2) + 1)
        elif day < 13:
            target_hands = min(10, (num_animals // 2) + 1)
        else:
            target_hands = min(12, (num_animals // 2) + 1)

        hands_to_hire = target_hands - len(hands)
        if hands_to_hire > 0 and farm["money"] > 300:
            for _ in range(min(hands_to_hire, 10)):
                market_orders.append(["HIRE"])

    # C. Livestock Replenishment
    if step < 520 and len(pastures_empty) > 0 and hour <= 4:
        if total_cows < TARGET_COWS and shed.get("COW", 0) == 0 and farm["money"] >= 2500:
            market_orders.append(["BUY_ANIMAL", "COW", 1])
        elif total_cows >= 4 and total_sheep < TARGET_SHEEP and shed.get("SHEEP", 0) == 0 and farm["money"] >= 2000:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])

    # D. Adaptive Seed Purchases (Based on Dynamic Profit Density)
    if day < 20 and hour <= 2:
        # Guarantee minimum 6-8 wheat tiles for free livestock feed
        if (len(wheat_tiles) + seeds.get("WHEAT", 0)) < 7 and farm["money"] > 1500:
            market_orders.append(["BUY_SEED", "WHEAT", 4])
        
        # Cash crops if profit density is high
        if best_profit > 15 and seeds.get(best_crop, 0) < 3 and farm["money"] > 3500:
            market_orders.append(["BUY_SEED", best_crop, 3])

    # E. Smart Fertilizer Monetization & Conservation
    fert_count = shed.get("FERTILIZER", 0)
    if day < 10:
        # Phase 1: 100% Sell for rapid cash compounding
        if fert_count > 0:
            market_orders.append(["SELL", "FERTILIZER", fert_count])
    else:
        # Phase 2: Reserve up to 4 fertilizer for Strawberry/Melon, sell surplus
        fert_reserve = min(4, len(unfertilized_cash_crops) + 1)
        if fert_count > fert_reserve:
            market_orders.append(["SELL", "FERTILIZER", fert_count - fert_reserve])

    # F. Product Sales with Price Floor & Day 28+ Final Liquidation
    sell_floors = {
        "MILK": 140, "WOOL": 142, "EGG": 15,
        "STRAWBERRY": 80, "MELON": 80, "CARROT": 20, "TOMATO": 25
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

    # ─── 4. Multi-Agent Worker Planner ────────────────────────────────────────
    worker_actions = []

    def handle_animal_care(wx, wy, inv, my_animals):
        for tx, ty, tile in my_animals:
            fed        = tile.get("fed_today", False)
            cared      = tile.get("cared_today", False)
            fert_avail = tile.get("fertilizer_available", False)
            yield_u    = tile.get("yield_units", 0)

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

    def handle_crop_work(wx, wy, inv):
        # 1. Fertilize unfertilized cash crops (only if holding fertilizer or passing shed)
        if day >= 10 and unfertilized_cash_crops:
            if inv.get("FERTILIZER", 0) > 0:
                cx, cy, _ = unfertilized_cash_crops[0]
                if (wx, wy) == (cx, cy):
                    return ["FERTILIZE"]
                else:
                    return [move_towards(wx, wy, cx, cy)]
            elif (wx, wy) in SHED_TILES and shed.get("FERTILIZER", 0) > 0 and len(unfertilized_cash_crops) > 0:
                return ["PICKUP", "FERTILIZER", 2]

        # 2. Water unwatered plants (CRITICAL daily task)
        for tx, ty, tile in wheat_tiles + fruit_tiles:
            if not tile.get("watered_today", False):
                if (wx, wy) == (tx, ty):
                    return ["WATER"]
                else:
                    return [move_towards(wx, wy, tx, ty)]

        # 3. Harvest mature plants
        for tx, ty, tile in wheat_tiles + fruit_tiles:
            if tile.get("yield_units", 0) > 0:
                if (wx, wy) == (tx, ty):
                    return ["HARVEST"]
                else:
                    return [move_towards(wx, wy, tx, ty)]
        return None

    for i, (wx, wy) in enumerate(workers):
        inv = obs["private"]["inventories"][i]

        # ── WORKER 0: General Contractor & Lead Builder ──────────────────────
        if i == 0:
            action = None

            # P1: Place Cow/Sheep in Pasture
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

            # P3: Care for animals if alone (Day 0-3)
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

            # P6: Plant Crops (prioritize highest profit density)
            if action is None and empty_tiles and day < 20:
                crop_order = [best_crop, "WHEAT", "STRAWBERRY", "MELON"]
                for crop in crop_order:
                    if seeds.get(crop, 0) > 0:
                        tx, ty = empty_tiles[0]
                        action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

            # P7: Fertilize, Water & Harvest crops
            if action is None:
                action = handle_crop_work(wx, wy, inv)

            worker_actions.append(action if action else ["PASS"])
            continue

        # ── WORKERS 1+: Caretakers & Specialized Field Force ─────────────────
        hand_idx = i - 1
        my_animals = animals[hand_idx * 2 : hand_idx * 2 + 2]
        action = None

        # P1: Tend assigned animals
        if my_animals:
            action = handle_animal_care(wx, wy, inv, my_animals)

        # P2: Help plant seeds on empty tiles
        if action is None and empty_tiles and day < 20:
            crop_order = [best_crop, "WHEAT", "STRAWBERRY", "MELON"]
            for crop in crop_order:
                if seeds.get(crop, 0) > 0:
                    tx, ty = empty_tiles[0]
                    action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                    break

        # P3: Help Fertilize, Water & Harvest crops
        if action is None:
            action = handle_crop_work(wx, wy, inv)

        worker_actions.append(action if action else ["PASS"])

    return {
        "farmer": worker_actions[0] if worker_actions else ["PASS"],
        "hands":  worker_actions[1:] if len(worker_actions) > 1 else [],
        "market": market_orders[:10],
    }
