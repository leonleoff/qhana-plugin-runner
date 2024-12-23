import marshmallow as ma
from qhana_plugin_runner.api.util import (
    FrontendFormBaseSchema,
)

class ClassicalStateAnalysisOrthogonalityParametersSchema(FrontendFormBaseSchema):
    vector1 = ma.fields.List(
        ma.fields.Float(),
        required=True,
        allow_none=False,
        metadata={
            "label": "Vector 1",
            "description": "The first vector for orthogonality analysis.",
            "input_type": "textarea",
        },
    )
    vector2 = ma.fields.List(
        ma.fields.Float(),
        required=True,
        allow_none=False,
        metadata={
            "label": "Vector 2",
            "description": "The second vector for orthogonality analysis.",
            "input_type": "textarea",
        },
    )
    tolerance = ma.fields.Float(
        required=False,
        allow_none=False,
        missing=1e-10,
        metadata={
            "label": "Tolerance",
            "description": "The tolerance value for checking orthogonality.",
            "input_type": "number",
        },
    )