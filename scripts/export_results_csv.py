"""Flatten schema-v2 benchmark results into a spreadsheet-friendly CSV."""
import csv, json
from pathlib import Path

RESULTS, OUT = Path("results/results.json"), Path("results/results.csv")

def add(rows, platform, metric, detail, value):
    rows.append({"platform": platform, "metric": metric, "detail": detail, **value})

def main():
    data = json.loads(RESULTS.read_text(encoding="utf-8")); rows = []
    for item in data.get("platforms", []):
        name = item["name"]
        if item.get("load"): add(rows, name, "ingest", "all", item["load"])
        for depth, values in item.get("traversals", {}).items(): add(rows, name, "traversal", depth, values)
        if item.get("lookup"): add(rows, name, "lookup", "point/id", item["lookup"])
        if item.get("aggregation"): add(rows, name, "aggregation", "top-rated movies", item["aggregation"])
        for concurrency, values in item.get("mixed", {}).items(): add(rows, name, "mixed", f"concurrency={concurrency}", values)
        if item.get("status") != "completed": add(rows, name, "run_status", "", {"error": item.get("error")})
    fields = sorted({key for row in rows for key in row})
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {OUT}")

if __name__ == "__main__": main()
