import subprocess, json, os

episodes = [94379715, 94378747, 94377852, 94376974, 94376087, 94375208]
replay_dir = "G:/po/kaggriculture/replays"

print(f"=== Downloading & Analyzing Recent V5 Public Matches ===")
for ep in episodes:
    target_path = os.path.join(replay_dir, f"episode-{ep}-replay.json")
    if not os.path.exists(target_path):
        subprocess.run(["py", "-m", "kaggle", "competitions", "replay", str(ep), "-p", replay_dir], capture_output=True)
    
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                r = json.load(f)
            teams = r["info"]["TeamNames"]
            our_idx = 1 if ("llRX" in teams[1] or "James" in teams[1]) else 0
            opp_idx = 1 - our_idx
            
            final = r["steps"][-1]
            our_m = final[our_idx]["observation"]["farms"][our_idx]["money"]
            opp_m = final[opp_idx]["observation"]["farms"][opp_idx]["money"]
            res = "WIN" if our_m > opp_m else "LOSS"
            print(f"[{res:4s}] Ep: {ep} | Us: {our_m:8.0f} | Opp ({teams[opp_idx]}): {opp_m:8.0f}")
        except Exception as e:
            print(f"Error reading {ep}: {e}")
    else:
        print(f"Failed to download episode {ep}")
