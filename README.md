# CognoDB Cloud Graph Database Benchmark

A reproducible benchmark harness for comparing CognoDB Cloud with managed graph databases on an identical MovieLens 100k graph and workload suite.

> Status: the benchmark harness is implemented. No performance claim is made until every platform has a completed, recorded run; this repository deliberately shows `pending` rather than fabricated measurements.

## Purpose

Created for the Wexa AI graph-database benchmarking assessment, this project prioritizes fair methodology, reproducible automation, and honest reporting over declaring a database “winner.”

The active benchmark configuration targets CognoDB Cloud, Neo4j AuraDB, Memgraph Cloud, and FalkorDB Cloud. Dgraph and TigerGraph adapters remain in the codebase but are excluded from the active run because a comparable no-cost tier was not available in time.

## Dataset and model

- Source: [MovieLens 100k](https://grouplens.org/datasets/movielens/100k/)
- Graph: 2,626 nodes (943 users; 1,683 movies) and 100,000 rating relationships
- Model: `(User)-[:RATED {rating, ts}]->(Movie)`

The same generated `data/nodes.csv` and `data/ratings.csv` inputs are used for every target.

## Methodology

- Same client machine and nearest comparable region for every platform.
- Entry tiers chosen as close as possible to CognoDB c0 (its console reports a 1 GiB standalone instance; CPU and RAM limits are not published in the available instance details).
- 20 unmeasured warm-up operations, then 100 measured iterations per read workload.
- Client-observed p50 and p95 latency (ms), not averages alone.
- Failed connections, timeouts, throttling, and unobservable metrics are retained and reported.
- Materially unequal resource tiers are documented as a limitation, not interpreted as a performance verdict.

| Platform | Target tier / region | vCPU | RAM | Disk | Run status |
|---|---|---:|---:|---:|---|
| CognoDB | c0 Standalone / N. Virginia (us-east4) | not published | not published | 1 GiB | completed |
| Neo4j AuraDB | Google Cloud / Mumbai (asia-south1) | 1 | 2 GB | 4 GB | completed; larger than CognoDB c0 |
| Memgraph Cloud | Asia Pacific / Sydney | 2 | 2 GB | 14 GB used | completed; larger than CognoDB c0 |
| FalkorDB Cloud | region not recorded | pending | pending | pending | completed |
| TigerGraph Cloud | excluded | — | — | — | paid/non-comparable workspace unavailable |

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

For account creation and URI formats, see the [platform setup guide](docs/setup-guide.md). `.env`, datasets, and generated results are excluded from Git.

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
| CognoDB | 538.29 | 229.99 / 252.76 ms | 234.51 / 257.49 ms | 234.31 / 239.95 ms | 230.17 / 234.49 ms | 407.97 / 480.64 ms | 1.85 / 10.47 / 11.70 |
| Neo4j | 3,247.98 | 22.28 / 32.80 ms | 24.14 / 41.04 ms | 22.45 / 33.84 ms | 22.78 / 32.32 ms | 71.13 / 110.88 ms | 10.12 / 31.68 / 29.87 |
| Memgraph | 505.95 | 250.34 / 267.52 ms | 250.43 / 263.17 ms | 250.36 / 265.19 ms | 250.87 / 302.62 ms | 286.29 / 318.04 ms | 0.66 / 12.73 / 23.12 |
| FalkorDB | 891.77 | 24.41 / 31.99 ms | 24.64 / 28.67 ms | 25.20 / 31.34 ms | 22.98 / 26.14 ms | 47.67 / 63.42 ms | 17.01 / 48.05 / 14.29 |
| TigerGraph | excluded | — | — | — | — | — | paid/non-comparable tier unavailable |

## Limitations

Free tiers may throttle, suspend, or share hardware. Cloud results include client-to-service network latency. Indexing, query syntax, and observability differ across providers. TigerGraph requires a graph schema, loading job, and stored RESTPP queries and its accessible workspace was not comparable to CognoDB c0. A missing or failed target is incomplete evidence, not a basis for inferring performance.

## Initial observation

The completed CognoDB c0 run loaded 100,000 relationships in 185.77 seconds (538.29 relationships/s). Client-observed p50 read latencies were approximately 230–234 ms for the bounded traversal and lookup workloads, while the aggregation p50 was 407.97 ms. Mixed-workload throughput increased from 1.85 operations/s at concurrency 1 to 11.70 operations/s at concurrency 40, with a higher p95 at 40 concurrent clients. These are measurements from one run, not a cross-platform conclusion; the remaining targets must complete under documented comparable conditions before comparison.

The completed FalkorDB run loaded 100,000 relationships in 112.14 seconds (891.77 relationships/s). Its bounded traversal and lookup p50 latencies were 23–25 ms, while aggregation p50 was 47.67 ms. Mixed-workload throughput peaked at 48.05 operations/s at concurrency 10 and declined at concurrency 40, a pattern consistent with saturation or shared-tier throttling. This is an observation from one client, one run, and non-identical instance resources; it is not a general product ranking.

The completed Memgraph run loaded 100,000 relationships in 197.65 seconds (505.95 relationships/s). Its p50 traversal/lookup values were approximately 250 ms and aggregation p50 was 286.29 ms. Mixed-workload throughput rose from 0.66 operations/s at concurrency 1 to 23.12 operations/s at concurrency 40. Memgraph reported compatibility warnings that named constraint/index identifiers are ignored; the logical labels and properties used by the workload remained present. These results are still a single-run observation and must be interpreted with the documented service-tier differences.

The Neo4j AuraDB run loaded 100,000 relationships in 30.79 seconds (3,247.98 relationships/s). Bounded traversal and lookup p50 latencies were approximately 22–24 ms, with aggregation p50 of 71.13 ms. Its mixed workload reached 31.68 operations/s at concurrency 10 and slightly declined to 29.87 operations/s at concurrency 40, while p95 latency increased to 110.78 ms. An earlier mixed-workload attempt timed out; a clean subsequent sweep completed, so both the earlier transient failure and completed retry should be retained in local run notes.

## Security

Never commit `.env`, credentials, connection URIs, downloaded credential files, API keys, tokens, generated data, or result artifacts. `.env.example` contains safe placeholders only.
