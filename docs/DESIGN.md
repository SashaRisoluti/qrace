# qora — Quantum Option Risk Advisor
## Design Specification (v0.1)

> Status: **approved design, ready to implement.** This document is the single source of
> truth for the first release. Decisions and their rationale are in [DECISIONS.md](DECISIONS.md);
> deferred features are in [ROADMAP.md](ROADMAP.md).

---

## 1. Summary

`qora` is a pip-installable Python library that answers one question honestly:

> **"Would a quantum computer actually help price / risk-assess *my* derivative — and if so, what would it cost?"**

Given a derivative spec, a target accuracy, and a hardware noise profile, `qora` returns a
structured **verdict**: the quantum resources required (logical qubits, transpiled depth,
two-qubit gate count), the two-qubit gate fidelity you would need to hit that accuracy,
noise-aware error bars from an actual noisy simulation, and the break-even point against
classical Monte Carlo. It does **not** try to be a new quantum pricing engine — it *wraps*
Qiskit's amplitude estimation and adds the honesty layer that no existing tool packages.

---

## 2. Problem & the gap being filled

The real goal is to fill a gap left open by current tools, not to re-implement what exists.

**What already exists (verified landscape):**
- **Qiskit Finance** implements amplitude-estimation option pricing, and is *not* deprecated.
  But it is a research/demo library: vanilla European/Asian options, analytic log-normal
  distribution loading only, focused on **price** (not risk), lightly maintained.
- **Quantum VaR / CVaR** exist only in papers (Woerner–Egger, Stamatopoulos, Laudagé–Turkalj
  2025 "Beyond CVaR"). No clean, installed, maintained library packages them.
- **Empirical / calibrated distribution loading** is a known open bottleneck (only analytic
  log-normal is standard; qGAN / tensor-network loaders are research).
- **Noise-aware error bars + honest resource estimation** live in papers, never in a tool.
  Nobody tells a practitioner: "for *your* option — this many qubits, this required fidelity,
  quantum beats classical yes/no."

**The gap `qora` fills:** the honest resource + noise **reality-check**. This is deliberately
the lowest-quantum-research-risk, highest-differentiation choice, and it plays to
data-science rigor (statistics, benchmarking, credible error bars) rather than to inventing
new quantum algorithms.

---

## 3. Scope

### In scope (v0.1)

- Python package, pip-installable, Python 3.11+.
- **Input**: derivative spec (European vanilla call/put), target accuracy, backend/noise profile.
- **Output** = a structured `Verdict`:
  - Resource estimate: logical qubits, transpiled depth, two-qubit-gate count, T-count, ancilla.
  - **Required two-qubit gate fidelity** to reach the target accuracy.
  - **Noise-aware error bar** from a real noisy Aer simulation (not just theory).
  - **Crossover vs classical Monte Carlo**: quantum oracle calls vs classical samples at equal
    target accuracy → break-even, plus the noise caveat that gates the practical win.
  - Classical ground-truth via **FinancePy**.
- **Shapley budget decomposition**: exact Shapley attribution of the total error/resource budget
  across the four pipeline stages `{loading, payoff, qae_iterations, decoherence}`. This is the
  headline interpretability feature.
- **Report mode**: a CLI / notebook helper that runs a grid of cases × noise levels and emits a
  comparison table (pandas) + plot (matplotlib).
- **Backend**: Qiskit-first, behind a **thin `Backend` seam** (2–3 methods), implemented only by
  Qiskit for now.

### Non-goals (v0.1) — state these explicitly in the README

- **Not** a new quantum pricing engine — it wraps Qiskit's `IterativeAmplitudeEstimation`, it
  does not re-implement it.
- **No** real-hardware execution (simulators + calibrated FakeBackends only). → roadmap.
- **No** SHAP surrogate predictor, **no** Greeks, **no** natural-language explainer. → roadmap.
- **No** empirical / qGAN distribution loaders (analytic log-normal only). → roadmap.
- **No** portfolio optimization; **no** VaR/CVaR as a primary API. The focus is the honesty
  layer, not new risk measures. → roadmap.
- **No** path-dependent options (Asian, barrier, American) in v0.1. → roadmap.

---

## 4. Architecture

One file = one responsibility. Small, focused, independently testable units.

| Module | Responsibility | Depends on |
|---|---|---|
| `qora/spec.py` | Frozen input dataclasses: `OptionSpec`, `AnalysisTarget`, `NoiseProfile` + validation | — |
| `qora/verdict.py` | Result dataclasses: `ResourceEstimate`, `Crossover`, `ShapleyBudget`, `Verdict` + `to_dict()` / pretty-print | — |
| `qora/backend.py` | Thin seam: `Backend` protocol (`transpile_stats`, `run_estimation`, `noise_model`) + `QiskitBackend` (Aer + FakeBackend) | qiskit, qiskit-aer |
| `qora/pricing.py` | **Wrap** Qiskit IAE: log-normal uncertainty model + European payoff encoding → estimate + circuit | qiskit-algorithms, qiskit-finance |
| `qora/classical.py` | Ground truth: FinancePy analytic price + classical Monte Carlo (+ samples-for-accuracy) | financepy, numpy |
| `qora/resources.py` | From a transpiled circuit: qubits / depth / 2q-gates / T-count; **required fidelity** = f(depth, error budget) | qiskit |
| `qora/crossover.py` | Quantum oracle calls vs classical MC samples at equal accuracy → break-even | numpy |
| `qora/shapley.py` | Exact Shapley over 4 stage "players" (2⁴ coalitions) via an injected `budget_fn(coalition)->value` | itertools |
| `qora/advisor.py` | Orchestrator: `analyze(option, target, backend, noise) -> Verdict` | all of the above |
| `qora/report.py` | Report mode: grid of cases → pandas table + matplotlib plot; `python -m qora.report` CLI | pandas, matplotlib |

### Data flow

```
OptionSpec + AnalysisTarget + NoiseProfile + Backend
        │
        ▼
  advisor.analyze():
    1. pricing.build_problem(option)         → amplitude-estimation problem + circuit
    2. backend.transpile_stats(circuit)      → resources.ResourceEstimate
    3. resources.required_fidelity(...)       → required 2q gate fidelity
    4. backend.run_estimation(problem, noise) → noise-aware estimate + error bar
    5. classical.reference_price(option)      → FinancePy ground truth
       classical.mc_samples_for(target)       → classical sample count
    6. crossover.compute(...)                 → Crossover (break-even, quantum_wins)
    7. shapley.decompose(budget_fn)           → ShapleyBudget (efficiency property holds)
        │
        ▼
     Verdict  ──►  report.run_report(...) for grids
```

### The `Backend` seam (deliberately thin — YAGNI)

Do **not** build a full pluggable multi-backend framework. v0.1 ships a single seam with a
handful of methods, implemented once by `QiskitBackend`. PennyLane (or a second backend) plugs
in *only when it actually exists*, not before.

```python
class Backend(Protocol):
    def transpile_stats(self, circuit) -> ResourceEstimate: ...
    def run_estimation(self, problem, noise: NoiseProfile, target: AnalysisTarget) -> EstimationResult: ...
    def noise_model(self, noise: NoiseProfile): ...   # returns an Aer NoiseModel or None
```

---

## 5. Public API (interface sketch)

Concrete shapes so the implementation has precise targets. Internals are left to TDD.

```python
# spec.py
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class OptionSpec:
    kind: Literal["european_call", "european_put"]
    spot: float
    strike: float
    maturity: float       # years
    volatility: float     # annualized
    rate: float           # risk-free rate

@dataclass(frozen=True)
class AnalysisTarget:
    target_abs_error: float    # desired absolute error on the discounted expected payoff
    confidence: float = 0.95

@dataclass(frozen=True)
class NoiseProfile:
    kind: Literal["ideal", "depolarizing", "fake_backend"]
    two_qubit_error: float | None = None      # for "depolarizing"
    fake_backend_name: str | None = None       # for "fake_backend", e.g. "FakeManilaV2"
```

```python
# verdict.py
@dataclass
class ResourceEstimate:
    logical_qubits: int
    circuit_depth: int
    two_qubit_gates: int
    t_count: int
    ancilla: int

@dataclass
class Crossover:
    quantum_oracle_calls: int      # M(ε) from IAE at target ε, confidence
    classical_mc_samples: int      # N(ε) = ceil((z * sigma / ε) ** 2)
    quantum_wins_in_queries: bool  # M < N
    breakeven_error: float         # ε at which query costs are equal

@dataclass
class ShapleyBudget:
    contributions: dict[str, float]   # keys: loading, payoff, qae_iters, decoherence
    total: float
    # invariant (tested): sum(contributions.values()) ≈ total  (efficiency)

@dataclass
class Verdict:
    resource: ResourceEstimate
    required_two_qubit_fidelity: float
    noise_aware_estimate: float
    noise_aware_error: float
    classical_reference: float
    crossover: Crossover
    shapley: ShapleyBudget
    quantum_advantageous: bool       # combines crossover + (achievable fidelity)
    def to_dict(self) -> dict: ...
```

```python
# advisor.py
def analyze(
    option: OptionSpec,
    target: AnalysisTarget,
    backend: Backend,
    noise: NoiseProfile,
) -> Verdict: ...
```

```python
# report.py
def run_report(
    cases: list[tuple[OptionSpec, AnalysisTarget]],
    noise_levels: list[NoiseProfile],
    backend: Backend,
) -> "ReportResult": ...
# CLI: python -m qora.report --preset demo --out report.html
```

### Core math (for the honesty layer)

- **Classical Monte Carlo** error ~ `σ/√N` ⇒ `N(ε) = ceil((z · σ / ε)²)`.
- **Quantum amplitude estimation** error ~ `1/M` (M oracle calls) ⇒ `M(ε) ∝ 1/ε` — the quadratic
  speedup in *query complexity*.
- **Crossover** compares `M(ε)` oracle calls against `N(ε)` samples at equal target ε. In pure
  query terms quantum wins for small ε; the **honest** verdict then gates this on whether the
  **required two-qubit fidelity** (derived from transpiled depth × per-gate error budget) is
  achievable on real/simulated hardware. `quantum_advantageous` is `True` only when quantum wins
  in queries **and** the required fidelity is within a plausible hardware envelope.

### Shapley budget (headline feature)

Four "players" = the four pipeline stages `{loading, payoff, qae_iters, decoherence}`. A
characteristic function `budget_fn(coalition: frozenset[str]) -> float` returns the value of the
chosen budget metric (default: total error; alternatives: circuit depth, 2q-gate count) when only
the stages in the coalition contribute their imperfection and the rest are ideal. With 4 players
there are 2⁴ = 16 coalitions → compute the **exact** Shapley value per stage. Guaranteed
properties to test: **efficiency** (contributions sum to the total), **null player**, **symmetry**.

---

## 6. Success criteria (verifiable — these are the definition of done)

1. `analyze(option, target, QiskitBackend(), NoiseProfile("ideal"))` returns a `Verdict`, and on
   an ideal simulator the QAE price is within tolerance of the FinancePy analytic price for a
   European call/put. → integration test with an explicit tolerance.
2. `crossover.compute(...)` returns numeric `quantum_oracle_calls` / `classical_mc_samples`, and
   `classical_mc_samples` is **monotone decreasing** in `target_abs_error`. → property test.
3. `shapley.decompose(...)` satisfies the **efficiency** property: `sum(contributions.values())`
   ≈ `total` within tolerance, across the 4 stages. → property test (plus null-player, symmetry).
4. `report.run_report(...)` produces a table + plot for a grid of cases without error. → smoke /
   snapshot test.

---

## 7. Dependencies & honest use of the starred repos

The library grew out of a review of ~100 starred GitHub repos. The **honest** finding: almost all
of them are LLM / agent / RAG projects with no bearing on quantum ML. **Only FinancePy is a genuine
dependency.** Do not force-fit other repos to "use them."

- **FinancePy** (`domokane/FinancePy`) → runtime dependency: classical analytic reference price
  (and Greeks, in v0.2).
- **Qiskit stack** (`qiskit`, `qiskit-aer`, `qiskit-algorithms`, `qiskit-finance`) → core (not from
  the starred corpus).
- Learning references only (README acknowledgements, not dependencies): `anthropics/courses`,
  `mlabonne/llm-course`, `patchy631/ai-engineering-hub`.
- `taipy` (dashboard) and `lastmile-ai/mcp-agent` / `datapizza-labs/datapizza-ai` (agentic
  test-case designer) are **roadmap only**.

> ⚠️ **API drift risk.** `qiskit-finance` and `qiskit-algorithms` move between versions
> (`EuropeanCallPricing`, `LogNormalDistribution`, `IterativeAmplitudeEstimation` have changed
> module paths historically). **Pin exact versions** in `pyproject.toml` and verify the current
> API against the installed package before writing `pricing.py`.

---

## 8. Testing strategy

- **pytest**, strict TDD (write the failing test first).
- Deterministic seeds everywhere randomness appears (Aer runs, classical MC).
- QAE-vs-analytic assertions are **tolerance-based**, not exact equality.
- `shapley` and `crossover` are pure numerics → fast, deterministic unit tests.
- `pricing` is the only module coupled to Qiskit → the `Backend` seam isolates it so the rest of
  the suite runs without a heavy quantum backend.
- `report` → snapshot test on the emitted table (structure, not floating-point exactness).

---

## 9. Packaging

- `pyproject.toml` (hatchling build backend).
- `ruff` (lint + format) + `mypy` (type check).
- GitHub Actions CI: install → ruff → mypy → pytest.
- MIT license.
- Python 3.11+.
- Optional extras group reserved for future `qora[llm]` (see ROADMAP) — **not** wired in v0.1.

### Deliverables

- `qora/` package + `tests/` mirror.
- Strong `README.md`, including an honest **"When quantum does NOT help"** section.
- Two notebooks: (1) quickstart reality-check on a European option; (2) comparative report with the
  Shapley budget + crossover.
- CI, license, `pyproject.toml`.
