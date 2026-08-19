import time
import json
import importlib.util
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

GLOBAL_PATHS = {
    'Kaito v27': r'g:/po/main.py',
    'Tetsutani': r'g:/po/tetsutani_agent/main.py',
    'V11 Apex': r'g:/po/kaggriculture/kaggriculture_v11_apex.py'
}

def load_agent(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent

def run_single_game(args):
    p0_name, p1_name, seed = args
    agent0 = load_agent(GLOBAL_PATHS[p0_name], p0_name.replace(' ', '_'))
    agent1 = load_agent(GLOBAL_PATHS[p1_name], p1_name.replace(' ', '_'))
    
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'randomSeed': seed})
    steps = env.run([agent0, agent1])
    m0 = float(steps[-1][0].observation['farms'][0]['money'])
    m1 = float(steps[-1][1].observation['farms'][1]['money'])
    winner = p0_name if m0 > m1 else (p1_name if m1 > m0 else 'TIE')
    return {'p0': p0_name, 'p1': p1_name, 'seed': seed, 'm0': m0, 'm1': m1, 'winner': winner}

if __name__ == '__main__':
    names = list(GLOBAL_PATHS.keys())
    # 10 random seeds for rigorous testing
    seeds = [10, 20, 30, 42, 100, 777, 1234, 2026, 5000, 9999]
    tasks = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            for s in seeds:
                tasks.append((n1, n2, s))
                tasks.append((n2, n1, s))
                
    print(f'Starting Top 3 Tournament ({len(tasks)} matches total)...')
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(run_single_game, tasks))
    duration = time.time() - t0
    print(f'All {len(tasks)} matches finished in {duration:.2f} seconds!\n')
    
    stats = {n: {'wins': 0, 'losses': 0, 'ties': 0, 'total_money': 0.0, 'games': 0} for n in names}
    h2h = {n1: {n2: {'w': 0, 'l': 0, 't': 0} for n2 in names} for n1 in names}
    
    for r in results:
        p0, p1, m0, m1, winner = r['p0'], r['p1'], r['m0'], r['m1'], r['winner']
        stats[p0]['total_money'] += m0
        stats[p0]['games'] += 1
        stats[p1]['total_money'] += m1
        stats[p1]['games'] += 1
        if winner == p0:
            stats[p0]['wins'] += 1
            stats[p1]['losses'] += 1
            h2h[p0][p1]['w'] += 1
            h2h[p1][p0]['l'] += 1
        elif winner == p1:
            stats[p1]['wins'] += 1
            stats[p0]['losses'] += 1
            h2h[p1][p0]['w'] += 1
            h2h[p0][p1]['l'] += 1
        else:
            stats[p0]['ties'] += 1
            stats[p1]['ties'] += 1
            h2h[p0][p1]['t'] += 1
            h2h[p1][p0]['t'] += 1
            
    print('=== TOURNAMENT LEADERBOARD ===')
    sorted_stats = sorted(stats.items(), key=lambda x: (x[1]['wins'], x[1]['total_money']), reverse=True)
    for rank, (name, s) in enumerate(sorted_stats, 1):
        avg_m = s['total_money'] / s['games']
        wr = (s['wins'] / s['games']) * 100
        print(f"{rank}. {name:15} | Wins: {s['wins']:2d}/{s['games']} ({wr:5.1f}%) | Losses: {s['losses']:2d} | Ties: {s['ties']:1d} | Avg Money: {avg_m:9.0f}")
        
    print('\n=== HEAD-TO-HEAD MATRIX (Row vs Col: W-L-T) ===')
    hdr = f"{'':16}" + ''.join([f"{n:>14}" for n in names])
    print(hdr)
    for n1 in names:
        row = f"{n1:15} "
        for n2 in names:
            if n1 == n2:
                row += f"{'---':>14}"
            else:
                score = f"{h2h[n1][n2]['w']}-{h2h[n1][n2]['l']}-{h2h[n1][n2]['t']}"
                row += f"{score:>14}"
        print(row)
