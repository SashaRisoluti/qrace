import pytest

from qrace.shapley import STAGES, decompose

WEIGHTS = {"loading": 0.4, "payoff": 0.3, "qae_iters": 0.2, "decoherence": 0.1}


def additive(coalition: frozenset[str]) -> float:
    return sum(WEIGHTS[s] for s in coalition)


def superadditive(coalition: frozenset[str]) -> float:
    return additive(coalition) ** 2


def test_exactly_four_stage_keys() -> None:
    budget = decompose(additive)
    assert set(budget.contributions.keys()) == {"loading", "payoff", "qae_iters", "decoherence"}
    assert set(STAGES) == set(budget.contributions.keys())


@pytest.mark.parametrize("budget_fn", [additive, superadditive])
def test_efficiency(budget_fn) -> None:  # type: ignore[no-untyped-def]
    budget = decompose(budget_fn)
    assert abs(sum(budget.contributions.values()) - budget.total) < 1e-9


def test_additive_recovers_weights() -> None:
    budget = decompose(additive)
    for stage, weight in WEIGHTS.items():
        assert abs(budget.contributions[stage] - weight) < 1e-9


def test_null_player_gets_zero() -> None:
    def null_decoherence(coalition: frozenset[str]) -> float:
        return sum(WEIGHTS[s] for s in coalition if s != "decoherence")

    budget = decompose(null_decoherence)
    assert abs(budget.contributions["decoherence"]) < 1e-9


def test_symmetry_interchangeable_stages_equal() -> None:
    def symmetric(coalition: frozenset[str]) -> float:
        # loading and payoff enter identically; the pair contributes only jointly
        base = 1.0 if {"loading", "payoff"} <= coalition else 0.0
        return base + (0.5 if "qae_iters" in coalition else 0.0)

    budget = decompose(symmetric)
    assert abs(budget.contributions["loading"] - budget.contributions["payoff"]) < 1e-9
