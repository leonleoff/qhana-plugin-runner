import marshmallow as ma
from common.encoding_registry import VectorEncodingEnum
from common.marshmallow_util import SETOFCOMPLEXVECTORS
from qhana_plugin_runner.api.extra_fields import EnumField
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class VectorsToQasmParametersSchema(FrontendFormBaseSchema):
    """
    Validates parameters to encode a set of complex vectors into QASM.
    """

    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A list of complex vectors, each element is [re, im]. "
                "Example: [[[1.0, 0.0], [0.0, 1.0]]] "
            ),
            "input_type": "textarea",
        },
    )

    attribute_filter_strategy = EnumField(
        VectorEncodingEnum,
        required=True,
        metadata={
            "label": "Encoding Strategy",
            "description": (
                "Pick an encoding strategy from the available options (e.g., split_complex_binary_encoding)."
            ),
            "input_type": "select",
        },
    )

    @ma.post_load
    def fix_data(self, data, **kwargs):
        """
        Convert the `attribute_filter_strategy` to a string value for JSON usage,
        returning a dict with consistent keys: 'vectors' and 'strategy_id'.
        """
        vectors = data.get("vectors")
        strategy_str = str(data["attribute_filter_strategy"].value)
        return {"vectors": vectors, "strategy_id": strategy_str}
