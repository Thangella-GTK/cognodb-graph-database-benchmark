import os
import random
from time import perf_counter
from typing import List

try:
    import redis
except Exception:
    redis = None


class RedisGraphRunner:
    def __init__(self, name, env, config=None):
        self.name = name
        self.env = env
        self.client = None
        self.graph_name = env.get('graph_name') or os.environ.get('REDISGRAPH_GRAPH', 'g')

    def connect(self):
        # If top-level import failed earlier, attempt dynamic import now
        if redis is None:
            try:
                import importlib
                globals()['redis'] = importlib.import_module('redis')
            except Exception:
                raise RuntimeError('redis package not installed; pip install redis redisgraph')
        uri = self.env.get('uri') or os.environ.get('REDISGRAPH_URI') or os.environ.get('FALKORDB_URI')
        if not uri:
            raise RuntimeError('REDISGRAPH_URI not set')
        self.client = redis.from_url(uri, socket_connect_timeout=30, socket_timeout=30)
        self.client.ping()

    def close(self):
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass

    def _run_query(self, q: str):
        # Use RedisGraph module if available otherwise use raw command
        try:
            # redis-py 4.x: client.execute_command
            return self.client.execute_command('GRAPH.QUERY', self.graph_name, q)
        except Exception as e:
            raise

    def load(self, nodes_csv: str, edges_csv: str, batch: int = 500):
        import csv
        started = perf_counter()
        nodes = edges = 0
        try:
            self.client.execute_command('GRAPH.DELETE', self.graph_name)
        except Exception:
            pass

        def flush(queries):
            pipe = self.client.pipeline(transaction=False)
            for query in queries:
                pipe.execute_command('GRAPH.QUERY', self.graph_name, query)
            pipe.execute()

        # Create nodes
        with open(nodes_csv, newline='', encoding='utf-8') as f:
            rdr = csv.DictReader(f)
            qbatch = []
            for r in rdr:
                rid = r['id'].replace("'", "\\'")
                if r.get('type','') == 'user':
                    q = f"CREATE (:User {{id:\'{rid}\'}})"
                else:
                    title = (r.get('title') or '').replace("'", "\\'")
                    q = f"CREATE (:Movie {{id:\'{rid}\', title:\'{title}\'}})"
                qbatch.append(q)
                if len(qbatch) >= batch:
                    flush(qbatch)
                    nodes += len(qbatch)
                    qbatch = []
            if qbatch:
                flush(qbatch)
                nodes += len(qbatch)

        # Edges
        with open(edges_csv, newline='', encoding='utf-8') as f:
            rdr = csv.DictReader(f)
            qbatch = []
            for r in rdr:
                uid = 'u' + r['user_id']
                mid = 'm' + r['movie_id']
                rating = int(r['rating'])
                q = f"MATCH (u:User {{id:\'{uid}\'}}),(m:Movie {{id:\'{mid}\'}}) CREATE (u)-[:RATED {{rating:{rating}}}]->(m)"
                qbatch.append(q)
                if len(qbatch) >= batch:
                    flush(qbatch)
                    edges += len(qbatch)
                    qbatch = []
            if qbatch:
                flush(qbatch)
                edges += len(qbatch)
        seconds = perf_counter() - started
        return {'wall_clock_s': seconds, 'nodes': nodes, 'relationships': edges,
                'nodes_per_s': nodes / seconds if seconds else None,
                'relationships_per_s': edges / seconds if seconds else None,
                'method': 'FalkorDB GRAPH.QUERY pipelined batches of 500'}

    def run_traversal(self, depth: int, iterations: int, sample_nodes: List[str] = None):
        lat = []
        for i in range(iterations):
            uid = None
            if sample_nodes:
                uid = random.choice(sample_nodes)
            else:
                # best-effort: pick a random user id via query
                res = self._run_query("MATCH (u:User) RETURN u.id LIMIT 1")
                try:
                    uid = res[1][0][0]
                except Exception:
                    uid = None
            if not uid:
                continue
            patterns = {
                1: "-[:RATED]->(:Movie)",
                2: "-[:RATED]->(:Movie)<-[:RATED]-(:User)",
                3: "-[:RATED]->(:Movie)<-[:RATED]-(:User)-[:RATED]->(:Movie)",
            }
            q = f"MATCH (u:User {{id:'{uid}'}}){patterns[depth]} RETURN count(*)"
            t0 = perf_counter()
            self._run_query(q)
            t1 = perf_counter()
            lat.append((t1 - t0) * 1000.0)
        return lat

    def run_lookup(self, iterations: int, indexed=True):
        lat = []
        for i in range(iterations):
            t0 = perf_counter()
            self._run_query("MATCH (m:Movie) RETURN m.id LIMIT 1")
            t1 = perf_counter()
            lat.append((t1 - t0) * 1000.0)
        return lat

    def run_aggregation(self, iterations: int):
        lat = []
        for i in range(iterations):
            t0 = perf_counter()
            self._run_query("MATCH (m:Movie)<-[:RATED]-() RETURN m.id, COUNT(*) AS c ORDER BY c DESC LIMIT 10")
            t1 = perf_counter()
            lat.append((t1 - t0) * 1000.0)
        return lat

    def run_mixed_workload(self, concurrency: int, iterations: int, read_pct: int):
        from concurrent.futures import ThreadPoolExecutor

        def op(i):
            r = random.randint(1,100)
            if r <= read_pct:
                return self.run_traversal(1,1)
            else:
                t0 = perf_counter()
                self._run_query("MATCH (u:User) RETURN u.id LIMIT 1")
                t1 = perf_counter()
                return (t1 - t0) * 1000.0

        res = []
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = [ex.submit(op, i) for i in range(iterations)]
            for f in futures:
                r = f.result()
                if isinstance(r, list):
                    res.extend(r)
                else:
                    res.append(r)
        return res
