"""Frozen input dataclasses: OptionSpec, AnalysisTarget, NoiseProfile."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OptionSpec:
    kind: Literal["european_call", "european_put"]
    spot: float
    strike: float
    maturity: float  # years
    volatility: float  # annualized
    rate: float  # risk-free rate

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError(f"spot must be positive, got {self.spot}")
        if self.strike <= 0:
            raise ValueError(f"strike must be positive, got {self.strike}")
        if self.maturity <= 0:
            raise ValueError(f"maturity must be positive, got {self.maturity}")
        if self.volatility <= 0:
            raise ValueError(f"volatility must be positive, got {self.volatility}")


@dataclass(frozen=True)
class AnalysisTarget:
    target_abs_error: float  # desired absolute error on the discounted expected payoff
    confidence: float = 0.95

    def __post_init__(self) -> None:
        if self.target_abs_error <= 0:
            raise ValueError(f"target_abs_error must be positive, got {self.target_abs_error}")
        if not 0 < self.confidence < 1:
            raise ValueError(f"confidence must be in (0, 1), got {self.confidence}")


@dataclass(frozen=True)
class NoiseProfile:
    kind: Literal["ideal", "depolarizing", "fake_backend"]
    two_qubit_error: float | None = None  # for "depolarizing"
    fake_backend_name: str | None = None  # for "fake_backend", e.g. "FakeManilaV2"

    def __post_init__(self) -> None:
        if self.kind == "depolarizing" and self.two_qubit_error is None:
            raise ValueError("depolarizing noise requires two_qubit_error")
        if self.kind == "fake_backend" and self.fake_backend_name is None:
            raise ValueError("fake_backend noise requires fake_backend_name")
