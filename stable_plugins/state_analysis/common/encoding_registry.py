from enum import Enum
from typing import Dict, List, Type

from .encoding_strategy import EncodingStrategy
from .split_complex_binary_encoding import SplitComplexBinaryEncoding


class EncodingRegistry:
    """
    Registry for encoding strategies.
    Maintains a collection of strategies and provides access by ID.
    """

    _strategies: Dict[str, EncodingStrategy] = {}

    @classmethod
    def register_strategy(cls, strategy: Type[EncodingStrategy]):
        """
        Registers a new encoding strategy.
        """
        instance = strategy()
        cls._strategies[instance.id] = instance

    @classmethod
    def get_strategy(cls, strategy_id: str) -> EncodingStrategy:
        """
        Returns the encoding strategy by its ID.
        """
        strategy = cls._strategies.get(strategy_id)
        if strategy is None:
            raise ValueError(f"Encoding strategy with ID '{strategy_id}' not found.")
        return strategy

    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        Returns a list of all registered strategy IDs.
        """
        return list(cls._strategies.keys())


# Register predefined strategies
EncodingRegistry.register_strategy(SplitComplexBinaryEncoding)


class VectorEncodingEnum(Enum):
    split_complex_binary_encoding = "split_complex_binary_encoding"
