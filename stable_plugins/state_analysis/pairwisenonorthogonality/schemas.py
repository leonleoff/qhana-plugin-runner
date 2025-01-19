import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS, TOLERANCE
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class PairwiseNonOrthogonalityParametersSchema(FrontendFormBaseSchema):
    """Schema for pairwise non-orthogonality plugin."""

    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": "A set of complex vectors. Example: [[[1.0,0.0],[0.0,0.0]], [[0.0,0.0],[1.0,0.0]]] etc.",
            "input_type": "textarea",
        },
    )

    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": "Optional tolerance. If not provided => 1e-10.",
            "input_type": "text",
        },
    )

    @ma.post_load
    def fix_tolerance(self, data, **kwargs):
        if data.get("tolerance") in ("", None):
            data["tolerance"] = None
        return data
