# qora — Implementation Plan

> **For the implementing session:** build strictly test-first. Each task = write the failing test →
> run it (confirm it fails) → write the minimal implementation → run (confirm pass) → commit.
> Keep changes surgical and simple (see the Karpathy guidelines note in KICKOFF_PROMPT.md). Follow
> the phases in order; each phase leaves the package importable and the suite green.

**Goal:** a pip-installable Python library that answers "would quantum help price/risk *my*
derivative, and at what cost?" — resource estimate, required fidelity, noise-aware error bars,
classical-MC crossover, and an exact Shapley decomposition of the error/resource budget.

**Architecture:** wrap Qiskit `IterativeAmplitudeEstimation` behind a thin `Backend` seam; add the
honesty layer (resources, crossover, Shapley) on top; FinancePy as the classical ground truth.

**Tech stack:** Python 3.11+, qiskit, qiskit-aer, qiskit-algorithms, qiskit-finance, financepy,
numpy, pandas, matplotlib; dev: pytest, ruff, mypy; CI: GitHub Actions.

---

## Phase 0 — Scaffold

- [ ] Create the project layout:
      `qora/__init__.py`, `qora/` modules (empty stubs), `tests/`, `pyproject.toml`,
      `README.md`, `LICENSE` (MIT), `.gitignore`, `.github/workflows/ci.yml`, `docs/` (move these
      handoff docs here).
- [ ] `pyproject.toml`: hatchling backend, project metadata, **pinned** runtime deps, dev extras
      (`pytest`, `ruff`, `mypy`), `python_requires = ">=3.11"`.
- [ ] `git init`; first commit `chore: scaffold qora package`.
- [ ] Trivial test `tests/test_smoke.py::test_import` → `import qora` works. Run, commit.
- [ ] CI workflow: install → `ruff check` → `mypy qora` → `pytest`. Commit.

## Phase 1 — Specs & verdict dataclasses

- [ ] `tests/test_spec.py`: constructing `OptionSpec` / `AnalysisTarget` / `NoiseProfile` with valid
      values works; invalid values (negative maturity, vol ≤ 0, confidence ∉ (0,1)) raise
      `ValueError`.
- [ ] Implement `qora/spec.py` (frozen dataclasses + `__post_init__` validation). Run, commit.
- [ ] `tests/test_verdict.py`: `Verdict.to_dict()` round-trips the nested dataclasses to a plain
      dict; keys stable.
- [ ] Implement `qora/verdict.py`. Run, commit.

## Phase 2 — Classical ground truth

- [ ] `tests/test_classical.py`:
      - `reference_price(call)` matches the Black–Scholes analytic value from FinancePy within
        `1e-9` for a known fixture.
      - `mc_samples_for(target)` returns a positive int and is **monotone decreasing** as
        `target_abs_error` grows.
      - `monte_carlo_price(option, samples, seed)` converges toward the analytic price as `samples`
        increases (loose tolerance).
- [ ] Implement `qora/classical.py` (FinancePy wrapper + seeded classical MC + `N(ε)` formula). Run,
      commit.

## Phase 3 — Backend seam & pricing (wrap Qiskit IAE)

> Verify the current `qiskit-finance` / `qiskit-algorithms` API against the installed versions
> before writing this — module paths drift. Pin versions.

- [ ] `tests/test_pricing.py`: `build_problem(european_call)` returns an object exposing the
      estimation problem and a circuit; the circuit has the expected number of qubits for the
      configured discretization.
- [ ] Implement `qora/pricing.py`: log-normal `LogNormalDistribution` uncertainty model + European
      payoff encoding → amplitude-estimation problem + circuit. Run, commit.
- [ ] `tests/test_backend.py`:
      - `QiskitBackend().transpile_stats(circuit)` returns a `ResourceEstimate` with positive
        qubit / depth / 2q-gate counts.
      - `QiskitBackend().run_estimation(problem, NoiseProfile("ideal"), target)` on an ideal
        simulator yields an estimate within tolerance of the FinancePy analytic price.
- [ ] Implement `qora/backend.py` (`Backend` protocol + `QiskitBackend` using Aer, `transpile`, and
      `IterativeAmplitudeEstimation`; `noise_model()` builds a depolarizing model or loads a
      FakeBackend). Run, commit.

## Phase 4 — Resource estimation & required fidelity

- [ ] `tests/test_resources.py`:
      - `estimate_from(transpiled)` extracts qubits / depth / 2q-gates / T-count / ancilla.
      - `required_two_qubit_fidelity(depth, target_error)` is in `(0, 1]`, and **increases toward 1**
        as either `depth` grows or `target_error` shrinks.
- [ ] Implement `qora/resources.py`. Run, commit.

## Phase 5 — Crossover (pure numerics)

- [ ] `tests/test_crossover.py`:
      - `compute(sigma, target, confidence)` returns a `Crossover` with positive
        `classical_mc_samples` and `quantum_oracle_calls`.
      - `classical_mc_samples` is **monotone decreasing** in `target_abs_error`.
      - `breakeven_error` is finite and positive.
- [ ] Implement `qora/crossover.py`. Run, commit.

## Phase 6 — Shapley budget decomposition

- [ ] `tests/test_shapley.py`, using a synthetic additive `budget_fn` and a non-additive one:
      - **Efficiency**: `sum(contributions.values()) ≈ total` (tolerance `1e-9`).
      - **Null player**: a stage that never changes the budget gets contribution ≈ 0.
      - **Symmetry**: two interchangeable stages get equal contributions.
      - Exactly 4 keys `{loading, payoff, qae_iters, decoherence}`.
- [ ] Implement `qora/shapley.py`: exact Shapley over 2⁴ coalitions of an injected
      `budget_fn(coalition: frozenset[str]) -> float`. Run, commit.

## Phase 7 — Advisor orchestration

- [ ] `tests/test_advisor.py` (integration, ideal backend):
      - `analyze(call, target, QiskitBackend(), NoiseProfile("ideal"))` returns a `Verdict`.
      - `verdict.noise_aware_estimate` is within tolerance of `verdict.classical_reference`.
      - `verdict.shapley` satisfies efficiency.
      - `verdict.quantum_advantageous` is a bool consistent with the crossover + required fidelity.
- [ ] Implement `qora/advisor.py` wiring the pipeline (pricing → transpile_stats → resources →
      run_estimation → classical → crossover → shapley → Verdict). Run, commit.

## Phase 8 — Report mode (absorbs the benchmark-suite idea)

- [ ] `tests/test_report.py`:
      - `run_report(cases, noise_levels, backend)` returns a result exposing a pandas DataFrame with
        one row per (case × noise) and the expected columns.
      - Snapshot the DataFrame **structure** (columns / row count), not float values.
      - A tiny grid renders a matplotlib figure without raising.
- [ ] Implement `qora/report.py` + `python -m qora.report` CLI (`--preset demo`, `--out`). Run,
      commit.

## Phase 9 — Docs, notebooks, polish

- [ ] `README.md`: what it is, the gap it fills, quickstart, and an honest
      **"When quantum does NOT help"** section. Badges, install, minimal example.
- [ ] `notebooks/01_quickstart.ipynb`: reality-check on one European option.
- [ ] `notebooks/02_report_and_shapley.ipynb`: comparative report + Shapley budget + crossover plot.
- [ ] Final pass: `ruff check`, `ruff format`, `mypy qora`, full `pytest` green. Tag `v0.1.0`.

---

## Self-review checklist (run before declaring done)

- [ ] Every success criterion in DESIGN.md §6 maps to a passing test.
- [ ] No placeholders / TODOs left in shipped code.
- [ ] Method / field names match DESIGN.md §5 exactly (e.g. `two_qubit_gates`, `qae_iters`,
      `quantum_advantageous`).
- [ ] `README.md` includes the honest non-goals and the "when quantum does NOT help" section.
- [ ] The `Backend` seam is thin (no speculative multi-backend framework) — YAGNI respected.
