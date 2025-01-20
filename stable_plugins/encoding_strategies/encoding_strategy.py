from abc import ABC, abstractmethod
from typing import Any, Dict


class EncodingStrategy(ABC):
    """
    Abstract base class for encoding strategies.
    Each strategy must provide an ID, an encoding method, and a decoding method.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique ID of the encoding strategy.
        """
        pass

    @abstractmethod
    def encode(self, data: Any, options: Dict[str, Any] = None):
        """
        Encodes the input data into qasm_code and circuit_divisions.

        Args:
            data (Any): The input data to encode.
            options (dict, optional): Additional options for encoding. Defaults to None.

        Returns:
            Tuple: A tuple containing:
                - qasm_code (str): The QASM representation of the encoded data.
                - circuit_divisions (Any): Metadata describing divisions in the circuit.
        """
        pass

    @abstractmethod
    def decode(
        self, qasm_code: str, circuit_divisions: Any, options: Dict[str, Any] = None
    ):
        """
        Decodes QASM-based data and circuit divisions back into the original data.

        Args:
            qasm_code (str): The QASM representation of the circuit.
            circuit_divisions (Any): Metadata describing divisions in the circuit.
            options (dict, optional): Additional options for decoding. Defaults to None.

        Returns:
            Any: The decoded data in its original format.
        """
        pass
