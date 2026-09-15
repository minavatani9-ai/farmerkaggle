"""Stress test: 30 additional seeds (11-40), head-to-head only, both seats."""
import sys, time, json, importlib.util
sys.path.insert(0, '.')
import kaggle_environments as ke

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

baseline = load("baseline_main", "champion_2540_no_throttle_main.py")
variant = load("variant_plan_v2_main", "variant_plan_v2_main.py")

SEEDS = list(range(1100, 4100, 100))  # 1100,1200,...,4000 = 30 seeds

def money(env):
    obs0 = env.steps[-1][0].observation
    return obs0['farms'][0]['money'], obs0['farms'][1]['money'], [s.status for s in env.steps[-1]]

results = []
t0 = time.time()

for s in SEEDS:
    for seat, agents in enumerate([[variant.agent, baseline.agent], [baseline.agent, variant.agent]]):
        env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run(agents)
        m0, m1, st = money(env)
        variant_money = m0 if seat == 0 else m1
        baseline_money = m1 if seat == 0 else m0
        delta = variant_money - baseline_money
        results.append({"seed": s, "variant_seat": seat, "variant_money": variant_money,
                         "baseline_money": baseline_money, "delta": delta, "statuses": st})
        print(f"seed={s} seat={seat} v=${variant_money:.0f} b=${baseline_money:.0f} d=${delta:.0f} t={time.time()-t0:.0f}s")

with open("experiment_plan_v2_stress_results.json", "w") as f:
    json.dump(results, f, indent=2)

# Analysis
import math
deltas = [r["delta"] for r in results]
n = len(deltas)
mean_d = sum(deltas) / n
var_d = sum((d - mean_d)**2 for d in deltas) / (n - 1)
se = math.sqrt(var_d / n)
ci95 = 1.96 * se

wins = sum(1 for d in deltas if d > 0)
losses = sum(1 for d in deltas if d < 0)
ties = sum(1 for d in deltas if d == 0)

# Per-seed analysis
seed_deltas = {}
for r in results:
    seed_deltas.setdefault(r["seed"], []).append(r["delta"])
seed_means = {s: sum(ds)/len(ds) for s, ds in seed_deltas.items()}
neg_seeds = sum(1 for m in seed_means.values() if m < 0)
pos_seeds = sum(1 for m in seed_means.values() if m > 0)
zero_seeds = sum(1 for m in seed_means.values() if m == 0)

# Seat breakdown
seat0 = [r["delta"] for r in results if r["variant_seat"] == 0]
seat1 = [r["delta"] for r in results if r["variant_seat"] == 1]
mean_s0 = sum(seat0) / len(seat0)
mean_s1 = sum(seat1) / len(seat1)

print(f"\n{'='*60}")
print(f"STRESS TEST: 30 new seeds (60 games)")
print(f"{'='*60}")
print(f"Record: {wins}W-{losses}L-{ties}T")
print(f"Mean delta: ${mean_d:.0f} (95% CI: ${mean_d-ci95:.0f} to ${mean_d+ci95:.0f})")
print(f"Seeds positive: {pos_seeds}/30, negative: {neg_seeds}/30, zero: {zero_seeds}/30")
print(f"Seat 0 (variant first) mean: ${mean_s0:.0f}")
print(f"Seat 1 (variant second) mean: ${mean_s1:.0f}")
print(f"Total time: {time.time()-t0:.1f}s")
