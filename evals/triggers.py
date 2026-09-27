#!/usr/bin/env python3
"""Trigger evaluation with one project directory per query run.

skill-creator's run_eval.py writes every parallel worker's temporary command into
the SAME .claude/commands/ directory, so each `claude -p` sees N identical copies
of the skill and "triggers" only when it happens to pick its own copy (~1/N).
This runner reuses its detector (run_single_query) but gives every run a private
project root, so a trigger rate measures the description and not the collision.

    SC=<skill-creator dir> uv run --no-project --python 3.12 python evals/triggers.py \
        --skill tidy [--skill git-hygiene ...] --runs 3 --workers 8 --model claude-opus-5-5
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.environ["SC"])
from scripts.run_eval import run_single_query  # noqa: E402
from scripts.utils import parse_skill_md  # noqa: E402


def one(query, name, desc, model, timeout):
    with tempfile.TemporaryDirectory(prefix="hk-trig-") as d:
        os.makedirs(os.path.join(d, ".claude"))
        return run_single_query(query, name, desc, timeout, d, model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", action="append", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "results-trigger.json"))
    a = ap.parse_args()
    report = {}
    for skill in a.skill:
        name, desc, _ = parse_skill_md(Path(ROOT) / "skills" / skill)
        queries = json.load(open(os.path.join(HERE, "trigger_sets", f"{skill}.json")))
        jobs = {}
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for qi, q in enumerate(queries):
                for r in range(a.runs):
                    jobs[ex.submit(one, q["query"], name, desc, a.model, a.timeout)] = qi
            hits = {i: [] for i in range(len(queries))}
            for f in as_completed(jobs):
                try:
                    hits[jobs[f]].append(bool(f.result()))
                except Exception:
                    hits[jobs[f]].append(False)
        rows = []
        for i, q in enumerate(queries):
            rate = sum(hits[i]) / len(hits[i])
            ok = rate >= 0.5 if q["should_trigger"] else rate < 0.5
            rows.append({"query": q["query"], "should_trigger": q["should_trigger"], "trigger_rate": round(rate, 2), "pass": ok})
        passed = sum(r["pass"] for r in rows)
        report[skill] = {"passed": passed, "total": len(rows), "results": rows}
        print(f"{skill}: {passed}/{len(rows)}", flush=True)
    json.dump(report, open(a.out, "w"), indent=2)


if __name__ == "__main__":
    main()
