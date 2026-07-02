"""Orchestrator: analyze(option, target, backend, noise) -> Verdict."""

import numpy as np

from qrace.backend import Backend
from qrace.classical import discounted_payoff_std, reference_price
from qrace.crossover import compute as compute_crossover
from qrace.pricing import PricingProblem, build_problem, exact_price
from qrace.resources import required_two_qubit_fidelity
from qrace.shapley import decompose
from qrace.spec import AnalysisTarget, NoiseProfile, OptionSpec
from qrace.verdict import Verdict

# Optimistic present-day two-qubit gate fidelity envelope; a verdict is only
# "advantageous" if the required fidelity is at or below this.
ACHIEVABLE_TWO_QUBIT_FIDELITY = 0.999

_IDEAL = NoiseProfile(kind="ideal")


def analyze(
    option: OptionSpec,
    target: AnalysisTarget,
    backend: Backend,
    noise: NoiseProfile,
) -> Verdict:
    pricing = build_problem(option)

    resource = backend.transpile_stats(pricing.circuit, pricing.num_state_qubits)
    # Fidelity compounds per two-qubit gate; budget is the target error in amplitude space.
    sensitivity = pricing.amplitude_sensitivity()
    amplitude_budget = target.target_abs_error / sensitivity if sensitivity > 0 else 0.5
    required_fidelity = required_two_qubit_fidelity(
        depth=resource.two_qubit_gates, target_error=amplitude_budget
    )

    ideal_result = backend.run_estimation(pricing, _IDEAL, target)
    noisy_result = (
        ideal_result if noise.kind == "ideal" else backend.run_estimation(pricing, noise, target)
    )

    analytic = reference_price(option)
    sigma = discounted_payoff_std(option)
    crossover = compute_crossover(sigma, target, measured_oracle_calls=noisy_result.oracle_calls)

    # Signed per-stage deviations of the final estimate from the analytic truth. A
    # coalition's budget is |sum of its members' deviations|, so cancelling biases
    # are attributed honestly and efficiency holds by construction.
    truncated = _discretized_truth(pricing, option)
    encoded = exact_price(pricing)
    deltas = {
        "loading": truncated - analytic,
        "payoff": encoded - truncated,
        "qae_iters": ideal_result.estimate - encoded,
        "decoherence": noisy_result.estimate - ideal_result.estimate,
    }
    shapley = decompose(lambda coalition: abs(sum(deltas[s] for s in coalition)))

    return Verdict(
        resource=resource,
        required_two_qubit_fidelity=required_fidelity,
        noise_aware_estimate=noisy_result.estimate,
        noise_aware_error=noisy_result.error,
        classical_reference=analytic,
        crossover=crossover,
        shapley=shapley,
        quantum_advantageous=(
            crossover.quantum_wins_in_queries
            and required_fidelity <= ACHIEVABLE_TWO_QUBIT_FIDELITY
        ),
    )


def _discretized_truth(pricing: PricingProblem, option: OptionSpec) -> float:
    """Discounted expected payoff of the truncated, discretized distribution."""
    if option.kind == "european_call":
        payoff = np.maximum(pricing.grid - option.strike, 0.0)
    else:
        payoff = np.maximum(option.strike - pricing.grid, 0.0)
    return float(np.sum(pricing.probabilities * payoff)) * pricing.discount
