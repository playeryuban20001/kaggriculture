import json

def extract_code_from_ipynb(ipynb_path):
    with open(ipynb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    print(f"\n{'='*60}\nFILE: {ipynb_path}\n{'='*60}")
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            code = "".join(cell.get("source", []))
            if any(k in code for k in ["replay", "Episode", "episode", "leaderboard", "requests", "kaggle"]):
                print("\n--- CODE CELL ---")
                print(code[:600])

extract_code_from_ipynb("./scratch/replay_miner/kaggriculture-replay-data-miner.ipynb")
extract_code_from_ipynb("./scratch/top_farms_meta/kaggriculture-what-the-top-farms-do-a-live-meta.ipynb")
