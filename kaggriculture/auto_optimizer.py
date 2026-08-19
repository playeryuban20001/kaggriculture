"""
Kaggriculture Strategy Parameter Auto-Tuner & Evolutionary Optimizer
Evaluates candidate parameter configurations against a diverse benchmark pool across multiple seeds.
"""

import sys, random, copy, time
from concurrent.futures import ProcessPoolExecutor
sys.path.append(r"G:\po\kaggriculture")

from kaggle_environments import make

# ─── Parametric Agent Builder ─────────────────────────────────────────────────
def make_parametric_agent(p_dict):
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

        TARGET_COWS     = p_dict["TARGET_COWS"]
        TARGET_SHEEP    = p_dict["TARGET_SHEEP"]
        TARGET_PASTURES = p_dict["TARGET_PASTURES"]

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

        # Market Decisions
        quads = len(farm.get("unlocked_quadrants", []))

        # Land Expansion
        if hour <= 2 and step < 480:
            if quads == 1 and (day >= p_dict["DAY_BUY_QUAD2"] or len(empty_tiles) <= 1) and farm["money"] >= p_dict["QUAD2_MONEY"]:
                market_orders.append(["BUY_LAND"])
            elif quads == 2 and (day >= p_dict["DAY_BUY_QUAD3"] or len(empty_tiles) <= 2) and farm["money"] >= p_dict["QUAD3_MONEY"]:
                market_orders.append(["BUY_LAND"])

        # Workforce Scaling
        if hour == 0 and step > 0:
            if num_animals == 0:
                target_hands = 0
            elif day < 4:
                target_hands = min(p_dict["MAX_HANDS_EARLY"], (num_animals // 2) + 1)
            elif day < 8:
                target_hands = min(p_dict["MAX_HANDS_MID"], (num_animals // 2) + 1)
            elif day < 13:
                target_hands = min(p_dict["MAX_HANDS_LATE"], (num_animals // 2) + 1)
            else:
                target_hands = min(12, (num_animals // 2) + 1)

            hands_to_hire = target_hands - len(hands)
            if hands_to_hire > 0 and farm["money"] > 300:
                for _ in range(min(hands_to_hire, 10)):
                    market_orders.append(["HIRE"])

        # Livestock
        if step < 520 and len(pastures_empty) > 0 and hour <= 4:
            if total_cows < TARGET_COWS and shed.get("COW", 0) == 0 and farm["money"] >= 2500:
                market_orders.append(["BUY_ANIMAL", "COW", 1])
            elif total_cows >= 3 and total_sheep < TARGET_SHEEP and shed.get("SHEEP", 0) == 0 and farm["money"] >= 2000:
                market_orders.append(["BUY_ANIMAL", "SHEEP", 1])

        # Seeds
        if day < p_dict["CROP_STOP_DAY"] and farm["money"] > 2500 and hour <= 2:
            if seeds.get("WHEAT", 0) < 5 and (len(wheat_tiles) + seeds.get("WHEAT", 0)) < p_dict["WHEAT_TARGET"]:
                market_orders.append(["BUY_SEED", "WHEAT", 4])
            if day >= 4 and seeds.get("STRAWBERRY", 0) < 3 and farm["money"] > 4000:
                market_orders.append(["BUY_SEED", "STRAWBERRY", 3])
            if day >= 6 and seeds.get("MELON", 0) < 2 and farm["money"] > 4500:
                market_orders.append(["BUY_SEED", "MELON", 2])

        # Fertilizer
        fert = shed.get("FERTILIZER", 0)
        if fert > 0:
            market_orders.append(["SELL", "FERTILIZER", fert])

        # Product Sales
        sell_floors = {
            "MILK": p_dict["MILK_FLOOR"], "WOOL": p_dict["WOOL_FLOOR"], "EGG": 15,
            "STRAWBERRY": 75, "MELON": 75, "CARROT": 20, "TOMATO": 25
        }
        for prod, floor in sell_floors.items():
            count = shed.get(prod, 0)
            if count > 0 and (prices.get(prod, 0) >= floor or day >= p_dict["LIQUIDATION_DAY"]):
                market_orders.append(["SELL", prod, count])

        # Wheat
        wheat_shed = shed.get("WHEAT", 0)
        wheat_reserve = max(num_animals * p_dict["WHEAT_RESERVE_MULT"], 4)
        if wheat_shed > wheat_reserve:
            market_orders.append(["SELL", "WHEAT", wheat_shed - wheat_reserve])

        # Worker Actions
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

        def handle_crop_work(wx, wy):
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
            if i == 0:
                action = None
                for anim in ("COW", "SHEEP"):
                    if inv.get(anim, 0) > 0 and pastures_empty:
                        tx, ty = pastures_empty[0]
                        action = ["PLACE", anim, 1] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                        break

                if action is None:
                    for anim in ("COW", "SHEEP"):
                        if shed.get(anim, 0) > 0 and pastures_empty:
                            if (wx, wy) in SHED_TILES:
                                action = ["PICKUP", anim, 1]
                            else:
                                ns = min(SHED_TILES, key=lambda s: dist(wx, wy, s[0], s[1]))
                                action = [move_towards(wx, wy, ns[0], ns[1])]
                            break

                if action is None and len(hands) == 0 and animals:
                    action = handle_animal_care(wx, wy, inv, animals)

                if action is None and total_pastures < TARGET_PASTURES and empty_tiles:
                    tx, ty = empty_tiles[0]
                    action = ["BUILD_PASTURE"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

                if action is None and weeds:
                    tx, ty = weeds[0]
                    action = ["DIG"] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]

                if action is None and empty_tiles and day < 18:
                    for crop in ("WHEAT", "STRAWBERRY"):
                        if seeds.get(crop, 0) > 0:
                            tx, ty = empty_tiles[0]
                            action = ["PLANT", crop] if (wx, wy) == (tx, ty) else [move_towards(wx, wy, tx, ty)]
                            break

                if action is None:
                    action = handle_crop_work(wx, wy)

                worker_actions.append(action if action else ["PASS"])
                continue

            hand_idx = i - 1
            my_animals = animals[hand_idx * 2 : hand_idx * 2 + 2]
            action = None

            if my_animals:
                action = handle_animal_care(wx, wy, inv, my_animals)

            if action is None and empty_tiles and day < 18:
                for crop in ("WHEAT", "STRAWBERRY"):
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
    return agent

# ─── Evolutionary Hyperparameter Search Engine ───────────────────────────────
DEFAULT_PARAMS = {
    "TARGET_COWS": 10,
    "TARGET_SHEEP": 6,
    "TARGET_PASTURES": 16,
    "DAY_BUY_QUAD2": 6,
    "DAY_BUY_QUAD3": 8,
    "QUAD2_MONEY": 1000,
    "QUAD3_MONEY": 2000,
    "MAX_HANDS_EARLY": 3,
    "MAX_HANDS_MID": 6,
    "MAX_HANDS_LATE": 10,
    "WHEAT_TARGET": 12,
    "CROP_STOP_DAY": 16,
    "MILK_FLOOR": 140,
    "WOOL_FLOOR": 140,
    "WHEAT_RESERVE_MULT": 2,
    "LIQUIDATION_DAY": 28,
}

import kaggriculture_v5_agent

def evaluate_params(candidate_params, seeds=[101, 202, 303, 404, 505]):
    cand_agent = make_parametric_agent(candidate_params)
    scores = []
    wins = 0
    for s in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "randomSeed": s})
        steps = env.run([cand_agent, kaggriculture_v5_agent.agent])
        score_cand = steps[-1][0].observation["farms"][0]["money"]
        score_opp  = steps[-1][1].observation["farms"][1]["money"]
        scores.append(score_cand)
        if score_cand > score_opp:
            wins += 1
    avg_score = sum(scores) / len(scores)
    return avg_score, wins, scores

if __name__ == "__main__":
    print("Testing baseline parameters...")
    base_avg, base_wins, base_scores = evaluate_params(DEFAULT_PARAMS)
    print(f"Base Score: {base_avg:.0f} | Wins: {base_wins}/5 | Scores: {base_scores}")
