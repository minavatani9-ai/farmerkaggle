import importlib.util
from collections import Counter, defaultdict

spec = importlib.util.spec_from_file_location("champion_2540_no_throttle_main", "champion_2540_no_throttle_main.py")
champion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(champion)
PLAN = champion._PLAN

def phase_of(t):
    if t <= 72: return 'opening'
    if t <= 500: return 'mid'
    return 'endgame_tape(501-695, still literal)'

# WHEAT/FERTILIZER SELL orders are literal (not reprojected) for ticks 0-695.
# For ticks 696-718 they're moot (plan() overrides everything).
wf_sell = defaultdict(list)
for t in range(0, 696):
    for op in PLAN[t].get('market', []):
        if op and op[0] == 'SELL' and op[1] in ('WHEAT', 'FERTILIZER'):
            wf_sell[op[1]].append((t, op[2] if len(op) > 2 else 1))

for item in ('WHEAT', 'FERTILIZER'):
    qtys = [q for (t, q) in wf_sell[item]]
    print(f"{item}: {len(qtys)} SELL orders in ticks 0-695, qty range {min(qtys)}-{max(qtys)}, sum={sum(qtys)}")
    large = [(t, q) for (t, q) in wf_sell[item] if q > 100]
    print(f"  orders with qty>100 (oversell placeholders): {len(large)} -> {large[:10]}")

# PICKUP breakdown by item, ticks 0-695
pickup_by_item_phase = defaultdict(Counter)
for t in range(0, 696):
    entry = PLAN[t]
    ph = phase_of(t)
    for op in [entry.get('farmer', ['PASS'])] + list(entry.get('hands', [])):
        if op and op[0] == 'PICKUP' and len(op) > 1:
            pickup_by_item_phase[ph][op[1]] += (op[2] if len(op) > 2 else 1)

print("\nPICKUP quantities by phase & item:")
for ph in ['opening', 'mid', 'endgame_tape(501-695, still literal)']:
    print(f" {ph}: {dict(pickup_by_item_phase[ph])}")

# FERTILIZE vs FERTILIZER sold/bought balance
fertilize_count = sum(1 for t in range(696) for op in [PLAN[t].get('farmer', ['PASS'])] + list(PLAN[t].get('hands', []))
                       if op and op[0] == 'FERTILIZE')
fert_sold = sum(q for (t, q) in wf_sell['FERTILIZER'])
fert_bought = sum(op[2] if len(op) > 2 else 1 for t in range(696) for op in PLAN[t].get('market', [])
                   if op and op[0] == 'BUY_PRODUCT' and op[1] == 'FERTILIZER')
print(f"\nFERTILIZE actions (consume 1 fertilizer each, applies yield bonus): {fertilize_count}")
print(f"FERTILIZER sold (literal qty summed, ticks 0-695): {fert_sold}")
print(f"FERTILIZER bought via BUY_PRODUCT (ticks 0-695): {fert_bought}")

# First tick of each crop's first PLANT to establish opening sequence in detail
print("\n=== First 30 non-trivial ticks (farmer op, hands ops, market ops) for opening reconstruction ===")
for t in range(0, 30):
    e = PLAN[t]
    print(t, "farmer:", e.get('farmer'), "hands:", e.get('hands'), "market:", e.get('market'))
