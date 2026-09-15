# Decoding `_PLAN` — the champion's 719-tick frozen strategy

Reverse-engineered directly from the decompressed `_PLAN` array (via
`zlib.decompress(base64.b85decode(...))` → 719 dicts, one per tick, each
`{'farmer': [...], 'hands': [[...], ...], 'market': [[...], ...]}`).

## 0. What actually executes at runtime (critical for interpreting the tape)

The raw `_PLAN` bytes are **not** all literally executed — three runtime
layers rewrite parts of it before the game engine sees an action:

| Tick range | Farmer/hand actions | Market SELL orders (per item) | Market BUY/HIRE/LAND orders |
|---|---|---|---|
| 0–167 | literal from `_PLAN` | literal from `_PLAN` (no reprojection yet) | literal from `_PLAN` |
| 168–695 | literal from `_PLAN` | **WHEAT/FERTILIZER**: literal from `_PLAN`. **All 7 other items**: silently replaced with the exact live-projected shed quantity via `_project_stock()` — the tape's own qty for these is a don't-care placeholder | literal from `_PLAN`, then `_repair_purchase()` may insert extra SELL orders (day ≤12 only) to fund an animal purchase shortfall |
| 696–718 | **replaced entirely** by the live `plan()` vehicle-router — `_PLAN`'s content for this range is never read at runtime | same — `plan()` computes its own SELL list from live state | `plan()` also emits its own HIRE orders |

This explains an oddity in the raw bytes: many `SELL` orders throughout the
tape (and especially ticks 692–718) request absurd quantities like `SELL
WHEAT 2186` or `SELL FERTILIZER 2002` — far beyond the 100-unit shed cap.
These are intentional **"sell everything you actually have" placeholders**:
the game engine caps to whatever's really in the shed, so the tape doesn't
need to track exact perishable-item quantities precisely; it just asks for
"more than could possibly exist" and lets truncation do the work. For
WHEAT/FERTILIZER specifically this placeholder value is taken literally
(no reprojection), but it's still just a safety-valve number, not a
meaningful literal quantity — only 6/222 WHEAT and 2/370 FERTILIZER SELL
orders in the always-executed 0–695 range even exceed 100.

## 1. Opening (ticks 0–72, days 0–3)

**Hiring**: 5 HIRE requests at tick 1 alone (day 0 total 5 requests), then
3/day 1, 4/day 2, 5/day 3 — cautious start, matches the Fibonacci-like HIRE
cost curve (`1,1,2,3,5,8,13,21,...` per successive hire) that makes each
additional hand more expensive.

**Opening market moves (tick 0, before any movement)**: `BUY_PRODUCT WHEAT
13`, `SELL WOOL 4`, `BUY_PRODUCT WHEAT 10`, `SELL WHEAT 17` — the very
first action of the game is buying wheat from town (to seed animal feed
stock before any crop has grown) while immediately selling initial WOOL/
WHEAT endowment. Tick 1 immediately buys `BUY_ANIMAL COW 2` and
`BUY_ANIMAL SHEEP 2` — livestock purchased before a single tile is planted.

**Structure-first sequencing**: `BUILD_PASTURE` at ticks 3, 4, 7, 9 (4
pastures by tick 9) — the farm builds animal housing before crops, then
places the day-1 COW/SHEEP purchases (ticks 4, 5, 8, 10 `PLACE`).

**Planting**: MELON is the very first crop planted (ticks 7, 8, 10, 11, 12,
15, 16, 18 — 12 MELON plants in the opening window vs. only 9 WHEAT).
MELON is the highest-base-price crop (base $250) and has a 10–12 day yield
window, so planting it on day 0–1 front-loads its long growth cycle. WHEAT
planting (fast: first yield day 2) starts at tick 13 once the MELON/animal
setup is underway — 9 WHEAT plants by tick 72 vs. 12 MELON, i.e. the
opening prioritizes the long-lead high-value crop over the fast staple.

**Fertilizer**: bought early (`BUY_PRODUCT FERTILIZER` starts day 5) and
also sold immediately (`SELL FERTILIZER` from tick 2) — the farm treats
early fertilizer as tradeable inventory, not yet as an input (no
`FERTILIZE` action appears until day 11 — see Section 3).

**Quadrant unlocks**: none yet — the farm operates entirely in its starting
NW quadrant (`unlocked_quadrants: ['NW']` confirmed via a fresh
`env.reset()`).

## 2. Mid-game (ticks 73–500, days 3–20)

**Hiring accelerates**: 7–8 HIRE requests/day through days 6–9, then 9–11/
day from day 10 onward, plateauing around 9–11/day for the rest of the
game (260 total HIRE market orders across all 719 ticks — note this is
*requests*, not confirmed hires; the tape over-requests using the same
"let the engine cap it" pattern as SELL, since unaffordable HIRE orders
are silent no-ops per `_repair_purchase`'s own Fibonacci-cost simulation).

**Quadrant unlocks — both happen here, and that's ALL of them**:
- Tick 150 (day 6, hour 6): `BUY_LAND` — land_count 1→2, cost $1,000
- Tick 265 (day 11, hour 1): `BUY_LAND` — land_count 2→3, cost $2,000

**The champion never buys the 4th and final quadrant** (`costs[3] =
$4,000`, land_count 3→4). One full 5×5 quadrant — 25% of the entire board
— sits `LOCKED` (unplantable, unbuildable) for the whole 30-day game. See
Section 5 for why this isn't a trivially-fixable gap.

**Planting shifts to sustaining crops**: WHEAT dominates (100 PLANT
actions in this window vs. 34 STRAWBERRY, 0 new MELON/CARROT) — the farm
has moved from "establish long-lead crops" to "keep the wheat pipeline
running" for both direct wheat sale (town buys it, price rises as supply
drops — the one net-demand item per the verified market model) and animal
feed (`FEED` actions climb steadily from 2/day at day 0 to 15–18/day by
day 13 onward, tracking herd growth).

**Animal purchases** (all 12 `BUY_ANIMAL` events in the whole game are
clustered in days 0–11): COW at ticks 1(×2), 65, 88, 150(×2), 169, 176;
SHEEP at ticks 1(×2), 196(×2), 217, 226; GOOSE at ticks 241(×2), 265. No
new animals are ever purchased after day 11 — herd size is fixed for the
remaining 19 days, with `_adjust_herd()` only reallocating COW↔SHEEP mix
at pickup/place time based on shop unlocks (YARN_STORE open + no
milk-shop open + sheep<12 + cows≥4 → redirect a COW purchase to SHEEP).

**Fertilizer usage finally starts**: the first `FERTILIZE` action (which
consumes 1 fertilizer from inventory for a 3-day yield-doubling bonus on a
crop tile) appears at tick 284 (day 11), and the real cadence doesn't pick
up until days 14–24 (4/day), peaking at 13/day on day 20 and 12/day on day
24. Across the *entire* always-executed range (ticks 0–695): only **72
FERTILIZE actions total**, consuming 72 units — against **1,836 units
sold** (`SELL FERTILIZER`, literal quantities) and only 64 units
separately purchased via `BUY_PRODUCT`. The farm is a massive net
fertilizer *producer* (from `COLLECT_FERTILIZER` on animal tiles) that
sells ~96% of its own output at what the verified market model says is a
fast-crashing, floor-bound price (`FERTILIZER: below_target 0.40 /
above_target 0.40`, "nobody buys, price crashes 100→1" per the confirmed
engine facts) instead of reinvesting it into yield bonus. This is a
strong signal for Section 5's improvement candidates, though not the one
tested this round (see rationale there).

**Sell reprojection kicks in at tick 168**: from here through tick 695,
every SELL order for CARROT/TOMATO/STRAWBERRY/MELON/EGG/MILK/WOOL is
silently replaced with the exact live shed quantity computed via
`_project_stock()`. Only WHEAT and FERTILIZER keep the tape's own literal
(possibly placeholder) numbers.

## 3. Endgame (ticks 501–718, days 21–29)

**Ticks 501–695 (days 21–28+)**: still literal `_PLAN` execution (same
rules as mid-game — WHEAT/FERTILIZER literal, others reprojected). PLANT
activity shifts again: 53 WHEAT + 31 CARROT plants in this window (CARROT
reappears for the first time since the opening — a fast-yield, cheap-seed
crop, sensible for a farm running out of runway to recoup slower crops).
DIG appears for the first time here (25 uses in 501–695 vs. 2 in
73–500) — likely clearing spent/weeded tiles that are no longer worth
replanting given the shrinking time horizon.

**Ticks 696–718 (last ~1 day)**: `_exp119_agent` switches entirely from
the frozen tape to the live `plan()` router — a simple greedy vehicle-
routing algorithm that scores each harvestable/collectable tile by
`value / (travel_cost ** exponent)`, assigns each farmer/hand a route
under a hard "must return to the shed by tick 719" deadline constraint,
and issues SELL orders for the projected end-of-route shed contents. This
is a genuinely adaptive, state-aware final sprint rather than a scripted
liquidation, which makes sense as the frozen tape can't know in advance
exactly which tiles will have ripe yield at that exact moment in a given
game.

**Final liquidation mechanics**: `_baseline_agent` also has its own
"sell everything currently in the shed" override for ticks 706–718 (via
`_post_action_shed`), but this is moot in normal play since `_exp119_agent`
already routes those ticks to `plan()` before `_baseline_agent` ever runs.

## 4. Cross-cutting design pattern: "over-request, let the engine cap it"

Three independent mechanisms in this codebase rely on the same trick —
issue a request larger than what's actually available/affordable and let
the game engine's own capping logic (shed contents for SELL, cash balance
for HIRE/BUY, quadrant cost table for BUY_LAND) truncate it to the correct
real value:
- SELL orders with quantities like 2186, 2002, 890 (shed cap is 100)
- Daily HIRE request counts (5–11/day) that don't necessarily match how
  many are actually affordable that day
- `_repair_purchase`'s own Fibonacci-cost HIRE simulation, which exists
  specifically because the tape doesn't track real-time affordability

This is a robustness-over-precision design: the frozen tape doesn't need
to perfectly predict live game state, because most of its economic orders
are self-correcting no-ops when wrong.

## 5. Improvement hypothesis tested this round

**Hypothesis**: extend `_exp119_agent`'s live `plan()` window earlier —
from the current 696–718 (last ~1 day, 23 ticks) to 600–718 (last ~5
days, 119 ticks) — on the theory that the state-aware live router should
out-adapt a frozen tape over a longer tail, especially against the loss
mechanisms previously identified in live replay forensics (opponent weed
diligence, per-game variance the tape can't see coming). This was
explicitly flagged in the continuation prompt as **untestable without the
real simulator** ("Cannot be validated... DO NOT attempt without the real
simulator") — which we now have.

**Result: rejected, cleanly and consistently.** See
`EXPERIMENT_PLAN_WINDOW.md` for the full numbers — the extended-window
variant lost money to the untouched baseline in **10/10 paired seeds**,
by 15–34% per game, with zero exceptions. This is not packaged.

**Why the 4th-quadrant gap (Section 2) wasn't tested this round instead**:
unlocking it is cheap in isolation (a market-only `BUY_LAND` order,
independent of farmer movement), but the frozen tape's farmer/hand
movement is a literal, path-dependent 719-tick coordinate script that was
never generated with that land available — buying it without also
routing workers onto the new tiles (which requires editing the movement
tape itself, a much higher-risk change than a market-order tweak) would
just spend $4,000 for zero production benefit. A real test of this
hypothesis needs either a live-router window long enough to develop new
land from scratch (which Section 5's result suggests the current
`plan()` isn't good enough to do profitably) or hand-authored new
movement/task logic for the freed quadrant — out of scope for a
same-session, low-risk test.
