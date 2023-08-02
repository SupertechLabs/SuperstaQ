from typing import Dict, List, Optional

import pytest
import qiskit

import general_superstaq as gss
import qiskit_superstaq as qss




class MockSuperstaqBackend(qss.SuperstaqBackend):
    def __init__(self, provider: qss.SuperstaqProvider, target: str) -> None:
        """Initializes a SuperstaqBackend.

        Args:
            provider: Provider for a Superstaq backend.
            target: A string containing the name of a target backend.
        """
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

        gss.validation.validate_target(target)

        qiskit.providers.BackendV1.__init__(self,
            configuration=qiskit.providers.models.BackendConfiguration.from_dict(
                self.configuration_dict
            ),
            provider=provider,
        )


class MockSuperstaqProvider(qss.SuperstaqProvider):  # pylint: disable=missing-class-docstring
    def __init__(
        self,
        api_key: Optional[str] = None,
        remote_host: Optional[str] = None,
        api_version: str = gss.API_VERSION,
        max_retry_seconds: int = 3600,
        verbose: bool = False,
    ) -> None:
        """Initializes a SuperstaqProvider.

        Args:
            api_key: A string that allows access to the Superstaq API. If no key is provided, then
                this instance tries to use the environment variable `SUPERSTAQ_API_KEY`. If
                `SUPERSTAQ_API_KEY` is not set, then this instance checks for the
                following files:
                - `$XDG_DATA_HOME/super.tech/superstaq_api_key`
                - `$XDG_DATA_HOME/coldquanta/superstaq_api_key`
                - `~/.super.tech/superstaq_api_key`
                - `~/.coldquanta/superstaq_api_key`
                If one of those files exists, then it is treated as a plain text file, and the first
                line of this file is interpreted as an API key.  Failure to find an API key raises
                an `EnvironmentError`.
            remote_host: The location of the API in the form of a URL. If this is None,
                then this instance will use the environment variable `SUPERSTAQ_REMOTE_HOST`.
                If that variable is not set, then this uses
                `https://superstaq.super.tech/{api_version}`,
                where `{api_version}` is the `api_version` specified below.
            api_version: The version of the API.
            max_retry_seconds: The number of seconds to retry calls for. Defaults to one hour.
            verbose: Whether to print to stdio and stderr on retriable errors.

        Raises:
            EnvironmentError: If an API key was not provided and could not be found.
        """
        self._name = "mock_superstaq_provider"

        self._client = gss.superstaq_client._SuperstaqClient(
            client_name="qiskit-superstaq",
            remote_host=remote_host,
            api_key=api_key,
            api_version=api_version,
            max_retry_seconds=max_retry_seconds,
            verbose=verbose,
        )

    def get_backend(self, name: str):
        return MockSuperstaqBackend(self, name)


@pytest.fixture()
def mock_target_info() -> Dict[str, object]:
    """Initializes mock Qiskit Runtime sampler fixture."""
    return {
        "target_info": {
            "num_qubits": 4,
            "target": "cq_hilbert_simulator",
            "coupling_map": [[0, 1], [0, 2], [1, 0], [1, 3], [2, 0], [2, 3], [3, 1], [3, 2]],
            "supports_midcircuit_measurement": None,
            "native_gate_set": ["cz", "gr", "rz"],
            "max_experiments": None,
            "max_shots": 2048,
            "processor_type": None,
            "open_pulse": False,
            "conditional": False,
        }
    }


@pytest.fixture()
def fake_superstaq_provider():
    return MockSuperstaqProvider(api_key="MY_TOKEN")