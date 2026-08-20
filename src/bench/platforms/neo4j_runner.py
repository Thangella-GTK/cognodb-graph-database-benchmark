"""Bolt/Cypher runner used for CognoDB, Neo4j, and Memgraph targets."""
import csv
import random
from pathlib import Path
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
from neo4j import GraphDatabase

from ..runner import PlatformRunner


class Neo4jRunner(PlatformRunner):
    def connect(self):
        uri = self.env.get("uri")
        user = self.env.get("user")
        password = self.env.get("password")
        if not all((uri, user, password)):
            raise RuntimeError(f"Credentials missing for {self.name}")
        self.driver = GraphDatabase.driver(uri, auth=(user, password), connection_timeout=30)
        self.driver.verify_connectivity()

    def _write(self, session, fn, rows):
        return session.execute_write(fn, rows) if hasattr(session, "execute_write") else session.write_transaction(fn, rows)

    def load(self, nodes_csv, edges_csv, batch=1_000):
        started = perf_counter(); nodes = edges = 0
        with self.driver.session() as session:
            # Each benchmark is a fresh load. Clear previous benchmark data so
            # repeated runs do not measure an increasingly expensive MERGE.
            while True:
                summary = session.run("MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(*) AS deleted").single()
                if not summary or summary["deleted"] == 0:
                    break
            # Labels are intentionally part of the physical schema: every workload below relies on them.
            session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE").consume()
            session.run("CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.id IS UNIQUE").consume()
            session.run("CREATE INDEX movie_title IF NOT EXISTS FOR (m:Movie) ON (m.title)").consume()
            for path, fn, kind in ((nodes_csv, self._nodes_tx, "node"), (edges_csv, self._edges_tx, "edge")):
                rows = []
                with open(path, newline="", encoding="utf-8") as handle:
                    for row in csv.DictReader(handle):
                        rows.append(row)
                        if len(rows) == batch:
                            self._write(session, fn, rows); nodes += len(rows) if kind == "node" else 0; edges += len(rows) if kind == "edge" else 0; rows = []
                if rows:
                    self._write(session, fn, rows); nodes += len(rows) if kind == "node" else 0; edges += len(rows) if kind == "edge" else 0
        seconds = perf_counter() - started
        return {"wall_clock_s": seconds, "nodes": nodes, "relationships": edges,
                "nodes_per_s": nodes / seconds if seconds else None, "relationships_per_s": edges / seconds if seconds else None,
                "method": "Bolt driver UNWIND batches of 1000"}

    @staticmethod
    def _nodes_tx(tx, rows):
        users = [{"id": r["id"]} for r in rows if r["type"] == "user"]
        movies = [{"id": r["id"], "title": r.get("title", "")} for r in rows if r["type"] == "movie"]
        if users: tx.run("UNWIND $rows AS r MERGE (:User {id:r.id})", rows=users).consume()
        if movies: tx.run("UNWIND $rows AS r MERGE (m:Movie {id:r.id}) SET m.title=r.title", rows=movies).consume()

    @staticmethod
    def _edges_tx(tx, rows):
        tx.run("UNWIND $rows AS r MATCH (u:User {id:'u'+r.user_id}), (m:Movie {id:'m'+r.movie_id}) "
               "CREATE (u)-[:RATED {rating:toInteger(r.rating), ts:toInteger(r.timestamp)}]->(m)", rows=rows).consume()

    def _time(self, query, **params):
        with self.driver.session() as session:
            started = perf_counter(); session.run(query, **params).consume(); return (perf_counter() - started) * 1000

    def _user_ids(self):
        with self.driver.session() as session:
            return [record["id"] for record in session.run("MATCH (u:User) RETURN u.id AS id ORDER BY u.id")]

    def run_traversal(self, depth, iterations):
        ids = self._user_ids()
        if not ids: return []
        # Bound expansions to 1,000 rows. Without a common cap, a 3-hop path on
        # MovieLens can explode combinatorially and turn a cloud timeout into a
        # misleading engine comparison. Apply this same cap in every adapter.
        patterns = {
            1: "MATCH (u:User {id:$id})-[:RATED]->(target:Movie)",
            2: "MATCH (u:User {id:$id})-[:RATED]->(:Movie)<-[:RATED]-(target:User)",
            3: "MATCH (u:User {id:$id})-[:RATED]->(:Movie)<-[:RATED]-(:User)-[:RATED]->(target:Movie)",
        }
        query = patterns[depth] + " WITH target LIMIT 1000 RETURN count(*)"
        return [self._time(query, id=random.choice(ids)) for _ in range(iterations)]

    def run_lookup(self, iterations):
        return [self._time("MATCH (m:Movie {id:$id}) RETURN m.title", id=f"m{random.randint(1,1682)}") for _ in range(iterations)]

    def run_aggregation(self, iterations):
        query = "MATCH (m:Movie)<-[:RATED]-(:User) RETURN m.id, count(*) AS ratings ORDER BY ratings DESC LIMIT 10"
        return [self._time(query) for _ in range(iterations)]

    def run_mixed_workload(self, concurrency, iterations, read_pct):
        def operation(i):
            if random.randint(1, 100) <= read_pct:
                vals = self.run_traversal(1, 1); return vals[0] if vals else None
            marker = f"bench-{random.randrange(1_000_000_000)}"
            return self._time("MATCH (u:User {id:'u1'}), (m:Movie {id:'m1'}) CREATE (u)-[r:BenchmarkWrite {id:$id}]->(m) DELETE r", id=marker)
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            return [result for result in pool.map(operation, range(iterations)) if result is not None]

    def footprint(self):
        # Cloud providers expose this differently; do not fabricate a value.
        return {"status": "not_observable", "note": "Record console-reported storage and instance specs in README."}

    def close(self):
        self.driver.close()
