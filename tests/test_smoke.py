def test_import() -> None:
    import qrace

    assert qrace.__version__


def test_public_api_exported_at_top_level() -> None:
    from qrace import (
        AnalysisTarget,
        NoiseProfile,
        OptionSpec,
        QiskitBackend,
        Verdict,
        analyze,
        run_report,
    )

    assert callable(analyze)
    assert callable(run_report)
    assert all(
        x is not None for x in (OptionSpec, AnalysisTarget, NoiseProfile, Verdict, QiskitBackend)
    )
