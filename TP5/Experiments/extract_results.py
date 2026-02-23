#!/usr/bin/env python3
"""
Extract simulation results from results.txt and create a CSV summary.

Supported block headers:
1) === results/stats_o3_w{width}_t{threads}_m{matrix}.txt ===
2) === size={matrix} width={width} threads={threads} ===
"""

import argparse
import csv
import re
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    from matplotlib import cm
except Exception:
    plt = None
    cm = None

HEADER_OLD_RE = re.compile(
    r"^===\s*(?P<run_dir>.+/stats_o3_w(?P<width>\d+)_t(?P<threads>\d+)_m(?P<matrix>\d+)\.txt)\s*===\s*$"
)
HEADER_NEW_RE = re.compile(
    r"^===\s*size=(?P<matrix>\d+)\s+width=(?P<width>\d+)\s+threads=(?P<threads>\d+)\s*===\s*$"
)
FILE_RE = re.compile(r"^file:\s*(?P<run_dir>.+?)\s*$")
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

        old_match = HEADER_OLD_RE.match(line)
        new_match = HEADER_NEW_RE.match(line)

        if old_match or new_match:
            if current is not None:
                blocks.append(current)

            if old_match:
                current = {
                    "run_dir": old_match.group("run_dir"),
                    "matrix": int(old_match.group("matrix")),
                    "width": int(old_match.group("width")),
                    "threads": int(old_match.group("threads")),
                    "metrics": {},
                }
            else:
                current = {
                    "run_dir": "",
                    "matrix": int(new_match.group("matrix")),
                    "width": int(new_match.group("width")),
                    "threads": int(new_match.group("threads")),
                    "metrics": {},
                }
            continue

        if current is None:
            continue

        file_match = FILE_RE.match(line)
        if file_match:
            current["run_dir"] = file_match.group("run_dir")
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

    ipc_max = _max_or_empty(metrics.get("ipc_max", []))
    cycles_max = _max_or_empty(metrics.get("cycles_max", []))
    insts_max = _max_or_empty(metrics.get("insts_max", []))
    sim_ticks = _max_or_empty(metrics.get("sim_ticks", []))
    sim_seconds = _max_or_empty(metrics.get("sim_seconds", []))

    status = "OK" if sim_seconds != "" else "FAIL"

    return {
        "matrix": block.get("matrix", ""),
        "threads": block["threads"],
        "width": block["width"],
        "ipc_max_cpu": _safe_float(ipc_max),
        "cycles_max_cpu": _safe_float(cycles_max),
        "insts_max_cpu": _safe_float(insts_max),
        "sim_ticks": _safe_float(sim_ticks),
        "sim_seconds": _safe_float(sim_seconds),
        "run_dir": block.get("run_dir", ""),
        "status": status,
    }


def extract_results(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as stream:
        blocks = parse_blocks(stream.readlines())

    results = [summarize_block(block) for block in blocks]
    results.sort(key=lambda row: (row["matrix"], row["width"], row["threads"]))

    fieldnames = [
        "matrix",
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
    return results


def _to_float(value):
    if value in ("", None):
        return None
    return float(value)


def _load_csv_rows(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if row.get("status") != "OK":
                continue
            rows.append(
                {
                    "matrix": int(row["matrix"]),
                    "threads": int(row["threads"]),
                    "width": int(row["width"]),
                    "sim_seconds": _to_float(row["sim_seconds"]),
                    "ipc_max_cpu": _to_float(row["ipc_max_cpu"]),
                    "cycles_max_cpu": _to_float(row["cycles_max_cpu"]),
                }
            )
    return rows


def _format_metric_value(metric_name, value):
    if value is None:
        return ""
    if metric_name == "sim_seconds":
        return f"{value:.6f}"
    if metric_name == "ipc_max_cpu":
        return f"{value:.3f}"
    if metric_name == "cycles_max_cpu":
        return f"{value:.0f}"
    if metric_name == "speedup":
        return f"{value:.2f}"
    return f"{value:.4g}"


def _annotate_2d_points(x_vals, y_vals, metric_name, color):
    for x_val, y_val in zip(x_vals, y_vals):
        plt.annotate(
            _format_metric_value(metric_name, y_val),
            (x_val, y_val),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
            color=color,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": color, "alpha": 0.65},
        )


def _x_offset_for_curve(curve_index, total_curves):
    if total_curves <= 1:
        return 0.0
    spread = 0.18
    center = (total_curves - 1) / 2.0
    return (curve_index - center) * spread


def _plot_2d(rows, plots_dir, matrix):
    matrix_rows = [r for r in rows if r["matrix"] == matrix]
    widths = sorted({r["width"] for r in matrix_rows})
    colors = plt.get_cmap("tab10")

    # Q9 (support): sim_seconds x threads por width
    plt.figure(figsize=(10, 6))
    for idx, width in enumerate(widths):
        wr = sorted([r for r in matrix_rows if r["width"] == width], key=lambda x: x["threads"])
        x = [r["threads"] for r in wr if r["sim_seconds"] is not None]
        y = [r["sim_seconds"] for r in wr if r["sim_seconds"] is not None]
        x_plot = [v + _x_offset_for_curve(idx, len(widths)) for v in x]
        color = colors(idx % 10)
        if x and y:
            plt.plot(x_plot, y, marker="o", linewidth=2.2, markersize=7, color=color, label=f"Largeur O3 = {width}")
            _annotate_2d_points(x_plot, y, "sim_seconds", color)

    plt.title(f"Temps simulé en fonction du nombre de threads (matrice={matrix})", fontsize=12, fontweight="bold")
    plt.xlabel("Nombre de threads", fontsize=10)
    plt.ylabel("Temps simulé (sim_seconds, s)", fontsize=10)
    thread_values = sorted({r["threads"] for r in matrix_rows})
    plt.xticks(thread_values, [str(v) for v in thread_values])
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend(title="Légende", frameon=True)
    out1 = plots_dir / f"q9_m{matrix}_sim_seconds_2d.png"
    plt.tight_layout()
    plt.savefig(out1, dpi=150)
    plt.close()

    # Q9: cycles_max_cpu x threads por width
    plt.figure(figsize=(10, 6))
    for idx, width in enumerate(widths):
        wr = sorted([r for r in matrix_rows if r["width"] == width], key=lambda x: x["threads"])
        x = [r["threads"] for r in wr if r["cycles_max_cpu"] is not None]
        y = [r["cycles_max_cpu"] for r in wr if r["cycles_max_cpu"] is not None]
        x_plot = [v + _x_offset_for_curve(idx, len(widths)) for v in x]
        color = colors(idx % 10)
        if x and y:
            plt.plot(x_plot, y, marker="o", linewidth=2.2, markersize=7, color=color, label=f"Largeur O3 = {width}")
            _annotate_2d_points(x_plot, y, "cycles_max_cpu", color)

    plt.title(f"Nombre maximal de cycles selon le nombre de threads (matrice={matrix})", fontsize=12, fontweight="bold")
    plt.xlabel("Nombre de threads", fontsize=10)
    plt.ylabel("Nombre maximal de cycles (cycles_max_cpu)", fontsize=10)
    thread_values = sorted({r["threads"] for r in matrix_rows})
    plt.xticks(thread_values, [str(v) for v in thread_values])
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend(title="Légende", frameon=True)
    out2 = plots_dir / f"q9_m{matrix}_cycles_2d.png"
    plt.tight_layout()
    plt.savefig(out2, dpi=150)
    plt.close()

    # Q10: speedup x threads por width (base thread=1)
    plt.figure(figsize=(10, 6))
    for idx, width in enumerate(widths):
        wr = sorted([r for r in matrix_rows if r["width"] == width and r["sim_seconds"] is not None], key=lambda x: x["threads"])
        if not wr:
            continue
        base = next((r["sim_seconds"] for r in wr if r["threads"] == 1), None)
        if base is None or base == 0:
            continue
        x = [r["threads"] for r in wr]
        y = [base / r["sim_seconds"] for r in wr]
        x_plot = [v + _x_offset_for_curve(idx, len(widths)) for v in x]
        color = colors(idx % 10)
        plt.plot(x_plot, y, marker="o", linewidth=2.2, markersize=7, color=color, label=f"Largeur O3 = {width}")
        _annotate_2d_points(x_plot, y, "speedup", color)

    plt.title(f"Accélération en fonction du nombre de threads (matrice={matrix})", fontsize=12, fontweight="bold")
    plt.xlabel("Nombre de threads", fontsize=10)
    plt.ylabel("Accélération (T1 / Tn)", fontsize=10)
    thread_values = sorted({r["threads"] for r in matrix_rows})
    plt.xticks(thread_values, [str(v) for v in thread_values])
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend(title="Légende", frameon=True)
    out3 = plots_dir / f"q10_m{matrix}_speedup_2d.png"
    plt.tight_layout()
    plt.savefig(out3, dpi=150)
    plt.close()

    # Q11 (support): IPC x threads por width
    plt.figure(figsize=(10, 6))
    for idx, width in enumerate(widths):
        wr = sorted([r for r in matrix_rows if r["width"] == width], key=lambda x: x["threads"])
        x = [r["threads"] for r in wr if r["ipc_max_cpu"] is not None]
        y = [r["ipc_max_cpu"] for r in wr if r["ipc_max_cpu"] is not None]
        x_plot = [v + _x_offset_for_curve(idx, len(widths)) for v in x]
        color = colors(idx % 10)
        if x and y:
            plt.plot(x_plot, y, marker="o", linewidth=2.2, markersize=7, color=color, label=f"Largeur O3 = {width}")
            _annotate_2d_points(x_plot, y, "ipc_max_cpu", color)

    plt.title(f"IPC maximal en fonction du nombre de threads (matrice={matrix})", fontsize=12, fontweight="bold")
    plt.xlabel("Nombre de threads", fontsize=10)
    plt.ylabel("IPC maximal (instructions par cycle)", fontsize=10)
    thread_values = sorted({r["threads"] for r in matrix_rows})
    plt.xticks(thread_values, [str(v) for v in thread_values])
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.legend(title="Légende", frameon=True)
    out4 = plots_dir / f"q11_m{matrix}_ipc_2d.png"
    plt.tight_layout()
    plt.savefig(out4, dpi=150)
    plt.close()

    return [out1, out2, out3, out4]


def _build_grid(rows, key, matrix):
    matrix_rows = [r for r in rows if r["matrix"] == matrix and r.get(key) is not None]
    widths = sorted({r["width"] for r in matrix_rows})
    threads = sorted({r["threads"] for r in matrix_rows})
    if not widths or not threads:
        return None, None, None

    zmap = {(r["width"], r["threads"]): r[key] for r in matrix_rows}
    w_vals = []
    t_vals = []
    z_vals = []
    for w in widths:
        for t in threads:
            val = zmap.get((w, t))
            if val is None:
                continue
            w_vals.append(w)
            t_vals.append(t)
            z_vals.append(val)
    return w_vals, t_vals, z_vals


def _plot_3d(rows, plots_dir, matrix):
    outputs = []
    metrics = [
        ("cycles_max_cpu", "cycles_max_cpu", "q9_m{matrix}_cycles_3d.png"),
        ("sim_seconds", "sim_seconds", "q9_m{matrix}_sim_seconds_3d.png"),
        ("ipc_max_cpu", "ipc_max_cpu", "q11_m{matrix}_ipc_3d.png"),
    ]

    for key, zlabel, pattern in metrics:
        w_vals, t_vals, z_vals = _build_grid(rows, key, matrix)
        if not w_vals:
            continue

        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection="3d")
        scat = ax.scatter(w_vals, t_vals, z_vals, c=z_vals, cmap=cm.viridis, s=70, edgecolors="black", linewidths=0.4)
        ax.set_title(f"{zlabel} (matrix={matrix})", fontsize=12, fontweight="bold")
        ax.set_xlabel("Largeur O3 (largeur d'émission)", fontsize=10)
        ax.set_ylabel("Nombre de threads", fontsize=10)
        if key == "cycles_max_cpu":
            z_title = "Nombre maximal de cycles (cycles_max_cpu)"
        elif key == "sim_seconds":
            z_title = "Temps simulé (sim_seconds, s)"
        else:
            z_title = "IPC maximal (instructions par cycle)"
        ax.set_zlabel(z_title, fontsize=10)
        fig.colorbar(scat, ax=ax, shrink=0.7, pad=0.1, label=z_title)

        for w_val, t_val, z_val in zip(w_vals, t_vals, z_vals):
            ax.text(
                w_val,
                t_val,
                z_val,
                _format_metric_value(key, z_val),
                fontsize=7,
                ha="left",
                va="bottom",
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "gray", "alpha": 0.6},
            )

        out = plots_dir / pattern.format(matrix=matrix)
        fig.tight_layout()
        fig.savefig(out, dpi=150)
        plt.close(fig)
        outputs.append(out)

    return outputs


def plot_results_from_csv(csv_path, plots_dir):
    if plt is None:
        print("⚠ matplotlib não disponível. Instale com: pip install matplotlib")
        return []

    rows = _load_csv_rows(csv_path)
    if not rows:
        print("⚠ Nenhuma linha OK para plotar.")
        return []

    plots_dir.mkdir(parents=True, exist_ok=True)
    matrices = sorted({r["matrix"] for r in rows})

    generated = []
    for matrix in matrices:
        generated.extend(_plot_2d(rows, plots_dir, matrix))
        generated.extend(_plot_3d(rows, plots_dir, matrix))

    return generated


if __name__ == "__main__":
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
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate 2D/3D plots from output CSV",
    )
    parser.add_argument(
        "--plots-dir",
        type=Path,
        default=Path(__file__).parent / "plots",
        help="Directory to save generated plots",
    )
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        raise SystemExit(1)

    extract_results(str(input_file), str(output_file))

    if args.plot:
        generated = plot_results_from_csv(output_file, args.plots_dir)
        if generated:
            print(f"✓ Generated {len(generated)} plot(s) in {args.plots_dir}")
            for plot_path in generated:
                print(f"  - {plot_path}")
