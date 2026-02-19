#!/usr/bin/env python3
"""
Extract simulation results from results.txt and create a CSV summary.
Parses blocks in the form:
=== results/stats_o3_w{width}_t{threads}_m{matrix}.txt ===
"""

import argparse
import csv
import re
from pathlib import Path

HEADER_RE = re.compile(
    r"^===\s*(?P<run_dir>.+/stats_o3_w(?P<width>\d+)_t(?P<threads>\d+)_m(?P<matrix>\d+)\.txt)\s*===\s*$"
)
STAT_RE = re.compile(r"^(?P<key>\S+)\s+(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)")


def _safe_float(value):
    if value is None:
        return ""
    return value


def _max_or_empty(values):
    return max(values) if values else ""


def parse_blocks(lines):
    blocks = []
    current = None

    for raw_line in lines:
        line = raw_line.strip()
        header_match = HEADER_RE.match(line)

        if header_match:
            if current is not None:
                blocks.append(current)

            current = {
                "run_dir": header_match.group("run_dir"),
                "width": int(header_match.group("width")),
                "threads": int(header_match.group("threads")),
                "metrics": {},
            }
            continue

        if not current:
            continue

        stat_match = STAT_RE.match(line)
        if stat_match:
            key = stat_match.group("key")
            value = float(stat_match.group("value"))
            current["metrics"].setdefault(key, []).append(value)

    if current is not None:
        blocks.append(current)

    return blocks


def summarize_block(block):
    metrics = block["metrics"]

    # script_collect.sh: ipc_max, cycles_max, insts_max, sim_seconds, sim_ticks
    ipc_max = _max_or_empty(metrics.get("ipc_max", []))
    cycles_max = _max_or_empty(metrics.get("cycles_max", []))
    insts_max = _max_or_empty(metrics.get("insts_max", []))
    sim_ticks = _max_or_empty(metrics.get("sim_ticks", []))
    sim_seconds = _max_or_empty(metrics.get("sim_seconds", []))

    status = "OK" if sim_seconds != "" else "FAIL"

    return {
        "threads": block["threads"],
        "width": block["width"],
        "ipc_max_cpu": _safe_float(ipc_max),
        "cycles_max_cpu": _safe_float(cycles_max),
        "insts_max_cpu": _safe_float(insts_max),
        "sim_ticks": _safe_float(sim_ticks),
        "sim_seconds": _safe_float(sim_seconds),
        "run_dir": block["run_dir"],
        "status": status,
    }


def extract_results(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as stream:
        blocks = parse_blocks(stream.readlines())

    results = [summarize_block(block) for block in blocks]
    results.sort(key=lambda row: (row["width"], row["threads"]))

    fieldnames = [
        "threads",
        "width",
        "ipc_max_cpu",
        "cycles_max_cpu",
        "insts_max_cpu",
        "sim_ticks",
        "sim_seconds",
        "run_dir",
        "status",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✓ Extracted {len(results)} runs to {output_file}")
    print("columns:", ", ".join(fieldnames))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract gem5 results summary from results.txt")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "results.txt",
        help="Path to input results.txt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "results.csv",
        help="Path to output CSV",
    )
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        exit(1)

    extract_results(str(input_file), str(output_file))
