"""Regenerate docs/img/crossover.png: measured QAE oracle calls vs classical MC samples.

Runs the real (noisy, seeded) iterative amplitude estimation for the README's demo call at
a grid of target accuracies, so the quantum curve is what IAE actually spends, not the
theoretical M(eps) model. The simulations take about 2 hours, so results are cached in
docs/img/crossover.csv and the figure is redrawn from that cache.

Usage:
    python -u scripts/crossover_figure.py           # plot from the cache (seconds)
    python -u scripts/crossover_figure.py --rerun   # rerun all simulations (~2 h)
"""

import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from qrace import AnalysisTarget, NoiseProfile, OptionSpec, QiskitBackend  # noqa: E402
from qrace.classical import discounted_payoff_std  # noqa: E402
from qrace.crossover import compute  # noqa: E402
from qrace.pricing import build_problem  # noqa: E402

IMG = Path(__file__).resolve().parent.parent / "docs" / "img"
OUT, CACHE = IMG / "crossover.png", IMG / "crossover.csv"
EPSILONS = [2.0, 1.0, 0.5, 0.25, 0.1, 0.05]
CONFIDENCE = 0.95
BLUE, ORANGE, INK = "#2a78d6", "#eb6834", "#1f1f1e"
OPTION = OptionSpec(
    kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)


def simulate() -> None:
    """Run noisy IAE at every epsilon and write the cache."""
    noise = NoiseProfile(kind="depolarizing", two_qubit_error=0.001)
    backend = QiskitBackend(seed=7)
    pricing = build_problem(OPTION)
    sigma = discounted_payoff_std(OPTION)
    IMG.mkdir(parents=True, exist_ok=True)
    with CACHE.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epsilon", "qae_oracle_calls", "mc_samples"])
        for eps in EPSILONS:
            target = AnalysisTarget(target_abs_error=eps, confidence=CONFIDENCE)
            calls = backend.run_estimation(pricing, noise, target).oracle_calls
            samples = compute(sigma, target).classical_mc_samples
            writer.writerow([eps, calls, samples])
            f.flush()
            print(f"eps={eps:<5}  QAE oracle calls={calls:>7}  MC samples={samples:>7}")


def plot() -> None:
    with CACHE.open() as f:
        rows = list(csv.DictReader(f))
    eps = [float(r["epsilon"]) for r in rows]
    quantum = [int(r["qae_oracle_calls"]) for r in rows]
    if any(q < int(r["mc_samples"]) for q, r in zip(quantum, rows, strict=True)):
        # shortcut: caption below assumes no crossover; rewrite it if a rerun finds one
        raise RuntimeError("cache now shows a crossover; update the figure caption")

    sigma = discounted_payoff_std(OPTION)
    dense = np.logspace(math.log10(min(eps)), math.log10(max(eps)), 100)
    n_dense = [
        compute(sigma, AnalysisTarget(target_abs_error=float(e))).classical_mc_samples
        for e in dense
    ]

    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=150)
    ax.loglog(dense, n_dense, color=BLUE, lw=2, label="classical MC samples N(ε)")
    ax.loglog(
        eps, quantum, color=ORANGE, lw=2, marker="o", ms=7, label="QAE oracle calls, measured"
    )
    ax.invert_xaxis()  # tighter accuracy to the right
    ax.set_xlabel("target absolute price error ε (tighter →)", color=INK)
    ax.set_ylabel("queries / samples", color=INK)
    ax.set_title(
        f"Demo call, 0.1% depolarising noise: no crossover for ε ≥ {min(eps):g}",
        color=INK,
        fontsize=10,
        loc="left",
    )
    ax.grid(True, which="major", color="#e6e5e0", lw=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    if "--rerun" in sys.argv or not CACHE.exists():
        simulate()
    plot()
