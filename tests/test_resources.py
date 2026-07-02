from qiskit import QuantumCircuit, transpile

from qrace.resources import estimate_from, required_two_qubit_fidelity


def transpiled_bell() -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.t(2)
    return transpile(qc, basis_gates=["rz", "sx", "x", "cx", "t"], optimization_level=0)


def test_estimate_from_extracts_counts() -> None:
    estimate = estimate_from(transpiled_bell(), num_state_qubits=1)
    assert estimate.logical_qubits == 3
    assert estimate.circuit_depth > 0
    assert estimate.two_qubit_gates == 2
    assert estimate.t_count == 1
    assert estimate.ancilla == 1  # 3 qubits - 1 state - 1 objective


def test_required_fidelity_in_unit_interval() -> None:
    fidelity = required_two_qubit_fidelity(depth=100, target_error=0.01)
    assert 0.0 < fidelity <= 1.0


def test_required_fidelity_increases_with_depth() -> None:
    shallow = required_two_qubit_fidelity(depth=10, target_error=0.01)
    deep = required_two_qubit_fidelity(depth=10_000, target_error=0.01)
    assert deep > shallow


def test_required_fidelity_increases_as_error_shrinks() -> None:
    loose = required_two_qubit_fidelity(depth=100, target_error=0.1)
    tight = required_two_qubit_fidelity(depth=100, target_error=0.001)
    assert tight > loose
