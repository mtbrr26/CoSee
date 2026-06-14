# Graphify — Reference for Copilot

**Source:** https://github.com/safishamsi/graphify  
**PyPI package:** `graphifyy` (double-y) | **CLI command:** `graphify`

---

## What it is

Graphify is a tool that maps any project folder — code, docs, PDFs, images — into a
queryable knowledge graph. It uses tree-sitter for AST extraction (local, no API key)
and an LLM for semantic extraction of docs/PDFs/images.

Output lands in `graphify-out/`:
```
graphify-out/
├── graph.html       # interactive browser visualisation
├── GRAPH_REPORT.md  # god nodes, surprising connections, suggested questions
└── graph.json       # full graph — queryable without re-reading files
```

---

## Install

```bash
# Recommended (manages PATH automatically)
uv tool install graphifyy

# Alternatives
pipx install graphifyy
pip install graphifyy        # may need manual PATH setup on macOS/Linux
```

Register with VS Code Copilot Chat once graphify is installed:
```bash
graphify vscode install
```

---

## Keeping the graph fresh

The git hook (installed via `graphify hook install`) auto-rebuilds the graph after every commit **for code changes only**. However, run `/graphify . --update` manually whenever you:

- Add or significantly edit **markdown / YAML / config files** (docs are not handled by the AST hook)
- Add a **new module or package** to the project
- Feel the graph answers are stale or missing context

`--update` only re-processes files that changed since the last run — it is fast.

---

## Core commands

```bash
# Build the graph
graphify .                         # current directory
graphify . --update                # re-extract only changed files
graphify . --cluster-only          # re-run clustering without re-extracting
graphify . --no-viz                # skip HTML, just report + JSON

# Query the graph
graphify query "what does the pipeline orchestrator do?"
graphify query "what connects cleaner to aligner?"
graphify path "BaseConnector" "CorrelationEngine"
graphify explain "pipeline"

# Auto-rebuild on git commit
graphify hook install

# Watch mode (auto-sync as files change)
graphify . --watch
```

---

## Useful for CoSee

| Use case | Command |
|---|---|
| Understand module connections before editing | `graphify query "how does pipeline.py connect to engine.py?"` |
| Find where a function is used | `graphify query "where is compute_rolling_correlation called?"` |
| Trace data flow | `graphify path "yahoo_finance" "CorrelationResult"` |
| Get architecture overview | Read `graphify-out/GRAPH_REPORT.md` |

---

## Privacy notes

- **Code** — extracted locally via tree-sitter. **Nothing leaves the machine.**
- **Docs / PDFs / images** — sent to the configured LLM backend (IDE session or API key).
- No telemetry, no usage tracking.

---

## Ignoring files

Create `.graphifyignore` in the project root (same syntax as `.gitignore`):
```
# example
graphify-out/
*.generated.py
```

`.gitignore` is respected automatically if no `.graphifyignore` is present.
