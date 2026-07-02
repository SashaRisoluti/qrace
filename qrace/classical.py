"""Classical ground truth: FinancePy analytic price + seeded Monte Carlo + N(eps)."""

import math
from statistics import NormalDist

import numpy as np
from financepy.models.black_scholes_analytic import bs_value
from financepy.utils.global_types import OptionTypes

from qrace.spec import AnalysisTarget, OptionSpec

_OPTION_TYPE = {
    "european_call": OptionTypes.EUROPEAN_CALL,
    "european_put": OptionTypes.EUROPEAN_PUT,
}


def reference_price(option: OptionSpec) -> float:
    """Black-Scholes analytic price via FinancePy (dividend yield 0)."""
    return float(
        bs_value(
            option.spot,
            option.maturity,
            option.strike,
            option.rate,
            0.0,
            option.volatility,
            _OPTION_TYPE[option.kind].value,
        )
    )


def _terminal_prices(option: OptionSpec, samples: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(samples)
    drift = (option.rate - 0.5 * option.volatility**2) * option.maturity
    diffusion = option.volatility * math.sqrt(option.maturity) * z
    return np.asarray(option.spot * np.exp(drift + diffusion))


def _discounted_payoffs(option: OptionSpec, samples: int, seed: int) -> np.ndarray:
    terminal = _terminal_prices(option, samples, seed)
    if option.kind == "european_call":
        payoff = np.maximum(terminal - option.strike, 0.0)
    else:
        payoff = np.maximum(option.strike - terminal, 0.0)
    return np.asarray(math.exp(-option.rate * option.maturity) * payoff)


def monte_carlo_price(option: OptionSpec, samples: int, seed: int) -> float:
    """Seeded GBM Monte Carlo estimate of the discounted expected payoff."""
    return float(_discounted_payoffs(option, samples, seed).mean())


def mc_samples_for(
    option: OptionSpec,
    target: AnalysisTarget,
    pilot_samples: int = 10_000,
    seed: int = 0,
) -> int:
    """Classical samples N(eps) = ceil((z * sigma / eps)^2) to hit the target error.

    sigma is the discounted-payoff standard deviation, estimated from a seeded pilot run.
    """
    sigma = float(_discounted_payoffs(option, pilot_samples, seed).std(ddof=1))
    z = NormalDist().inv_cdf(0.5 + target.confidence / 2)
    return math.ceil((z * sigma / target.target_abs_error) ** 2)
