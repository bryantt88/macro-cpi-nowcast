# Memory Index

*One `- [Title](file.md) — hook` line per memory file. Index only — never put content here.*

- [Roadmap & decisions](project-roadmap.md) — goal, build order + status, decisions locked, next actions
- [Daily log](daily-log.md) — session-by-session progress; update every session
- [OIS / rate-futures endogeneity](reference-rates-endogeneity.md) — parked idea: inflation drives rate expectations, not the reverse; circular as a CPI predictor; revisit only with a free curve source

## Skills (slash commands in this project)
- `/compact` → `.claude/commands/compact.md` — session handoff + cumulative-memory fold; writes `memory/session-compact-<date>.md`, updates daily-log + roadmap
- `/pm-review` → `.claude/commands/pm-review.md` — unbiased macro-PM assessment of goal alignment, model health, complexity, impact
- `/concise-answer` → `.claude/commands/concise-answer.md` — compresses the previous answer into scannable point-form (no new analysis)
- `/short-code` → `.claude/commands/short-code.md` — compresses/tightens a named file WITHOUT changing behavior; verifies via py_compile + smoke

## Project Layout (to be filled as the project is built)
- `memory/` — canonical in-repo memory (this index + roadmap + daily-log + dated session-compacts)
- `.claude/commands/` — slash command skill definitions
- `.claude/settings*.json` — permissions (local file accumulates approved commands)
