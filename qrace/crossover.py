"""Crossover: quantum oracle calls vs classical MC samples at equal target accuracy."""

import math
from statistics import NormalDist

from qrace.spec import AnalysisTarget
from qrace.verdict import Crossover


def _z(confidence: float) -> float:
    return NormalDist().inv_cdf(0.5 + confidence / 2)


def _classical_samples(sigma: float, epsilon: float, confidence: float) -> int:
    # classical MC error ~ sigma / sqrt(N)  =>  N(eps) = ceil((z * sigma / eps)^2)
    return math.ceil((_z(confidence) * sigma / epsilon) ** 2)


def _quantum_calls(epsilon: float, confidence: float) -> int:
    # first-order IAE query model: M(eps) = ceil(pi/(4 eps) * ln(2/alpha)) — the 1/eps
    # amplitude-estimation scaling with the confidence-dependent log factor
    alpha = 1 - confidence
    return math.ceil(math.pi / (4 * epsilon) * math.log(2 / alpha))


def compute(
    sigma: float,
    target: AnalysisTarget,
    measured_oracle_calls: int | None = None,
) -> Crossover:
    """Compare quantum vs classical query cost at the target accuracy.

    sigma is the standard deviation of the discounted payoff (drives classical MC cost).
    measured_oracle_calls, when given, replaces the theoretical M(eps) with the count
    actually used by the IAE run.
    """
    if sigma <= 0:
        raise ValueError(f"sigma must be positive, got {sigma}")
    epsilon = target.target_abs_error
    classical = _classical_samples(sigma, epsilon, target.confidence)
    quantum = (
        measured_oracle_calls
        if measured_oracle_calls is not None
        else _quantum_calls(epsilon, target.confidence)
    )
    # break-even: (z sigma / eps)^2 = c / eps  =>  eps* = c / (z sigma)^2, with c the
    # coefficient of the theoretical quantum model
    c = math.pi / 4 * math.log(2 / (1 - target.confidence))
    breakeven = c / (_z(target.confidence) * sigma) ** 2
    return Crossover(
        quantum_oracle_calls=quantum,
        classical_mc_samples=classical,
        quantum_wins_in_queries=quantum < classical,
        breakeven_error=breakeven,
    )
