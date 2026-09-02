import json, glob, os, sys, gc

US = 'MOHAMMADJAFAR ZAMANI'
SRC = '/tmp/claude-0/-home-user-farmerkaggle/d51305fc-7ce7-587f-801e-8ba710d935d7/scratchpad/live3'

def tile_summary(tiles):
    animals = {"COW":0,"SHEEP":0,"GOOSE":0}
    crops = {"WHEAT":0,"CARROT":0,"TOMATO":0,"STRAWBERRY":0,"MELON":0}
    weed=0; empty=0; locked=0
    for row in tiles:
        for t in row:
            if t is None: empty+=1
            elif t=="LOCKED": locked+=1
            elif isinstance(t, dict):
                k=t.get("kind")
                if k=="WEED": weed+=1
                elif k=="PLANT": crops[t["crop"]]=crops.get(t["crop"],0)+1
                elif k in ("COOP","PASTURE"):
                    an=t.get("animal")
                    if an: animals[an]=animals.get(an,0)+1
    return {"animals":animals,"crops":crops,"weed":weed,"empty":empty,"locked":locked}

def process(fname):
    with open(os.path.join(SRC, fname)) as f:
        d = json.load(f)
    info = d['info']
    names = info['TeamNames']
    rewards = d['rewards']
    if names[0]==US and names[1]==US:
        seat=0; opp='SELF-MIRROR'
    elif names[0]==US:
        seat=0; opp=names[1]
    elif names[1]==US:
        seat=1; opp=names[0]
    else:
        seat=None; opp='UNKNOWN'
    our_r = rewards[seat]; opp_r = rewards[1-seat]
    margin = our_r-opp_r
    outcome = 'TIE' if margin==0 else ('WIN' if margin>0 else 'LOSS')
    steps = d['steps']
    final_farms = steps[-1][0]['observation']['farms']
    final_tiles = [tile_summary(final_farms[p]['tiles']) for p in (0,1)]
    final_unlocked = [len(final_farms[p]['unlocked_quadrants']) for p in (0,1)]
    # day-9 and day-19 snapshots for animal-count trend
    snaps = {}
    for day in (5,9,14,19,24):
        step_idx = day*24
        if step_idx < len(steps):
            farms = steps[step_idx][0]['observation']['farms']
            snaps[day] = {
                'our_money': farms[seat]['money'], 'opp_money': farms[1-seat]['money'],
                'our_animals': sum(v for v in tile_summary(farms[seat]['tiles'])['animals'].values()),
                'opp_animals': sum(v for v in tile_summary(farms[1-seat]['tiles'])['animals'].values()),
            }
    result = {
        'episode_id': info['EpisodeId'], 'opponent': opp, 'seed': info.get('seed'), 'seat': seat,
        'our_reward': our_r, 'opp_reward': opp_r, 'margin': margin, 'outcome': outcome,
        'final_tiles_us': final_tiles[seat], 'final_tiles_opp': final_tiles[1-seat],
        'final_unlocked_us': final_unlocked[seat], 'final_unlocked_opp': final_unlocked[1-seat],
        'snaps': snaps,
    }
    del d, steps
    gc.collect()
    return result

if __name__ == '__main__':
    files = sorted(glob.glob(os.path.join(SRC, '*.json')))
    out = []
    for fp in files:
        r = process(os.path.basename(fp))
        out.append(r)
        print(r['episode_id'], r['opponent'], r['seat'], r['our_reward'], r['opp_reward'], r['margin'], r['outcome'])
    with open(os.path.join(SRC, 'live_summaries.json'), 'w') as f:
        json.dump(out, f, indent=1)
