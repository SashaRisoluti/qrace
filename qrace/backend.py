"""Thin Backend seam: protocol + QiskitBackend (Aer, IAE, noise models)."""

from dataclasses import dataclass
from typing import Any, Protocol

from qiskit import QuantumCircuit, transpile
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit_aer.primitives import SamplerV2
from qiskit_algorithms import IterativeAmplitudeEstimation
from qiskit.transpiler import generate_preset_pass_manager

from qrace.pricing import PricingProblem
from qrace.resources import estimate_from
from qrace.spec import AnalysisTarget, NoiseProfile
from qrace.verdict import ResourceEstimate

# Fully decomposed basis: Aer 0.17.2 segfaults on the raw `multiplexer` instruction
# that LogNormalDistribution's state preparation contains, so everything is lowered
# to one- and two-qubit basis gates before execution and resource counting.
BASIS_GATES = ["rz", "sx", "x", "cx"]

# Guardrails for the amplitude epsilon handed to IAE: below ~1e-4 the Grover powers
# make the (classically simulated) run intractable; 0.49 is IAE's validity limit.
_MIN_EPSILON = 1e-4
_MAX_EPSILON = 0.49


@dataclass
class EstimationResult:
    estimate: float  # discounted price, currency units
    error: float  # confidence-interval half-width, currency units
    oracle_calls: int  # quantum oracle queries used by IAE


class Backend(Protocol):
    def transpile_stats(self, circuit: QuantumCircuit) -> ResourceEstimate: ...

    def run_estimation(
        self, pricing: PricingProblem, noise: NoiseProfile, target: AnalysisTarget
    ) -> EstimationResult: ...

    def noise_model(self, noise: NoiseProfile) -> Any: ...


class QiskitBackend:
    """Aer-based implementation of the Backend seam (the only one in v0.1)."""

    def __init__(self, seed: int = 42, shots: int = 2048) -> None:
        self.seed = seed
        self.shots = shots

    def transpile_stats(
        self, circuit: QuantumCircuit, num_state_qubits: int | None = None
    ) -> ResourceEstimate:
        transpiled = transpile(circuit, basis_gates=BASIS_GATES, optimization_level=1)
        return estimate_from(transpiled, num_state_qubits=num_state_qubits)

    def noise_model(self, noise: NoiseProfile) -> NoiseModel | None:
        if noise.kind == "ideal":
            return None
        if noise.kind == "depolarizing":
            model = NoiseModel()
            assert noise.two_qubit_error is not None  # enforced by NoiseProfile validation
            model.add_all_qubit_quantum_error(
                depolarizing_error(noise.two_qubit_error, 2), ["cx"]
            )
            return model
        # fake_backend
        import qiskit_ibm_runtime.fake_provider as fake_provider

        backend_cls = getattr(fake_provider, str(noise.fake_backend_name), None)
        if backend_cls is None:
            raise ValueError(f"unknown fake backend: {noise.fake_backend_name}")
        return NoiseModel.from_backend(backend_cls())

    def run_estimation(
        self, pricing: PricingProblem, noise: NoiseProfile, target: AnalysisTarget
    ) -> EstimationResult:
        model = self.noise_model(noise)
        options = {"backend_options": {"noise_model": model}} if model is not None else None
        sampler = SamplerV2(seed=self.seed, default_shots=self.shots, options=options)

        sensitivity = pricing.amplitude_sensitivity()
        epsilon = target.target_abs_error / sensitivity if sensitivity > 0 else _MAX_EPSILON
        epsilon = min(max(epsilon, _MIN_EPSILON), _MAX_EPSILON)

        iae = IterativeAmplitudeEstimation(
            epsilon_target=epsilon,
            alpha=1 - target.confidence,
            sampler=sampler,
            transpiler=generate_preset_pass_manager(
                optimization_level=1, basis_gates=BASIS_GATES
            ),
        )
        result = iae.estimate(pricing.problem)
        low, high = result.confidence_interval_processed
        return EstimationResult(
            estimate=pricing.interpret_amplitude(float(result.estimation)),
            error=abs(high - low) / 2 * pricing.discount,
            oracle_calls=int(result.num_oracle_queries),
        )
