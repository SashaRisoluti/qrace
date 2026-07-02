# qora — Decision Log

Why the design is what it is. Read this before proposing changes — most alternatives were already
considered and rejected for stated reasons. Don't re-litigate settled decisions.

---

### D1 — Deliverable format: reusable library
Chosen over: portfolio showcase, deep technical demo, agentic project.
**Why:** a pip-installable tool with a clean API is the most durable, most useful, and most
maintainable artifact for an ML/AI + data-science portfolio.

### D2 — Domain: quantum option pricing / risk
Chosen over: quantum kernels for financial time series, quantum portfolio optimization, generic QML
toolkit.
**Why:** the user's starred repos lean heavily on quant finance (FinancePy, FinRL, nautilus_trader,
TradingAgents). But the **real** stated goal is to *fill a gap left open by current tools*, not to
re-implement Qiskit Finance.

### D3 — The gap: honest resource + noise reality-check
Chosen over: risk-first API (VaR/CVaR), empirical/calibrated distribution loaders, a combo of the
first two.
**Why:** verified landscape shows Qiskit Finance is price-focused / log-normal / lightly maintained;
quantum VaR/CVaR and noise-aware resource honesty exist only in papers. The reality-check
("does quantum help for *my* derivative, and at what cost?") is the lowest quantum-research-risk,
highest-differentiation gap, and it plays to data-science rigor rather than novel quantum algorithms.

### D4 — Framework: Qiskit-first behind a thin Backend seam
Chosen over: PennyLane-primary, backend-agnostic from day one.
**Why:** the reality-check needs realistic noise models (Aer, calibrated FakeBackends) and resource
estimation via transpilation — Qiskit's strengths. A full pluggable multi-backend framework for a
PennyLane backend that does not yet exist is speculative flexibility (**YAGNI**). v0.1 ships one thin
seam (`transpile_stats`, `run_estimation`, `noise_model`) implemented only by Qiskit; a second
backend plugs in when it actually exists.

### D5 — Interpretability: exact Shapley decomposition of the error/resource budget (core v0.1)
Chosen over: SHAP surrogate "advantage predictor", native Greeks, hooks-only.
**Why:** SHAP/LIME explain *supervised predictors* via feature attribution; the QAE engine is an
expected-value estimator, not a predictor, and the native interpretability of a pricer is already
the **Greeks** (price sensitivities). Putting SHAP where Greeks belong reinvents the wheel badly.
Instead, apply **Shapley values** (the theory behind SHAP) honestly to the *circuit stages* —
game-theoretic attribution of the total error / resource budget across
`{loading, payoff, qae_iters, decoherence}`. This is a genuine novelty, domain-appropriate, and
moderate scope. (The SHAP surrogate and native Greeks are deferred to the roadmap.)

### D6 — Approach A ("advisor engine that wraps IAE"), absorbing the benchmark suite as report mode
Chosen over: B (full quantum pricing/risk engine with honesty built in), C (standalone benchmark /
leaderboard).
**Why:** B overlaps with Qiskit Finance and is high-risk scope creep. C is a research artifact, not a
tool you import — so it is absorbed as a **report mode** feature inside A rather than a separate
project. A wraps `IterativeAmplitudeEstimation`; the novelty is the honesty layer, which does not
exist anywhere else.

### D7 — Claude / LLM explainer layer: parked in roadmap (undecided)
**Why:** v0.1 is deliberately LLM-free (a pure quantum/numerical library, installable without any API
key). A natural-language explainer that turns the structured `Verdict` into a plain-English
recommendation is a coherent fit for the "advisor" framing, but it is a scope addition and the user
had not committed to it at handoff time. If added later it must be an **optional dependency**
(`pip install qora[llm]`) using the official `anthropic` SDK, default model `claude-opus-4-8`,
adaptive thinking, with the core staying LLM-free. See ROADMAP.md.

### D8 — Honest use of the starred repos
**Why:** of ~100 starred repos, only **FinancePy** is a genuine dependency (classical reference
pricing). The rest are LLM/agent/RAG projects unrelated to quantum ML. The design does not force-fit
repos just to "use them"; other repos appear only as roadmap items or learning-reference
acknowledgements.
