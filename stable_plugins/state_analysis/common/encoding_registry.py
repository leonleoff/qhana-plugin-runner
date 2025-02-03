from enum import Enum
from typing import Dict, List, Type

from .encoding_strategy import EncodingStrategy
from .split_complex_binary_encoding import SplitComplexBinaryEncoding


class EncodingRegistry:
    """
    Central registry for encoding/decoding strategies.
    Each strategy must inherit from EncodingStrategy and be registered here.
    """

    _strategies: Dict[str, EncodingStrategy] = {}

    @classmethod
    def register_strategy(cls, strategy: Type[EncodingStrategy]):
        """Register a new strategy by its class."""
        instance = strategy()
        cls._strategies[instance.id] = instance

    @classmethod
    def get_strategy(cls, strategy_id: str) -> EncodingStrategy:
        """Retrieve a strategy instance by its ID."""
        strategy = cls._strategies.get(strategy_id)
        if not strategy:
            raise ValueError(f"Encoding strategy with ID '{strategy_id}' not found.")
        return strategy

    @classmethod
    def list_strategies(cls) -> List[str]:
        """List all available strategy IDs."""
        return list(cls._strategies.keys())


# Default or example registration
EncodingRegistry.register_strategy(SplitComplexBinaryEncoding)


class VectorEncodingEnum(Enum):
    """
    Enumerates possible vector encoding strategies for easy usage in Marshmallow fields.
    """

    split_complex_binary_encoding = "split_complex_binary_encoding"
