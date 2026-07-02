"""Wrap Qiskit amplitude-estimation pricing: log-normal model + European payoff encoding.

Verified against qiskit==2.4.2, qiskit-algorithms==0.4.0, qiskit-finance==0.4.1.
"""

import math
from dataclasses import dataclass

from qiskit import QuantumCircuit
from qiskit.circuit.library import LinearAmplitudeFunction
from qiskit_algorithms import EstimationProblem
from qiskit_finance.circuit.library import LogNormalDistribution

from qrace.spec import OptionSpec

# qiskit 2.4.2's LogNormalDistribution isometry decomposition fails ("Input matrix is
# not unitary") for num_qubits >= 9 on this stack — keep discretizations at or below 7.
MAX_STATE_QUBITS = 7


@dataclass
class PricingProblem:
    """Amplitude-estimation problem for one option, plus interpretation helpers."""

    problem: EstimationProblem
    circuit: QuantumCircuit  # the A operator (state preparation)
    num_state_qubits: int
    discount: float  # exp(-r * T)

    def interpret_amplitude(self, amplitude: float) -> float:
        """Map a raw amplitude to a discounted price in currency units."""
        return float(self.problem.post_processing(amplitude)) * self.discount

    def amplitude_sensitivity(self) -> float:
        """|d(price)/d(amplitude)| around a = 0.5, for target-error -> epsilon mapping."""
        delta = 1e-4
        lo = self.interpret_amplitude(0.5 - delta)
        hi = self.interpret_amplitude(0.5 + delta)
        return abs(hi - lo) / (2 * delta)


def build_problem(
    option: OptionSpec,
    num_state_qubits: int = 5,
    rescaling_factor: float = 0.25,
    stddev_range: float = 3.0,
) -> PricingProblem:
    """Log-normal uncertainty model + piecewise-linear European payoff -> QAE problem."""
    if not 1 <= num_state_qubits <= MAX_STATE_QUBITS:
        raise ValueError(f"num_state_qubits must be in [1, {MAX_STATE_QUBITS}]")

    mu = math.log(option.spot) + (option.rate - 0.5 * option.volatility**2) * option.maturity
    sigma = option.volatility * math.sqrt(option.maturity)
    mean = math.exp(mu + sigma**2 / 2)
    std = math.sqrt(math.exp(sigma**2) - 1) * mean
    low = max(0.0, mean - stddev_range * std)
    high = mean + stddev_range * std

    uncertainty = LogNormalDistribution(
        num_state_qubits, mu=mu, sigma=sigma**2, bounds=(low, high)
    )

    strike = option.strike
    if option.kind == "european_call":
        breakpoints = [low, strike]
        slopes: list[float] = [0.0, 1.0]
        offsets: list[float] = [0.0, 0.0]
        f_max = high - strike
    else:  # european_put
        breakpoints = [low, strike]
        slopes = [-1.0, 0.0]
        offsets = [strike - low, 0.0]
        f_max = strike - low

    payoff = LinearAmplitudeFunction(
        num_state_qubits,
        slopes,
        offsets,
        domain=(low, high),
        image=(0.0, f_max),
        breakpoints=breakpoints,
        rescaling_factor=rescaling_factor,
    )

    circuit = QuantumCircuit(payoff.num_qubits)
    circuit.compose(uncertainty, range(uncertainty.num_qubits), inplace=True)
    circuit.compose(payoff, range(payoff.num_qubits), inplace=True)

    def post_processing(amplitude: float) -> float:
        return float(payoff.post_processing(amplitude))

    problem = EstimationProblem(
        state_preparation=circuit,
        objective_qubits=[num_state_qubits],
        post_processing=post_processing,
    )
    discount = math.exp(-option.rate * option.maturity)
    return PricingProblem(
        problem=problem, circuit=circuit, num_state_qubits=num_state_qubits, discount=discount
    )
