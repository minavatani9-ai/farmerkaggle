import json, glob, os, sys, gc

US = 'MOHAMMADJAFAR ZAMANI'
SRC = '/tmp/claude-0/-home-user-farmerkaggle/d51305fc-7ce7-587f-801e-8ba710d935d7/scratchpad/extract'
OUT = '/tmp/claude-0/-home-user-farmerkaggle/d51305fc-7ce7-587f-801e-8ba710d935d7/scratchpad/analysis'

CROPS = ["WHEAT","CARROT","TOMATO","STRAWBERRY","MELON"]
ANIMALS = ["COW","SHEEP","GOOSE"]
PREMIUM = ["STRAWBERRY","MELON","MILK","WOOL"]

def tile_summary(tiles):
    counts = {c:0 for c in CROPS}
    acounts = {a:0 for a in ANIMALS}
    weed = 0; empty = 0; locked = 0; coop_empty=0; pasture_empty=0
    for row in tiles:
        for t in row:
            if t is None:
                empty += 1
            elif t == "LOCKED":
                locked += 1
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "WEED":
                    weed += 1
                elif k == "PLANT":
                    counts[t["crop"]] = counts.get(t["crop"],0)+1
                elif k in ("COOP","PASTURE"):
                    an = t.get("animal")
                    if an:
                        acounts[an] = acounts.get(an,0)+1
                    else:
                        if k=="COOP": coop_empty+=1
                        else: pasture_empty+=1
    return {"crops":counts,"animals":acounts,"weed":weed,"empty":empty,"locked":locked,
            "coop_empty":coop_empty,"pasture_empty":pasture_empty}

def process(fname):
    path = os.path.join(SRC, fname)
    with open(path) as f:
        d = json.load(f)
    info = d['info']
    names = info['TeamNames']
    rewards = d['rewards']
    seed = info.get('seed')
    if names[0]==US and names[1]==US:
        seat=0; opp='SELF-MIRROR'
    elif names[0]==US:
        seat=0; opp=names[1]
    elif names[1]==US:
        seat=1; opp=names[0]
    else:
        seat=None; opp='UNKNOWN'
    our_r = rewards[seat]; opp_r = rewards[1-seat]
    margin = our_r - opp_r
    outcome = 'TIE' if margin==0 else ('WIN' if margin>0 else 'LOSS')

    steps = d['steps']
    turns_per_day = d['configuration'].get('turnsPerDay', 24)
    nsteps = len(steps)

    # action tallies per player (0 and 1, we'll relabel to us/opp after)
    tally = [dict(), dict()]  # per player: op -> count ; and market op-item -> qty
    market_qty = [dict(), dict()]  # (op,item) -> total qty
    hire_count = [0,0]
    buyland_count = [0,0]
    unit_op_count = [dict(), dict()]

    # day trajectories
    day_money = [[], []]
    day_prices = {p: [] for p in PREMIUM+["WHEAT"]}
    day_shed = [[], []]   # list of dicts sampled once per day (at hour 0)
    day_tiles = [[], []]  # tile_summary sampled at select days
    sample_days = set([0,4,9,14,19,24,29])

    last_day_seen = -1
    for i in range(nsteps):
        entry = steps[i]
        obs0 = entry[0]['observation']
        hour = obs0.get('hour', i % turns_per_day)
        day = obs0.get('day', i // turns_per_day)
        farms = obs0.get('farms')
        market = obs0.get('market', {})
        # sample at start of each day (hour==0), once
        if hour == 0 and day != last_day_seen and farms:
            last_day_seen = day
            for p in (0,1):
                day_money[p].append((day, farms[p]['money']))
            prices = market.get('prices', {})
            for item in PREMIUM+["WHEAT"]:
                day_prices[item].append((day, prices.get(item)))
            if day in sample_days:
                for p in (0,1):
                    day_tiles[p].append((day, tile_summary(farms[p]['tiles'])))
                    priv = entry[p]['observation'].get('private', {})
                    day_shed[p].append((day, dict(priv.get('shed', {}))))

        for p in (0,1):
            action = entry[p].get('action')
            if not isinstance(action, dict):
                continue
            farmer = action.get('farmer')
            if isinstance(farmer, list) and farmer:
                op = farmer[0]
                unit_op_count[p][op] = unit_op_count[p].get(op,0)+1
                if op == 'PLANT' and len(farmer)>=2:
                    key = f'PLANT_{farmer[1]}'
                    unit_op_count[p][key] = unit_op_count[p].get(key,0)+1
            for hand in (action.get('hands') or []):
                if isinstance(hand, list) and hand:
                    op = hand[0]
                    unit_op_count[p][op] = unit_op_count[p].get(op,0)+1
                    if op == 'PLANT' and len(hand)>=2:
                        key = f'PLANT_{hand[1]}'
                        unit_op_count[p][key] = unit_op_count[p].get(key,0)+1
            for order in (action.get('market') or []):
                if not isinstance(order, list) or not order:
                    continue
                mop = order[0]
                tally[p][mop] = tally[p].get(mop,0)+1
                if mop == 'HIRE':
                    hire_count[p]+=1
                elif mop == 'BUY_LAND':
                    buyland_count[p]+=1
                elif mop in ('SELL','BUY_SEED','BUY_PRODUCT','BUY_ANIMAL') and len(order)>=3:
                    item = order[1]
                    try:
                        qty = int(order[2])
                    except (TypeError, ValueError):
                        qty = 0
                    k = (mop, item)
                    market_qty[p][f'{mop}_{item}'] = market_qty[p].get(f'{mop}_{item}',0) + qty

    final_farms = steps[-1][0]['observation']['farms']
    final_tiles = [tile_summary(final_farms[p]['tiles']) for p in (0,1)]
    final_shed = [dict(steps[-1][p]['observation'].get('private',{}).get('shed',{})) for p in (0,1)]
    final_unlocked = [final_farms[p]['unlocked_quadrants'] for p in (0,1)]

    result = {
        'episode_id': info['EpisodeId'],
        'opponent': opp,
        'seed': seed,
        'seat': seat,
        'our_reward': our_r,
        'opp_reward': opp_r,
        'margin': margin,
        'outcome': outcome,
        'hire_count': {'us': hire_count[seat], 'opp': hire_count[1-seat]},
        'buyland_count': {'us': buyland_count[seat], 'opp': buyland_count[1-seat]},
        'market_qty': {'us': market_qty[seat], 'opp': market_qty[1-seat]},
        'unit_ops': {'us': unit_op_count[seat], 'opp': unit_op_count[1-seat]},
        'day_money': {'us': day_money[seat], 'opp': day_money[1-seat]},
        'day_prices': day_prices,
        'day_tiles': {'us': day_tiles[seat], 'opp': day_tiles[1-seat]},
        'day_shed': {'us': day_shed[seat], 'opp': day_shed[1-seat]},
        'final_tiles': {'us': final_tiles[seat], 'opp': final_tiles[1-seat]},
        'final_shed': {'us': final_shed[seat], 'opp': final_shed[1-seat]},
        'final_unlocked': {'us': final_unlocked[seat], 'opp': final_unlocked[1-seat]},
    }
    del d, steps
    gc.collect()
    return result

def main():
    files = sorted([f for f in glob.glob(os.path.join(SRC,'*.json'))
                     if os.path.basename(f) not in ('104837395-0.json','104837395-1.json','104837395 (1).json')])
    out_all = []
    for fp in files:
        fname = os.path.basename(fp)
        sys.stderr.write(f'processing {fname}\n')
        r = process(fname)
        out_all.append(r)
        with open(os.path.join(OUT, f"summary_{r['episode_id']}.json"), 'w') as f:
            json.dump(r, f)
    with open(os.path.join(OUT, 'all_summaries.json'), 'w') as f:
        json.dump(out_all, f)
    print('DONE', len(out_all))

if __name__ == '__main__':
    main()
