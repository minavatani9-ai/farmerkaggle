# Champion baseline ("Friday 2148") — real simulator confirmation

Per the continuation prompt's explicit instruction, this is Priority 1 /
"IMMEDIATE FIRST STEPS" steps 1–4 only: extract the champion, confirm the
real simulator runs it, record baseline numbers. **No code changes made.**

## Provenance

- Source: `champion_baseline_no_throttle.zip`, uploaded this session.
- Contains `main.py` (SHA-256
  `404cc9b2ab6d645bed60a7a6b13be4e658ede70bb10f55c74d15dafba04f6ceb`,
  793 lines, 44,386 bytes) + `LICENSE_KAGGLE.txt`.
- This is the code the prompt identifies as "Friday 2148" — the submission
  that scored **2540.1** live (and 2189.5 on a separate run of identical
  bytes, illustrating the ~±350 leaderboard noise band).
- Saved unmodified into the repo at `champion_2540_no_throttle_main.py`.
- Structure confirmed by AST/grep to match the prompt's layered
  architecture exactly, with no throttle layer present:
  - `_PLAN` — zlib+base85-compressed 719-tick frozen action script
  - `_scheduled()` — looks up `_PLAN[tick]`
  - `_baseline_agent()` — runs `_scheduled()` ticks 0–705, liquidates
    706–718
  - `_production_agent()` — wraps baseline, adds `_adjust_herd()` +
    shed-stock reprojection for SELL orders (ticks 168–706)
  - `_exp119_agent()` — delegates to `_production_agent()` except ticks
    696–718, where it switches to the live `plan()` router
  - `_repair_purchase()` — post-hoc cash-shortfall fix, runs last
  - `agent()` — `_exp119_agent()` then `_repair_purchase()`
  - No `_throttle_sales` anywhere in this file — confirmed clean baseline.

## Environment

- `kaggle-environments==1.32.7` (already installed, version match confirmed
  again this session).
- Real `kaggriculture` env, `episodeSteps=720`, default configuration.
- Standalone module load (no package context) succeeds; `agent` callable
  confirmed; `_PLAN` has all 719 entries.

## Results — 5 real-engine games per matchup (seeds 101/202/303/404/505)

All 20 games completed with `DONE`/`DONE` status on both seats — zero
exceptions, zero non-terminal statuses.

### Self-play (champion vs. itself)
| seed | p0 money | p1 money |
|---|---|---|
| 101 | $112,164 | $112,164 |
| 202 | $144,135 | $144,135 |
| 303 | $73,978 | $74,912 |
| 404 | $92,069 | $92,069 |
| 505 | $51,849 | $51,849 |

Mean: p0 = **$94,839**, p1 = **$95,026** (symmetric, as expected — three of
five seeds are byte-identical mirror outcomes, seed 303 diverges slightly
due to tie-breaking in simultaneous market fills).

### vs. built-in `pass` (does nothing)
Mean champion = **$179,161**, opponent = **$3,000** (starting money,
untouched). Won 5/5.

### vs. built-in `random`
Mean champion = **$162,131**, opponent = **$0** (random spends itself to
ruin, as noted in prior sonnet001 forensics). Won 5/5.

### vs. built-in `starter` (single-tile carrot loop)
Mean champion = **$185,807**, opponent = **$3,548**. Won 5/5.

## Interpretation (descriptive only — no changes made)

- The champion's revenue is strongly market-contention-dependent: self-play
  (~$95k mean, two identical agents splitting/competing for the same
  market liquidity) is roughly half of what it earns against passive
  opponents (~$160–186k), who don't compete for market inventory or
  compress prices. This matches the architecture note in the continuation
  prompt that score is Elo/TrueSkill against a live population, not raw
  money — self-play money is a weak proxy for competitive strength.
- Confirms the simulator, the extracted champion code, and the harness
  pattern (`ke.make("kaggriculture", ...)`, `env.run([agent, opp])`,
  reading `env.steps[-1][0].observation['farms'][player]['money']`) all
  work correctly with zero runtime failures across 20 games and both
  seats.
- This is the reference baseline against which any future `_PLAN`
  modification, throttle-removal confirmation, or targeted strategic
  change (Priorities 3–5 in the continuation prompt) must be measured.

## Next steps (not yet started, per explicit user instruction to stop after baseline)

Priority 3 (decode `_PLAN`'s opening/mid-game/endgame strategy),
Priority 4 (competitive opponent modeling — no non-self-play replays are
available in this session's uploads), and Priority 5 (targeted strategic
hypotheses: earlier quadrant unlock, wheat-heavy planting, animal timing,
fertilizer use vs. sale, hiring pace) remain open, to be run only after
this baseline is reviewed.
