"""Result dataclasses: ResourceEstimate, Crossover, ShapleyBudget, Verdict."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ResourceEstimate:
    logical_qubits: int
    circuit_depth: int
    two_qubit_gates: int
    t_count: int
    ancilla: int


@dataclass
class Crossover:
    quantum_oracle_calls: int  # M(eps) from IAE at target eps, confidence
    classical_mc_samples: int  # N(eps) = ceil((z * sigma / eps) ** 2)
    quantum_wins_in_queries: bool  # M < N
    breakeven_error: float  # eps at which query costs are equal


@dataclass
class ShapleyBudget:
    contributions: dict[str, float]  # keys: loading, payoff, qae_iters, decoherence
    total: float
    # invariant (tested): sum(contributions.values()) == total (efficiency)


@dataclass
class Verdict:
    resource: ResourceEstimate
    required_two_qubit_fidelity: float
    noise_aware_estimate: float
    noise_aware_error: float
    classical_reference: float
    crossover: Crossover
    shapley: ShapleyBudget
    quantum_advantageous: bool  # combines crossover + achievable fidelity

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
