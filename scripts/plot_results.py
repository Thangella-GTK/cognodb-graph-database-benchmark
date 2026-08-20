"""Create latency and mixed-throughput charts from schema-v2 results."""
import json
from pathlib import Path
import matplotlib.pyplot as plt

RESULTS, OUT = Path("results/results.json"), Path("results/plots")

def completed(data): return [item for item in data.get("platforms", []) if item.get("status") == "completed"]

def main():
    data = json.loads(RESULTS.read_text(encoding="utf-8")); rows = completed(data)
    if not rows:
        print("No completed platform results to plot"); return
    OUT.mkdir(parents=True, exist_ok=True)
    for metric, title in (("traversals", "Traversal latency"),):
        plt.figure(figsize=(9, 5))
        for item in rows:
            values = item.get(metric, {}); x = list(values); y = [values[key].get("p50_ms") for key in x]
            if x and all(value is not None for value in y): plt.plot(x, y, marker="o", label=item["name"])
        plt.title(title); plt.ylabel("p50 client latency (ms)"); plt.xlabel("hop depth"); plt.legend(); plt.grid(); plt.tight_layout(); plt.savefig(OUT / "traversal_p50.png"); plt.close()
    plt.figure(figsize=(9, 5))
    for item in rows:
        values = item.get("mixed", {}); x = [int(key) for key in values]; y = [values[str(key)].get("operations_per_s") for key in x]
        if x and all(value is not None for value in y): plt.plot(x, y, marker="o", label=item["name"])
    plt.title("Mixed workload throughput"); plt.ylabel("completed operations/s"); plt.xlabel("client concurrency"); plt.legend(); plt.grid(); plt.tight_layout(); plt.savefig(OUT / "mixed_throughput.png"); plt.close()
    print(f"Wrote charts to {OUT}")

if __name__ == "__main__": main()
