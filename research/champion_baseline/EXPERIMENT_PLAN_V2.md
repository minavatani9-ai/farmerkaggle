# Experiment: Conservative plan() v2 Improvement

## Hypothesis
Targeted improvements to `plan()` (ticks 696-718) can increase endgame revenue
without triggering first-mover market-price loss, unlike the rejected v1 variant.

## Changes (sells-first order preserved)
1. **Skip COLLECT_FERTILIZER** — $1/unit, wastes worker-ticks on low-value tasks
2. **Filter low-value sells** — remove sells where `quantity * price < $5` (WOOL at $3, FERTILIZER at $1-2)
3. **Sort sells by value** — highest-value sells first to maximize revenue under 10-order cap
4. **hires=11** — matches tape's achievement (was passing 10, tape gets 11 hands)

Key design: sells still come BEFORE hires in the market order list. The rejected
v1 variant put HIRE first, which delayed sells by 1 tick and lost first-mover
advantage (-$521 mean h2h). V2 instead frees HIRE slots by filtering out
low-value sells ($3 WOOL, $2 FERTILIZER).

## Results (70 games, 10 seeds)

### Head-to-head vs champion (20 games)
| Seed | Seat 0 delta | Seat 1 delta |
|------|-------------|-------------|
| 101  | -$112       | -$112       |
| 202  | +$20        | +$20        |
| 303  | -$16        | +$2,090     |
| 404  | +$579       | +$579       |
| 505  | +$153       | +$153       |
| 606  | -$146       | -$146       |
| 707  | -$147       | -$147       |
| 808  | +$1,207     | +$1,207     |
| 909  | +$2,128     | +$2,128     |
| 1010 | +$693       | +$693       |

**Record: 13W-7L-0T, mean delta +$541**

- Wins are large: +$2,128, +$2,090, +$1,207
- Losses are all small: max loss -$147
- 8/10 seeds show identical results regardless of seat (deterministic tape)
- Seed 303 asymmetry: the variant's filtering/sorting matters more in one seat

### Self-play comparison (10 games each)
- Variant self-play mean total: $180,003
- Baseline self-play mean total: $180,261
- Delta: -$258 (within noise, expected for minor endgame changes)

### Variant vs built-in opponents (30 games)
- vs pass: all wins, mean $171,286 (identical to baseline range)
- vs random: all wins, mean $165,993
- vs starter: all wins, mean $174,746

All 70 games completed with DONE status, no errors.

## Comparison with rejected variants
| Variant | H2H Record | Mean Delta | Status |
|---------|-----------|------------|--------|
| Quad4 unlock | 0W-10L | -$4,000 | REJECTED |
| Plan v1 (HIRE first) | 0W-10L | -$521 | REJECTED |
| **Plan v2 (conservative)** | **13W-7L** | **+$541** | **ACCEPTED** |

## Conclusion
The conservative v2 variant shows consistent improvement over the champion
baseline in head-to-head play. The wins are large and concentrated in seeds
where filtering low-value sells frees market slots for more valuable operations.
Losses are small and within noise range.

Recommendation: Package as new submission.
