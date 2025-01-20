import marshmallow as ma
from common.marshmallow_util import SETOFTWOCOMPLEXVECTORS, TOLERANCE, NullAbleFileUrl
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisOrthogonalityParametersSchema(FrontendFormBaseSchema):
    """
    Validates parameters for orthogonality checks:
      - two vectors, or
      - a circuit descriptor (.qcd) with the needed metadata.
    """

    vectors = SETOFTWOCOMPLEXVECTORS(
        required=False,
        metadata={
            "label": "Input Vectors",
            "description": "A pair of complex vectors for orthogonality analysis.",
            "input_type": "textarea",
        },
    )

    innerproduct_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Inner Product Tolerance",
            "description": (
                "Threshold for the inner product used to determine orthogonality. "
                "If omitted, defaults to 1e-10."
            ),
            "input_type": "text",
        },
    )

    circuit = NullAbleFileUrl(
        required=False,
        allow_none=True,
        data_input_type="application/x-qcd",
        data_content_types="application/json",
        metadata={
            "label": "Quantum Circuit Descriptor (.qcd)",
            "description": (
                "A JSON-based circuit descriptor file containing fields like 'circuit' (QASM code) "
                "and 'metadata' (with 'strategy_id' and 'circuit_divisions')."
            ),
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": (
                "Minimum probability threshold for decoding the statevector from QASM. "
                "If omitted, defaults to around 1e-5."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        """
        Ensures that either 'vectors' or 'circuit' is provided, not both.
        Adjusts default tolerance values if none is provided.
        """

        if data.get("innerproduct_tolerance") in ("", None):
            data["innerproduct_tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        # Option 1: vectors
        if data.get("vectors") not in ("", None):
            if data.get("circuit") not in ("", None):
                raise ValueError(
                    "Either 'vectors' or 'circuit' can be provided, not both."
                )
            data["circuit"] = None
            data["probability_tolerance"] = None
            return data

        # Option 2: circuit
        if data.get("circuit") not in ("", None):
            if data.get("vectors") not in ("", None):
                raise ValueError(
                    "Either 'vectors' or 'circuit' can be provided, not both."
                )
            data["vectors"] = None
            data["innerproduct_tolerance"] = None
            return data

        raise ValueError("Must provide either 'vectors' or 'circuit' input.")
