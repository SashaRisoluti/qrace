# qora — Roadmap (post-v0.1)

Deliberately deferred from v0.1 to keep the first release tight (see DECISIONS.md). Order is
indicative, not committed.

## v0.2 — interpretability & risk depth
- **Native Greeks** (delta, gamma, vega, rho, theta) as the pricing-native sensitivity / interpretability
  surface — the correct answer to "explain the price", distinct from SHAP.
- **SHAP surrogate "advantage predictor"**: run many simulations, collect features
  (option type, moneyness, maturity, vol, target accuracy, qubit budget, noise level, distribution
  type) → targets (quantum-advantage yes/no, estimated error, resources); train a light gradient-boosted
  model that predicts the reality-check *without* re-running the heavy simulation; use **SHAP** to explain
  the drivers. Reuses the report-mode grid as training data. This is where SHAP legitimately belongs.
- **Risk-first API**: VaR / CVaR / spectral risk measures as first-class outputs over QAE, calibrated
  to market data.

## v0.3 — realism
- **Empirical / calibrated distribution loaders**: beyond analytic log-normal — empirical, mixture, and
  qGAN-trained loaders calibrated to real market data, with fidelity/cost benchmarks.
- **Path-dependent options**: Asian, barrier, American.
- **Real-hardware execution** via IBM Runtime (behind the same `Backend` seam), with credible
  hardware-noise error bars.
- **PennyLane backend** — implement the `Backend` seam a second time. Only build this once a genuine
  second backend is needed (YAGNI until then).

## v0.4 — surfaces
- **taipy dashboard** for report mode (interactive grids/plots). Depends on the report-mode core.
- **Optional Claude explainer** (`pip install qora[llm]`) — *pending user decision* (see DECISIONS.md
  D7). Turns the structured `Verdict` into a plain-English recommendation. Constraints if built:
  - Official `anthropic` Python SDK (not raw HTTP).
  - Default model `claude-opus-4-8`, adaptive thinking.
  - Structured `Verdict` in → narrative out (optionally `messages.parse` for structured
    `recommendation` / `confidence` fields).
  - **Optional dependency**: core stays LLM-free and installable without an API key.
- **Agentic test-case designer**: an agent that proposes derivative scenarios to benchmark — the point
  where `lastmile-ai/mcp-agent` or `datapizza-labs/datapizza-ai` (from the starred corpus) would enter.

## Explicitly out of scope (unless the project pivots)
- Becoming a general-purpose quantum finance framework (that is Qiskit Finance's territory).
- Portfolio optimization (QAOA/VQE) as a primary feature.
