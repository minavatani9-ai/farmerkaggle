import sys, time, json, importlib.util
sys.path.insert(0, '.')
import kaggle_environments as ke

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

baseline = load("baseline_main", "champion_2540_no_throttle_main.py")
variant = load("variant_window600_main", "variant_plan_window600_main.py")

SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]

def money(env):
    obs0 = env.steps[-1][0].observation
    return obs0['farms'][0]['money'], obs0['farms'][1]['money'], [s.status for s in env.steps[-1]]

results = {"head_to_head": [], "variant_selfplay": [], "baseline_selfplay": [],
           "variant_vs_pass": [], "variant_vs_random": [], "variant_vs_starter": []}

t0 = time.time()

# 1. Head-to-head: variant vs baseline, both seat orders
for s in SEEDS:
    for seat, agents in enumerate([[variant.agent, baseline.agent], [baseline.agent, variant.agent]]):
        env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run(agents)
        m0, m1, st = money(env)
        variant_money = m0 if seat == 0 else m1
        baseline_money = m1 if seat == 0 else m0
        results["head_to_head"].append({"seed": s, "variant_seat": seat, "variant_money": variant_money,
                                         "baseline_money": baseline_money, "statuses": st})
        print(f"[h2h] seed={s} variant_seat={seat} variant=${variant_money:.0f} baseline=${baseline_money:.0f} statuses={st} t={time.time()-t0:.0f}s")

# 2. Variant self-play
for s in SEEDS:
    env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
    env.run([variant.agent, variant.agent])
    m0, m1, st = money(env)
    results["variant_selfplay"].append({"seed": s, "p0": m0, "p1": m1, "statuses": st})
    print(f"[variant_sp] seed={s} p0=${m0:.0f} p1=${m1:.0f} statuses={st} t={time.time()-t0:.0f}s")

# 3. Baseline self-play at SAME seeds (paired reference)
for s in SEEDS:
    env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
    env.run([baseline.agent, baseline.agent])
    m0, m1, st = money(env)
    results["baseline_selfplay"].append({"seed": s, "p0": m0, "p1": m1, "statuses": st})
    print(f"[baseline_sp] seed={s} p0=${m0:.0f} p1=${m1:.0f} statuses={st} t={time.time()-t0:.0f}s")

# 4. Variant vs built-in opponents
for opp_name in ["pass", "random", "starter"]:
    for s in SEEDS:
        env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run([variant.agent, opp_name])
        m0, m1, st = money(env)
        key = f"variant_vs_{opp_name}"
        results[key].append({"seed": s, "variant_money": m0, "opp_money": m1, "statuses": st})
        print(f"[{key}] seed={s} variant=${m0:.0f} opp=${m1:.0f} statuses={st} t={time.time()-t0:.0f}s")

with open("experiment_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nTotal time: {time.time()-t0:.1f}s, total games: {20+10+10+30}")
