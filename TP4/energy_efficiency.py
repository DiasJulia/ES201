#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute energy efficiency (IPC/mW) from L1 sweep results and generate plots.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent


# Power consumption at fmax (from Q10)
POWER_CONSUMPTION = {
    "A7": 100.0,   # mW
    "A15": 500.0,  # mW
}


def load_csv(csv_path: Path) -> List[Dict[str, str]]:
    """Load results CSV file."""
    rows: List[Dict[str, str]] = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


def compute_efficiency(rows: List[Dict[str, str]], cpu: str) -> List[Dict[str, str]]:
    """Compute energy efficiency (IPC/mW) for each row."""
    power = POWER_CONSUMPTION.get(cpu, 1.0)
    results: List[Dict[str, str]] = []
    
    for row in rows:
        ipc_str = row.get("ipc")
        if not ipc_str or ipc_str == "None":
            continue
        
        try:
            ipc = float(ipc_str)
        except ValueError:
            continue
        
        efficiency = ipc / power
        
        result = {
            "bench": row.get("bench", ""),
            "l1_size": row.get("l1_size", ""),
            "ipc": ipc_str,
            "power_mw": str(power),
            "efficiency": f"{efficiency:.6f}",
        }
        results.append(result)
    
    return results


def write_efficiency_csv(rows: List[Dict[str, str]], csv_path: Path) -> None:
    """Write efficiency results to CSV."""
    if not rows:
        return
    
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["bench", "l1_size", "ipc", "power_mw", "efficiency"]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _size_key(size: str) -> Tuple[int, str]:
    """Sort key for L1 sizes."""
    digits = "".join(ch for ch in size if ch.isdigit())
    unit = "".join(ch for ch in size if ch.isalpha()).lower()
    num = int(digits) if digits else 0
    return (num, unit)


def plot_efficiency(efficiency_csv: Path, out_dir: Path) -> None:
    """Generate efficiency plots from CSV."""
    import matplotlib.pyplot as plt
    
    if not efficiency_csv.exists():
        raise SystemExit(f"CSV not found: {efficiency_csv}")
    
    rows: List[Dict[str, str]] = []
    with efficiency_csv.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    
    if not rows:
        return
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine CPU from power (100mW = A7, 500mW = A15)
    for row in rows:
        power = float(row.get("power_mw", 0))
        if power == 100.0:
            row["cpu"] = "A7"
        elif power == 500.0:
            row["cpu"] = "A15"
        else:
            row["cpu"] = "Unknown"
    
    benches = sorted({r["bench"] for r in rows})
    cpus = sorted({r["cpu"] for r in rows if r["cpu"] != "Unknown"})
    
    # Plot 1: Combined (all applications and CPUs together)
    plt.figure(figsize=(12, 6))
    for bench in benches:
        bench_rows = [r for r in rows if r["bench"] == bench]
        bench_rows.sort(key=lambda r: (r["cpu"], _size_key(r["l1_size"])))
        
        xs = [r["l1_size"] for r in bench_rows]
        ys = [float(r["efficiency"]) for r in bench_rows]
        
        plt.plot(xs, ys, marker="o", label=bench, linewidth=2)
    
    plt.title("Energy Efficiency Comparison (IPC/mW) - All Applications")
    plt.xlabel("L1 size")
    plt.ylabel("Efficiency (IPC/mW)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    out_path = out_dir / "combined_energy_efficiency.png"
    plt.savefig(out_path, dpi=160)
    plt.close()
    
    # Plot 2-3: By application (Dijkstra and Blowfish), comparing A7 and A15
    for bench in benches:
        plt.figure(figsize=(10, 6))
        bench_rows = [r for r in rows if r["bench"] == bench]
        
        for cpu in cpus:
            cpu_rows = [r for r in bench_rows if r["cpu"] == cpu]
            cpu_rows.sort(key=lambda r: _size_key(r["l1_size"]))
            
            xs = [r["l1_size"] for r in cpu_rows]
            ys = [float(r["efficiency"]) for r in cpu_rows]
            
            if xs and ys:
                plt.plot(xs, ys, marker="o", label=f"Cortex {cpu}", linewidth=2)
        
        plt.title(f"Energy Efficiency - {bench.capitalize()}")
        plt.xlabel("L1 size")
        plt.ylabel("Efficiency (IPC/mW)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        out_path = out_dir / f"{bench}_energy_efficiency.png"
        plt.savefig(out_path, dpi=160)
        plt.close()
    
    # Plot 4-5: By CPU (A7 and A15), comparing applications
    for cpu in cpus:
        plt.figure(figsize=(10, 6))
        cpu_rows = [r for r in rows if r["cpu"] == cpu]
        
        for bench in benches:
            bench_rows = [r for r in cpu_rows if r["bench"] == bench]
            bench_rows.sort(key=lambda r: _size_key(r["l1_size"]))
            
            xs = [r["l1_size"] for r in bench_rows]
            ys = [float(r["efficiency"]) for r in bench_rows]
            
            if xs and ys:
                plt.plot(xs, ys, marker="o", label=bench.capitalize(), linewidth=2)
        
        plt.title(f"Energy Efficiency - Cortex {cpu}")
        plt.xlabel("L1 size")
        plt.ylabel("Efficiency (IPC/mW)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        out_path = out_dir / f"cortex_{cpu.lower()}_energy_efficiency.png"
        plt.savefig(out_path, dpi=160)
        plt.close()


def _extract_cpu(bench: str) -> Optional[str]:
    """Extract CPU name (A7 or A15) from benchmark name."""
    if "A7" in bench or "a7" in bench:
        return "A7"
    elif "A15" in bench or "a15" in bench:
        return "A15"
    return None




def main() -> None:
    parser = argparse.ArgumentParser(description="Compute and plot energy efficiency")
    
    parser.add_argument("--cpu", required=True, choices=["A7", "A15"],
                        help="CPU type")
    parser.add_argument("--input-csv", required=True,
                        help="Input CSV from l1_sweep results")
    parser.add_argument("--output-csv", 
                        help="Output CSV for efficiency results (default: auto)")
    parser.add_argument("--output-dir",
                        help="Output directory for plots (default: auto)")
    parser.add_argument("--plot-only", action="store_true",
                        help="Skip CSV generation and only plot from existing CSV")
    
    args = parser.parse_args()
    
    # Set defaults based on CPU
    if args.output_csv is None:
        args.output_csv = str(
            Path(args.input_csv).parent / f"efficiency_{args.cpu.lower()}.csv"
        )
    if args.output_dir is None:
        args.output_dir = str(
            Path(args.input_csv).parent.parent / "figures_energy"
        )
    
    if not args.plot_only:
        # Compute efficiency
        rows = load_csv(Path(args.input_csv))
        efficiency_rows = compute_efficiency(rows, args.cpu)
        write_efficiency_csv(efficiency_rows, Path(args.output_csv))
        print(f"Wrote efficiency CSV to {args.output_csv}")
    
    # Plot
    plot_efficiency(Path(args.output_csv), Path(args.output_dir))
    print(f"Plots saved to {args.output_dir}")


if __name__ == "__main__":
    main()
