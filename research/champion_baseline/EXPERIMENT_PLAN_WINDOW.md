# Experiment: extend `plan()`'s live-router window from 696→600

## Hypothesis

`_exp119_agent` currently delegates to the live, state-aware `plan()`
vehicle-router only for the final ~1 day (ticks 696–718); every earlier
tick replays the frozen `_PLAN` tape verbatim. The continuation prompt
flagged this as untested territory: *"Cannot be validated without the
real game simulator... DO NOT attempt without the real simulator."*

Hypothesis: since `plan()` reacts to real, current board/shed/price state
rather than a script recorded once and replayed blind, extending its
window to cover the last ~5 days (ticks 600–718, a mature mid/late-game
state — not the empty-board tick 0 the prompt warned about) should let
the agent adapt to per-game variance (weeds, opponent interference, the
loss mechanisms found in the earlier live-replay forensics) that the
frozen tape structurally cannot see coming, and should out-earn the
frozen tape over that stretch.

## Change made

Single-line diff in `_exp119_agent`, isolated in
`variant_plan_window600_main.py` (`champion_2540_no_throttle_main.py` is
untouched):

```diff
-    if supported and 696 <= tick <= 718:
+    if supported and 600 <= tick <= 718:
```

No other code, and no byte of `_PLAN` itself, was touched.

## Test design

All games run via the real `kaggle-environments==1.32.7` `kaggriculture`
env, `episodeSteps=720`, 10 fixed seeds
`[101,202,303,404,505,606,707,808,909,1010]` — the same 5 seeds used for
the Priority-1 baseline confirmation plus 5 new ones.

1. **Head-to-head, variant vs. untouched baseline** — both seat orders,
   10 seeds → 20 games (the game is seat-symmetric so seat-swapped runs
   reproduce the same real trial; treated as 10 independent seeds below).
2. **Variant self-play** — 10 seeds → 10 games.
3. **Baseline self-play, same 10 seeds** — 10 games, as a paired
   reference (also a reproducibility check against the Priority-1
   numbers already recorded).
4. **Variant vs. built-in `pass`/`random`/`starter`** — 10 seeds each →
   30 games.

70 games total, ~380s wall-clock, **zero exceptions, all `DONE`/`DONE`**.
Full per-game data: `experiment_plan_window600_results.json`.

## Results

### Head-to-head (variant vs. untouched baseline, same seed both sides)

| seed | variant $ | baseline $ | Δ% |
|---|---|---|---|
| 101 | 97,315 | 113,944 | -14.6% |
| 202 | 123,103 | 144,680 | -14.9% |
| 303 | 61,343–62,454 | 76,291–77,381 | -20.7% |
| 404 | 78,660 | 93,810 | -16.1% |
| 505 | 44,686 | 54,183 | -17.5% |
| 606 | 63,853 | 73,973 | -13.7% |
| 707 | 131,592 | 157,146 | -16.3% |
| 808 | 42,661 | 57,653 | -26.0% |
| 909 | 44,236 | 73,146 | -39.5% |
| 1010 | 61,443 | 75,919 | -19.1% |

**Variant wins: 0/10. Mean change: -19.8%.** Every single seed is a loss,
by a substantial and highly consistent margin.

### Self-play (variant vs. itself, same 10 seeds, paired against baseline self-play)

- Variant self-play mean: **$74,474**
- Baseline self-play mean (same 10 seeds — matches Priority-1 numbers
  exactly on the 5 shared seeds, confirming reproducibility): **$90,130**
- Variant lower in **10/10 seeds**, mean paired diff **-$15,657 (-17.4%)**

### vs. built-in opponents (10 seeds each)

| Opponent | Variant mean | Priority-1 baseline mean (5 seeds) |
|---|---|---|
| `pass` | $140,939 | $179,161 |
| `random` | $132,384 | $162,131 |
| `starter` | $144,561 | $185,807 |

Directionally identical to every other test: **-18% to -22%** below the
untouched champion in all three matchups. The variant still wins big
against these weak opponents in absolute terms (they can't compete
regardless), but it's leaving money on the table relative to what the
frozen tape alone earns in the same matchup.

## Verdict: hypothesis rejected — do not package

**All 70 games, across four independent test conditions, point the same
direction with no exceptions:** extending the live `plan()` router's
window earlier makes the champion measurably worse, not better. The
effect is large (13.7%–39.5% per-game loss in direct competition, mean
-19.8%) and fully consistent (0 wins out of 10 paired head-to-head games).

This confirms and quantifies what the continuation prompt's own replay
diff already hinted at (`plan()` disagrees with `_PLAN` on 715/719 ticks
even within its *existing* 23-tick window) — the simple greedy
vehicle-router is a substantially weaker strategy than whatever process
generated the frozen tape, and that gap doesn't shrink in a more mature
board state; if anything the seed with the worst regression (909, -39.5%)
suggests it can compound badly. The frozen tape's superiority isn't just
about the opening (tick 0) — it holds over the mid/late game too.

**Per the task's standing rule ("do not package anything unless the
improvement is consistent and clear"): this result is consistent and
clear, but negative. Nothing is packaged from this experiment.**

## What this rules out / what's next

- Confirms `plan()` should **not** be extended earlier than its current
  696 cutoff without a substantially better live-routing algorithm than
  what exists in this file today — not just a parameter tweak.
- Leaves the 4th-quadrant gap (Section 5 of `PLAN_DECODE.md`) and the
  fertilizer-sell-vs-fertilize-use imbalance (1,836 sold vs. 72 used,
  `PLAN_DECODE.md` Section 2) as the two most concrete, evidence-backed
  opportunities still on the table — both require editing the frozen
  tape's actual farmer/hand movement paths (not just market-order
  parameters), which is higher-risk and wasn't attempted this round.
- A follow-up worth trying instead of widening `plan()`'s window: improve
  `plan()` itself (its scoring function, hires target, or watering logic)
  and re-test only the existing 696–718 window before ever considering
  widening it again.
