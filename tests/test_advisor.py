import pytest

from qrace.advisor import analyze
from qrace.backend import QiskitBackend
from qrace.spec import AnalysisTarget, NoiseProfile, OptionSpec
from qrace.verdict import Verdict

CALL = OptionSpec(
    kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)
TARGET = AnalysisTarget(target_abs_error=0.5, confidence=0.95)
IDEAL_TOLERANCE = 0.75  # systematic discretization/payoff bias, see test_backend.py


@pytest.fixture(scope="module")
def verdict() -> Verdict:
    return analyze(CALL, TARGET, QiskitBackend(seed=7), NoiseProfile(kind="ideal"))


def test_analyze_returns_verdict(verdict: Verdict) -> None:
    assert isinstance(verdict, Verdict)


def test_estimate_within_tolerance_of_reference(verdict: Verdict) -> None:
    assert abs(verdict.noise_aware_estimate - verdict.classical_reference) < IDEAL_TOLERANCE


def test_shapley_efficiency_holds(verdict: Verdict) -> None:
    assert (
        abs(sum(verdict.shapley.contributions.values()) - verdict.shapley.total) < 1e-9
    )


def test_quantum_advantageous_consistent(verdict: Verdict) -> None:
    assert isinstance(verdict.quantum_advantageous, bool)
    if verdict.quantum_advantageous:
        assert verdict.crossover.quantum_wins_in_queries
