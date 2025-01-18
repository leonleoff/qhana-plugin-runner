import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS, TOLERANCE
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisLineardependenceParametersSchema(FrontendFormBaseSchema):
    """Schema for classical state analysis of linear dependence."""

    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A set of complex vectors. "
                "Example: [[[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]], "
                "[[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]], "
                "[[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]]]"
            ),
            "input_type": "textarea",
        },
    )

    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": (
                "Provide an optional tolerance value for the analysis. "
                "If not provided, the default value `1e-10` will be used."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        # Transform 'tolerance' using dict.get()
        if data.get("tolerance") in ("", None):
            data["tolerance"] = None
        return data
