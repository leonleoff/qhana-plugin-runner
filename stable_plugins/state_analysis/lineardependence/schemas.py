import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema
from .marshmallow import TOLERANCE

class ClassicalStateAnalysisLineardependenceParametersSchema(FrontendFormBaseSchema):
    vectors = ma.fields.List(
        ma.fields.List(ma.fields.Float(), required=True),
        required=True,
        allow_none=False,
        metadata={
            "label": "Input Vectors",
            "description": (
                "Provide a list of vectors. Each vector must be a list of numbers. "
                "Example: [[1.0, 0.0, 3.5], [0.0, 1.0, -3.5], [2.0, 1.0, 0.0]]"
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
            "If not provided, a default value will be used. Example: 1e-10"
        ),
        "input_type": "text",
    },
)


    @ma.post_load
    def validate_data(self, data, **kwargs):
        """Validate the input data."""
        try:
            # Validate that 'vectors' is a list of lists of numbers
            if not isinstance(data["vectors"], list) or not all(
                isinstance(vec, list) and all(isinstance(num, (int, float)) for num in vec)
                for vec in data["vectors"]
            ):
                raise ma.ValidationError("'vectors' must be a list of lists of numbers.")

            # Validate 'tolerance' if provided
            if "tolerance" in data and data["tolerance"] is not None and not isinstance(data["tolerance"], (int, float)):
                raise ma.ValidationError("'tolerance' must be a number if provided.")

            return data
        except Exception as e:
            raise ma.ValidationError(f"Validation error: {str(e)}")
