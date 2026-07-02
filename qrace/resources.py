"""Resource extraction from transpiled circuits + required two-qubit fidelity."""

from qiskit import QuantumCircuit

from qrace.verdict import ResourceEstimate


def estimate_from(transpiled: QuantumCircuit, num_state_qubits: int | None = None) -> ResourceEstimate:
    """Extract qubit/depth/gate counts from an already-transpiled circuit.

    Ancilla = qubits beyond the state register and the single objective qubit,
    when the state-register size is known.
    """
    ops = transpiled.count_ops()
    ancilla = 0
    if num_state_qubits is not None:
        ancilla = max(0, transpiled.num_qubits - num_state_qubits - 1)
    return ResourceEstimate(
        logical_qubits=transpiled.num_qubits,
        circuit_depth=transpiled.depth(),
        two_qubit_gates=int(ops.get("cx", 0)),
        t_count=int(ops.get("t", 0)) + int(ops.get("tdg", 0)),
        ancilla=ancilla,
    )


def required_two_qubit_fidelity(depth: int, target_error: float) -> float:
    """Per-two-qubit-gate fidelity needed to keep total circuit noise within budget.

    Compounding model: F ** depth >= 1 - budget, so F = (1 - budget) ** (1 / depth).
    The budget is the target error capped below 1 so the result stays in (0, 1].
    """
    budget = min(target_error, 0.99)
    return float((1.0 - budget) ** (1.0 / max(depth, 1)))
