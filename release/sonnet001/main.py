"""Dynamic production-cycle agent for Kaggriculture.

Genuinely state-driven: every decision reads the current observation, and
nothing is keyed off opponent identity, episode/seed, or a replay tape.

Architecture
------------
- Static per-tile role map (WHEAT/CARROT/MELON/STRAWBERRY/COW/SHEEP/GOOSE)
  assigned deterministically by board position once a quadrant is unlocked.
  Shed-access tiles are reserved for WHEAT so the feed loop starts one step
  from the shed.
- Each unit (farmer + today's hired hands) carries a *sticky task*
  (persisted in module-level state, keyed by seat+unit index, cleared each
  new day since units respawn at the shed): a single outstanding job such
  as "water tile (x,y)" or "feed the animal at (x,y)". A unit keeps working
  its task across turns (walking toward it, then executing) until the task
  completes or is invalidated, at which point a fresh global nearest-need
  scan picks its next job. Jobs already claimed by another unit's sticky
  task are skipped, so units never contend for the same tile.
- Two-legged jobs (FEED, PLACE, FERTILIZE) resolve their prerequisite
  in-line: if the unit isn't already carrying the needed item, it detours
  through the shed first. Harvested wheat rides in the harvesting unit's
  own inventory, so a FEED job usually needs no shed trip at all — this is
  the feed-self-sufficiency mechanism.
- Market orders (BUY_LAND, HIRE, BUY_SEED, BUY_ANIMAL, an emergency
  BUY_PRODUCT WHEAT safety net, SELL, terminal liquidation) are decided
  centrally each turn from real shed/seed/money state, independent of unit
  position.
"""

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
STRUCTURE_OF = {a: ANIMALS[a]["structure"] for a in ANIMALS}
LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = {"NE": 1000, "SW": 2000, "SE": 4000}
LAND_BUY_DAY_CUTOFF = {"NE": 30, "SW": 30, "SE": 18}  # don't buy SE too late to pay back

# Portfolio: fraction of workable tiles per role. WHEAT weighted high for
# feed self-sufficiency (PHASE 1 forensics: wheat buy/sell churn and
# animal-starve risk were live failure modes). Melon/strawberry/wool stay a
# minority of tiles since their market curves crash hard on oversupply.
ROLE_CYCLE = [
    "WHEAT", "COW", "WHEAT", "SHEEP", "MELON", "WHEAT", "STRAWBERRY", "COW",
    "CARROT", "WHEAT", "SHEEP", "MELON", "WHEAT", "GOOSE", "STRAWBERRY", "COW",
    "WHEAT", "CARROT", "SHEEP", "WHEAT",
]

MAX_HANDS_PER_DAY = 10
FIB = [1, 1]
while len(FIB) < MAX_HANDS_PER_DAY + 2:
    FIB.append(FIB[-1] + FIB[-2])

SELL_KEEP_BUFFER = {"FERTILIZER": 25}  # keep a deep reserve: FERTILIZE (roughly doubles a
# crop tile's per-tick yield) is worth far more than the ~$100 raw sell price, so fertilizer
# should mostly be consumed by the FERTILIZE job, not sold — sell only genuine overflow.
PICKUP_BATCH = {"WHEAT": 6, "FERTILIZER": 4}
ANIMAL_CASH_RESERVE = 500

_STATE = {0: None, 1: None}


def _get(o, key, default=None):
    if isinstance(o, dict):
        return o.get(key, default)
    getter = getattr(o, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(o, key, default)


def _new_action():
    return {"farmer": ["PASS"], "hands": [], "market": []}


def _quadrant_of(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def _shed_tiles(board_size):
    half = board_size // 2
    return {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}


def _tile_role(x, y, board_size):
    idx = (y * board_size + x) % len(ROLE_CYCLE)
    return ROLE_CYCLE[idx]


CORE_TILE_CAP = 40
# A live-replay loss (episode 104907637) showed an opponent running only 6
# total animals the entire game out-earn us 2:1 by the end despite us
# running 12-14 animals across a full 75-tile footprint. The same pattern
# was independently visible in the old frozen-tape submission's own final
# tile counts (~8 cow + 6 sheep + 4 wheat tiles, nothing else, yet a much
# higher live average than this agent's solo ceiling). A crew this size
# cannot give daily service (water/feed/harvest) to every tile in a
# sprawling footprint — missed days show up as lost yield, not just
# delayed cash. Capping the active footprint lets the same crew give
# near-full daily coverage to fewer, better-tended tiles.
def _plan_tiles(unlocked, board_size, shed_pos_set):
    all_tiles = []
    for y in range(board_size):
        for x in range(board_size):
            if _quadrant_of(x, y, board_size) in unlocked:
                all_tiles.append((x, y))
    if len(all_tiles) > CORE_TILE_CAP:
        all_tiles.sort(key=lambda t: min(_dist(t, s) for s in shed_pos_set))
        all_tiles = all_tiles[:CORE_TILE_CAP]
    roles = {}
    for (x, y) in all_tiles:
        roles[(x, y)] = "WHEAT" if (x, y) in shed_pos_set else _tile_role(x, y, board_size)
    return roles


def _new_state():
    return {"last_step": -1, "day": -1, "tasks": {}}


def _step_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x == tx and y == ty:
        return None
    if x < tx:
        return "EAST"
    if x > tx:
        return "WEST"
    if y < ty:
        return "SOUTH"
    if y > ty:
        return "NORTH"
    return None


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _plant_ready_harvest(tile, day):
    if tile.get("yield_units", 0) <= 0:
        return False
    cd = CROPS.get(tile.get("crop"))
    if cd is None:
        return False
    return (day - tile.get("planted_day", 0)) >= cd["first_yield_day"]


def _unit_positions(farm):
    return [farm["farmer"]] + list(farm.get("hands") or [])


def _unit_inventory(private, idx):
    invs = private.get("inventories") or []
    return invs[idx] if idx < len(invs) else {}


def _desired_hands(n_tiles, money):
    # Empirically tuned against fixed-seed solo evaluation (see eval.py):
    # a leaner 1-hand-per-6-tiles ratio capped at 10 outperformed both
    # smaller and much larger crews (more hands past this point mostly
    # idled — see the movement/PASS histogram investigation — while their
    # hire cost still crowded out BUY_SEED/BUY_ANIMAL spend on the low-cash
    # early game).
    if n_tiles <= 0:
        return 0
    target = max(1, (n_tiles + 5) // 6)
    target = min(target, MAX_HANDS_PER_DAY)
    cum = 0
    afford = 0
    for n in range(target):
        cum += FIB[n]
        if cum > max(0.0, money) * 0.7:
            break
        afford += 1
    return afford


# --------------------------------------------------------------------------
# Per-tile "what does this tile need" query, and the free (no-carry) local
# action available for a unit standing on it right now.
# --------------------------------------------------------------------------

def _free_local_action(tile, day):
    """Action requiring nothing carried, available for whoever stands here."""
    if not isinstance(tile, dict):
        return None
    kind = tile.get("kind")
    if kind == "WEED":
        return ["DIG"]
    if kind == "PLANT":
        if tile.get("yield_units", 0) and _plant_ready_harvest(tile, day):
            return ["HARVEST"]
        if not tile.get("watered_today"):
            return ["WATER"]
        return None
    if kind in ("COOP", "PASTURE") and tile.get("animal"):
        if tile.get("fertilizer_available"):
            return ["COLLECT_FERTILIZER"]
        if tile.get("yield_units", 0) > 0:
            return ["HARVEST"]
        if not tile.get("cared_today"):
            return ["CARE"]
        return None
    return None


def _job_at_tile(x, y, tile, role, day, seeds, shed):
    """Return (kind, payload) for the outstanding job at this tile, or None.
    kind in WATER/HARVEST/DIG/CARE/COLLECT_FERTILIZER/FEED/PLACE/PLANT/BUILD.
    """
    if isinstance(tile, dict):
        kind = tile.get("kind")
        if kind == "WEED":
            return ("DIG", None)
        if kind == "PLANT":
            if tile.get("yield_units", 0) and _plant_ready_harvest(tile, day):
                return ("HARVEST", None)
            if not tile.get("watered_today"):
                return ("WATER", None)
            if tile.get("fertilized_until_day", -1) < day and shed.get("FERTILIZER", 0) > 0:
                return ("FERTILIZE", None)
            return None
        if kind in ("COOP", "PASTURE"):
            if tile.get("animal"):
                if tile.get("fertilizer_available"):
                    return ("COLLECT_FERTILIZER", None)
                if tile.get("yield_units", 0) > 0:
                    return ("HARVEST", None)
                if not tile.get("fed_today"):
                    return ("FEED", None)
                if not tile.get("cared_today"):
                    return ("CARE", None)
                return None
            else:
                if role in ANIMALS and shed.get(role, 0) > 0:
                    return ("PLACE", role)
                return None
        return None
    if tile is None:
        if role in CROPS and seeds.get(role, 0) > 0:
            return ("PLANT", role)
        if role in ANIMALS:
            return ("BUILD", role)
    return None


JOB_PRIORITY = ["DIG", "HARVEST", "FEED", "COLLECT_FERTILIZER", "CARE", "WATER", "PLACE", "PLANT", "BUILD", "FERTILIZE"]
JOB_RANK = {k: i for i, k in enumerate(JOB_PRIORITY)}
# Jobs are picked by (distance band, tier rank) rather than strict tier-first
# priority: a strict "priority always beats distance" scan sends a unit
# clear across the board for a marginal-priority job while ignoring
# low-priority work one tile away, which was the dominant source of wasted
# turns (movement was >60% of all actions before this fix). Banding lets
# urgency still win among comparably-close jobs, without causing long treks
# for a one-tier priority edge.
DISTANCE_BAND = 4


def _find_new_task(pos, roles, tiles_grid, day, seeds, shed, claimed):
    """Global need scan across every workable tile, skipping tiles another
    unit's sticky task already claims this turn. Picks the job minimizing
    (distance band, tier rank, exact distance)."""
    best = None
    best_key = None
    for (x, y), role in roles.items():
        if (x, y) in claimed:
            continue
        tile = tiles_grid[y][x]
        job = _job_at_tile(x, y, tile, role, day, seeds, shed)
        if job is None:
            continue
        kind, payload = job
        d = _dist(pos, (x, y))
        key = (d // DISTANCE_BAND, JOB_RANK[kind], d)
        if best_key is None or key < best_key:
            best_key = key
            best = {"kind": kind, "tile": (x, y), "payload": payload}
    return best


def _task_still_valid(task, tiles_grid, day, seeds, shed):
    if task["kind"] == "DROP":
        return True
    x, y = task["tile"]
    tile = tiles_grid[y][x]
    role = task["payload"] if task["kind"] in ("PLANT", "BUILD", "PLACE") else None
    # Re-derive what's needed at this tile right now and check it matches.
    if task["kind"] in ("WATER", "HARVEST", "DIG", "CARE", "COLLECT_FERTILIZER"):
        if not isinstance(tile, dict):
            return False
        kind = tile.get("kind")
        if task["kind"] == "DIG":
            return kind == "WEED"
        if task["kind"] == "WATER":
            return kind == "PLANT" and not tile.get("watered_today")
        if task["kind"] == "HARVEST":
            return tile.get("yield_units", 0) > 0 and (
                (kind == "PLANT" and _plant_ready_harvest(tile, day)) or ("animal" in tile)
            )
        if task["kind"] == "CARE":
            return "animal" in tile and not tile.get("cared_today")
        if task["kind"] == "COLLECT_FERTILIZER":
            return "animal" in tile and bool(tile.get("fertilizer_available"))
    if task["kind"] == "FEED":
        return isinstance(tile, dict) and "animal" in tile and not tile.get("fed_today")
    if task["kind"] == "FERTILIZE":
        return (
            isinstance(tile, dict) and tile.get("kind") == "PLANT"
            and tile.get("fertilized_until_day", -1) < day
        )
    if task["kind"] == "PLANT":
        return tile is None and seeds.get(role, 0) > 0
    if task["kind"] == "BUILD":
        return tile is None
    if task["kind"] == "PLACE":
        return (
            isinstance(tile, dict)
            and tile.get("kind") in ("COOP", "PASTURE")
            and not tile.get("animal")
        )
    return False


def _act_on_task(task, pos, inv, tile, shed_pos_set):
    """We are standing on task['tile']. Return the action to execute, given
    what we're carrying (two-legged jobs may still need a shed detour, which
    the caller handles before calling this)."""
    kind = task["kind"]
    if kind == "DIG":
        return ["DIG"]
    if kind == "WATER":
        return ["WATER"]
    if kind == "HARVEST":
        return ["HARVEST"]
    if kind == "CARE":
        return ["CARE"]
    if kind == "COLLECT_FERTILIZER":
        return ["COLLECT_FERTILIZER"]
    if kind == "FEED":
        return ["FEED"]
    if kind == "FERTILIZE":
        return ["FERTILIZE"]
    if kind == "PLANT":
        return ["PLANT", task["payload"]]
    if kind == "BUILD":
        return ["BUILD_" + STRUCTURE_OF[task["payload"]]]
    if kind == "PLACE":
        return ["PLACE", task["payload"]]
    return ["PASS"]


def _needs_carry(task):
    if task["kind"] == "FEED":
        return "WHEAT"
    if task["kind"] == "FERTILIZE":
        return "FERTILIZER"
    if task["kind"] == "PLACE":
        return task["payload"]
    return None


def _decide_unit(unit_key, pos, inv, tasks, roles, tiles_grid, day, seeds, shed,
                  board_size, shed_pos_set, claimed):
    pos = (int(pos[0]), int(pos[1]))
    task = tasks.get(unit_key)

    if task is not None and not _task_still_valid(task, tiles_grid, day, seeds, shed):
        task = None
        tasks.pop(unit_key, None)

    if task is None:
        # Opportunistic free action on the current tile before committing to
        # a new (possibly distant) task.
        tile_here = tiles_grid[pos[1]][pos[0]]
        free_act = _free_local_action(tile_here, day)
        if free_act is not None:
            return free_act
        task = _find_new_task(pos, roles, tiles_grid, day, seeds, shed, claimed)
        if task is None:
            if sum(v for v in inv.values() if v) > 0:
                task = {"kind": "DROP", "tile": None, "payload": None}
            else:
                return ["PASS"]
        tasks[unit_key] = task

    claimed.add(task["tile"])

    if task["kind"] == "DROP":
        if pos in shed_pos_set:
            tasks.pop(unit_key, None)
            return ["DROP"]
        target = min(shed_pos_set, key=lambda t: _dist(pos, t))
        step = _step_toward(pos, target)
        return [step] if step else ["PASS"]

    need = _needs_carry(task)
    if need is not None and inv.get(need, 0) <= 0:
        if shed.get(need, 0) <= 0:
            tasks.pop(unit_key, None)
            return ["PASS"]
        if pos in shed_pos_set:
            qty = PICKUP_BATCH.get(need, 1)
            return ["PICKUP", need, min(qty, shed.get(need, 0))]
        target = min(shed_pos_set, key=lambda t: _dist(pos, t))
        step = _step_toward(pos, target)
        return [step] if step else ["PASS"]

    target = task["tile"]
    if pos == target:
        tile_here = tiles_grid[pos[1]][pos[0]]
        act = _act_on_task(task, pos, inv, tile_here, shed_pos_set)
        tasks.pop(unit_key, None)
        return act
    step = _step_toward(pos, target)
    return [step] if step else ["PASS"]


def _sell_orders(shed, market_prices, market_orders_left, wheat_keep):
    prices = market_prices or {}
    items = []
    for item, qty in shed.items():
        if item in ANIMALS:
            continue
        keep = wheat_keep if item == "WHEAT" else SELL_KEEP_BUFFER.get(item, 0)
        excess = int(qty) - keep
        if excess > 0:
            items.append((prices.get(item, 0), item, excess))
    items.sort(reverse=True)
    orders = []
    for price, item, qty in items:
        if len(orders) >= market_orders_left:
            break
        orders.append(["SELL", item, qty])
    return orders


def _agent_impl(obs):
    step = int(_get(obs, "step", 0) or 0)
    seat = int(_get(obs, "player", 0) or 0)
    seat = 1 if seat == 1 else 0
    day = int(_get(obs, "day", 0) or 0)
    hour = int(_get(obs, "hour", step % 24) or 0)

    state = _STATE[seat]
    if state is None or step == 0 or step < state["last_step"]:
        state = _new_state()
        _STATE[seat] = state
    state["last_step"] = step
    if day != state["day"]:
        state["day"] = day
        state["tasks"] = {}

    farms = list(_get(obs, "farms", []) or [])
    if len(farms) <= seat:
        return _new_action()
    farm = farms[seat]
    private = _get(obs, "private", {}) or {}
    market = _get(obs, "market", {}) or {}
    prices = _get(market, "prices", {}) or {}
    shed = dict(_get(private, "shed", {}) or {})
    seeds = dict(_get(private, "seeds", {}) or {})
    money = float(farm.get("money", 0) or 0)
    board_size = len(farm.get("tiles") or []) or 10
    tiles_grid = farm["tiles"]
    unlocked = list(farm["unlocked_quadrants"])
    shed_pos_set = _shed_tiles(board_size)

    action = _new_action()
    market_orders = []

    # ---- Centralized market decisions -------------------------------
    # Live-replay evidence (see CORE_TILE_CAP note) showed money staying
    # near zero through day ~19 in nearly every game — real opponents had
    # $1k-26k by then. Buying land the capped footprint doesn't need is
    # capital locked up for zero return; only buy the next quadrant while
    # it's still needed to reach CORE_TILE_CAP.
    n_extra = len(unlocked) - 1
    tiles_per_quadrant = (board_size // 2) ** 2
    if n_extra < len(LAND_ORDER) and len(unlocked) * tiles_per_quadrant < CORE_TILE_CAP:
        next_land = LAND_ORDER[n_extra]
        cost = LAND_PRICES[next_land]
        if day <= LAND_BUY_DAY_CUTOFF[next_land] and money >= cost + 400:
            market_orders.append(["BUY_LAND"])
            money -= cost
            unlocked = unlocked + [next_land]

    roles = _plan_tiles(unlocked, board_size, shed_pos_set)
    n_workable = len(roles)

    if hour == 0:
        target_hands = _desired_hands(n_workable, money)
        already = int(farm.get("hires_today", 0) or 0)
        need = max(0, target_hands - already)
        committed_cost = 0
        cum_cost = 0
        for n in range(already, already + need):
            if n >= len(FIB):
                break
            cum_cost += FIB[n]
            if cum_cost > money:
                break
            market_orders.append(["HIRE"])
            committed_cost = cum_cost
        money -= committed_cost

    crop_need = {c: 0 for c in CROPS}
    animal_need = {a: 0 for a in ANIMALS}
    for (x, y), role in roles.items():
        tile = tiles_grid[y][x]
        if tile is None:
            if role in CROPS:
                crop_need[role] += 1
            elif role in ANIMALS:
                animal_need[role] += 1
        elif isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and not tile.get("animal"):
            if role in ANIMALS:
                animal_need[role] += 1

    # One batched order per item type (not one order per unit) — a market
    # order already carries a quantity, and maxMarketOrdersPerTurn caps the
    # number of *orders*, not units, so batching is what leaves slots free
    # for SELL every turn.
    for crop, need in crop_need.items():
        have = seeds.get(crop, 0)
        want = min(max(0, need - have), 12)
        if want <= 0:
            continue
        cost_each = CROPS[crop]["seed"]
        qty = min(want, int(money // cost_each))
        if qty > 0 and len(market_orders) < 9:
            market_orders.append(["BUY_SEED", crop, qty])
            money -= qty * cost_each

    # Live-replay evidence: our money sat near zero through day ~19 in
    # nearly every game while several real opponents already had
    # $1k-26k banked by then (episodes 104900754, 104903340, 104905146,
    # 104907637). Animals take 6-8 days to first yield; continuously
    # reinvesting every spare dollar into more of them (the old want<=4,
    # reserve=200 policy) meant cash never got the chance to accumulate.
    # A real cash reserve and a smaller per-turn batch force the surplus
    # to actually bank before more capital gets locked into non-liquid
    # assets.
    n_units_today = 1 + len(farm.get("hands") or [])
    for animal, need in animal_need.items():
        have = shed.get(animal, 0) + sum(
            _unit_inventory(private, i).get(animal, 0) for i in range(n_units_today)
        )
        want = min(max(0, need - have), 2)
        if want <= 0:
            continue
        cost_each = ANIMALS[animal]["cost"]
        qty = min(want, max(0, int((money - ANIMAL_CASH_RESERVE) // cost_each)))
        if qty > 0 and len(market_orders) < 9:
            market_orders.append(["BUY_ANIMAL", animal, qty])
            money -= qty * cost_each

    total_animals = 0
    unfed_animals = 0
    for y in range(board_size):
        for x in range(board_size):
            t = tiles_grid[y][x]
            if isinstance(t, dict) and "animal" in t:
                total_animals += 1
                if not t.get("fed_today"):
                    unfed_animals += 1
    carried_wheat_total = shed.get("WHEAT", 0)
    for i in range(n_units_today):
        carried_wheat_total += _unit_inventory(private, i).get("WHEAT", 0)
    shortfall = unfed_animals - carried_wheat_total
    if shortfall > 0 and len(market_orders) < 9:
        market_orders.append(["BUY_PRODUCT", "WHEAT", min(shortfall, 20)])

    wheat_keep = max(8, total_animals * 3)

    if step >= 714:
        for item, qty in list(shed.items()):
            if item in ANIMALS or qty <= 0:
                continue
            if len(market_orders) >= 10:
                break
            market_orders.append(["SELL", item, int(qty)])
    else:
        remaining_slots = 10 - len(market_orders)
        if remaining_slots > 0:
            market_orders.extend(_sell_orders(shed, prices, remaining_slots, wheat_keep))

    action["market"] = market_orders[:10]

    # ---- Per-unit farmer/hand decisions ------------------------------
    tasks = state["tasks"]
    claimed = {t["tile"] for t in tasks.values() if t.get("tile") is not None}
    positions = _unit_positions(farm)
    unit_actions = []
    for idx, pos in enumerate(positions):
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            unit_actions.append(["PASS"])
            continue
        x, y = int(pos[0]), int(pos[1])
        if not (0 <= x < board_size and 0 <= y < board_size):
            unit_actions.append(["PASS"])
            continue
        inv = _unit_inventory(private, idx)
        act = _decide_unit(
            idx, (x, y), inv, tasks, roles, tiles_grid, day, seeds, shed,
            board_size, shed_pos_set, claimed,
        )
        unit_actions.append(act)

    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return action


def agent(obs):
    try:
        return _agent_impl(obs)
    except Exception:
        try:
            seat = int(_get(obs, "player", 0) or 0)
            farms = list(_get(obs, "farms", []) or [])
            n_hands = len(farms[seat].get("hands") or []) if seat < len(farms) else 0
        except Exception:
            n_hands = 0
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n_hands)], "market": []}
