from qrace.pricing import build_problem
from qrace.spec import OptionSpec

CALL = OptionSpec(
    kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)
PUT = OptionSpec(
    kind="european_put", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)


def test_build_problem_exposes_problem_and_circuit() -> None:
    pricing = build_problem(CALL, num_state_qubits=3)
    assert pricing.problem.state_preparation is pricing.circuit
    assert pricing.num_state_qubits == 3


def test_circuit_qubits_match_discretization() -> None:
    # LinearAmplitudeFunction payoff: n state + (n - 1) comparator ancilla + 1 comparator
    # + 1 objective = 2n + 1 qubits
    for n in (3, 5):
        pricing = build_problem(CALL, num_state_qubits=n)
        assert pricing.circuit.num_qubits == 2 * n + 1
        assert pricing.problem.objective_qubits == [n]


def test_put_problem_builds_and_post_processes() -> None:
    pricing = build_problem(PUT, num_state_qubits=3)
    assert pricing.circuit.num_qubits == 7
    # post-processing of a mid-range amplitude gives a finite discounted price
    price = pricing.interpret_amplitude(0.5)
    assert price >= 0.0


def test_amplitude_sensitivity_positive_for_call() -> None:
    pricing = build_problem(CALL, num_state_qubits=3)
    assert pricing.amplitude_sensitivity() > 0.0
