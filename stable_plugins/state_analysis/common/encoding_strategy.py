from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class EncodingStrategy(ABC):
    """
    Base class for encoding and decoding quantum data.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """A unique identifier for this strategy."""
        pass

    @abstractmethod
    def encode(self, data: Any, options: Dict[str, Any] = None) -> Tuple[str, Any]:
        """
        Encodes the given data into (qasm_code, circuit_divisions).

        :param data: The data to encode (e.g., list of vectors).
        :param options: Optional dictionary with encoding parameters.
        :return: A tuple (qasm_code, circuit_divisions).
        """
        pass

    @abstractmethod
    def decode(
        self, qasm_code: str, circuit_divisions: Any, options: Dict[str, Any] = None
    ) -> Any:
        """
        Decodes the original data from QASM code + metadata.

        :param qasm_code: The QASM representation of the circuit.
        :param circuit_divisions: Metadata describing how the circuit was divided.
        :param options: Optional dictionary with decoding parameters (e.g., probability_tolerance).
        :return: The decoded data (e.g., list of vectors).
        """
        pass
