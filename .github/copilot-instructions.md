# CoSee — Copilot Instructions

## What this project is

**CoSee** (Correlated Asset Pair Identification Engine) is a Python algorithmic pipeline that scans global financial markets to identify statistically significant correlations between assets (stocks, ETFs, commodities, indices).

It fetches price data, cleans and normalises it, aligns series to a common date index, then computes pairwise Pearson correlations (rolling and static) and surfaces the top correlated pairs.

---

## Project layout

```
cosee/                  Main package
  config.py             Loads settings.yaml + COSEE_* env-var overrides
  logging_config.py     Centralised logging setup
  models/
    asset.py            Asset dataclass + AssetType enum
    correlation_result.py
  ingestion/
    base.py             Abstract BaseConnector
    yahoo_finance.py    yfinance connector (no API key needed)
    alpha_vantage.py    Alpha Vantage REST connector (placeholder)
    factory.py          Connector factory — returns the right connector
  processing/
    cleaner.py          Dedup, fill NaN, outlier removal
    normalizer.py       Returns: log_return | pct_return | z_score | min_max | none
    aligner.py          Aligns multiple series to a common DatetimeIndex
    pipeline.py         Orchestrator: clean → normalise → align
  correlation/
    engine.py           Rolling & static pairwise Pearson correlation

config/
  settings.yaml         Default app settings (see table below)
  assets.yaml           Asset universe — add/remove tickers here

scripts/
  run_pipeline.py       CLI entry point

tests/                  pytest unit tests (one file per package module)
```

### Key settings (`config/settings.yaml`)

| Key                    | Default         | Notes                                     |
|------------------------|-----------------|-------------------------------------------|
| `data_source`          | `yahoo_finance` | `yahoo_finance` or `alpha_vantage`        |
| `default_window`       | `30`            | Rolling window in trading days            |
| `top_n_pairs`          | `20`            | Pairs returned by the pipeline            |
| `normalisation_method` | `log_return`    | See `normalizer.py` for supported methods |
| `start_date`/`end_date`| `""`            | ISO-8601; blank = connector default       |

Settings can be overridden at runtime with `COSEE_<KEY>=value` env vars.

---

## Coding conventions

- **Stay consistent with existing code** — match the style, patterns, and idioms already present in each file before writing new code.
- Keep architecture and code **simple**. Prefer straightforward solutions over clever abstractions.
- Do not introduce new dependencies without **confirming with the user first**.
- Do not add unnecessary abstractions, helpers, or layers for one-off operations.

## Testing rules

- Every **public function** must have a corresponding unit test in `tests/`.
- Test files mirror the module structure: `cosee/processing/cleaner.py` → `tests/test_processing.py`.
- Use `pytest`; run with `pytest` from the project root.

## What to always confirm before doing

- Adding **any new dependency** (Python package or otherwise).
- Making **significant architectural changes** (new modules, new config keys, changing public APIs).
- **Deleting or renaming** existing files or functions.
- Any change that affects the **YAML schema** of `config/settings.yaml` or `config/assets.yaml`.

## What NOT to do

- Do not silently add imports, packages, or config keys.
- Do not over-engineer: no ORMs, no heavy frameworks, no unnecessary abstraction layers.
- Do not change the config loading mechanism in `config.py` without confirmation.
- Do not bypass the connector factory (`factory.py`) to instantiate connectors directly in pipeline code.

---

## Related reference files

- [.github/graphify.md](.github/graphify.md) — Graphify tool reference (knowledge graph, query commands, CoSee-specific usage)

---

## Quick reference — run the project

```bash
# Install
pip install -e ".[yahoo,dev]"

# Run pipeline (defaults)
python scripts/run_pipeline.py

# Custom run
python scripts/run_pipeline.py --start 2022-01-01 --end 2024-01-01 --window 60 --top-n 10

# Tests
pytest
```

## graphify

For any question about this repo's architecture, structure, components, or how to add/modify/find
code, your first action should be `graphify query "<question>"` when `graphify-out/graph.json`
exists. Use `graphify path "<A>" "<B>"` for relationship questions and `graphify explain "<concept>"`
for focused-concept questions. These return a scoped subgraph, usually much smaller than the full
report or raw grep output.

Triggers: "how do I…", "where is…", "what does … do", "add/modify a <component>",
"explain the architecture", or anything that depends on how files or classes relate.

If `graphify-out/wiki/index.md` exists, use it for broad navigation. Read `graphify-out/GRAPH_REPORT.md`
only for broad architecture review or when query/path/explain do not surface enough context. Only read
source files when (a) modifying/debugging specific code, (b) the graph lacks the needed detail, or
(c) the graph is missing or stale.

Type `/graphify` in Copilot Chat to build or update the graph.
