# Graph Report - .  (2026-06-14)

## Corpus Check
- Corpus is ~8,211 words - fits in a single context window. You may not need a graph.

## Summary
- 281 nodes · 604 edges · 13 communities (9 shown, 4 thin omitted)
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 156 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

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
- [[_COMMUNITY_Development Guidelines|Development Guidelines]]

## God Nodes (most connected - your core abstractions)
1. `Asset` - 62 edges
2. `CorrelationEngine` - 28 edges
3. `BaseConnector` - 28 edges
4. `DataCleaner` - 26 edges
5. `DataNormalizer` - 25 edges
6. `ConnectorError` - 24 edges
7. `CorrelationResult` - 24 edges
8. `DataAligner` - 24 edges
9. `ProcessingPipeline` - 24 edges
10. `AlphaVantageConnector` - 22 edges

## Surprising Connections (you probably didn't know these)
- `ArgumentParser` --uses--> `CorrelationEngine`  [INFERRED]
  scripts/run_pipeline.py → cosee/correlation/engine.py
- `Asset` --uses--> `CorrelationEngine`  [INFERRED]
  scripts/run_pipeline.py → cosee/correlation/engine.py
- `CorrelationResult` --uses--> `CorrelationEngine`  [INFERRED]
  scripts/run_pipeline.py → cosee/correlation/engine.py
- `Path` --uses--> `CorrelationEngine`  [INFERRED]
  scripts/run_pipeline.py → cosee/correlation/engine.py
- `ArgumentParser` --uses--> `AssetType`  [INFERRED]
  scripts/run_pipeline.py → cosee/models/asset.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline Configuration Settings** — config_settings_data_source, config_settings_normalisation_method, config_settings_default_window, config_settings_top_n_pairs [EXTRACTED 1.00]
- **Core Pipeline Concepts (data ingestion → processing → correlation)** — readme_pipeline_flow, readme_asset_universe_concept, readme_rolling_static_correlation, config_assets_asset_universe [EXTRACTED 1.00]

## Communities (13 total, 4 thin omitted)

### Community 0 - "Data Ingestion & Connectors"
Cohesion: 0.07
Nodes (39): ABC, BaseConnector, Asset, DataFrame, date, BaseConnector, Asset, DataFrame (+31 more)

### Community 1 - "Processing Pipeline (Clean/Normalise/Align)"
Cohesion: 0.08
Nodes (30): DataFrame, Series, DataFrame, Timestamp, DataAligner, DataCleaner, DataNormalizer, DataAligner (+22 more)

### Community 2 - "Correlation Engine"
Cohesion: 0.10
Nodes (19): CorrelationEngine, Correlation engine.  Computes pairwise Pearson correlations (both static and rol, Return the full pairwise correlation matrix.          Args:             returns:, Compute correlation between two series.          Returns:             Tuple of `, Computes pairwise correlations between asset return series.      Args:         w, Compute correlations and return the top-N pairs.          Args:             retu, Correlation analysis subpackage., CorrelationResult (+11 more)

### Community 3 - "Domain Models (Asset & Results)"
Cohesion: 0.10
Nodes (16): Enum, Asset, AssetType, Supported asset categories., Represents a single tradeable or trackable market asset.      Attributes:, CorrelationResult domain model., Domain models for CoSee., load_assets() (+8 more)

### Community 4 - "Configuration & Asset Universe"
Cohesion: 0.11
Nodes (20): Asset universe configuration (tickers, names, types), Asset types: stock, etf, commodity, index, company, Setting: data_source (yahoo_finance or alpha_vantage), Setting: default_window — rolling window in trading days (default 30), COSEE_* environment variable override mechanism, Setting: normalisation_method (log_return | pct_return | z_score | min_max | none), Setting: top_n_pairs — number of top correlated pairs to display (default 20), Architectural Rule: always route connectors through factory.py (+12 more)

### Community 5 - "Config Loading & Settings"
Cohesion: 0.18
Nodes (8): Any, _load_dotenv(), _load_yaml(), Path, Configuration management for CoSee.  Reads settings from:   1. ``config/settings, Minimal .env loader (no third-party dependency required)., Central configuration object.      All values can be overridden with environment, Settings

### Community 6 - "CLI & Logging"
Cohesion: 0.26
Nodes (11): ArgumentParser, configure_logging(), Centralised logging setup for CoSee.  Call ``configure_logging()`` once at appli, Configure the root logger for CoSee.      Args:         level: Log level string, build_parser(), main(), _print_csv(), _print_json() (+3 more)

### Community 7 - "BaseConnector Interface"
Cohesion: 0.31
Nodes (6): Asset, DataFrame, date, Ensure the returned DataFrame meets minimum requirements., Fetch OHLCV data for a single asset.          Args:             asset: The asset, Fetch data for multiple assets.          Default implementation calls :meth:`fet

### Community 8 - "Series Alignment"
Cohesion: 0.38
Nodes (5): DataFrame, Series, Timestamp, Align all *series* onto a common DatetimeIndex.          Args:             serie, Convenience wrapper – filters *series_map* to *tickers* before aligning.

## Knowledge Gaps
- **12 isolated node(s):** `Timestamp`, `DataFrame`, `Series`, `CLI Entry Point (run_pipeline.py)`, `Graphify: project knowledge graph tool` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Asset` connect `Domain Models (Asset & Results)` to `Data Ingestion & Connectors`, `Correlation Engine`, `CLI & Logging`, `BaseConnector Interface`?**
  _High betweenness centrality (0.412) - this node is a cross-community bridge._
- **Why does `ProcessingPipeline` connect `Processing Pipeline (Clean/Normalise/Align)` to `Domain Models (Asset & Results)`, `CLI & Logging`?**
  _High betweenness centrality (0.346) - this node is a cross-community bridge._
- **Why does `CorrelationEngine` connect `Correlation Engine` to `Domain Models (Asset & Results)`, `CLI & Logging`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `Asset` (e.g. with `ArgumentParser` and `CorrelationEngine`) actually correct?**
  _`Asset` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `CorrelationEngine` (e.g. with `ArgumentParser` and `Asset`) actually correct?**
  _`CorrelationEngine` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `BaseConnector` (e.g. with `Asset` and `DataFrame`) actually correct?**
  _`BaseConnector` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `DataCleaner` (e.g. with `DataFrame` and `Timestamp`) actually correct?**
  _`DataCleaner` has 12 INFERRED edges - model-reasoned connections that need verification._