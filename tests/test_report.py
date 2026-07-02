import matplotlib

matplotlib.use("Agg")

import pytest

from qrace.backend import QiskitBackend
from qrace.report import EXPECTED_COLUMNS, run_report
from qrace.spec import AnalysisTarget, NoiseProfile, OptionSpec

CALL = OptionSpec(
    kind="european_call", spot=100.0, strike=105.0, maturity=1.0, volatility=0.2, rate=0.05
)
# structural test only: coarse target + few shots keep the noisy Aer simulation of
# the IAE Grover powers in seconds instead of minutes
CASES = [(CALL, AnalysisTarget(target_abs_error=6.0))]
NOISE_LEVELS = [
    NoiseProfile(kind="ideal"),
    NoiseProfile(kind="depolarizing", two_qubit_error=0.001),
]


@pytest.fixture(scope="module")
def report():  # type: ignore[no-untyped-def]
    return run_report(CASES, NOISE_LEVELS, QiskitBackend(seed=7, shots=256))


def test_one_row_per_case_times_noise(report) -> None:  # type: ignore[no-untyped-def]
    assert len(report.table) == len(CASES) * len(NOISE_LEVELS)


def test_table_structure_snapshot(report) -> None:  # type: ignore[no-untyped-def]
    assert list(report.table.columns) == list(EXPECTED_COLUMNS)


def test_figure_renders_without_raising(report) -> None:  # type: ignore[no-untyped-def]
    fig = report.figure()
    assert fig is not None
