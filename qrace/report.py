"""Report mode: grid of cases x noise levels -> pandas table + matplotlib plot + CLI."""

import argparse
from dataclasses import dataclass

import pandas as pd
from matplotlib.figure import Figure

from qrace.advisor import analyze
from qrace.backend import Backend, QiskitBackend
from qrace.spec import AnalysisTarget, NoiseProfile, OptionSpec

EXPECTED_COLUMNS = (
    "kind",
    "spot",
    "strike",
    "maturity",
    "volatility",
    "target_abs_error",
    "noise",
    "logical_qubits",
    "circuit_depth",
    "two_qubit_gates",
    "required_two_qubit_fidelity",
    "noise_aware_estimate",
    "noise_aware_error",
    "classical_reference",
    "quantum_oracle_calls",
    "classical_mc_samples",
    "quantum_wins_in_queries",
    "quantum_advantageous",
)


def _noise_label(noise: NoiseProfile) -> str:
    if noise.kind == "depolarizing":
        return f"depolarizing({noise.two_qubit_error})"
    if noise.kind == "fake_backend":
        return f"fake_backend({noise.fake_backend_name})"
    return "ideal"


@dataclass
class ReportResult:
    table: pd.DataFrame

    def figure(self) -> Figure:
        """Noise-aware estimates with error bars against the classical reference."""
        fig = Figure(figsize=(8, 4.5))
        ax = fig.add_subplot()
        x = range(len(self.table))
        ax.errorbar(
            x,
            self.table["noise_aware_estimate"],
            yerr=self.table["noise_aware_error"],
            fmt="o",
            capsize=4,
            label="QAE estimate (noise-aware)",
        )
        ax.plot(x, self.table["classical_reference"], "x", label="classical reference")
        labels = [f"{row.kind}@{row.strike}\n{row.noise}" for row in self.table.itertuples()]
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylabel("discounted price")
        ax.legend()
        fig.tight_layout()
        return fig


def run_report(
    cases: list[tuple[OptionSpec, AnalysisTarget]],
    noise_levels: list[NoiseProfile],
    backend: Backend,
) -> ReportResult:
    """Run analyze() over the full grid; one table row per (case x noise level)."""
    rows = []
    for option, target in cases:
        for noise in noise_levels:
            verdict = analyze(option, target, backend, noise)
            rows.append(
                {
                    "kind": option.kind,
                    "spot": option.spot,
                    "strike": option.strike,
                    "maturity": option.maturity,
                    "volatility": option.volatility,
                    "target_abs_error": target.target_abs_error,
                    "noise": _noise_label(noise),
                    "logical_qubits": verdict.resource.logical_qubits,
                    "circuit_depth": verdict.resource.circuit_depth,
                    "two_qubit_gates": verdict.resource.two_qubit_gates,
                    "required_two_qubit_fidelity": verdict.required_two_qubit_fidelity,
                    "noise_aware_estimate": verdict.noise_aware_estimate,
                    "noise_aware_error": verdict.noise_aware_error,
                    "classical_reference": verdict.classical_reference,
                    "quantum_oracle_calls": verdict.crossover.quantum_oracle_calls,
                    "classical_mc_samples": verdict.crossover.classical_mc_samples,
                    "quantum_wins_in_queries": verdict.crossover.quantum_wins_in_queries,
                    "quantum_advantageous": verdict.quantum_advantageous,
                }
            )
    return ReportResult(table=pd.DataFrame(rows, columns=list(EXPECTED_COLUMNS)))


def _demo_grid() -> tuple[list[tuple[OptionSpec, AnalysisTarget]], list[NoiseProfile]]:
    call = OptionSpec(
        kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
    )
    put = OptionSpec(
        kind="european_put", spot=100.0, strike=95.0, maturity=1.0, volatility=0.2, rate=0.05
    )
    target = AnalysisTarget(target_abs_error=0.5)
    noise_levels = [
        NoiseProfile(kind="ideal"),
        NoiseProfile(kind="depolarizing", two_qubit_error=0.001),
    ]
    return [(call, target), (put, target)], noise_levels


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m qrace.report")
    parser.add_argument("--preset", choices=["demo"], default="demo")
    parser.add_argument("--out", default=None, help="write the table to this HTML file")
    args = parser.parse_args(argv)

    cases, noise_levels = _demo_grid()
    result = run_report(cases, noise_levels, QiskitBackend())
    if args.out:
        result.table.to_html(args.out, index=False)
        print(f"report written to {args.out}")
    else:
        print(result.table.to_string(index=False))


if __name__ == "__main__":
    main()
