## COMPACT — 2026-08-20 (covers since project kickoff)

**In one line:** Scaffolded the Macro Economic Prediction Model (file/system conventions + locked spec) and explained the methodology to Bryant; no code built yet — Stage 1 is next, pending one open data-source decision.

### WHAT CHANGED
- Built project file management mirroring Credit Rating / Factor-Alpha: `.claude/commands/` (4 skills), `.claude/settings*.json` (empty allow-list, nothing pre-granted), in-repo `memory/`, root `CLAUDE.md`.
- Locked the spec from Bryant's project note (target, models, validation, stack, strict 5-stage build order).
- Explained the whole project + methodology in plain terms (Bryant is market-literate, learning tech).
- Clarified naive baseline = **persistence** (next MoM = this MoM), NOT 0%/level-walk. Persistence only.
- Causality discussed: inflation → OIS/rate-futures, not reverse → saved `reference-rates-endogeneity.md` (parked).
- Reviewed input data; flagged weak features (gold, SPY, industrial prod, fiscal, rates=circular) and stronger missing ones (retail gasoline `GASREGW`, PPI, food commodities).

### WHERE THINGS STAND
- Project folder = scaffold only (conventions + memory). No `src/`, no `pyproject.toml`, no code yet.
- `memory/project-roadmap.md` — spec + decisions locked; status = SPEC LOCKED, ready for Stage 1.
- `memory/reference-rates-endogeneity.md` — parked OIS/rate-futures idea, indexed.

### DO NEXT
1. Get Bryant's call on the data set: fold **retail gasoline (`GASREGW`) + PPI + food commodities** into the Stage-2 plan and demote gold/SPY/fiscal to optional context — OR keep the note's list as-is.
2. Then start **Stage 1 (Scaffold)**: pyproject/uv, `src/` layout, git init, `.env.example` (FRED key slot), README with run instructions. Stop after Stage 1 for review.
- Blocked on: Bryant's answer on adding gasoline/PPI/food.
- Also needed before Stage 2: free FRED API key (goes in local gitignored `.env`).

### DECISIONS LOCKED
- Target = headline CPI `CPIAUCSL`, MoM %, 1-month-ahead, config-swappable.
- Point-in-time = ALFRED vintages (first prints; no revision leak).
- Naive = persistence only. Walk-forward expanding window only, no k-fold.
- No magic numbers / no hardcoded paths; all config in `config.py`/`.env`. Stages run strictly in order, stop after each.
