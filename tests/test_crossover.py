from qrace.crossover import compute
from qrace.spec import AnalysisTarget


def test_compute_returns_positive_counts() -> None:
    result = compute(sigma=13.0, target=AnalysisTarget(target_abs_error=0.01))
    assert result.classical_mc_samples > 0
    assert result.quantum_oracle_calls > 0


def test_classical_samples_monotone_decreasing_in_error() -> None:
    errors = [0.005, 0.01, 0.02, 0.05]
    samples = [
        compute(sigma=13.0, target=AnalysisTarget(target_abs_error=e)).classical_mc_samples
        for e in errors
    ]
    assert samples == sorted(samples, reverse=True)
    assert samples[0] > samples[-1]


def test_breakeven_error_finite_positive() -> None:
    result = compute(sigma=13.0, target=AnalysisTarget(target_abs_error=0.01))
    assert result.breakeven_error > 0.0
    assert result.breakeven_error != float("inf")


def test_quantum_wins_flag_consistent() -> None:
    result = compute(sigma=13.0, target=AnalysisTarget(target_abs_error=0.001))
    assert result.quantum_wins_in_queries == (
        result.quantum_oracle_calls < result.classical_mc_samples
    )


def test_measured_oracle_calls_override() -> None:
    result = compute(
        sigma=13.0, target=AnalysisTarget(target_abs_error=0.01), measured_oracle_calls=777
    )
    assert result.quantum_oracle_calls == 777
