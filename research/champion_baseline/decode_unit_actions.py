import importlib.util, json
from collections import Counter, defaultdict

spec = importlib.util.spec_from_file_location("champion_2540_no_throttle_main", "champion_2540_no_throttle_main.py")
champion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(champion)
PLAN = champion._PLAN

def phase_of(tick):
    if tick <= 72: return 'opening(0-72)'
    if tick <= 500: return 'mid(73-500)'
    return 'endgame(501-718)'

# Farmer+hands ops, only meaningful for ticks 0-695 (real execution range)
op_by_phase = defaultdict(Counter)
plant_by_phase_crop = defaultdict(lambda: Counter())
harvest_by_phase_crop = defaultdict(lambda: Counter())
fertilize_ticks = []
build_events = []  # (tick, day, kind)
place_animal_events = []  # (tick, day, animal)
feed_events_by_day = Counter()

for t in range(0, 696):  # only the range where PLAN farmer/hands actually executes
    entry = PLAN[t]
    day = t // 24
    ph = phase_of(t)
    ops = [entry.get('farmer', ['PASS'])] + list(entry.get('hands', []))
    for op in ops:
        if not op:
            continue
        kind = op[0]
        op_by_phase[ph][kind] += 1
        if kind == 'PLANT' and len(op) > 1:
            plant_by_phase_crop[ph][op[1]] += 1
        elif kind == 'HARVEST':
            pass  # crop unknown without tile state
        elif kind == 'FERTILIZE':
            fertilize_ticks.append(t)
        elif kind in ('BUILD_COOP', 'BUILD_PASTURE'):
            build_events.append((t, day, kind))
        elif kind == 'PLACE' and len(op) > 1 and op[1] in ('COW', 'SHEEP', 'GOOSE'):
            place_animal_events.append((t, day, op[1]))
        elif kind == 'FEED':
            feed_events_by_day[day] += 1

print("=== Farmer+hand op-kind counts by phase (ticks 0-695 only) ===")
for ph in ['opening(0-72)', 'mid(73-500)', 'endgame(501-718)']:
    print(f"\n{ph}:")
    for k, v in op_by_phase[ph].most_common():
        print(f"  {k}: {v}")

print("\n=== PLANT counts by phase & crop ===")
for ph in ['opening(0-72)', 'mid(73-500)', 'endgame(501-718)']:
    print(f"\n{ph}:")
    for crop, n in plant_by_phase_crop[ph].most_common():
        print(f"  {crop}: {n}")

print("\n=== FERTILIZE tick list (count={}) ===".format(len(fertilize_ticks)))
print("first 20 ticks:", fertilize_ticks[:20])
print("by day:", Counter(t // 24 for t in fertilize_ticks))

print("\n=== BUILD_COOP / BUILD_PASTURE events ===")
for e in build_events:
    print(" ", e)

print("\n=== PLACE animal events (tick, day, animal) ===")
for e in place_animal_events:
    print(" ", e)

print("\n=== FEED events by day ===")
for d in sorted(feed_events_by_day):
    print(f"  day {d}: {feed_events_by_day[d]}")
