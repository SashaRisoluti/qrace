import pytest

from qrace.spec import AnalysisTarget, NoiseProfile, OptionSpec


def valid_call() -> OptionSpec:
    return OptionSpec(
        kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
    )


def test_valid_option_spec() -> None:
    option = valid_call()
    assert option.strike == 105.0


def test_option_spec_is_frozen() -> None:
    option = valid_call()
    with pytest.raises(Exception):
        option.spot = 1.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "field,value",
    [
        ("spot", -1.0),
        ("strike", 0.0),
        ("maturity", -0.5),
        ("volatility", 0.0),
        ("volatility", -0.2),
    ],
)
def test_option_spec_rejects_invalid(field: str, value: float) -> None:
    kwargs = dict(
        kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
    )
    kwargs[field] = value
    with pytest.raises(ValueError):
        OptionSpec(**kwargs)  # type: ignore[arg-type]


def test_valid_analysis_target() -> None:
    target = AnalysisTarget(target_abs_error=0.01)
    assert target.confidence == 0.95


@pytest.mark.parametrize("error,confidence", [(0.0, 0.95), (-0.01, 0.95), (0.01, 0.0), (0.01, 1.0)])
def test_analysis_target_rejects_invalid(error: float, confidence: float) -> None:
    with pytest.raises(ValueError):
        AnalysisTarget(target_abs_error=error, confidence=confidence)


def test_valid_noise_profiles() -> None:
    assert NoiseProfile(kind="ideal").two_qubit_error is None
    assert NoiseProfile(kind="depolarizing", two_qubit_error=0.001).two_qubit_error == 0.001
    assert NoiseProfile(kind="fake_backend", fake_backend_name="FakeManilaV2").fake_backend_name


def test_depolarizing_requires_error_rate() -> None:
    with pytest.raises(ValueError):
        NoiseProfile(kind="depolarizing")


def test_fake_backend_requires_name() -> None:
    with pytest.raises(ValueError):
        NoiseProfile(kind="fake_backend")
