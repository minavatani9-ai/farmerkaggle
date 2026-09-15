import importlib.util, json
from collections import Counter, defaultdict

spec = importlib.util.spec_from_file_location("champion_2540_no_throttle_main", "champion_2540_no_throttle_main.py")
champion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(champion)
PLAN = champion._PLAN

def day_hour(t):
    return t // 24, t % 24

# 1. Market orders: full timeline
market_events = []  # (tick, day, hour, kind, item_or_none, qty_or_none)
for t, entry in enumerate(PLAN):
    day, hour = day_hour(t)
    for op in entry.get('market', []):
        if not op:
            continue
        kind = op[0]
        item = op[1] if len(op) > 1 else None
        qty = op[2] if len(op) > 2 else None
        market_events.append((t, day, hour, kind, item, qty))

print("Total market events across 719 ticks:", len(market_events))
kind_counts = Counter(e[3] for e in market_events)
print("Market event kind counts:", kind_counts)

# HIRE schedule: first tick of each HIRE, cumulative count by day
hires_by_day = Counter()
for (t, day, hour, kind, item, qty) in market_events:
    if kind == 'HIRE':
        hires_by_day[day] += 1
print("\nHIRE orders per day (day: count):")
for d in sorted(hires_by_day):
    print(f"  day {d}: {hires_by_day[d]} hires")
print("Total HIRE orders:", sum(hires_by_day.values()))

# BUY_LAND (quadrant unlocks)
land_events = [(t, day, hour) for (t, day, hour, kind, item, qty) in market_events if kind == 'BUY_LAND']
print("\nBUY_LAND events (tick, day, hour):", land_events)

# BUY_ANIMAL timeline
animal_buys = [(t, day, hour, item, qty) for (t, day, hour, kind, item, qty) in market_events if kind == 'BUY_ANIMAL']
print("\nBUY_ANIMAL events (tick, day, hour, animal, qty):")
for e in animal_buys:
    print(" ", e)

# BUY_SEED timeline (aggregated by day/crop)
seed_buys_by_day_crop = defaultdict(int)
for (t, day, hour, kind, item, qty) in market_events:
    if kind == 'BUY_SEED':
        seed_buys_by_day_crop[(day, item)] += (qty or 1)
print("\nBUY_SEED totals by (day, crop) [first 60 entries]:")
for k in sorted(seed_buys_by_day_crop)[:60]:
    print(" ", k, seed_buys_by_day_crop[k])

# BUY_PRODUCT (wheat buying to feed animals presumably)
buy_product_by_day_item = defaultdict(int)
for (t, day, hour, kind, item, qty) in market_events:
    if kind == 'BUY_PRODUCT':
        buy_product_by_day_item[(day, item)] += (qty or 1)
print("\nBUY_PRODUCT totals by (day,item) [first 40]:")
for k in sorted(buy_product_by_day_item)[:40]:
    print(" ", k, buy_product_by_day_item[k])

# SELL totals by item, split by phase
def phase_of(day):
    t = day * 24
    if t <= 72: return 'opening'
    if t <= 500: return 'mid'
    return 'endgame'

sell_by_phase_item = defaultdict(int)
for (t, day, hour, kind, item, qty) in market_events:
    if kind == 'SELL':
        sell_by_phase_item[(phase_of(day), item)] += (qty or 1)
print("\nSELL totals by (phase, item):")
for k in sorted(sell_by_phase_item):
    print(" ", k, sell_by_phase_item[k])

with open("market_events.json", "w") as f:
    json.dump(market_events, f)
