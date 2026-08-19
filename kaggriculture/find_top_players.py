import kaggle

kaggle.api.authenticate()

lb = kaggle.api.competition_leaderboard_view('kaggriculture')
for entry in lb[:15]:
    print(f"TeamID: {entry.team_id} | TeamName: {entry.team_name} | Score: {entry.score}")
