import sys
sys.path.append(r"G:\po\kaggriculture")
from kaggle_environments import make

# Let's inspect how crop mechanics work in the environment
env = make("kaggriculture", configuration={"episodeSteps": 120, "randomSeed": 42})

def test_farmer(obs):
    p = obs["player"]
    step = obs["step"]
    farm = obs["farms"][p]
    seeds = obs["private"].get("seeds", {})
    market = []
    farmer = ["PASS"]
    
    # Step 0: buy 5 wheat seeds
    if step == 0:
        market.append(["BUY_SEED", "WHEAT", 5])
    
    # Step 1: plant wheat at (4,3) if adjacent
    fx, fy = farm["farmer"]
    if step == 1:
        farmer = ["NORTH"]
    elif step == 2:
        farmer = ["PLANT", "WHEAT"]
    elif step == 3:
        farmer = ["WATER"]
    
    return {"farmer": farmer, "hands": [], "market": market}

steps = env.run([test_farmer, test_farmer])
for i in range(10):
    t = steps[i][0].observation["farms"][0]["tiles"][3][4]
    print(f"Step {i}: Tile(4,3) = {t}")
