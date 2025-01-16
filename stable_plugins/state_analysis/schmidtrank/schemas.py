import marshmallow as ma
from common.marshmallow_util import COMPLEXVECTOR, TOLERANCE
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisSchmidtrankParametersSchema(FrontendFormBaseSchema):
    vector = COMPLEXVECTOR(
        required=True,
        metadata={
            "label": "Input Vector",
            "description": (
                "A complex vector. "
                "Example: [[[1.0, 0.0], [1.0, 0.0], [1.0, 0.0], [1.0, 0.0]]]"
            ),
            "input_type": "textarea",
        },
    )

    dimA = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim A",
            "description": ("A number specifying the dimension of A. " "Example: 2"),
            "input_type": "number",
        },
    )

    dimB = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim B",
            "description": ("A number specifying the dimension of B. " "Example: 2"),
            "input_type": "number",
        },
    )

    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": (
                "Optional tolerance value for the analysis. " "Default: 1e-10."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        # transform 'tolerance'
        if data["tolerance"] == "":
            data["tolerance"] = None
        return data
