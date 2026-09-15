# Experiment: 4th quadrant unlock (BUY_LAND at tick 290)

## Hypothesis

The champion never buys the 4th and final quadrant (cost $4,000), leaving
25% of the board permanently LOCKED. Unlocking it via a single `BUY_LAND`
market order insertion — with NO changes to the frozen farmer/hand movement
paths — might provide indirect benefits (e.g. `plan()` in ticks 696-718
could route workers to new tiles, or there could be game mechanics that
reward having more land).

## Change made

Single `BUY_LAND` market order inserted at tick 290 (day 12, hour 2) — a
tick with zero existing market orders in the original `_PLAN`. All farmer
and hand movement paths are identical to the champion. The two existing
`BUY_LAND` orders (tick 150, tick 265) are untouched.

Isolated in `variant_quad4_unlock_main.py`; `champion_2540_no_throttle_main.py`
is untouched.

## Test design

Identical to the plan-window experiment: real `kaggle-environments==1.32.7`
`kaggriculture` env, `episodeSteps=720`, 10 fixed seeds
`[101,202,303,404,505,606,707,808,909,1010]`.

1. Head-to-head, variant vs baseline, both seat orders, 10 seeds -> 20 games
2. Variant self-play, 10 seeds -> 10 games
3. Baseline self-play, same 10 seeds -> 10 games (paired reference)
4. Variant vs pass/random/starter, 10 seeds each -> 30 games

70 games total, ~363s wall-clock, **zero exceptions, all `DONE`/`DONE`**.
Full per-game data: `experiment_quad4_results.json`.

## Results

### Head-to-head (variant vs. untouched baseline, same seed both sides)

| seed | variant $ | baseline $ | delta |
|---|---|---|---|
| 101 | 96,265 | 100,265 | -$4,000 |
| 202 | 146,916 | 150,916 | -$4,000 |
| 303 | 61,974-62,911 | 65,974-66,911 | -$3,063 to -$4,937 |
| 404 | 97,373 | 101,373 | -$4,000 |
| 505 | 51,595 | 55,595 | -$4,000 |
| 606 | 81,077 | 85,077 | -$4,000 |
| 707 | 149,508-151,117 | 153,508-155,117 | -$4,000 |
| 808 | 61,010 | 65,010 | -$4,000 |
| 909 | 58,095 | 62,095 | -$4,000 |
| 1010 | 67,479 | 71,479 | -$4,000 |

**Variant wins: 0/10. Mean delta: exactly -$4,000.** The result is
pixel-perfect: buying the 4th quadrant for $4,000 with no workers routed
there produces exactly -$4,000 of revenue loss, no more, no less. There
are zero indirect benefits — no game mechanic rewards owning more land
absent production activity on it.

### Self-play (variant vs. itself, paired against baseline self-play)

| seed | variant p0 | baseline p0 | delta |
|---|---|---|---|
| 101 | 94,814 | 112,164 | -17,350 |
| 202 | 134,192 | 144,135 | -9,943 |
| 303 | 74,142 | 73,978 | +164 |
| 404 | 79,702 | 92,069 | -12,367 |
| 505 | 58,682 | 51,849 | +6,833 |
| 606 | 60,454 | 72,194 | -11,740 |
| 707 | 151,030 | 156,575 | -5,545 |
| 808 | 50,356 | 55,818 | -5,462 |
| 909 | 59,285 | 69,171 | -9,886 |
| 1010 | 84,175 | 72,885 | +11,290 |

Variant self-play mean: **$84,683** vs. baseline self-play mean: **$90,084**.
Mean delta: **-$5,401 (-6.0%)**.

Note: self-play deltas are larger and noisier than the head-to-head
-$4,000 because self-play is variant-vs-variant (both copies spend the
$4,000, so the game's internal market dynamics and price evolution diverge
slightly from the baseline-vs-baseline trajectory).

### vs. built-in opponents (10 seeds each)

| Opponent | Variant mean | Baseline mean (5 seeds, from Priority-1) | delta |
|---|---|---|---|
| `pass` | $163,946 | $179,161 | -$15,215 |
| `random` | $159,331 | $162,131 | -$2,800 |
| `starter` | $171,437 | $185,807 | -$14,370 |

Note: baseline means use 5 seeds (101-505) from Priority-1 while variant
uses 10 seeds, so these aren't perfectly paired. The directional signal is
consistent: variant earns less against all weak opponents.

## Verdict: hypothesis rejected — do not package

The head-to-head result is about as clean as an experiment can get: **the
4th quadrant unlock with unchanged movement paths produces exactly -$4,000
of revenue loss per game, equal to the purchase cost, with zero offsetting
benefit.** The unlocked quadrant sits completely idle — no worker ever visits
it, and the `plan()` router in ticks 696-718 doesn't route there either
(the tiles are empty/unplanted, so they score zero in plan()'s
`value/(travel_cost^exponent)` ranking).

This confirms the architecture analysis from `PLAN_DECODE.md` Section 5:
"buying it without also routing workers onto the new tiles would just spend
$4,000 for zero production benefit."

**Per the standing rule: this result is consistent and clear, but negative.
Nothing is packaged from this experiment.**

## What this rules out / what's next

- **Rules out**: market-order-only 4th quadrant unlock without movement
  changes. The game has no indirect benefit to owning more land.
- **Still on the table**: Utilizing the 4th quadrant productively requires
  editing the frozen movement tape to route workers there AND editing the
  task tape (PLANT/HARVEST/etc.) to develop those tiles. This is a
  higher-risk change than any tested so far.
- **Alternative lead**: improving `plan()` itself (scoring function, hire
  targeting, watering logic) for the existing 696-718 window. The plan
  window experiment showed plan() is weaker than the tape, so making plan()
  better would directly improve the endgame — and only requires code
  changes to `plan()`, not tape edits.
- **Fertilizer reinvestment**: The 1,836-sold vs. 72-used fertilizer
  imbalance is still the other major structural inefficiency. Testing it
  requires movement tape edits (to route workers to FERTILIZE instead of
  COLLECT_FERTILIZER→SELL) — same difficulty class as the 4th quadrant
  worker routing.
