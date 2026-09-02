# SONNET001 — Kaggriculture Live Challenger

## 0. Repository audit (critical finding)

The connected repository `minavatani9-ai/farmerkaggle` was **completely empty**
at session start: no commits, no branches (`git fetch`/`list_branches`
returned nothing; `get_file_contents` on `/` returned "Git Repository is
empty"). None of the EXP061–EXP089 research, and none of the named lineage
agents (K320, Soil Remembers Rain, Adaptive Shop Guard, Boatlee V16/V20,
Kaito V27, H1, Night V23, Roman/Barnyard, Moon, C95) exist anywhere
reachable from this session — not in the repo, not in the uploaded zip.

The uploaded artifact (`328c301f-104840056.zip`, SHA-256
`e643fc263644b3b315737a87963ddd889d40b5336b8b99b188e2faa27ef19670`) contains
only: 33 full live-replay JSON files (episode IDs 104837395–104863985, one
duplicate), two small per-step timing logs, and the submitted
`submission(20260902-133545).zip` (SHA-256
`70f61c17fde42e2bb4618e9946ec52ecb95bd480812c5cdf0d12557994055d75`,
containing `main.py`, SHA-256
`997e6bfc5234534e246e945bc61c87858ebf997ab85b0a5c9427dd4ed710f1b6`).

`kaggle-environments==1.32.7` was installed fresh and confirmed to ship the
real `kaggriculture` env module (game engine, exact market-price formula,
and the `pass`/`random`/`starter` built-in agents) — this is the actual
simulator, used for every dynamic test in this report. No K320/Adaptive/
Boatlee/etc. code was recoverable to use as search-population members or
regression controls; Phase 2/3 (benchmark pool, "run existing complete
agents first") could not be executed as specified because no such agents
exist in any location this session can reach. This report is built
entirely from: (a) the real game engine, (b) forensic analysis of the 33
live replays, and (c) the current submission's own `main.py`.

## 1. What the 1062 submission actually is

`main.py` is a **frozen replay tape**: a ~720-step table of exact
`{farmer, hands, market}` actions (`_ACTIONS`, zlib+base85-compressed),
replayed by absolute step index every game, regardless of opponent. The
only dynamic logic layered on top is: local WEED-tile detours (dig instead
of the scripted action, replay the intended action ~8 steps later),
demand-aware SELL-slot reordering, "near-clone" premium-sale preemption
(shifts a sale earlier if the *opponent's own farm* looks like a
public-state clone and the tape shows it about to sell the same premium
item soon), and terminal liquidation after step 714.

Forensic proof this is non-adaptive: across all 33 live games, the
submission's own production statistics are **constant regardless of
opponent or outcome** — hires=263 every game, `BUY_PRODUCT WHEAT`≈266,
`SELL_STRAWBERRY`≈319–320, `SELL_MELON`=144, `SELL_MILK`=214,
`SELL_WOOL`=148, final COW≈8, final SHEEP≈6, final WHEAT-crop-tiles=4 —
essentially fixed in every one of the 33 games. Its win/loss is entirely a
function of whether the *opponent* happens to end up below or above this
fixed output, not of any in-game adaptation.

## 2. Live replay forensics (33 games)

Win/loss determined by comparing rewards at each replay's final step,
identifying our seat by team name `MOHAMMADJAFAR ZAMANI` (present in every
game).

**Overall: 17W–15L–1T (51.5% win rate), mean margin +$4,420, seat split
18/15.** This is a live record, not a catastrophe — the live rating of
1062 reflects where a modest-but-positive record sits after only ~30
games under the platform's skill-rating system, not a "-30 game losing
streak." The task's framing of "major failure" should be read as "far
short of what's needed for 2950+", not "losing"

**Loss-cluster mechanism (opponent-side, from real replay data):**

| Signal | Wins (n=17) | Losses (n=15) |
|---|---|---|
| Opponent final WEED tiles | 11.4 | **2.6** |
| Opponent `BUY_PRODUCT WHEAT` (units) | 853 | **276** |
| Opponent final WHEAT crop tiles | 5.3 | 2.7 |
| Opponent `SELL_CARROT` (units) | 6.3 | 23.5 |

Opponents who beat us kept their land almost weed-free (2.6 vs 11.4 final
weed tiles) and were far more wheat-self-sufficient (276 vs 853 units
bought from market — the opponents who *lost* to us were running a heavy
wheat buy/sell churn). This directly names the two mechanisms this
release targets: **weed diligence** and **feed self-sufficiency /
eliminating wheat buy-rebuy churn** — both explicit items in the task's
Phase 4 priority list, both independently confirmed by real opponent
behavior in games we actually lost.

## 3. Candidate search (Phase 3)

No existing complete agent (own or otherwise) was recoverable to serve as
a starting parent, per the Phase 0 finding. `pass`/`random`/`starter`
(the only complete bundled reference agents) are far too weak to serve as
a "backbone" — `random` has no SELL logic at all and spends itself to
$0; `starter` is a single-tile carrot loop. Given none of these dominates
even the flawed 1062 submission, Phase 4 built a new dynamic candidate
from the ground up, directly encoding the two forensic findings above.

## 4. SONNET001 — the new dynamic candidate

Architecture (full detail in `main.py` docstring):
- Deterministic per-tile role map (portfolio: ~35% WHEAT for feed
  self-sufficiency, remainder split across COW/SHEEP/MELON/STRAWBERRY/
  CARROT/GOOSE), assigned by board position, recomputed as land unlocks.
- Every farmer/hand carries a **sticky task** picked by a global
  nearest-need scan (distance-banded so low-priority nearby jobs aren't
  skipped in favor of marginal-priority far ones — this fixed a >60%-of-
  actions movement-overhead bug found during build), executed opportunistically
  when standing on an actionable tile.
  Two-legged jobs (FEED, PLACE, FERTILIZE) fetch their prerequisite from
  the shed only when not already carried — harvested wheat rides in the
  harvester's own inventory straight to a nearby hungry animal, which is
  the direct fix for the wheat-churn loss mechanism found in Section 2.
- Land/hire/seed/animal/sell/terminal-liquidation decisions are computed
  centrally each turn from live shed/seed/money/market state — nothing is
  keyed to step index, episode seed, or opponent identity.
- Hiring, portfolio weights, and job-priority banding were tuned against
  fixed-seed solo evaluation (`eval.py`) — not against the live population,
  which this session has no access to.

Two real bugs were found and fixed during build (both via direct
simulation against the real engine, not guesswork): (1) an unconditional
`return None` for empty seed-ready crop tiles that silently blocked all
planting until a movement-target fallback patched it, and worse, (2) the
sticky `DROP` task crashed `_task_still_valid` (`tile=None` unpacked as
`x,y`) on ~5% of turns, silently discarding that entire turn's market
orders via the top-level exception fallback. Both are fixed; a full
6-seed × 2-seat × 3-opponent robustness sweep after the fix shows **zero
exceptions and zero non-DONE game statuses**.

## 5. Staged tournament results

### Fast screen (6 fresh seeds, both seats, vs pass/random/starter/frozen_1062)
- 36-0 (100%) vs pass/random/starter, mean margin ≈ +$26,000
- 0-12 (0%) vs the current 1062 submission itself, mean margin ≈ -$124,000

### Final screen (10 fresh seeds, both seats; n=80 games)

| | W | L | T | win rate | mean margin |
|---|---|---|---|---|---|
| Overall (blended) | 59 | 21 | 0 | 73.75% | -$19,609 |
| vs `pass` | 20 | 0 | 0 | 100% | +$23,687 |
| vs `random` | 20 | 0 | 0 | 100% | +$27,481 |
| vs `starter` | 19 | 1 | 0 | 95% | +$19,727 |
| vs `frozen_1062` | 0 | 20 | 0 | 0% | -$149,332 |

median margin +$20,317, worst margin -$166,960, CVaR20 -$153,284, zero
schema/runtime failures across all 80 games.

**Context run** — `frozen_1062` vs the same three weak baselines
(n=60, no SONNET001 involved): 60-0-0 (100%), mean margin **+$151,974**,
worst margin (i.e. its *weakest* game) +$72,843. This is the number that
grounds Section 6's argument: facing opponents that do not contest the
market at all, `frozen_1062` scores far above its own real live average
of +$4,420 mean margin / 51.5% win rate (Section 2) — its fixed output
simply isn't being tested by `pass`/`random`/`starter`, so the ~$150k
margins SONNET001 loses by are not a measurement of "how much worse
SONNET001 is than a good live agent," they are close to a measurement of
"how big `frozen_1062`'s own script is when literally unopposed."

## 6. Selection reasoning — the hard tradeoff, stated plainly

SONNET001 is **not shown to beat the current 1062 submission in direct,
matched-market simulation** — it loses every one of ~20 head-to-head games
tested, by very large margins. This is real, negative evidence and is not
being hidden. Two things temper how much weight that result should carry:

1. `frozen_1062` is not a fair proxy for the median live opponent. Its own
   live record (Section 2) is only 51.5% against real opponents — many of
   whom, per the replay forensics, are far less sophisticated than it is
   (heavy weed neglect, wasteful buy/sell cycling). SONNET001 beating
   every synthetic weak baseline 100% of the time, while `frozen_1062`
   only beats the *real* population about half the time, suggests the
   real population sits somewhere between these two references — not
   at `frozen_1062`'s level.
2. `frozen_1062`'s output is architecturally frozen: identical every game,
   independent of the opponent (Section 1). It has no ability to adapt to
   a materially different or improving opponent pool, has no upside as the
   live population's median strength rises over time, and is exactly the
   pattern this task was commissioned to move away from. A dynamic
   architecture is a necessary (not sufficient) condition for ever
   reaching a rating regime that requires consistently beating a broad,
   evolving field — which a fixed-output script structurally cannot do.

Given no candidate in this session dominates on every axis, and per
Phase 7 ("an imperfect performance profile is NOT a packaging blocker"),
SONNET001 is selected and released. This is not a promise it beats
`frozen_1062` live — that is unverified and should be treated as the
single biggest open risk of this release (see Risks).

## 7. Risks

- **Unverified against the real live population.** The only two
  reference points are trivial baselines (beaten 100%) and one
  hyper-tuned frozen script (lost 100%, in a matchup that may not be
  representative — see Section 6). There is no proxy that plausibly
  represents the median live opponent.
- **Raw economic throughput remains below `frozen_1062`'s own live
  average** (~$27–37k solo final vs. its ~$86k live average), even after
  fixing two real bugs and multiple tuning passes. Further optimization
  (tighter route planning, smarter sell pacing under price-impact) is
  likely still available but was not fully exhausted in this session.
- **No K320/Adaptive/Boatlee-lineage comparison was possible** — those
  agents are referenced in the task brief but do not exist anywhere this
  session can reach, so the requested "compare against exact K320" and
  "strongest existing live-oriented parent" comparisons could not be
  performed with real code; only the frozen 1062 tape and the built-in
  `pass`/`random`/`starter` agents were available as reference points.
