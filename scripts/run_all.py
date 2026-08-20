#!/usr/bin/env python3
"""Reproducible benchmark orchestrator.

It deliberately records failed platforms and never replaces a completed result on a
dry run. Real measurements require user-provided cloud credentials.
"""
import argparse, json, os, random, subprocess, sys
from math import ceil
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from bench.runner import get_runner_for

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def percentile(values, p):
    if not values: return None
    values = sorted(values); pos = (len(values) - 1) * p / 100; lo = int(pos); hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)

def stats(values):
    return {"p50_ms": percentile(values, 50), "p95_ms": percentile(values, 95), "sample_count": len(values)}

def read_config(path):
    import yaml
    with open(path, encoding="utf-8") as handle: return yaml.safe_load(handle)

def resolved_env(platform):
    result = {}
    for field, target in (("uri", "env_uri"), ("user", "env_user"), ("password", "env_pass"), ("token", "env_token")):
        if platform.get(target): result[field] = os.getenv(platform[target])
    return result

def prepare_data(cfg, dry_run):
    dataset = cfg["dataset"]
    if dry_run: return
    # Reuse the deterministic CSVs when they already exist. This lets a benchmark
    # be rerun without depending on the public dataset host being reachable.
    if (ROOT / "data/nodes.csv").exists() and (ROOT / "data/ratings.csv").exists():
        print("Using existing prepared dataset CSVs.")
        return
    subprocess.run([sys.executable, str(ROOT / "scripts/datasets/download_movielens.py"), dataset["source_url"], dataset["local_zip"], dataset["extracted_dir"]], check=True)
    subprocess.run([sys.executable, str(ROOT / "src/bench/loader.py"), dataset["extracted_dir"], str(ROOT / "data")], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--platform", action="append", help="Run only this named platform; repeatable")
    args = parser.parse_args()
    if load_dotenv:
        load_dotenv(ROOT / ".env")
    cfg = read_config(args.config)
    random.seed(cfg.get("run", {}).get("seed", 0)); (ROOT / "results").mkdir(exist_ok=True)
    selected = [p for p in cfg["platforms"] if not args.platform or p["name"] in args.platform]
    plan = {"dataset": cfg["dataset"]["name"], "platforms": [{"name": p["name"], "driver": p["driver"], "tier": p.get("tier")} for p in selected]}
    if args.dry_run:
        print(json.dumps(plan, indent=2)); print("Dry run passed; no files or cloud targets were changed."); return
    prepare_data(cfg, False)
    nodes, edges = ROOT / "data/nodes.csv", ROOT / "data/ratings.csv"
    if not nodes.exists() or not edges.exists(): raise RuntimeError("Dataset preparation did not produce data/nodes.csv and data/ratings.csv")
    workload = cfg["workload"]; iterations = int(workload["iterations"]); warmup = int(workload.get("warmup_iterations", ceil(iterations * .1)))
    result = {"schema_version": 2, "run": cfg.get("run", {}), "dataset": cfg["dataset"]["name"], "platforms": []}
    for platform in selected:
        entry = {"name": platform["name"], "driver": platform["driver"], "tier": platform.get("tier"), "status": "failed"}
        runner = None
        try:
            runner = get_runner_for(platform["name"], resolved_env(platform), platform); runner.connect()
            entry["load"] = runner.load(str(nodes), str(edges))
            runner.run_traversal(1, warmup)
            entry["traversals"] = {f"{depth}_hop": stats(runner.run_traversal(depth, iterations)) for depth in (1, 2, 3)}
            entry["lookup"] = stats(runner.run_lookup(iterations))
            entry["aggregation"] = stats(runner.run_aggregation(iterations))
            entry["mixed"] = {}
            for concurrency in workload["concurrency_sweep"]:
                started = perf_counter(); samples = runner.run_mixed_workload(int(concurrency), iterations, int(workload["read_write_mix"]["reads"])); seconds = perf_counter() - started
                entry["mixed"][str(concurrency)] = {**stats(samples), "wall_clock_s": seconds, "operations_per_s": len(samples) / seconds if seconds else None, "read_percent": workload["read_write_mix"]["reads"]}
            entry["footprint"] = runner.footprint(); entry["status"] = "completed"
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            if runner:
                try: runner.close()
                except Exception: pass
        result["platforms"].append(entry)
    path = ROOT / "results/results.json"; path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {path}")

if __name__ == "__main__": main()
