import marshmallow as ma
from common.marshmallow_util import SETOFTWOCOMPLEXVECTORS, TOLERANCE, NullAbleFileUrl

from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisOrthogonalityParametersSchema(FrontendFormBaseSchema):
    """Schema for classical state analysis parameters, focusing on orthogonality analysis."""

    vectors = SETOFTWOCOMPLEXVECTORS(
        required=False,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A set of two complex vectors to analyze. "
                "Example: [[[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]]]"
            ),
            "input_type": "textarea",
        },
    )

    innerproduct_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Inner Product Tolerance",
            "description": (
                "Optional orthogonality_task value for the inner product calculation. "
                "If not provided, the default value is `1e-10`."
            ),
            "input_type": "text",
        },
    )

    circuit = NullAbleFileUrl(
        required=False,
        allow_none=True,
        data_input_type="executable/circuit",
        data_content_types="text/x-qasm",
        metadata={
            "label": "OpenQASM Circuit",
            "description": (
                "URL to a quantum circuit in the OpenQASM format. The circuit should specify "
                "how vectors are mapped and processed."
            ),
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": (
                "The minimum probability threshold for interpreting quantum states during decoding. "
                "Values below this threshold will be interpreted as 0 rather than 1. "
                "If not provided, the default value is `1e-5`."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        """Validate and preprocess the provided data."""

        # Default handling for tolerances
        if data.get("innerproduct_tolerance") in ("", None):
            data["innerproduct_tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        # Case: Vectors provided
        if data.get("vectors") not in ("", None):

            # Ensure circuit URL is not also provided
            if data.get("circuit") not in ("", None):
                raise Exception(
                    "Only one input type is allowed: either 'vectors' or 'circuit'. Both cannot be provided."
                )

            # Clear circuit-related fields if vectors are used
            data["circuit"] = None
            data["probability_tolerance"] = None
            return data

        # Case: Circuit URL provided
        if data.get("circuit") not in ("", None):

            # Ensure vectors are not also provided
            if data.get("vectors") not in ("", None):
                raise Exception(
                    "Only one input type is allowed: either 'vectors' or 'circuit'. Both cannot be provided."
                )

            # Clear vector-related fields if circuit is used
            data["vectors"] = None
            data["innerproduct_tolerance"] = None
            return data

        # Raise error if neither vectors nor circuit are provided
        raise Exception(
            "At least one input must be provided: either 'vectors' or 'circuit'."
        )
