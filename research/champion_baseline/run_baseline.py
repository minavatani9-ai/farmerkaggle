import sys, time, json, importlib.util
sys.path.insert(0, '.')
import kaggle_environments as ke

spec = importlib.util.spec_from_file_location('champion_2540_no_throttle_main', 'champion_2540_no_throttle_main.py')
champion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(champion)

SEEDS = [101, 202, 303, 404, 505]

def final_money(env):
    last = env.steps[-1]
    obs0 = last[0].observation
    m0 = obs0['farms'][0]['money']
    m1 = obs0['farms'][1]['money']
    statuses = [s.status for s in last]
    return m0, m1, statuses

results = {"self_play": [], "vs_pass": [], "vs_random": [], "vs_starter": []}

t0 = time.time()
for s in SEEDS:
    env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
    env.run([champion.agent, champion.agent])
    m0, m1, statuses = final_money(env)
    results["self_play"].append({"seed": s, "p0_money": m0, "p1_money": m1, "statuses": statuses})
    print(f"[self_play] seed={s} p0=${m0:.0f} p1=${m1:.0f} statuses={statuses} elapsed={time.time()-t0:.1f}s")

for opp_name in ["pass", "random", "starter"]:
    for s in SEEDS:
        env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run([champion.agent, opp_name])
        m0, m1, statuses = final_money(env)
        key = f"vs_{opp_name}"
        results[key].append({"seed": s, "champion_money": m0, "opp_money": m1, "statuses": statuses})
        print(f"[vs_{opp_name}] seed={s} champion=${m0:.0f} opp=${m1:.0f} statuses={statuses} elapsed={time.time()-t0:.1f}s")

with open("baseline_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n=== SUMMARY ===")
sp = results["self_play"]
print(f"self_play p0 mean: {sum(r['p0_money'] for r in sp)/len(sp):.0f}")
print(f"self_play p1 mean: {sum(r['p1_money'] for r in sp)/len(sp):.0f}")
for opp_name in ["pass", "random", "starter"]:
    rs = results[f"vs_{opp_name}"]
    cm = sum(r['champion_money'] for r in rs)/len(rs)
    om = sum(r['opp_money'] for r in rs)/len(rs)
    wins = sum(1 for r in rs if r['champion_money'] > r['opp_money'])
    print(f"vs_{opp_name}: champion mean=${cm:.0f} opp mean=${om:.0f} wins={wins}/{len(rs)}")
print(f"Total time: {time.time()-t0:.1f}s")
