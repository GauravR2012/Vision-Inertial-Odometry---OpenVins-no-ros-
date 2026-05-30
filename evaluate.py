"""
evaluate.py — Compute ATE metrics and generate 3D trajectory visualization
for OpenVINS simulation output.

Usage:
    python evaluate.py
    python evaluate.py --traj results/trajectory.txt --gt results/groundtruth.txt
    python evaluate.py --no-plot
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Evaluate OpenVINS trajectory accuracy")
    p.add_argument("--traj",     default="results/trajectory.txt",    help="Estimated trajectory file")
    p.add_argument("--gt",       default="results/groundtruth.txt",   help="Ground truth file")
    p.add_argument("--out",      default="results/openvins_trajectory.html", help="Output HTML visualization")
    p.add_argument("--no-plot",  action="store_true",                 help="Skip visualization")
    return p.parse_args()


# ── Load ──────────────────────────────────────────────────────────────────────

def load_trajectory(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        print(f"[ERROR] File not found: {path}")
        print("        Have you run bash run.sh yet?")
        sys.exit(1)
    df = pd.read_csv(p, sep=r"\s+", comment="#", header=None, names=["t", "x", "y", "z"])
    return df


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_ate(traj: pd.DataFrame, gt: pd.DataFrame) -> dict:
    N = min(len(traj), len(gt))
    t  = traj.iloc[:N]
    g  = gt.iloc[:N]

    err = np.sqrt((t.x.values - g.x.values)**2 +
                  (t.y.values - g.y.values)**2 +
                  (t.z.values - g.z.values)**2)

    # Trajectory length from ground truth
    diffs = np.diff(g[["x", "y", "z"]].values, axis=0)
    length = float(np.sum(np.linalg.norm(diffs, axis=1)))

    return {
        "n_points":      N,
        "traj_length_m": length,
        "ate_rmse":      float(np.sqrt(np.mean(err**2))),
        "mean_err":      float(np.mean(err)),
        "median_err":    float(np.median(err)),
        "max_err":       float(np.max(err)),
        "min_err":       float(np.min(err)),
        "rel_error_pct": float(np.sqrt(np.mean(err**2)) / length * 100),
        "err_series":    err,
    }


def print_metrics(m: dict):
    print()
    print("=" * 50)
    print("  OpenVINS Evaluation Results")
    print("=" * 50)
    print(f"  Points evaluated      : {m['n_points']}")
    print(f"  Trajectory length     : {m['traj_length_m']:.2f} m")
    print("-" * 50)
    print(f"  ATE RMSE              : {m['ate_rmse']:.4f} m")
    print(f"  Mean position error   : {m['mean_err']:.4f} m")
    print(f"  Median position error : {m['median_err']:.4f} m")
    print(f"  Max position error    : {m['max_err']:.4f} m")
    print(f"  Min position error    : {m['min_err']:.4f} m")
    print("-" * 50)
    print(f"  Relative error        : {m['rel_error_pct']:.4f} %")
    print("=" * 50)
    print()


def save_metrics(m: dict, path: str = "results/ate_results.txt"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("OpenVINS Evaluation Results\n")
        f.write("===========================\n")
        f.write(f"Points evaluated           : {m['n_points']}\n")
        f.write(f"Trajectory Length          : {m['traj_length_m']:.2f} m\n\n")
        f.write(f"ATE RMSE                   : {m['ate_rmse']:.4f} m\n")
        f.write(f"Mean Position Error        : {m['mean_err']:.4f} m\n")
        f.write(f"Median Position Error      : {m['median_err']:.4f} m\n")
        f.write(f"Max Position Error         : {m['max_err']:.4f} m\n")
        f.write(f"Min Position Error         : {m['min_err']:.4f} m\n\n")
        f.write(f"Relative Trajectory Error  : {m['rel_error_pct']:.4f} %\n")
    print(f"[evaluate] Metrics saved → {path}")


# ── Visualization ─────────────────────────────────────────────────────────────

def plot_trajectory(traj: pd.DataFrame, gt: pd.DataFrame, m: dict, out: str):
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("[evaluate] plotly not installed — skipping visualization.")
        print("           pip install plotly")
        return

    N = m["n_points"]
    t = traj.iloc[:N]
    g = gt.iloc[:N]

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=t.x, y=t.y, z=t.z,
        mode="lines",
        name="OpenVINS Estimate",
        line=dict(color="#00b4d8", width=3)
    ))

    fig.add_trace(go.Scatter3d(
        x=g.x, y=g.y, z=g.z,
        mode="lines",
        name="Ground Truth",
        line=dict(color="#f77f00", width=3, dash="dash")
    ))

    fig.add_trace(go.Scatter3d(
        x=[g.x.iloc[0]], y=[g.y.iloc[0]], z=[g.z.iloc[0]],
        mode="markers",
        name="Start",
        marker=dict(color="green", size=8, symbol="circle")
    ))

    fig.add_trace(go.Scatter3d(
        x=[g.x.iloc[-1]], y=[g.y.iloc[-1]], z=[g.z.iloc[-1]],
        mode="markers",
        name="End",
        marker=dict(color="red", size=8, symbol="square")
    ))

    fig.update_layout(
        title=dict(
            text=(
                f"OpenVINS: Estimated vs Ground Truth Trajectory<br>"
                f"<sup>ATE RMSE: {m['ate_rmse']:.4f} m &nbsp;|&nbsp; "
                f"Relative Error: {m['rel_error_pct']:.4f}% &nbsp;|&nbsp; "
                f"Length: {m['traj_length_m']:.2f} m</sup>"
            ),
            font=dict(size=14)
        ),
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data"
        ),
        legend=dict(x=0.01, y=0.99),
        height=700,
        margin=dict(l=0, r=0, t=80, b=0)
    )

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"[evaluate] Visualization saved → {out}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print(f"[evaluate] Loading trajectory : {args.traj}")
    print(f"[evaluate] Loading ground truth: {args.gt}")

    traj = load_trajectory(args.traj)
    gt   = load_trajectory(args.gt)

    m = compute_ate(traj, gt)
    print_metrics(m)
    save_metrics(m)

    if not args.no_plot:
        plot_trajectory(traj, gt, m, args.out)

    print("[evaluate] Done.")


if __name__ == "__main__":
    main()
