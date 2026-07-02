# qrace — Quantum Risk Advisor & Crossover Estimator

> **"Would a quantum computer actually help price *my* derivative — and if so, what would it cost?"**

`qrace` is an **honesty layer** on top of quantum amplitude estimation for option pricing.
Given a derivative spec, a target accuracy, and a hardware noise profile, it returns a
structured **verdict**: the quantum resources required, the two-qubit gate fidelity you would
need, noise-aware error bars from an actual noisy simulation, the break-even point against
classical Monte Carlo — and an exact **Shapley decomposition** of the error budget across the
four circuit stages, so you can see *where* the budget goes.

It does **not** try to be a new quantum pricing engine. It wraps Qiskit's
`IterativeAmplitudeEstimation` and adds the reality-check that no existing tool packages.

## Why

Qiskit Finance implements amplitude-estimation option pricing, but it is a research/demo
library focused on *price*. Noise-aware error bars, honest resource estimation, and the
"does quantum actually beat classical Monte Carlo for *my* case?" question live in papers
(Woerner–Egger, Stamatopoulos et al.), never in a tool. `qrace` packages exactly that gap.

## Install

```bash
pip install -e .          # from a clone; Python 3.11+
pip install -e .[dev]     # + pytest, ruff, mypy
```

Dependency versions are pinned exactly — the Qiskit ecosystem moves fast and module paths
drift between releases (verified against `qiskit==2.4.2`, `qiskit-algorithms==0.4.0`,
`qiskit-finance==0.4.1`, `qiskit-aer==0.17.2`).

## Quickstart

```python
from qrace import AnalysisTarget, NoiseProfile, OptionSpec, QiskitBackend, analyze

option = OptionSpec(kind="european_call", spot=100.0, strike=105.0,
                    maturity=1.0, volatility=0.2, rate=0.05)
target = AnalysisTarget(target_abs_error=0.5, confidence=0.95)
noise = NoiseProfile(kind="depolarizing", two_qubit_error=0.001)

verdict = analyze(option, target, QiskitBackend(seed=7), noise)
```

A real run of the above (seeded, reproducible):

```text
resource:                     11 qubits, depth 381, 192 two-qubit gates
required_two_qubit_fidelity:  0.999983          # what the target accuracy demands
noise_aware_estimate:         11.85 +/- 0.35    # what a noisy device actually returns
classical_reference:          8.02              # FinancePy Black-Scholes ground truth
crossover:                    12288 quantum oracle calls vs 2622 classical MC samples
shapley error budget:         loading -0.12 | payoff +0.38 | qae_iters -0.01 | decoherence +3.58
quantum_advantageous:         False
```

The verdict is blunt: at a realistic two-qubit error rate of 10⁻³, decoherence owns
3.58 of the 3.83 total error budget, the fidelity required (0.999983) exceeds anything
deployed today, and at this target accuracy classical Monte Carlo needs *fewer* samples
than the quantum algorithm needs oracle calls. Quantum does not help here — and now you
know why, stage by stage.

## What's in a `Verdict`

| Field | Meaning |
|---|---|
| `resource` | logical qubits, transpiled depth, two-qubit gates, T-count, ancilla |
| `required_two_qubit_fidelity` | per-gate fidelity needed to keep total noise inside the accuracy budget |
| `noise_aware_estimate` / `noise_aware_error` | price and CI half-width from a real noisy Aer simulation |
| `classical_reference` | FinancePy analytic (Black–Scholes) price |
| `crossover` | quantum oracle calls M(ε) vs classical MC samples N(ε) = ⌈(zσ/ε)²⌉, break-even ε |
| `shapley` | exact Shapley attribution of the error budget over `{loading, payoff, qae_iters, decoherence}` |
| `quantum_advantageous` | `True` only if quantum wins in queries **and** the required fidelity is plausibly achievable |

### The Shapley budget (headline feature)

The four pipeline stages are treated as players in a cooperative game. Each stage's
signed deviation is measured separately (truncation/discretization of the log-normal
model, payoff-encoding approximation, amplitude-estimation statistics, decoherence),
and a coalition's cost is the absolute value of its summed deviations — so biases that
*cancel* are attributed honestly. With 4 players the 2⁴ coalitions are enumerated
exactly; efficiency, null-player, and symmetry hold by construction (and are tested).

## When quantum does NOT help

Honesty layer, so let's be honest:

- **Loose accuracy targets.** Classical MC needs N(ε) = (zσ/ε)² samples; amplitude
  estimation needs M(ε) ∝ 1/ε oracle calls. The quadratic advantage only bites at *tight*
  ε. At ε = 0.5 on the option above, classical wins outright (2.6k samples vs 12.3k calls).
- **Any present-day noise level.** The required two-qubit fidelity scales like
  (1−ε)^(1/gates). A ~200-two-qubit-gate circuit at useful accuracy demands 99.998%+ —
  beyond today's hardware. The depolarizing example above is *optimistic* and still fails.
- **Oracle calls ≠ wall-clock.** Even where M(ε) < N(ε), a classical sample is nanoseconds;
  a coherent oracle call is not. Query-count crossover is a *necessary*, nowhere near
  *sufficient*, condition — which is why `quantum_advantageous` also gates on fidelity.
- **Cheap classical baselines.** European vanilla options have closed-form prices. QAE for
  them is a benchmark, not a use case; the interesting question is what the same pipeline
  costs for payoffs where classical pricing is genuinely expensive.

## Report mode

Compare a grid of cases × noise levels:

```python
from qrace import run_report
result = run_report(cases, noise_levels, QiskitBackend())
result.table     # pandas DataFrame, one row per (case, noise)
result.figure()  # matplotlib: estimates + error bars vs classical reference
```

or from the command line:

```bash
python -m qrace.report --preset demo --out report.html
```

## Notebooks

- [notebooks/01_quickstart.ipynb](notebooks/01_quickstart.ipynb) — reality-check on one European option.
- [notebooks/02_report_and_shapley.ipynb](notebooks/02_report_and_shapley.ipynb) — comparative report, Shapley budget, crossover plot.

## Non-goals (v0.1)

- Not a new quantum pricing engine — it wraps `IterativeAmplitudeEstimation`.
- No real-hardware execution (simulators + fake-backend noise models only).
- No SHAP surrogate, no Greeks, no LLM explainer.
- No empirical / qGAN distribution loaders (analytic log-normal only).
- No VaR/CVaR API, no portfolio optimization, no path-dependent options.

All deliberately deferred — see [docs/ROADMAP.md](docs/ROADMAP.md) and
[docs/DECISIONS.md](docs/DECISIONS.md) for why.

## Architecture

```
spec.py       frozen inputs: OptionSpec, AnalysisTarget, NoiseProfile
pricing.py    wraps qiskit-finance: log-normal model + payoff encoding -> QAE problem
backend.py    thin Backend seam (transpile_stats / run_estimation / noise_model), Qiskit-only
classical.py  FinancePy analytic reference + seeded Monte Carlo + N(eps)
resources.py  transpiled-circuit resource counts + required fidelity model
crossover.py  quantum-vs-classical query costs, break-even
shapley.py    exact Shapley over the 4 stage "players"
advisor.py    orchestrates everything -> Verdict
report.py     grid runner: pandas table + matplotlib figure + CLI
```

Development: strict TDD (every feature landed as failing test → minimal implementation),
`ruff` + `mypy --strict` clean, deterministic seeds everywhere randomness appears.

```bash
pytest && ruff check . && mypy qrace
```

## Acknowledgements

Built on [Qiskit](https://www.ibm.com/quantum/qiskit) (Finance/Algorithms/Aer) and
[FinancePy](https://github.com/domokane/FinancePy). Methodology informed by the
quantum-finance literature on amplitude-estimation option pricing and its noise limits.

## License

MIT
