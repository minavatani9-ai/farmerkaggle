import json, statistics as st
from collections import defaultdict

d = json.load(open('/tmp/claude-0/-home-user-farmerkaggle/d51305fc-7ce7-587f-801e-8ba710d935d7/scratchpad/analysis/all_summaries.json'))

def bucket(games):
    n = len(games)
    if n==0: return {}
    def avg(key_fn):
        vals = [key_fn(g) for g in games]
        vals = [v for v in vals if v is not None]
        return sum(vals)/len(vals) if vals else None
    out = {}
    out['n'] = n
    out['mean_margin'] = avg(lambda g: g['margin'])
    out['mean_our_final'] = avg(lambda g: g['our_reward'])
    out['mean_opp_final'] = avg(lambda g: g['opp_reward'])
    out['mean_hire_us'] = avg(lambda g: g['hire_count']['us'])
    out['mean_hire_opp'] = avg(lambda g: g['hire_count']['opp'])
    out['mean_buyland_us'] = avg(lambda g: g['buyland_count']['us'])
    out['mean_buyland_opp'] = avg(lambda g: g['buyland_count']['opp'])
    for item in ['WHEAT']:
        out[f'mean_buyproduct_{item}_us'] = avg(lambda g: g['market_qty']['us'].get(f'BUY_PRODUCT_{item}',0))
        out[f'mean_buyproduct_{item}_opp'] = avg(lambda g: g['market_qty']['opp'].get(f'BUY_PRODUCT_{item}',0))
        out[f'mean_sell_{item}_us'] = avg(lambda g: g['market_qty']['us'].get(f'SELL_{item}',0))
        out[f'mean_sell_{item}_opp'] = avg(lambda g: g['market_qty']['opp'].get(f'SELL_{item}',0))
    for item in ['STRAWBERRY','MELON','MILK','WOOL','FERTILIZER','CARROT','TOMATO']:
        out[f'mean_sell_{item}_us'] = avg(lambda g: g['market_qty']['us'].get(f'SELL_{item}',0))
        out[f'mean_sell_{item}_opp'] = avg(lambda g: g['market_qty']['opp'].get(f'SELL_{item}',0))
    # final tiles avg counts
    for role in ['us','opp']:
        for a in ['COW','SHEEP','GOOSE']:
            out[f'mean_final_{a}_{role}'] = avg(lambda g,a=a,role=role: g['final_tiles'][role]['animals'].get(a,0))
        for c in ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON']:
            out[f'mean_final_crop_{c}_{role}'] = avg(lambda g,c=c,role=role: g['final_tiles'][role]['crops'].get(c,0))
        out[f'mean_final_locked_{role}'] = avg(lambda g,role=role: g['final_tiles'][role]['locked'])
        out[f'mean_final_weed_{role}'] = avg(lambda g,role=role: g['final_tiles'][role]['weed'])
    return out

wins = [g for g in d if g['outcome']=='WIN']
losses = [g for g in d if g['outcome']=='LOSS']
ties = [g for g in d if g['outcome']=='TIE']

print("=== ALL ===")
print(json.dumps(bucket(d), indent=1))
print("=== WINS ===")
print(json.dumps(bucket(wins), indent=1))
print("=== LOSSES ===")
print(json.dumps(bucket(losses), indent=1))
