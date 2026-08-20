"""Common interface and driver factory for benchmark targets."""
from abc import ABC, abstractmethod
from typing import Dict


class PlatformRunner(ABC):
    def __init__(self, name: str, env: Dict[str, str], config: Dict = None):
        self.name, self.env, self.config = name, env, config or {}

    @abstractmethod
    def connect(self): ...

    @abstractmethod
    def load(self, nodes_csv: str, edges_csv: str) -> Dict: ...

    @abstractmethod
    def run_traversal(self, depth: int, iterations: int): ...

    @abstractmethod
    def run_lookup(self, iterations: int): ...

    @abstractmethod
    def run_aggregation(self, iterations: int): ...

    @abstractmethod
    def run_mixed_workload(self, concurrency: int, iterations: int, read_pct: int): ...

    def footprint(self) -> Dict:
        return {"status": "not_observable"}

    def close(self):
        pass


def get_runner_for(name: str, env: Dict[str, str], config: Dict = None) -> PlatformRunner:
    driver = (config or {}).get("driver", name).lower()
    if driver in ("neo4j", "bolt"):
        from .platforms.neo4j_runner import Neo4jRunner
        return Neo4jRunner(name, env, config)
    if driver in ("redisgraph", "falkordb", "redis"):
        from .platforms.redisgraph_runner import RedisGraphRunner
        return RedisGraphRunner(name, env, config)
    if driver == "dgraph":
        from .platforms.dgraph_runner import DgraphRunner
        return DgraphRunner(name, env, config)
    if driver in ("tigergraph", "tg"):
        from .platforms.tigergraph_runner import TigerGraphRunner
        return TigerGraphRunner(name, env, config)
    raise ValueError(f"Unsupported driver {driver!r} for {name}")
