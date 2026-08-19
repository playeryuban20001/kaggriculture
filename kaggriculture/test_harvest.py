import sys
sys.path.append(r"G:\po\kaggriculture")
from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 10, "randomSeed": 42})

def test_farmer(obs):
    step = obs["step"]
    farm = obs["farms"][0]
    market = []
    farmer = ["PASS"]
    
    if step == 0:
        market.append(["BUY_SEED", "WHEAT", 1])
    elif step == 1:
        farmer = ["NORTH"]
    elif step == 2:
        farmer = ["PLANT", "WHEAT"]
    elif step == 3:
        farmer = ["HARVEST"]
    
    return {"farmer": farmer, "hands": [], "market": market}

steps = env.run([test_farmer, test_farmer])
for i in range(5):
    inv = steps[i][0].observation["private"]["inventories"][0]
    shed = steps[i][0].observation["private"]["shed"]
    t = steps[i][0].observation["farms"][0]["tiles"][3][4]
    print(f"Step {i}: Tile={t} | Inv={inv.get('WHEAT', 0)} | Shed={shed.get('WHEAT', 0)}")
