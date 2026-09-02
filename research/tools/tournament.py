import sys, json, statistics as st
sys.path.insert(0, '.')
import kaggle_environments as ke
import agent_dev
import frozen_1062

OPPONENTS = {
    'pass': 'pass',
    'random': 'random',
    'starter': 'starter',
    'frozen_1062': frozen_1062.agent,
}

def play(a0, a1, seed):
    env = ke.make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed}, debug=False)
    env.run([a0, a1])
    final = env.steps[-1]
    return [s.reward for s in final], [s.status for s in final]

def run_matrix(seeds, opponents=OPPONENTS, challenger=agent_dev.agent, tag=''):
    rows = []
    for oname, ofn in opponents.items():
        for seed in seeds:
            for seat in (0, 1):
                a0 = challenger if seat == 0 else ofn
                a1 = ofn if seat == 0 else challenger
                rewards, statuses = play(a0, a1, seed)
                our_r = rewards[seat]
                opp_r = rewards[1 - seat]
                margin = our_r - opp_r
                outcome = 'TIE' if margin == 0 else ('WIN' if margin > 0 else 'LOSS')
                rows.append({
                    'tag': tag, 'opponent': oname, 'seed': seed, 'seat': seat,
                    'our': our_r, 'opp': opp_r, 'margin': margin, 'outcome': outcome,
                    'statuses': statuses,
                })
    return rows

def summarize(rows, label):
    n = len(rows)
    wins = sum(1 for r in rows if r['outcome'] == 'WIN')
    losses = sum(1 for r in rows if r['outcome'] == 'LOSS')
    ties = sum(1 for r in rows if r['outcome'] == 'TIE')
    margins = sorted(r['margin'] for r in rows)
    mean_m = sum(margins) / n
    median_m = st.median(margins)
    worst = margins[0]
    k = max(1, int(round(0.2 * n)))
    cvar20 = sum(margins[:k]) / k
    bad = [r for r in rows if any(s != 'DONE' for s in r['statuses'])]
    print(f"=== {label} (n={n}) ===")
    print(f"W-L-T: {wins}-{losses}-{ties}  win_rate={wins/n:.2%}")
    print(f"mean_margin={mean_m:.0f}  median_margin={median_m:.0f}  worst_margin={worst:.0f}  CVaR20={cvar20:.0f}")
    print(f"schema/runtime failures: {len(bad)}")
    per_opp = {}
    for r in rows:
        per_opp.setdefault(r['opponent'], []).append(r)
    for oname, orows in per_opp.items():
        ow = sum(1 for r in orows if r['outcome'] == 'WIN')
        ol = sum(1 for r in orows if r['outcome'] == 'LOSS')
        ot = sum(1 for r in orows if r['outcome'] == 'TIE')
        om = sum(r['margin'] for r in orows) / len(orows)
        print(f"  vs {oname}: {ow}-{ol}-{ot}  mean_margin={om:.0f}")
    return {'n': n, 'wins': wins, 'losses': losses, 'ties': ties, 'mean_margin': mean_m,
            'median_margin': median_m, 'worst_margin': worst, 'cvar20': cvar20, 'bad': len(bad)}

if __name__ == '__main__':
    import time
    t0 = time.time()
    fast_seeds = [5001, 5002, 5003, 5004, 5005, 5006]
    fast_opps = {'pass': 'pass', 'random': 'random', 'starter': 'starter', 'frozen_1062': frozen_1062.agent}
    rows = run_matrix(fast_seeds, fast_opps, tag='fast')
    with open('fast_screen.json', 'w') as f:
        json.dump(rows, f)
    summarize(rows, 'FAST SCREEN')
    print('elapsed', round(time.time() - t0, 1))
