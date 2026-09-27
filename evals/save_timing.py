#!/usr/bin/env python3
"""Record a subagent run's timing: save_timing.py <run-dir> <total_tokens> <duration_ms>"""
import json
import sys

run, tokens, ms = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
json.dump({"total_tokens": tokens, "duration_ms": ms, "total_duration_seconds": round(ms / 1000, 1)},
          open(f"{run}/timing.json", "w"), indent=2)
