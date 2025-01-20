import marshmallow as ma
from common.encoding_registry import VectorEncodingEnum
from common.marshmallow_util import SETOFCOMPLEXVECTORS
from qhana_plugin_runner.api.extra_fields import EnumField
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class VectorsToQasmParametersSchema(FrontendFormBaseSchema):
    """
    Schema for validating parameters for encoding vectors into QASM code.
    """

    # Field for input vectors
    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",  # Label displayed on the frontend
            "description": (
                "A set (list) of complex vectors. "
                "Each vector is represented as a list of [re, im] pairs (real and imaginary parts). "
                "Example: [[[1.0, 0.0], [0.0, 1.0]]] "
            ),
            "input_type": "textarea",  # Suggests a text area for input in the frontend
        },
    )

    # Field for selecting the encoding strategy
    attribute_filter_strategy = EnumField(
        VectorEncodingEnum,  # Enum class that defines available encoding strategies
        required=True,
        metadata={
            "label": "Attribute Filter Setting",  # Label displayed on the frontend
            "description": (
                "Specify the encoding strategy to use for transforming the vectors into QASM. "
                "Choose from the available strategies in the dropdown."
            ),
            "input_type": "select",  # Suggests a dropdown menu for selection in the frontend
        },
    )

    @ma.post_load
    def fix_data(self, data, **kwargs):
        """
        Hook to post-process the data after validation.

        Returns the validated data in a consistent format for further processing.
        """
        return data
