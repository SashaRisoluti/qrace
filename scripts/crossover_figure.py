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
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import qrace.backend  # noqa: E402
from qrace import AnalysisTarget, NoiseProfile, OptionSpec, QiskitBackend  # noqa: E402
from qrace.classical import discounted_payoff_std, reference_price  # noqa: E402
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


class _RecordingIAE(qrace.backend.IterativeAmplitudeEstimation):  # type: ignore[misc]
    """Keeps the last raw IAE result so the Grover power schedule can be cached."""

    last: Any = None

    def estimate(self, estimation_problem: Any) -> Any:
        _RecordingIAE.last = super().estimate(estimation_problem)
        return _RecordingIAE.last


def simulate() -> None:
    """Run noisy IAE at every epsilon and write the cache."""
    # shortcut: script-local patch to read IAE internals; move into EstimationResult if reused
    qrace.backend.IterativeAmplitudeEstimation = _RecordingIAE  # type: ignore[misc]
    reference = reference_price(OPTION)
    noise = NoiseProfile(kind="depolarizing", two_qubit_error=0.001)
    backend = QiskitBackend(seed=7)
    pricing = build_problem(OPTION)
    sigma = discounted_payoff_std(OPTION)
    IMG.mkdir(parents=True, exist_ok=True)
    with CACHE.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "epsilon",
                "qae_oracle_calls",
                "mc_samples",
                "noisy_estimate",
                "ci_half_width",
                "abs_error_vs_reference",
                "iae_rounds",
                "max_grover_power",
            ]
        )
        for eps in EPSILONS:
            target = AnalysisTarget(target_abs_error=eps, confidence=CONFIDENCE)
            res = backend.run_estimation(pricing, noise, target)
            powers = _RecordingIAE.last.powers
            samples = compute(sigma, target).classical_mc_samples
            row = [
                eps,
                res.oracle_calls,
                samples,
                round(res.estimate, 4),
                round(res.error, 4),
                round(abs(res.estimate - reference), 4),
                len(powers) - 1,
                max(powers),
            ]
            writer.writerow(row)
            f.flush()
            print(dict(zip(["eps", "calls", "mc", "est", "ci", "abs_err", "rounds", "kmax"], row)))


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
    missed = [float(r["abs_error_vs_reference"]) > e for r, e in zip(rows, eps, strict=True)]
    ax.loglog(eps, quantum, color=ORANGE, lw=2, label="QAE oracle calls, measured")
    hit = [(e, q) for e, q, m in zip(eps, quantum, missed, strict=True) if not m]
    miss = [(e, q) for e, q, m in zip(eps, quantum, missed, strict=True) if m]
    if hit:
        ax.plot(*zip(*hit, strict=True), "o", color=ORANGE, ms=7, label="target accuracy reached")
    if miss:
        ax.plot(
            *zip(*miss, strict=True),
            "o",
            mfc="white",
            mec=ORANGE,
            mew=2,
            ms=8,
            label="target not reached (|estimate − BS| > ε)",
        )
    ax.invert_xaxis()  # tighter accuracy to the right
    ax.set_xlabel("target absolute price error ε (tighter →)", color=INK)
    ax.set_ylabel("queries / samples", color=INK)
    ax.set_title(
        f"Demo call, 0.1% depolarising noise: no crossover for ε ≥ {min(eps):g}\n"
        f"{sum(missed)} of {len(eps)} points miss the target accuracy",
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
