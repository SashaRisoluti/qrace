from qrace.verdict import Crossover, ResourceEstimate, ShapleyBudget, Verdict


def sample_verdict() -> Verdict:
    return Verdict(
        resource=ResourceEstimate(
            logical_qubits=5, circuit_depth=120, two_qubit_gates=48, t_count=0, ancilla=1
        ),
        required_two_qubit_fidelity=0.9995,
        noise_aware_estimate=4.51,
        noise_aware_error=0.03,
        classical_reference=4.49,
        crossover=Crossover(
            quantum_oracle_calls=1000,
            classical_mc_samples=40000,
            quantum_wins_in_queries=True,
            breakeven_error=0.005,
        ),
        shapley=ShapleyBudget(
            contributions={"loading": 0.01, "payoff": 0.02, "qae_iters": 0.005, "decoherence": 0.015},
            total=0.05,
        ),
        quantum_advantageous=False,
    )


def test_to_dict_round_trips_nested_dataclasses() -> None:
    d = sample_verdict().to_dict()
    assert d["resource"]["two_qubit_gates"] == 48
    assert d["crossover"]["quantum_wins_in_queries"] is True
    assert d["shapley"]["contributions"]["decoherence"] == 0.015
    assert d["quantum_advantageous"] is False


def test_to_dict_keys_stable() -> None:
    d = sample_verdict().to_dict()
    assert set(d.keys()) == {
        "resource",
        "required_two_qubit_fidelity",
        "noise_aware_estimate",
        "noise_aware_error",
        "classical_reference",
        "crossover",
        "shapley",
        "quantum_advantageous",
    }
