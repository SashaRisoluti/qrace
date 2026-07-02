from qrace.backend import QiskitBackend
from qrace.classical import reference_price
from qrace.pricing import build_problem
from qrace.spec import AnalysisTarget, NoiseProfile, OptionSpec

CALL = OptionSpec(
    kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)

# Systematic bias of the n=5, +/-3 sigma, c=0.25 discretization (truncation + linear
# payoff approximation) dominates the QAE statistical error; see docs/DESIGN.md section 6.
IDEAL_TOLERANCE = 0.75


def test_transpile_stats_positive_counts() -> None:
    pricing = build_problem(CALL, num_state_qubits=3)
    estimate = QiskitBackend().transpile_stats(pricing.circuit)
    assert estimate.logical_qubits >= 7
    assert estimate.circuit_depth > 0
    assert estimate.two_qubit_gates > 0


def test_noise_model_kinds() -> None:
    backend = QiskitBackend()
    assert backend.noise_model(NoiseProfile(kind="ideal")) is None
    assert backend.noise_model(NoiseProfile(kind="depolarizing", two_qubit_error=0.01)) is not None
    assert (
        backend.noise_model(NoiseProfile(kind="fake_backend", fake_backend_name="FakeManilaV2"))
        is not None
    )


def test_ideal_estimation_matches_analytic_reference() -> None:
    pricing = build_problem(CALL, num_state_qubits=5)
    target = AnalysisTarget(target_abs_error=0.5, confidence=0.95)
    result = QiskitBackend(seed=7).run_estimation(pricing, NoiseProfile(kind="ideal"), target)
    assert abs(result.estimate - reference_price(CALL)) < IDEAL_TOLERANCE
    assert result.error > 0
    assert result.oracle_calls > 0
