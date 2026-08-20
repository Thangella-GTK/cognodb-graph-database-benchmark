import os
import json
import random
from time import perf_counter
from typing import List
import requests


class DgraphRunner:
    def __init__(self, name, env, config=None):
        self.name = name
        self.env = env
        self.base = env.get('uri') or os.environ.get('DGRAPH_URI')
        if self.base and self.base.endswith('/'):
            self.base = self.base[:-1]

    def connect(self):
        if not self.base:
            raise RuntimeError('Dgraph endpoint not provided (DGRAPH_URI)')
        # set minimal schema
        schema = '\n'.join([
            'id: string @index(exact) .',
            'title: string .',
            'rating: int .',
            'ts: int .',
            'dgraph.type: string .',
            'rated: uid .'
        ])
        r = requests.post(f'{self.base}/alter', data=schema)
        if r.status_code >= 400:
            raise RuntimeError(f'Failed to set schema: {r.status_code} {r.text}')

    def close(self):
        pass

    def _mutate(self, data: dict):
        headers = {'Content-Type': 'application/json'}
        r = requests.post(f'{self.base}/mutate?commitNow=true', json=data, headers=headers)
        if r.status_code >= 400:
            raise RuntimeError(f'Mutate failed: {r.status_code} {r.text}')
        return r.json()

    def load(self, nodes_csv: str, edges_csv: str, batch: int = 500):
        import csv
        # Load nodes (users and movies)
        node_sets = []
        with open(nodes_csv, newline='', encoding='utf-8') as f:
            rdr = csv.DictReader(f)
            batch_rows = []
            for r in rdr:
                obj = {'uid': f'_: {r["id"]}'.replace(' ', ''), 'id': r['id']}
                if r.get('type') == 'movie':
                    obj['title'] = r.get('title','')
                    obj['dgraph.type'] = 'Movie'
                else:
                    obj['dgraph.type'] = 'User'
                batch_rows.append(obj)
                if len(batch_rows) >= batch:
                    self._mutate({'set': batch_rows})
                    batch_rows = []
            if batch_rows:
                self._mutate({'set': batch_rows})

        # Edges: create rated relationships with facets as properties
        with open(edges_csv, newline='', encoding='utf-8') as f:
            rdr = csv.DictReader(f)
            batch_rows = []
            for r in rdr:
                uid = f'_:u{r["user_id"]}'
                mid = f'_:m{r["movie_id"]}'
                obj = {'uid': uid, 'rated': [{'uid': mid, 'rating': int(r['rating']), 'ts': int(r['timestamp'])}]}
                batch_rows.append(obj)
                if len(batch_rows) >= batch:
                    self._mutate({'set': batch_rows})
                    batch_rows = []
            if batch_rows:
                self._mutate({'set': batch_rows})

    def _query(self, q: str):
        r = requests.post(f'{self.base}/query', data=q)
        if r.status_code >= 400:
            raise RuntimeError(f'Query failed: {r.status_code} {r.text}')
        return r.json()

    def run_traversal(self, depth: int, iterations: int, sample_nodes: List[str] = None):
        lat = []
        for i in range(iterations):
            # Dgraph query: find user by id then traverse
            uid = None
            if sample_nodes:
                uid = random.choice(sample_nodes)
            else:
                # pick one
                res = self._query('{ q(func: has(id), first:1) { id } }')
                try:
                    uid = res['q'][0]['id']
                except Exception:
                    uid = None
            if not uid:
                continue
            if depth == 1:
                q = f'{{ q(func: eq(id, "{uid}")) {{ rated {{ uid }} }} }}'
            else:
                q = f'{{ q(func: eq(id, "{uid}")) {{ rated {{ uid }} }} }}'
            t0 = perf_counter()
            self._query(q)
            t1 = perf_counter()
            lat.append((t1 - t0) * 1000.0)
        return lat

    def run_lookup(self, iterations: int, indexed=True):
        lat = []
        for i in range(iterations):
            q = '{ q(func: has(title), first:1) { id title } }'
            t0 = perf_counter()
            self._query(q)
            t1 = perf_counter()
            lat.append((t1 - t0) * 1000.0)
        return lat

    def run_aggregation(self, iterations: int):
        # simple group-by via count of incoming rated edges
        lat = []
        for i in range(iterations):
            q = '{ q(func: type(Movie)) { id count(val(rated)) } }'
            t0 = perf_counter()
            self._query(q)
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
                # perform a small mutation and delete
                uid = f'_:tmp{random.randint(1,1000000)}'
                data = {'set': [{'uid': uid, 'dgraph.type': 'Temp', 'id': uid}]}
                t0 = perf_counter()
                self._mutate(data)
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
