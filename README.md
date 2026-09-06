# Macro Nowcast — 1-Month-Ahead US CPI

Predict **next month's US headline CPI (MoM % change) before the BLS releases it**, on a
strict point-in-time basis, and honestly report whether it beats a naive last-value guess.
Target is config-swappable (`CPIAUCSL` today; core CPI / PCE later).

---

## The mega plan (end to end)

```
                            ┌─────────────────────────────────────────────┐
                            │  FREE DATA SOURCES  (each = one ingest module)│
                            │  FRED/ALFRED   yfinance      US Treasury      │
                            │  CPI, PPI,     WTI, DXY,      fiscal (context) │
                            │  gasoline,     SPY, gold                       │
                            │  food, gas...  (real-time)                     │
                            └───────────────────────┬─────────────────────┘
                                                    │  fetch → validate → store
                                                    ▼
   STAGE 2                    ┌─────────────────────────────────────────────┐
   Ingestion                 │  SQLite  (one tidy 'long' table)             │
                             │  observations: series_id, obs_date, value,   │
                             │  release_date, vintage_date, ...             │
                             │  ── release/vintage = NO LOOK-AHEAD guard ── │
                             └───────────────────────┬─────────────────────┘
                                                     │  read as-of release date
                                                     ▼
   STAGE 3                    ┌─────────────────────────────────────────────┐
   Features                  │  Point-in-time feature matrix (curated ~15-30)│
   (point-in-time)           │  target lags · CPI MoM (change) · CPI YoY     │
                             │  (level/regime) · energy MoM · PPI · food ·   │
                             │  ISM · slope · z-scores                        │
                             └───────────────────────┬─────────────────────┘
                                                     ▼
   STAGE 4         ┌──────────────────────┐   compare   ┌────────────────────────┐
   Model +         │  Ridge + shallow     │ ──────────▶ │  BASELINE: persistence  │
   validation      │  LightGBM            │             │  "next MoM = this MoM"  │
   (walk-forward)  │  expanding window    │             └────────────────────────┘
                   └──────────┬───────────┘
                              │  RMSE · MAE · direction · hit-vs-naive (fold-by-fold)
                              ▼
   STAGE 5                    ┌─────────────────────────────────────────────┐
   Report                    │  reports/{run_date}_baseline.md              │
                             │  coverage · features · params · folds ·      │
                             │  pred-vs-actual · 1-line plain-language read  │
                             └─────────────────────────────────────────────┘
```

**The bet:** the market/energy inputs update *during* the in-progress month, so they carry
signal the persistence baseline is blind to — that's why energy-heavy headline CPI is
beatable. A model that *crushes* naive is treated as a suspected leak, not a win.

---

## Build status

| Stage | What | Status |
|------:|------|--------|
| 1 | Scaffold — layout, config, DB schema, CLI, tests | ✅ **done** |
| 2 | Ingestion — sources → tidy store (needs FRED key) | ⬜ next |
| 3 | Features — point-in-time matrix | ⬜ |
| 4 | Model + walk-forward validation | ⬜ |
| 5 | Markdown report | ⬜ |

Stages run **strictly in order**, stopping after each for review.

## Layout

```
src/macro_nowcast/
  config.py            # paths, target spec, LOCKED series catalog (data, not logic)
  db/schema.py         # tidy long 'observations' table + series_catalog
  db/session.py        # engine, init_db (create + seed)
  ingest/base.py       # shared fetch/validate/store interface
  ingest/fred.py       # FRED/ALFRED source          (Stage 2 stub)
  ingest/market.py     # yfinance source             (Stage 2 stub)
  features/build.py    # point-in-time features       (Stage 3 stub)
  models/baseline.py   # persistence baseline         (live)
  models/train.py      # walk-forward train + score   (Stage 4 stub)
  report/build.py      # markdown report              (Stage 5 stub)
  cli.py               # one entry point per stage
tests/                 # schema + baseline smoke tests
data/                  # SQLite DB lives here (gitignored)
reports/               # generated reports (gitignored)
```

## Run it

```bash
# 1) install (editable). uv preferred; pip works too.
pip install -e ".[dev]"        #  or:  uv pip install -e ".[dev]"

# 2) Stage 1 — create the empty DB + seed the series catalog
python -m macro_nowcast.cli    #  or:  macro-initdb

# 3) tests
pytest -q

# Later stages (need a free FRED key in .env first — see .env.example):
#   macro-ingest  →  macro-features  →  macro-train  →  macro-report
```

## Rules (non-negotiable)

- **No fabricated numbers** — a gap is stored `NULL`, never guessed.
- **No look-ahead** — values usable only on/after their `release_date` (ALFRED vintages).
- **Always beat a stated baseline** — persistence, reported honestly fold-by-fold.
- **Config over hardcoding** — series list, target, horizon all live in `config.py` / `.env`.
