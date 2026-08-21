# CognoDB Cloud Graph Database Benchmark

A reproducible benchmark harness created for the Wexa AI Backend Engineer assessment. It compares managed graph databases on the same MovieLens 100k graph and a common workload suite.

> Submission status: completed runs are recorded for CognoDB, Neo4j AuraDB, Memgraph Cloud, and FalkorDB Cloud. TigerGraph is documented as excluded; no metrics have been fabricated for it.

## Scope

The completed comparison covers CognoDB Cloud, Neo4j AuraDB, Memgraph Cloud, and FalkorDB Cloud. Dgraph and TigerGraph adapters remain in the codebase but are excluded from the active configuration. The available TigerGraph Savanna workspace did not expose a discoverable public RESTPP endpoint/token workflow or a compatible automated loading-job route in its UI before the deadline.

## Dataset and graph model

- Source: [MovieLens 100k](https://grouplens.org/datasets/movielens/100k/)
- Graph: 2,626 nodes (943 users and 1,683 movies), with 100,000 rating relationships
- Model: `(User)-[:RATED {rating, ts}]->(Movie)`
- Inputs: the same generated `data/nodes.csv` and `data/ratings.csv` files are used for every target

## Methodology

- The benchmark is run from the same client machine.
- Each read workload has 20 warm-up operations and 100 measured operations.
- Read measurements report client-observed p50 and p95 latency in milliseconds.
- The mixed workload uses 90% reads and 10% writes at concurrency 1, 10, and 40.
- Failures, timeouts, and unavailable resource information are retained instead of replaced with estimates.
- Different resource tiers are documented and are not interpreted as an engine-to-engine performance verdict.

| Platform | Target tier / region | vCPU | RAM | Disk | Run status |
|---|---|---:|---:|---:|---|
| CognoDB | c0 Standalone / N. Virginia (us-east4) | not published | not published | 1 GiB | completed |
| Neo4j AuraDB | Google Cloud / Mumbai (asia-south1) | 1 | 2 GB | 4 GB | completed; larger than CognoDB c0 |
| Memgraph Cloud | Asia Pacific / Sydney | 2 | 2 GB | 14 GB used | completed; larger than CognoDB c0 |
| FalkorDB Cloud | AWS / Mumbai (ap-south-1a), public standalone; FalkorDB v4.20.1 | not published | not published | not published | completed; HA, backups, and autoscaling disabled |
| TigerGraph Savanna | AWS / Mumbai (ap-south-1), TG-00 (16 GiB) | not comparable | 16 GiB plan | not published | excluded: endpoint, token, and compatible loading-job workflow unavailable in the UI |

## Workloads

| Category | Logical workload | Reported metrics |
|---|---|---|
| Ingest | Load users, movies, and ratings | wall-clock time and relationships/s |
| Traversal | 1-hop, 2-hop, and 3-hop user/movie paths | p50/p95 latency |
| Lookup | Indexed movie-ID lookup | p50/p95 latency |
| Aggregation | Ten most-rated movies | p50/p95 latency |
| Mixed | 90% read / 10% write at concurrency 1, 10, and 40 | p50/p95 and operations/s |

## Reproduce

Prerequisites: Python 3.10+ and credentials for the selected cloud databases.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/check_env.py
python scripts/run_all.py --config configs/config.yml --platform cognodb
python scripts/export_results_csv.py
python scripts/plot_results.py
```

Run another configured target by replacing `cognodb` with its platform name, or omit `--platform` to run all configured targets. Account setup and expected environment-variable formats are in [docs/setup-guide.md](docs/setup-guide.md). `.env`, datasets, and generated raw results are intentionally excluded from Git.

## Repository layout

```text
configs/config.yml              Target and workload configuration
scripts/run_all.py              Benchmark orchestrator
scripts/datasets/               Dataset download and preparation
src/bench/platforms/            Per-platform runner adapters
scripts/export_results_csv.py   CSV export
scripts/plot_results.py         Chart generation
```

## Results

The orchestrator writes local evidence to `results/results.json`, followed by `results/results.csv` and charts. The table below contains measurements from completed runs.

| Platform | Ingest rel/s | 1-hop p50/p95 | 2-hop p50/p95 | 3-hop p50/p95 | Lookup p50/p95 | Aggregation p50/p95 | Mixed ops/s (1/10/40) |
|---|---:|---|---|---|---|---|---|
| CognoDB | 538.29 | 229.99 / 252.76 ms | 234.51 / 257.49 ms | 234.31 / 239.95 ms | 230.17 / 234.49 ms | 407.97 / 480.64 ms | 1.85 / 10.47 / 11.70 |
| Neo4j | 3,247.98 | 22.28 / 32.80 ms | 24.14 / 41.04 ms | 22.45 / 33.84 ms | 22.78 / 32.32 ms | 71.13 / 110.88 ms | 10.12 / 31.68 / 29.87 |
| Memgraph | 505.95 | 250.34 / 267.52 ms | 250.43 / 263.17 ms | 250.36 / 265.19 ms | 250.87 / 302.62 ms | 286.29 / 318.04 ms | 0.66 / 12.73 / 23.12 |
| FalkorDB | 891.77 | 24.41 / 31.99 ms | 24.64 / 28.67 ms | 25.20 / 31.34 ms | 22.98 / 26.14 ms | 47.67 / 63.42 ms | 17.01 / 48.05 / 14.29 |
| TigerGraph | excluded | - | - | - | - | - | unavailable to this automated harness |

## Interpretation and limitations

CognoDB c0 loaded 100,000 relationships in 185.77 seconds. Its p50 bounded traversal and lookup latencies were approximately 230-234 ms; aggregation p50 was 407.97 ms. Its mixed-workload throughput increased from 1.85 operations/s at concurrency 1 to 11.70 operations/s at concurrency 40.

FalkorDB loaded 100,000 relationships in 112.14 seconds. Its bounded traversal and lookup p50 latencies were 23-25 ms, aggregation p50 was 47.67 ms, and mixed-workload throughput peaked at 48.05 operations/s at concurrency 10.

Memgraph loaded 100,000 relationships in 197.65 seconds. Its p50 traversal and lookup values were approximately 250 ms and aggregation p50 was 286.29 ms. Neo4j AuraDB loaded the graph in 30.79 seconds and had p50 bounded traversal and lookup latencies of approximately 22-24 ms; its aggregation p50 was 71.13 ms.

These are client-observed measurements from individual runs, not a general product ranking. Neo4j and Memgraph have materially larger published resource allocations than CognoDB c0. FalkorDB does not publish comparable resource limits, and TigerGraph's available 16 GiB tier was not comparable and could not be integrated with the automated harness. The assessment requests CognoDB plus four comparison databases; this submission contains four completed platforms in total, so it is one competitor short of that target.

## Security

Never commit `.env`, credentials, connection URIs, downloaded credential files, API keys, or tokens. `.env.example` contains placeholders only.
