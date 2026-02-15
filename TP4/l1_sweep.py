#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sweep L1 sizes for A7/A15 configs, parse gem5 stats, and generate CSV + plots.
Defaults to auto-discovering *.riscv binaries under TP4/Projet.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent


def parse_stats(stats_path: Path) -> Dict[str, float]:
    stats: Dict[str, float] = {}
    if not stats_path.exists():
        return stats

    with stats_path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("----") or line.startswith("End Simulation"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            key, value = parts[0], parts[1]
            try:
                stats[key] = float(value)
            except ValueError:
                continue
    return stats


def get_first(stats: Dict[str, float], patterns: Iterable[str]) -> Optional[float]:
    for p in patterns:
        if p in stats:
            return stats[p]
    for p in patterns:
        for k, v in stats.items():
            if k.endswith(p):
                return v
    return None


def compute_metrics(stats: Dict[str, float]) -> Dict[str, Optional[float]]:
    metrics: Dict[str, Optional[float]] = {}

    metrics["sim_seconds"] = stats.get("sim_seconds")
    metrics["sim_ticks"] = stats.get("sim_ticks")
    metrics["sim_insts"] = stats.get("sim_insts")

    metrics["num_cycles"] = get_first(stats, [
        "system.cpu.numCycles",
        "numCycles",
    ])

    metrics["ipc"] = get_first(stats, [
        "system.cpu.ipc",
        "ipc",
    ])

    metrics["cpi"] = get_first(stats, [
        "system.cpu.cpi",
        "cpi",
    ])

    metrics["i_miss_rate"] = get_first(stats, [
        "system.cpu.icache.overallMissRate::total",
        "system.cpu.icache.MissRate::total",
        "system.cpu.icache.demandMissRate::total",
        "icache.overallMissRate::total",
        "icache.MissRate::total",
        "icache.demandMissRate::total",
    ])

    metrics["d_miss_rate"] = get_first(stats, [
        "system.cpu.dcache.overallMissRate::total",
        "system.cpu.dcache.MissRate::total",
        "system.cpu.dcache.demandMissRate::total",
        "dcache.overallMissRate::total",
        "dcache.MissRate::total",
        "dcache.demandMissRate::total",
    ])

    metrics["l2_miss_rate"] = get_first(stats, [
        "system.l2cache.overallMissRate::total",
        "system.l2cache.MissRate::total",
        "system.l2cache.demandMissRate::total",
        "l2cache.overallMissRate::total",
        "l2cache.MissRate::total",
        "l2cache.demandMissRate::total",
    ])

    pred = get_first(stats, [
        "system.cpu.branchPred.condPredicted",
        "system.cpu.branchPred.condPred",
    ])
    incorrect = get_first(stats, [
        "system.cpu.branchPred.condIncorrect",
        "system.cpu.branchPred.condMispred",
    ])

    if pred and incorrect is not None and pred > 0:
        metrics["branch_mispred_rate"] = incorrect / pred
    else:
        metrics["branch_mispred_rate"] = None

    return metrics


def discover_binaries(root: Path) -> List[Tuple[str, Path, List[str]]]:
    bins: List[Tuple[str, Path, List[str]]] = []
    for path in root.rglob("*.riscv"):
        name = path.stem
        bins.append((name, path, []))
    return sorted(bins, key=lambda x: x[0])


def parse_bench_list(values: List[str]) -> List[Tuple[str, Path, List[str]]]:
    benches: List[Tuple[str, Path, List[str]]] = []
    for v in values:
        bench_spec, args_str = (v.split("::", 1) + [""])[:2]
        if ":" in bench_spec:
            name, path = bench_spec.split(":", 1)
            bench_path = Path(path).expanduser().resolve()
            bench_name = name
        else:
            p = Path(bench_spec).expanduser().resolve()
            bench_name = p.stem
            bench_path = p
        options = shlex.split(args_str) if args_str else []
        benches.append((bench_name, bench_path, options))
    return benches


def run_gem5(
    gem5_bin: Path,
    cfg: Path,
    outdir: Path,
    cmd: Path,
    l1i: str,
    l1d: str,
    options: List[str],
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    args = [
        str(gem5_bin),
        "-d",
        str(outdir),
        str(cfg),
        f"--cmd={cmd}",
        f"--l1i={l1i}",
        f"--l1d={l1d}",
    ]
    if options:
        args.append("--options")
        args.extend(options)
    subprocess.run(args, check=True)


def run_sweep(args: argparse.Namespace) -> None:
    gem5_bin = Path(args.gem5).expanduser().resolve()
    cfg = Path(args.cfg).expanduser().resolve()
    out_root = Path(args.out_root).expanduser().resolve()

    if args.bench:
        benches = parse_bench_list(args.bench)
    else:
        benches = discover_binaries(ROOT)

    if not benches:
        raise SystemExit("Nenhum binário encontrado (.riscv). Use --bench.")

    sizes = args.sizes

    for bench_name, bench_path, bench_opts in benches:
        for size in sizes:
            outdir = out_root / args.cpu / bench_name / f"l1_{size}"
            run_gem5(
                gem5_bin=gem5_bin,
                cfg=cfg,
                outdir=outdir,
                cmd=bench_path,
                l1i=size,
                l1d=size,
                options=bench_opts,
            )


def collect_results(out_root: Path, cpu: str) -> List[Dict[str, Optional[float]]]:
    rows: List[Dict[str, Optional[float]]] = []
    if not out_root.exists():
        return rows

    for bench_dir in sorted((out_root / cpu).glob("*")):
        if not bench_dir.is_dir():
            continue
        bench_name = bench_dir.name
        for l1_dir in sorted(bench_dir.glob("l1_*")):
            if not l1_dir.is_dir():
                continue
            l1_size = l1_dir.name.replace("l1_", "")
            stats = parse_stats(l1_dir / "stats.txt")
            metrics = compute_metrics(stats)
            metrics["bench"] = bench_name
            metrics["l1_size"] = l1_size
            rows.append(metrics)
    return rows


def write_csv(rows: List[Dict[str, Optional[float]]], csv_path: Path) -> None:
    if not rows:
        return
    fieldnames = [
        "bench",
        "l1_size",
        "sim_seconds",
        "sim_ticks",
        "sim_insts",
        "num_cycles",
        "ipc",
        "cpi",
        "i_miss_rate",
        "d_miss_rate",
        "l2_miss_rate",
        "branch_mispred_rate",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fieldnames})


def plot_from_csv(csv_path: Path, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    if not csv_path.exists():
        raise SystemExit("CSV nao encontrado")

    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)

    if not rows:
        return

    benches = sorted({r["bench"] for r in rows})
    metrics = [
        ("ipc", "IPC"),
        ("cpi", "CPI"),
        ("i_miss_rate", "I$ miss rate"),
        ("d_miss_rate", "D$ miss rate"),
        ("l2_miss_rate", "L2 miss rate"),
        ("branch_mispred_rate", "Branch mispred rate"),
        ("sim_seconds", "Tempo simulado (s)"),
    ]

    out_dir.mkdir(parents=True, exist_ok=True)

    for bench in benches:
        bench_rows = [r for r in rows if r["bench"] == bench]
        sizes = [r["l1_size"] for r in bench_rows]

        for key, title in metrics:
            xs = []
            ys = []
            for r in bench_rows:
                val = r.get(key)
                if val is None or val == "" or val == "None":
                    continue
                xs.append(r["l1_size"])
                ys.append(float(val))
            if not xs:
                continue

            plt.figure()
            plt.plot(xs, ys, marker="o")
            plt.title(f"{bench} - {title} vs L1")
            plt.xlabel("L1 size")
            plt.ylabel(title)
            plt.grid(True, alpha=0.3)
            out_path = out_dir / f"{bench}_{key}.png"
            plt.tight_layout()
            plt.savefig(out_path, dpi=160)
            plt.close()


def default_sizes(cpu: str) -> List[str]:
    if cpu.upper() == "A7":
        return ["1kB", "2kB", "4kB", "8kB", "16kB"]
    if cpu.upper() == "A15":
        return ["2kB", "4kB", "8kB", "16kB", "32kB"]
    raise SystemExit("CPU invalido: use A7 ou A15")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sweep L1 sizes for gem5 A7/A15 configs")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="executa simulacoes")
    run.add_argument("--cpu", required=True, choices=["A7", "A15"])
    run.add_argument("--gem5", required=True, help="caminho do gem5.opt")
    run.add_argument("--cfg", required=True, help="script se_A7.py ou se_A15.py")
    run.add_argument("--out-root", default=str(ROOT / "results_l1"))
    run.add_argument("--bench", action="append", default=[], help="nome:caminho ou caminho do binario")
    run.add_argument("--sizes", nargs="+", help="override lista de tamanhos (ex: 1kB 2kB)")

    collect = sub.add_parser("collect", help="gera CSV a partir dos m5out")
    collect.add_argument("--cpu", required=True, choices=["A7", "A15"])
    collect.add_argument("--out-root", default=str(ROOT / "results_l1"))
    collect.add_argument("--csv", default=str(ROOT / "results_l1" / "results.csv"))

    plot = sub.add_parser("plot", help="gera figuras a partir do CSV")
    plot.add_argument("--csv", default=str(ROOT / "results_l1" / "results.csv"))
    plot.add_argument("--out-dir", default=str(ROOT / "results_l1" / "figures"))

    return p


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.cmd == "run":
        args.sizes = args.sizes if args.sizes else default_sizes(args.cpu)
        run_sweep(args)
        return

    if args.cmd == "collect":
        out_root = Path(args.out_root).expanduser().resolve()
        rows = collect_results(out_root, args.cpu)
        csv_path = Path(args.csv).expanduser().resolve()
        write_csv(rows, csv_path)
        return

    if args.cmd == "plot":
        csv_path = Path(args.csv).expanduser().resolve()
        out_dir = Path(args.out_dir).expanduser().resolve()
        plot_from_csv(csv_path, out_dir)
        return


if __name__ == "__main__":
    main()
