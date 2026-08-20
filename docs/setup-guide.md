# Platform setup guide

This guide is separate from the submission README so that the repository landing page stays focused on the benchmark itself.

## Local credential file

```powershell
Copy-Item .env.example .env
code .env
```

Fill only the values that you have. `.env` is ignored by Git and loaded automatically by the scripts.

## CognoDB

1. Create a c0 instance at [CognoDB Cloud](https://console.cognodb.com/signup).
2. Copy the Bolt URI, database username, and generated password from the connection panel.
3. Set `COGNODB_URI`, `COGNODB_USER`, and `COGNODB_PASS` in `.env`.
4. If authentication fails, reset the database password and update `.env`.

## Neo4j AuraDB

1. Create an empty smallest-tier instance at [Neo4j Aura](https://console.neo4j.io/).
2. Download the credentials file when it is displayed.
3. Add its Bolt URI, database username, and database password as `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASS`.

An Aura instance ID or console email address is not enough to run the benchmark.

## Memgraph Cloud

1. Create the smallest available project at [Memgraph Cloud](https://memgraph.com/cloud).
2. Copy the database host, port, user, and password.
3. When SSL is enabled, use `bolt+ssc://HOST:7687` for `MEMGRAPH_URI`.

## FalkorDB Cloud

1. Create the smallest managed database at [FalkorDB](https://www.falkordb.com/).
2. Copy its host, port, user, password, and TLS requirement.
3. The runner uses Redis Python client, so set `FALKORDB_URI` as `redis://USER:PASSWORD@HOST:PORT` or `rediss://...`.

## TigerGraph Cloud

1. Create a smallest-tier cluster at [TigerGraph Cloud](https://tgcloud.io/).
2. In GraphStudio define a `movielens` graph with `User`, `Movie`, and directed `RATED` types.
3. Create a loading job or API mapping for `data/nodes.csv` and `data/ratings.csv`.
4. Add stored queries named `one_hop`, `lookup`, `agg`, and `write_sim` with equivalent logic.
5. Generate a secret in **Admin Portal -> User Management**, then create a temporary RESTPP token:

```powershell
$body = @{ secret = 'YOUR_SECRET'; lifetime = 86400 } | ConvertTo-Json
$reply = Invoke-RestMethod -Method Post -Uri 'https://YOUR-DOMAIN.i.tgcloud.io/restpp/requesttoken' -ContentType 'application/json' -Body $body
```

6. Set `TIGERGRAPH_URI=https://YOUR-DOMAIN.i.tgcloud.io` and `TIGERGRAPH_TOKEN=$reply.token`.

## Run order

```powershell
python scripts/check_env.py
python scripts/run_all.py --config configs/config.yml --platform cognodb
```

Run only fully configured targets. Retain every error or timeout as benchmark evidence.
