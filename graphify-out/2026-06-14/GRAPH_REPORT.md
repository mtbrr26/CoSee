# Graph Report - CoSee  (2026-06-14)

## Corpus Check
- 6 files · ~3,830 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 70 nodes · 83 edges · 13 communities (7 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e176d3d3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Data Ingestion & Connectors|Data Ingestion & Connectors]]
- [[_COMMUNITY_Processing Pipeline (CleanNormaliseAlign)|Processing Pipeline (Clean/Normalise/Align)]]
- [[_COMMUNITY_Correlation Engine|Correlation Engine]]
- [[_COMMUNITY_Domain Models (Asset & Results)|Domain Models (Asset & Results)]]
- [[_COMMUNITY_Configuration & Asset Universe|Configuration & Asset Universe]]
- [[_COMMUNITY_Config Loading & Settings|Config Loading & Settings]]
- [[_COMMUNITY_CLI & Logging|CLI & Logging]]
- [[_COMMUNITY_BaseConnector Interface|BaseConnector Interface]]
- [[_COMMUNITY_Series Alignment|Series Alignment]]
- [[_COMMUNITY_Data Cleaning|Data Cleaning]]
- [[_COMMUNITY_Package Init|Package Init]]
- [[_COMMUNITY_Test Suite Init|Test Suite Init]]
- [[_COMMUNITY_Community 14|Community 14]]

## God Nodes (most connected - your core abstractions)
1. `_download_asset()` - 10 edges
2. `CoSee — Copilot Instructions` - 10 edges
3. `Graphify — Reference for Copilot` - 8 edges
4. `Clean → Normalise → Align → Correlate Pipeline Flow` - 7 edges
5. `_parquet_path()` - 6 edges
6. `main()` - 6 edges
7. `_load_assets()` - 5 edges
8. `_read_existing()` - 5 edges
9. `_write()` - 5 edges
10. `_last_stored_date()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Clean → Normalise → Align → Correlate Pipeline Flow` --conceptually_related_to--> `Setting: default_window — rolling window in trading days (default 30)`  [INFERRED]
  README.md → config/settings.yaml
- `Clean → Normalise → Align → Correlate Pipeline Flow` --conceptually_related_to--> `Setting: normalisation_method (log_return | pct_return | z_score | min_max | none)`  [INFERRED]
  README.md → config/settings.yaml
- `Clean → Normalise → Align → Correlate Pipeline Flow` --conceptually_related_to--> `Setting: top_n_pairs — number of top correlated pairs to display (default 20)`  [INFERRED]
  README.md → config/settings.yaml
- `Rolling and Static Pairwise Pearson Correlation` --conceptually_related_to--> `Setting: default_window — rolling window in trading days (default 30)`  [INFERRED]
  README.md → config/settings.yaml
- `build_parser()` --references--> `ArgumentParser`  [EXTRACTED]
  scripts/run_pipeline.py → scripts/download_data.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline Configuration Settings** — config_settings_data_source, config_settings_normalisation_method, config_settings_default_window, config_settings_top_n_pairs [EXTRACTED 1.00]
- **Core Pipeline Concepts (data ingestion → processing → correlation)** — readme_pipeline_flow, readme_asset_universe_concept, readme_rolling_static_correlation, config_assets_asset_universe [EXTRACTED 1.00]

## Communities (13 total, 6 thin omitted)

### Community 1 - "Processing Pipeline (Clean/Normalise/Align)"
Cohesion: 0.38
Nodes (6): Asset, _build_parser(), _load_assets(), main(), Download and cache market data as local Parquet files.  Fetches daily OHLCV data, Load assets from YAML config.

### Community 2 - "Correlation Engine"
Cohesion: 0.40
Nodes (6): date, _download_asset(), _last_stored_date(), Return the most recent date in a stored DataFrame., Fetch data for *asset* and update the local cache.      Returns True on success,, YahooFinanceConnector

### Community 3 - "Domain Models (Asset & Results)"
Cohesion: 0.24
Nodes (12): ArgumentParser, build_parser(), load_assets(), main(), _print_csv(), _print_json(), _print_table(), Asset (+4 more)

### Community 4 - "Configuration & Asset Universe"
Cohesion: 0.29
Nodes (8): Setting: default_window — rolling window in trading days (default 30), Setting: normalisation_method (log_return | pct_return | z_score | min_max | none), Setting: top_n_pairs — number of top correlated pairs to display (default 20), Asset Universe (stocks, ETFs, commodities, indices), CLI Entry Point (run_pipeline.py), CoSee: Correlated Asset Pair Identification Engine, Clean → Normalise → Align → Correlate Pipeline Flow, Rolling and Static Pairwise Pearson Correlation

### Community 6 - "CLI & Logging"
Cohesion: 0.17
Nodes (11): Coding conventions, CoSee — Copilot Instructions, graphify, Key settings (`config/settings.yaml`), Project layout, Quick reference — run the project, Related reference files, Testing rules (+3 more)

### Community 8 - "Series Alignment"
Cohesion: 0.22
Nodes (8): Core commands, Graphify — Reference for Copilot, Ignoring files, Install, Keeping the graph fresh, Privacy notes, Useful for CoSee, What it is

### Community 9 - "Data Cleaning"
Cohesion: 0.29
Nodes (8): Path, _parquet_path(), DataFrame, Return the Parquet file path for *ticker*., Return the stored DataFrame for *ticker*, or None if absent., Write *df* to the Parquet cache for *ticker*., _read_existing(), _write()

## Knowledge Gaps
- **25 isolated node(s):** `What this project is`, `Key settings (`config/settings.yaml`)`, `Coding conventions`, `Testing rules`, `What to always confirm before doing` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_build_parser()` connect `Processing Pipeline (Clean/Normalise/Align)` to `Domain Models (Asset & Results)`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `ArgumentParser` connect `Domain Models (Asset & Results)` to `Processing Pipeline (Clean/Normalise/Align)`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Clean → Normalise → Align → Correlate Pipeline Flow` (e.g. with `Setting: default_window — rolling window in trading days (default 30)` and `Setting: normalisation_method (log_return | pct_return | z_score | min_max | none)`) actually correct?**
  _`Clean → Normalise → Align → Correlate Pipeline Flow` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Download and cache market data as local Parquet files.  Fetches daily OHLCV data`, `Load assets from YAML config.`, `Return the Parquet file path for *ticker*.` to the rest of the system?**
  _34 weakly-connected nodes found - possible documentation gaps or missing edges._