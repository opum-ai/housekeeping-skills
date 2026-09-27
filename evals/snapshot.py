#!/usr/bin/env python3
"""Copy a benchmark iteration into evals/benchmarks/, scrubbed of machine paths.

    python3 evals/snapshot.py <workspace>/iteration-N [--name iteration-N]

The repository is public: nothing in it may carry an absolute machine path,
a username, or a hostname. Grading, timing, reports and the benchmark are
copied; fixtures (which contain whole git repos) are not.
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRUB = [
    (re.compile(r"/private/tmp/claude-\d+/[^\s\"'`)]*?/hk-workspace"), "<workspace>"),
    (re.compile(r"/private/tmp/claude-\d+(/[^\s\"'`)]*)?"), "<tmp>"),
    (re.compile(r"/private/var/folders/[^\s\"'`)]*"), "<tmpdir>"),
    (re.compile(r"/Volumes/external/repos/housekeeping-skills"), "<repo>"),
    (re.compile(r"/Volumes/external/repos/[\w.-]+"), "<repos>/…"),
    (re.compile(r"/Users/[\w.-]+"), "~"),
]


def scrub(text: str) -> str:
    for pat, rep in SCRUB:
        text = pat.sub(rep, text)
    return text


def copy(src: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, encoding="utf-8", errors="replace") as fh:
        data = fh.read()
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(scrub(data))


def main(src_iter: str, name: str) -> None:
    out = os.path.join(HERE, "benchmarks", name)
    if os.path.isdir(out):
        shutil.rmtree(out)
    for f in ("benchmark.json", "benchmark.md"):
        if os.path.exists(os.path.join(src_iter, f)):
            copy(os.path.join(src_iter, f), os.path.join(out, f))
    for dp, dns, fns in os.walk(src_iter):
        dns[:] = [d for d in dns if d not in ("fixture",) and not d.startswith("contaminated")]
        for f in fns:
            if f in ("grading.json", "timing.json", "response.md", "eval_metadata.json"):
                rel = os.path.relpath(os.path.join(dp, f), src_iter).replace("/outputs/", "/")
                copy(os.path.join(dp, f), os.path.join(out, rel))
    print(f"snapshot -> {os.path.relpath(out, os.path.dirname(HERE))}")


if __name__ == "__main__":
    src = sys.argv[1]
    name = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--name" else os.path.basename(src.rstrip("/"))
    main(src, name)
