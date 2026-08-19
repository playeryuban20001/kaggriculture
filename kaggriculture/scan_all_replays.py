import json, glob, os

files = glob.glob(r"C:\Users\ma130\.gemini\antigravity\brain\0253be35-dd3e-4304-896b-2c5228cd5d6b\scratch\*.json")
files += glob.glob(r"G:\po\kaggriculture\replays\*.json")

for f in files:
    if "metadata" in f: continue
    try:
        data = json.load(open(f, "r", encoding="utf-8"))
        info = data.get("info", {})
        teams = info.get("TeamNames", [])
        ep_id = info.get("EpisodeId", os.path.basename(f))
        print(f"File: {os.path.basename(f)} | Ep: {ep_id} | Teams: {teams}")
    except:
        pass
