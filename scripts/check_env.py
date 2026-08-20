import json, os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass
keys = ["COGNODB_URI", "COGNODB_USER", "COGNODB_PASS", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASS", "MEMGRAPH_URI", "MEMGRAPH_USER", "MEMGRAPH_PASS", "FALKORDB_URI", "DGRAPH_URI", "TIGERGRAPH_URI", "TIGERGRAPH_TOKEN"]
print(json.dumps({key: bool(os.getenv(key)) for key in keys}, indent=2))
