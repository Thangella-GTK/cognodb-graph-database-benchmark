import os
import requests
from time import perf_counter
import random


class TigerGraphRunner:
    """Minimal TigerGraph runner.

    Note: TigerGraph Cloud requires generating an auth token and using REST endpoints.
    This runner implements a small subset: connectivity test and simple query execution
    via the /restpp/query endpoint. For full loading, create a loading job in TigerGraph
    and run it; this runner expects the data to already be loaded when running workloads.
    """

    def __init__(self, name, env, config=None):
        self.name = name
        self.env = env
        self.base = env.get('uri') or os.environ.get('TIGERGRAPH_URI')
        self.token = env.get('token') or os.environ.get('TIGERGRAPH_TOKEN')
        self.graph_name = (config or {}).get('graph_name', 'movielens')

    def connect(self):
        if not self.base:
            raise RuntimeError('TIGERGRAPH_URI not provided')
        # test connectivity
        headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        r = requests.get(self.base, headers=headers)
        if r.status_code >= 400:
            raise RuntimeError(f'Connectivity test failed: {r.status_code} {r.text}')

    def close(self):
        pass

    def load(self, nodes_csv: str, edges_csv: str):
        raise NotImplementedError('TigerGraph loading should be done via a GSQL loading job; create the job and call it manually or extend this runner to invoke the job via REST API')

    def run_traversal(self, depth: int, iterations: int, sample_nodes=None):
        # Execute a stored query named 'one_hop' etc via RESTPP if available
        lat = []
        headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        for i in range(iterations):
            url = f'{self.base}/restpp/query/mygraph/one_hop'
            t0 = perf_counter()
            requests.get(url, headers=headers)
            t1 = perf_counter()
            lat.append((t1 - t0) * 1000.0)
        return lat

    def run_lookup(self, iterations: int, indexed=True):
        lat = []
        headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        for i in range(iterations):
            url = f'{self.base}/restpp/query/mygraph/lookup'
            t0 = perf_counter()
            requests.get(url, headers=headers)
            t1 = perf_counter()
            lat.append((t1 - t0) * 1000.0)
        return lat

    def run_aggregation(self, iterations: int):
        lat = []
        headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        for i in range(iterations):
            url = f'{self.base}/restpp/query/mygraph/agg'
            t0 = perf_counter()
            requests.get(url, headers=headers)
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
                # TigerGraph does not support ad-hoc writes via restpp in free tier uniformly;
                # we simulate a write by calling a specific query designed to perform a write if present.
                url = f'{self.base}/restpp/query/mygraph/write_sim'
                t0 = perf_counter()
                requests.get(url, headers={'Authorization': f'Bearer {self.token}'} if self.token else {})
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
