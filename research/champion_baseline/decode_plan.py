import importlib.util, json
from collections import Counter, defaultdict

spec = importlib.util.spec_from_file_location("champion_2540_no_throttle_main", "champion_2540_no_throttle_main.py")
champion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(champion)
PLAN = champion._PLAN
print("PLAN length:", len(PLAN))
print("Sample tick 0:", PLAN[0])
print("Sample tick 1:", PLAN[1])
print("Sample tick 24:", PLAN[24])

# Basic shape check
max_hands = max(len(t.get('hands', [])) for t in PLAN)
print("max hands length across all ticks:", max_hands)

# hands count trajectory (how many hand-slots the plan addresses at each tick)
hand_lens = [len(t.get('hands', [])) for t in PLAN]
# find ticks where hand_lens increases
prev = 0
growth = []
for i, n in enumerate(hand_lens):
    if n != prev:
        growth.append((i, prev, n))
        prev = n
print("\nHand-slot-length growth points (tick, old, new):")
for g in growth:
    print(g)
