# CoSee — Correlated Asset Pair Identification Engine

Develop an algorithmic pipeline that scans global markets to identify statistically significant correlations between assets, including stocks, commodities, ETFs, and companies.

---

## Project Structure

```
cosee/                      # Main Python package
├── __init__.py
├── config.py               # Settings (YAML + env-var override)
├── logging_config.py       # Centralised logging setup
├── models/                 # Domain models
│   ├── asset.py            # Asset dataclass + AssetType enum
│   └── correlation_result.py
├── ingestion/              # Market data connectors
│   ├── base.py             # Abstract BaseConnector
│   ├── yahoo_finance.py    # yfinance connector (no key needed)
│   ├── alpha_vantage.py    # Alpha Vantage REST connector (placeholder)
│   └── factory.py          # Connector factory
├── processing/             # Data transformation pipeline
│   ├── cleaner.py          # Dedup, fill NaN, outlier removal
│   ├── normalizer.py       # Returns: log, pct, z-score, min-max
│   ├── aligner.py          # Align multiple series to common DatetimeIndex
│   └── pipeline.py         # Orchestrator: clean → normalise → align
└── correlation/
    └── engine.py           # Rolling & static pairwise Pearson correlation

config/
├── settings.yaml           # Default app settings
└── assets.yaml             # Asset universe (stocks, ETFs, commodities, indices)

scripts/
└── run_pipeline.py         # CLI entry point

tests/                      # pytest unit tests
├── test_models.py
├── test_ingestion.py
├── test_processing.py
└── test_correlation.py
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure (optional)

```bash
cp .env.example .env
# Edit .env to add your Alpha Vantage key (not needed for Yahoo Finance)
```

Edit `config/assets.yaml` to customise the asset universe.

### 3. Run the pipeline

```bash
# Default: 1-year window, Yahoo Finance, top-20 pairs
python scripts/run_pipeline.py

# Custom options
python scripts/run_pipeline.py \
  --start 2022-01-01 \
  --end   2024-01-01 \
  --window 60 \
  --top-n  10 \
  --output json
```

### 4. Run tests

```bash
pytest
```

---

## Configuration

All settings live in `config/settings.yaml` and can be overridden with
environment variables prefixed `COSEE_` (e.g. `COSEE_LOG_LEVEL=DEBUG`).

| Setting               | Default          | Description                              |
|-----------------------|------------------|------------------------------------------|
| `log_level`           | `INFO`           | Logging verbosity                        |
| `data_source`         | `yahoo_finance`  | Connector to use                         |
| `default_window`      | `30`             | Rolling correlation window (trading days)|
| `top_n_pairs`         | `20`             | Number of top pairs to display           |
| `normalisation_method`| `log_return`     | Return series method                     |

---

## Adding a New Data Source

1. Create `cosee/ingestion/my_source.py` that inherits from `BaseConnector`.
2. Implement the `fetch(asset, start, end, interval)` method.
3. Register it in `cosee/ingestion/factory.py`.

---

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Asset Config   │───▶│  Data Ingestion  │───▶│  Processing Pipeline│
│  (assets.yaml)  │    │  (BaseConnector) │    │  clean→norm→align   │
└─────────────────┘    └──────────────────┘    └──────────┬──────────┘
                                                           │
                                               ┌───────────▼──────────┐
                                               │  Correlation Engine  │
                                               │  rolling Pearson r   │
                                               └───────────┬──────────┘
                                                           │
                                               ┌───────────▼──────────┐
                                               │  CLI / Output        │
                                               │  table | csv | json  │
                                               └──────────────────────┘
```
