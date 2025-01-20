# schemas.py

import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS, TOLERANCE, NullAbleFileUrl
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class PairwiseOrthogonalityParametersSchema(FrontendFormBaseSchema):
    """
    Validates input for pairwise orthogonality checks.
    Accepts multiple vectors or a .qcd circuit descriptor.
    """

    vectors = SETOFCOMPLEXVECTORS(
        required=False,
        metadata={
            "label": "Input Vectors",
            "description": "A set of complex vectors for pairwise checking.",
            "input_type": "textarea",
        },
    )
    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": "Threshold for orthonormal check. Defaults to 1e-10.",
            "input_type": "text",
        },
    )

    circuit = NullAbleFileUrl(
        required=False,
        allow_none=True,
        data_input_type="application/x-qcd",
        data_content_types="application/json",
        metadata={
            "label": "Circuit Descriptor (.qcd)",
            "description": "If provided, we decode from QASM. The plugin then checks pairwise orthonormality.",
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": "Min probability for bit=1. Defaults to ~1e-5.",
            "input_type": "text",
        },
    )

    @ma.post_load
    def fix_data(self, data, **kwargs):
        if data.get("tolerance") in ("", None):
            data["tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        if data.get("vectors") and data.get("circuit"):
            raise ValueError("Either 'vectors' or 'circuit' can be provided, not both.")
        if not data.get("vectors") and not data.get("circuit"):
            raise ValueError("Must provide either 'vectors' or 'circuit'.")

        if data.get("vectors"):
            data["circuit"] = None
            data["probability_tolerance"] = None
        else:
            data["vectors"] = None
            data["tolerance"] = None

        return data
