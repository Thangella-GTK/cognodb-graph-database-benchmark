# CognoDB Cloud graph benchmark

An honest, repeatable comparison of CognoDB Cloud against Neo4j, Memgraph, FalkorDB, Dgraph, and TigerGraph using MovieLens 100k. This repository contains the harness; it does **not** claim benchmark results until `results/results.json` contains a completed run for each target.

## Scope and fairness

The graph has 2,626 nodes (943 users and 1,683 movies) and 100,000 `RATED` relationships. Its source is [MovieLens 100k](https://grouplens.org/datasets/movielens/100k/). Every target must receive the same generated `nodes.csv` and `ratings.csv`, using the same logical model: `User -[:RATED {rating, ts}]-> Movie`.

Run each target from the same client machine and client region. Select tiers as close as possible to CognoDB c0 (0.5 vCPU, 256 MB RAM, 1 GB disk), record the advertised limits below, and do not compare unequal tiers as a performance verdict.

| Platform | Target tier / region | vCPU | RAM | Disk | Status |
|---|---|---:|---:|---:|---|
| CognoDB | c0 / _record_ | 0.5 | 256 MB | 1 GB | pending |
| Neo4j | _record_ | _record_ | _record_ | _record_ | pending |
| Memgraph | _record_ | _record_ | _record_ | _record_ | pending |
| FalkorDB | _record_ | _record_ | _record_ | _record_ | pending |
| Dgraph | _record_ | _record_ | _record_ | _record_ | pending |
| TigerGraph | _record_ | _record_ | _record_ | _record_ | pending |

## Reproduce

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/run_all.py --dry-run
```

Copy `configs/config.yml` to a local untracked configuration only if you need to change tiers or regions. Set the credentials named in the configuration, for example:

```powershell
$env:COGNODB_URI='bolt+s://...'
$env:COGNODB_USER='cognodb'
$env:COGNODB_PASS='...'
$env:NEO4J_URI='neo4j+s://...'
$env:NEO4J_USER='neo4j'
$env:NEO4J_PASS='...'
# Set equivalent variables for MEMGRAPH, FALKORDB, DGRAPH, and TIGERGRAPH.
python scripts/check_env.py
python scripts/run_all.py --config configs/config.yml
python scripts/export_results_csv.py
python scripts/plot_results.py
```

Alternatively, and preferably, copy `.env.example` to `.env` and fill in the values locally. The scripts load `.env` automatically; `.gitignore` prevents it from being added to Git.

Use `--platform cognodb` to retry a single failed target. Do not commit URIs, passwords, tokens, `data/`, or `results/`.

## Beginner setup guide: accounts, credentials, and environment variables

### First, understand what you are creating

You are creating **hosted graph-database instances**: small servers on the internet that store graph data. The script connects to each server, loads exactly the same MovieLens files, and measures how long queries take. An **environment variable** is a temporary named setting in your terminal used to pass a secret to the script without writing it into this repository.

Do not create every account blindly. Some providers have trials or require a payment method, and their smallest plans may not match CognoDB's resources. Check the displayed price and resource limits before clicking a paid option. Record them in the table above. If a provider cannot offer a comparable small instance, keep it as a documented caveat or replace it with a comparable platform; do not present an unequal comparison as fair.

### A. Create CognoDB first (required)

1. Visit [CognoDB Cloud sign-up](https://console.cognodb.com/signup) and create an account.
2. Create the free **c0** instance. Choose a region close to where you will run this project (for example, the closest region to India).
3. When CognoDB displays the generated password, copy it immediately. It is normally shown only once.
4. Copy the connection URI. It looks like `bolt+s://something.databases.cognodb.cloud`.
5. In the PowerShell terminal in this project, set the three values. Replace only the text inside quotes:

```powershell
$env:COGNODB_URI = 'bolt+s://your-instance.databases.cognodb.cloud'
$env:COGNODB_USER = 'cognodb'
$env:COGNODB_PASS = 'paste-the-generated-password-here'
```

CognoDB is Bolt/Cypher compatible, so this project uses the official Neo4j Python driver for it. See the [CognoDB driver documentation](https://cognodb.com/docs).

### B. Create Neo4j AuraDB (the easiest comparison target)

1. Visit the [Neo4j Aura console](https://console.neo4j.io/) and sign up.
2. Click **Create instance** / **New instance**, select an empty database and the smallest available tier. Choose the same or nearest region used for CognoDB.
3. Wait for the instance status to become **Running**.
4. Download the credentials file when prompted. It contains the URI, username, and password; the generated password is not shown again later.
5. Set the values in PowerShell:

```powershell
$env:NEO4J_URI = 'neo4j+s://your-instance.databases.neo4j.io'
$env:NEO4J_USER = 'neo4j'
$env:NEO4J_PASS = 'paste-the-generated-password-here'
```

The [Aura connection guide](https://neo4j.com/docs/aura/getting-started/connect-instance/) explains where these values appear.

### C. Create Memgraph Cloud (Bolt/Cypher comparison)

1. Go to [Memgraph Cloud](https://memgraph.com/cloud) and choose its current trial/entry option.
2. Create one project in the closest available region and choose the smallest memory size.
3. In the project connection panel, copy the Bolt host/port and the database username/password. If the panel says **SSL Encryption**, use `bolt+ssc://HOST:PORT`.
4. Set:

```powershell
$env:MEMGRAPH_URI = 'bolt+ssc://your-host:7687'
$env:MEMGRAPH_USER = 'your-user'
$env:MEMGRAPH_PASS = 'your-password'
```

Memgraph Cloud availability and prices change; its [current pricing page](https://memgraph.com/pricing) is the source of truth. Stop if its smallest plan is not an acceptable match and document that decision.

### D. Create FalkorDB Cloud (RedisGraph-protocol comparison)

1. Go to the [FalkorDB website](https://www.falkordb.com/) and select the managed cloud/service option currently offered.
2. Create the smallest database in the closest region.
3. On its connection/details page, copy the host, port, user, password, and TLS requirement. FalkorDB tools accept `falkor://` URLs, but this harness uses the Redis Python client, so use the equivalent `redis://` or `rediss://` URL.
4. Set only this value (the current runner uses a URI):

```powershell
$env:FALKORDB_URI = 'redis://user:password@host:port'
```

If FalkorDB Cloud is unavailable in your region or unsuitable for a fair entry-tier test, do not substitute random credentials or a different service silently: record the limitation or select another comparable database and update `configs/config.yml`.

### E. Dgraph is optional for this submission

You already have three comparison targets (Neo4j, Memgraph, and FalkorDB). TigerGraph below is a fourth, so you do **not** need Dgraph to satisfy the assignment. Do not spend time creating a Dgraph account unless you specifically want a sixth platform.

1. Visit [Dgraph](https://dgraph.io/) and use the current managed-cloud/trial route, if available. If the provider no longer provides an accessible managed entry tier, use a small self-hosted deployment with fixed resource limits and record it as self-hosted.
2. Create a blank graph/backend in the closest region.
3. Find its HTTP Alpha/API endpoint. The current runner expects an endpoint ending in the server port, for example `https://your-host:8080`—do not append `/query`.
4. If authentication is required, do not run it yet: the current Dgraph runner must be extended with the provider's documented auth header before a valid comparison can be made.
5. For an unauthenticated test endpoint, set:

```powershell
$env:DGRAPH_URI = 'https://your-host:8080'
```

### F. Create TigerGraph Cloud (use this as your fourth comparison target)

1. Visit [TigerGraph Cloud](https://tgcloud.io/) and create an account/solution using the smallest available trial or entry tier.
2. Open the cluster/solution details and copy its domain name, for example `your-name.i.tgcloud.io`.
3. In GraphStudio open **Admin Portal -> User Management**, generate a secret, and copy it. This secret is shown only once.
4. In PowerShell, turn the secret into a short-lived RESTPP token. Replace the placeholders locally; do not commit either value:

```powershell
$body = @{ secret = 'YOUR_TIGERGRAPH_SECRET'; lifetime = 86400 } | ConvertTo-Json
$reply = Invoke-RestMethod -Method Post -Uri 'https://YOUR-DOMAIN.i.tgcloud.io/restpp/requesttoken' -ContentType 'application/json' -Body $body
$env:TIGERGRAPH_TOKEN = $reply.token
```

5. Set the base URL:

```powershell
$env:TIGERGRAPH_URI = 'https://your-solution.i.tgcloud.io'
```

TigerGraph is not an ad-hoc Cypher database. Before running it, create a graph named `movielens` with `User` and `Movie` vertex types, a directed `RATED` edge type, and RESTPP queries called `one_hop`, `lookup`, `agg`, and `write_sim`. It also needs a loading job or REST ingestion mapping for `data/nodes.csv` and `data/ratings.csv`. This is a platform-specific prerequisite; use the [TigerGraph Cloud documentation](https://docs.tigergraph.com/) for the exact UI/API version you see. Do not mark TigerGraph complete until its load and all four queries have been tested manually.

### G. Check, run, and save results

Open a **new PowerShell terminal** only after setting variables, or set them again—`$env:` values last only for the current terminal session. Then run:

```powershell
python scripts/check_env.py
python scripts/run_all.py --config configs/config.yml --platform cognodb
python scripts/run_all.py --config configs/config.yml --platform neo4j
```

Start with CognoDB and Neo4j. When both work, repeat for the other platforms. Finally run all targets, export the CSV, and create plots:

```powershell
python scripts/run_all.py --config configs/config.yml
python scripts/export_results_csv.py
python scripts/plot_results.py
```

`results/results.json` is the evidence file. Keep it, plus failed-run errors and timeout notes. Copy only actual completed measurements into the Results table; leave a platform as `failed`/`not comparable` when appropriate.

### H. Publish on GitHub without exposing secrets

1. Create a new empty repository at [github.com/new](https://github.com/new). Choose **Public** unless the assignment permits a private repository and you will grant the reviewer access.
2. In this project folder, initialize and publish it:

```powershell
git init
git add .
git commit -m 'Add reproducible CognoDB graph benchmark harness'
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

3. Before `git add .`, confirm that `.env`, `data/`, and `results/` remain ignored. Never add a credentials file, downloaded password file, URI, API key, or token.
4. Open the repository on GitHub, check the README renders correctly, then send that repository URL to the assessment contact.

## Workloads and metrics

The harness performs 20 unmeasured warm-up operations, then 100 measured operations per read workload. It reports p50/p95 client-observed latency in milliseconds. Traversals begin from randomly sampled users and use the same alternating user/movie path at 1, 2, and 3 hops. Lookups use the indexed `Movie.id`; aggregation returns the ten most-rated movies.

Loading records total wall-clock seconds plus node and relationship throughput. The mixed workload uses a 90/10 read/write split and concurrency 1, 10, and 40; it reports p50/p95 and completed operations/second. The orchestrator records a failed platform and error instead of silently omitting it. Footprint is marked `not_observable` unless a provider-exposed value is collected separately.

Indexes: Bolt targets create unique indexes/constraints on `User.id` and `Movie.id` plus a `Movie.title` index. Record equivalent indexes for non-Cypher targets in the final report.

## Results

Run-generated raw evidence lives in `results/results.json`; `scripts/export_results_csv.py` makes `results/results.csv`; `scripts/plot_results.py` creates charts. Fill this matrix only from completed runs:

| Platform | Ingest rel/s | 1-hop p50/p95 | 2-hop p50/p95 | 3-hop p50/p95 | Lookup p50/p95 | Aggregation p50/p95 | Mixed QPS (1/10/40) |
|---|---:|---|---|---|---|---|---|
| CognoDB | pending | pending | pending | pending | pending | pending | pending |
| Neo4j | pending | pending | pending | pending | pending | pending | pending |
| Memgraph | pending | pending | pending | pending | pending | pending | pending |
| FalkorDB | pending | pending | pending | pending | pending | pending | pending |
| Dgraph | pending | pending | pending | pending | pending | pending | pending |
| TigerGraph | pending | pending | pending | pending | pending | pending | pending |

## Caveats and interpretation

Free/entry tiers may throttle, suspend, share hardware, or differ in query language and indexing behaviour. Network latency from the client is included because the benchmark measures a cloud service. Repeat runs, retain failures/timeouts, and report variance instead of declaring a winner from one run. Never infer engine quality from data collected on materially unequal resource allocations.
