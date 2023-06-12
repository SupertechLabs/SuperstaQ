# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

import qiskit

import qiskit_superstaq as qss


def validate_target(target: str) -> None:
    """Checks that a device name contains a valid format, vendor prefix, and device type.

    Args:
        target: String containing the name of a target backend.

    Raises:
        ValueError: If `target` has invalid format, vendor prefix, or device type.
    """
    vendor_prefixes = [
        "aqt",
        "aws",
        "cq",
        "hqs",
        "ibmq",
        "ionq",
        "oxford",
        "quera",
        "rigetti",
        "sandia",
        "ss",
    ]

    target_device_types = ["qpu", "simulator"]

    match = re.fullmatch("^([A-Za-z0-9-]+)_([A-Za-z0-9-.]+)_([a-z]+)", target)
    if not match:
        raise ValueError(
            f"{target} does not have a valid string format. "
            "Valid target strings should be in the form: "
            "<provider>_<device>_<type>, e.g. ibmq_lagos_qpu."
        )

    prefix, _, device_type = match.groups()

    if prefix not in vendor_prefixes:
        raise ValueError(
            f"{target} does not have a valid target prefix. "
            f"Valid target prefixes are: {vendor_prefixes}."
        )

    if device_type not in target_device_types:
        raise ValueError(
            f"{target} does not have a valid target device type. "
            f"Valid target device types are: {target_device_types}."
        )


class SuperstaQBackend(qiskit.providers.BackendV1):
    """This class represents a Superstaq backend.

    Args:
        provider: Provider for a Superstaq backend.
        target: String containing the name of a target backend.
    """

    def __init__(self, provider: qss.SuperstaQProvider, target: str) -> None:
        self._provider = provider
        self.configuration_dict = {
            "backend_name": target,
            "backend_version": "n/a",
            "n_qubits": -1,
            "basis_gates": None,
            "gates": [],
            "local": False,
            "simulator": False,
            "conditional": False,
            "open_pulse": False,
            "memory": False,
            "max_shots": -1,
            "coupling_map": None,
        }

        validate_target(target)

        super().__init__(
            configuration=qiskit.providers.models.BackendConfiguration.from_dict(
                self.configuration_dict
            ),
            provider=provider,
        )

    @classmethod
    def _default_options(cls) -> qiskit.providers.Options:
        return qiskit.providers.Options(shots=1000)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, qss.SuperstaQBackend):
            return False

        return (
            self._provider == other._provider
            and self.configuration_dict == other.configuration_dict
        )

    def run(
        self,
        circuits: Union[qiskit.QuantumCircuit, List[qiskit.QuantumCircuit]],
        shots: int,
        method: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> qss.SuperstaQJob:
        """Runs circuits on the stored Superstaq backend.

        Args:
            circuits: A list of circuits to run.
            shots: The number of execution shots (times to run the circuit).
            method:  Optional execution method (e.g. 'dry-run', 'statevector', etc.).
            options: Optional dictionary of optimization and execution parameters.

        Returns:
            A Superstaq job storing ID and other related info.
        """

        if isinstance(circuits, qiskit.QuantumCircuit):
            circuits = [circuits]

        if not all(circuit.count_ops().get("measure") for circuit in circuits):
            # TODO: only raise if the run method actually requires samples (and not for e.g. a
            # statevector simulation)
            raise ValueError("Circuit has no measurements to sample.")

        qiskit_circuits = qss.serialization.serialize_circuits(circuits)

        result = self._provider._client.create_job(
            serialized_circuits={"qiskit_circuits": qiskit_circuits},
            repetitions=shots,
            target=self.name(),
            method=method,
            options=options,
        )

        #  we make a virtual job_id that aggregates all of the individual jobs
        # into a single one, that comma-separates the individual jobs:
        job_id = ",".join(result["job_ids"])
        job = qss.SuperstaQJob(self, job_id)

        return job

    def target_info(self) -> Dict[str, Any]:
        """Returns information about this backend.

        Returns:
            A dictionary of target information.
        """
        return self._provider._client.target_info(self.name())["target_info"]
