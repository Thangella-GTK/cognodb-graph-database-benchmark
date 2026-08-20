# CognoDB Cloud Graph Database Benchmark

A reproducible benchmark harness for comparing CognoDB Cloud with managed graph databases on an identical MovieLens 100k graph and workload suite.

> Status: the benchmark harness is implemented. No performance claim is made until every platform has a completed, recorded run; this repository deliberately shows `pending` rather than fabricated measurements.

## Purpose

Created for the Wexa AI graph-database benchmarking assessment, this project prioritizes fair methodology, reproducible automation, and honest reporting over declaring a database “winner.”

Targets: CognoDB Cloud, Neo4j AuraDB, Memgraph Cloud, FalkorDB Cloud, and TigerGraph Cloud. Dgraph is included as an optional sixth adapter.

## Dataset and model

- Source: [MovieLens 100k](https://grouplens.org/datasets/movielens/100k/)
- Graph: 2,626 nodes (943 users; 1,683 movies) and 100,000 rating relationships
- Model: `(User)-[:RATED {rating, ts}]->(Movie)`

The same generated `data/nodes.csv` and `data/ratings.csv` inputs are used for every target.

## Methodology

- Same client machine and nearest comparable region for every platform.
- Entry tiers chosen as close as possible to CognoDB c0 (0.5 vCPU, 256 MB RAM, 1 GB disk).
- 20 unmeasured warm-up operations, then 100 measured iterations per read workload.
- Client-observed p50 and p95 latency (ms), not averages alone.
- Failed connections, timeouts, throttling, and unobservable metrics are retained and reported.
- Materially unequal resource tiers are documented as a limitation, not interpreted as a performance verdict.

| Platform | Target tier / region | vCPU | RAM | Disk | Run status |
|---|---|---:|---:|---:|---|
| CognoDB | c0 / pending | 0.5 | 256 MB | 1 GB | credentials reset required |
| Neo4j AuraDB | pending | pending | pending | pending | credentials required |
| Memgraph Cloud | pending | pending | pending | pending | connection verification pending |
| FalkorDB Cloud | pending | pending | pending | pending | endpoint verified; benchmark pending |
| TigerGraph Cloud | pending | pending | pending | pending | account/schema/token required |

## Workloads and metrics

| Category | Logical workload | Metrics |
|---|---|---|
| Ingest | Load users, movies, ratings | Wall-clock time, nodes/s, relationships/s |
| Traversal | 1-hop, 2-hop, 3-hop user/movie paths | p50/p95 latency |
| Lookup | Indexed movie ID lookup | p50/p95 latency |
| Aggregation | Ten most-rated movies | p50/p95 latency |
| Mixed | 90% read / 10% write; concurrency 1, 10, 40 | p50/p95 and completed operations/s |
| Footprint | Provider-exposed storage/memory details | Recorded or `not_observable` |

## Reproduce

Prerequisites: Python 3.10+ and cloud accounts for the selected targets.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/run_all.py --dry-run
```

Fill `.env` locally, validate it, and begin with one target:

```powershell
python scripts/check_env.py
python scripts/run_all.py --config configs/config.yml --platform cognodb
python scripts/export_results_csv.py
python scripts/plot_results.py
```

For account creation, URI formats, credentials, and TigerGraph setup, see the [platform setup guide](docs/setup-guide.md). `.env`, datasets, and generated results are excluded from Git.

## Repository layout

```text
configs/config.yml              Target and workload configuration
scripts/run_all.py              Benchmark orchestrator
scripts/datasets/               Dataset download/preparation
src/bench/platforms/            Per-platform runner adapters
scripts/export_results_csv.py   CSV export
scripts/plot_results.py         Chart generation
```

## Results

The orchestrator writes local evidence to `results/results.json`, followed by `results/results.csv` and charts. Results remain pending until genuine completed measurements are available.

| Platform | Ingest rel/s | 1-hop p50/p95 | 2-hop p50/p95 | 3-hop p50/p95 | Lookup p50/p95 | Aggregation p50/p95 | Mixed ops/s (1/10/40) |
|---|---:|---|---|---|---|---|---|
| CognoDB | pending | pending | pending | pending | pending | pending | pending |
| Neo4j | pending | pending | pending | pending | pending | pending | pending |
| Memgraph | pending | pending | pending | pending | pending | pending | pending |
| FalkorDB | pending | pending | pending | pending | pending | pending | pending |
| TigerGraph | pending | pending | pending | pending | pending | pending | pending |

## Limitations

Free tiers may throttle, suspend, or share hardware. Cloud results include client-to-service network latency. Indexing, query syntax, and observability differ across providers. TigerGraph also requires a graph schema, loading job, and stored RESTPP queries before it can be benchmarked. A missing or failed target is incomplete evidence, not a basis for inferring performance.

## Security

Never commit `.env`, credentials, connection URIs, downloaded credential files, API keys, tokens, generated data, or result artifacts. `.env.example` contains safe placeholders only.
