"""qrace — Quantum Risk Advisor & Crossover Estimator."""

from qrace.advisor import analyze
from qrace.backend import Backend, QiskitBackend
from qrace.report import run_report
from qrace.spec import AnalysisTarget, NoiseProfile, OptionSpec
from qrace.verdict import Crossover, ResourceEstimate, ShapleyBudget, Verdict

__version__ = "0.1.0"

__all__ = [
    "AnalysisTarget",
    "Backend",
    "Crossover",
    "NoiseProfile",
    "OptionSpec",
    "QiskitBackend",
    "ResourceEstimate",
    "ShapleyBudget",
    "Verdict",
    "analyze",
    "run_report",
    "__version__",
]
