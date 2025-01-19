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
                "Optional threshold for the inner product. If not provided, default `1e-10`."
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
                "URL to a quantum circuit in OpenQASM format. The file itself is JSON in text/x-qasm with fields {qasm_code, circuit_borders}."
            ),
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": (
                "Min probability threshold when decoding the circuit. Default ~1e-5 or so."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        """Validate and preprocess the provided data."""

        # sanitize
        if data.get("innerproduct_tolerance") in ("", None):
            data["innerproduct_tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        # case A: vectors
        if data.get("vectors") not in ("", None):
            if data.get("circuit") not in ("", None):
                raise Exception(
                    "Either 'vectors' OR 'circuit' can be provided, not both!"
                )
            # circuit-Felder leer machen
            data["circuit"] = None
            data["probability_tolerance"] = None
            return data

        # case B: circuit
        if data.get("circuit") not in ("", None):
            if data.get("vectors") not in ("", None):
                raise Exception(
                    "Either 'vectors' OR 'circuit' can be provided, not both!"
                )
            data["vectors"] = None
            data["innerproduct_tolerance"] = None
            return data

        # keins
        raise Exception("Must provide either 'vectors' or 'circuit'!")
