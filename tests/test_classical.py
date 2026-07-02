from qrace.classical import mc_samples_for, monte_carlo_price, reference_price
from qrace.spec import AnalysisTarget, OptionSpec

CALL = OptionSpec(
    kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)
PUT = OptionSpec(
    kind="european_put", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)

# FinancePy bs_value fixtures for the specs above (financepy==1.0.1)
CALL_PRICE = 8.02136397242735
PUT_PRICE = 7.9004535450023194


def test_reference_price_matches_financepy_fixture() -> None:
    assert abs(reference_price(CALL) - CALL_PRICE) < 1e-9
    assert abs(reference_price(PUT) - PUT_PRICE) < 1e-9


def test_mc_samples_for_positive_int() -> None:
    n = mc_samples_for(CALL, AnalysisTarget(target_abs_error=0.01))
    assert isinstance(n, int)
    assert n > 0


def test_mc_samples_for_monotone_decreasing_in_error() -> None:
    errors = [0.005, 0.01, 0.02, 0.05]
    counts = [mc_samples_for(CALL, AnalysisTarget(target_abs_error=e)) for e in errors]
    assert counts == sorted(counts, reverse=True)
    assert counts[0] > counts[-1]


def test_discounted_payoff_std_positive_and_seeded() -> None:
    from qrace.classical import discounted_payoff_std

    a = discounted_payoff_std(CALL, samples=10_000, seed=0)
    b = discounted_payoff_std(CALL, samples=10_000, seed=0)
    assert a > 0
    assert a == b


def test_monte_carlo_converges_to_analytic() -> None:
    coarse = monte_carlo_price(CALL, samples=2_000, seed=42)
    fine = monte_carlo_price(CALL, samples=500_000, seed=42)
    assert abs(coarse - CALL_PRICE) < 1.5
    assert abs(fine - CALL_PRICE) < 0.1
