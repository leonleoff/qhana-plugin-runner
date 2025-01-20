import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS, TOLERANCE, NullAbleFileUrl
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisLineardependenceParametersSchema(FrontendFormBaseSchema):
    """
    Validates input for lineardependence checks, either multiple vectors or a .qcd circuit.
    """

    vectors = SETOFCOMPLEXVECTORS(
        required=False,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A set of complex vectors. Example: [[[1.0, 0.0],[1.0, 0.0]], ...]"
            ),
            "input_type": "textarea",
        },
    )

    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": "Optional tolerance. Defaults to 1e-10.",
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
            "description": "URL to a QCD file with 'circuit' (QASM) + 'metadata.circuit_divisions'.",
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": "Min probability threshold when decoding QASM from .qcd. Default ~1e-5.",
            "input_type": "text",
        },
    )

    @ma.post_load
    def fix_data(self, data, **kwargs):
        if data.get("tolerance") in ("", None):
            data["tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        # If vectors exist => we ignore circuit, else if circuit => we ignore vectors
        if data.get("vectors") and data.get("circuit"):
            raise ValueError("Either 'vectors' or 'circuit' can be provided, not both.")
        if not data.get("vectors") and not data.get("circuit"):
            raise ValueError("Must provide either 'vectors' or 'circuit' input.")

        if data.get("vectors"):
            # circuit-based fields not used
            data["circuit"] = None
            data["probability_tolerance"] = None
        else:
            # vector-based fields not used
            data["vectors"] = None
            data["tolerance"] = None

        return data
