# qrace — Kickoff Prompt for the Build Session

This file is the handoff. Open a **new Claude Code chat in the `qrace/` folder** and paste the prompt
in the box below. The design is already finalized in `docs/` — the new session implements it; it does
**not** re-run brainstorming.

---

## ▶️ Paste this into the new chat

> I'm building **qrace — Quantum Risk Advisor & Crossover Estimator**, a pip-installable Python library, in this
> folder. The design is **already finalized** — do not re-brainstorm the concept. Read these first
> and treat them as the source of truth:
>
> - `docs/DESIGN.md` — full specification (scope, architecture, module table, API sketch, success criteria)
> - `docs/PLAN.md` — the phased, test-first implementation plan (build in this order)
> - `docs/DECISIONS.md` — why each choice was made (don't re-litigate settled decisions)
> - `docs/ROADMAP.md` — deferred features (do NOT build these in v0.1)
>
> **What to do:**
> 1. Read all four docs.
> 2. Scaffold the package per `PLAN.md` Phase 0 and `git init`.
> 3. Implement **strictly test-first**, phase by phase (Phase 0 → 9). For every task: write the
>    failing test → run it and confirm it fails → write the minimal implementation → run and confirm
>    it passes → commit. Small, frequent commits.
> 4. Keep changes **surgical and simple** — no speculative abstractions, no features beyond the spec,
>    no error handling for impossible cases. The `Backend` seam stays thin (Qiskit only in v0.1).
> 5. Before writing `qrace/pricing.py` and `qrace/backend.py`, **verify the current `qiskit-finance`
>    and `qiskit-algorithms` API** against the installed versions — those module paths drift between
>    releases. Pin exact versions in `pyproject.toml`.
> 6. Stop and check with me at the end of each phase (leave the suite green and the package
>    importable at every phase boundary).
>
> **Definition of done** = the four success criteria in `DESIGN.md` §6 each map to a passing test,
> plus a strong `README.md` (with the honest "When quantum does NOT help" section) and the two
> notebooks.
>
> Start by reading the docs and confirming the plan back to me, then do Phase 0.

---

## Context for whoever runs the build session

**What qrace is:** an honesty layer on top of quantum amplitude estimation for option pricing. It tells
a practitioner, for *their* specific derivative + target accuracy + hardware noise profile, whether
quantum would actually help and what it would cost (qubits, transpiled depth, required two-qubit gate
fidelity, noise-aware error bars, and the break-even vs classical Monte Carlo) — plus an exact Shapley
decomposition of the error/resource budget across the four circuit stages. It **wraps** Qiskit's
`IterativeAmplitudeEstimation`; it does not re-implement it. FinancePy is the classical ground truth.

**Positioning:** portfolio-grade project for an ML/AI engineer + data scientist. The README and code
quality matter as much as the functionality. Fills a real gap (nobody packages the honest
resource+noise reality-check) — keep that framing front and center, and keep the non-goals explicit.

**Recommended skills / workflow for the build session:**
- `superpowers:test-driven-development` — the plan is written for strict TDD.
- `andrej-karpathy-skills:karpathy-guidelines` — surgical changes, simplicity first, verifiable goals.
- `superpowers:executing-plans` or `superpowers:subagent-driven-development` — to work through
  `docs/PLAN.md` task by task.
- `superpowers:verification-before-completion` — run the tests and show output before claiming done.
- (If Qiskit API questions arise, verify against the installed package rather than guessing.)

**Tech stack:** Python 3.11+ · qiskit, qiskit-aer, qiskit-algorithms, qiskit-finance, financepy, numpy,
pandas, matplotlib · dev: pytest, ruff, mypy · CI: GitHub Actions · MIT license.

**Environment notes:**
- Windows (PowerShell primary; a Bash tool is also available — each takes its own syntax).
- A C++ build toolchain may be needed for some quantum/scientific wheels; prefer prebuilt wheels and a
  fresh virtual environment (`python -m venv .venv`).
- Pin exact dependency versions — the Qiskit ecosystem moves fast.

**Do NOT in v0.1:** SHAP surrogate, native Greeks, natural-language / Claude explainer, empirical or
qGAN distribution loaders, path-dependent options, VaR/CVaR API, real-hardware execution, a second
backend, or a taipy dashboard. All of those are in `docs/ROADMAP.md`.

**Where the code goes:** build the Python package in this same folder (`qrace/` package + `tests/`
alongside the existing `docs/`). If you prefer a clean top level, the docs can move under the repo as
`docs/` — they already are.
