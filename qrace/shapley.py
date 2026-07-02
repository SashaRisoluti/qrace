"""Exact Shapley decomposition of the error/resource budget over the 4 pipeline stages."""

import math
from itertools import combinations
from typing import Callable

from qrace.verdict import ShapleyBudget

STAGES = ("loading", "payoff", "qae_iters", "decoherence")

BudgetFn = Callable[[frozenset[str]], float]


def decompose(budget_fn: BudgetFn) -> ShapleyBudget:
    """Exact Shapley values over the 2^4 coalitions of the pipeline stages.

    budget_fn(coalition) returns the budget metric when only the stages in the
    coalition contribute their imperfection. total = v(all stages) - v(empty),
    which the contributions sum to exactly (efficiency).
    """
    n = len(STAGES)
    values = {
        frozenset(subset): budget_fn(frozenset(subset))
        for size in range(n + 1)
        for subset in combinations(STAGES, size)
    }
    contributions: dict[str, float] = {}
    for stage in STAGES:
        others = [s for s in STAGES if s != stage]
        phi = 0.0
        for size in range(n):
            weight = math.factorial(size) * math.factorial(n - size - 1) / math.factorial(n)
            for subset in combinations(others, size):
                coalition = frozenset(subset)
                phi += weight * (values[coalition | {stage}] - values[coalition])
        contributions[stage] = phi
    total = values[frozenset(STAGES)] - values[frozenset()]
    return ShapleyBudget(contributions=contributions, total=total)
