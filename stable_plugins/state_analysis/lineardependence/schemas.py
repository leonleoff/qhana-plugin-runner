import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema
from .marshmallow_util import TOLERANCE, SETOFCOMPLEXVECTORS

class ClassicalStateAnalysisLineardependenceParametersSchema(FrontendFormBaseSchema):
    """Schema for classical state analysis of linear dependence."""

    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": (
                "Provide a list of vectors. Each vector must be a list of complex numbers, "
                "where each complex number is represented as a real and imaginary part. "
                "Example: [[[1.0, 0.0], [0.0, 1.0]], [[2.0, 1.0], [0.0, -1.0]]]"
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
                "If not provided, the default value: `1e-10` will be used."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        """Validate the input data."""
        try:
            # The 'vectors' field is validated by the SETOFCOMPLEXVECTORSField itself
            if "vectors" not in data or not data["vectors"]:
                raise ma.ValidationError("'vectors' field is required and cannot be empty.")

            # Validate 'tolerance' to ensure it's a number if present
            if "tolerance" in data and data["tolerance"] is not None and not isinstance(data["tolerance"], (int, float)):
                raise ma.ValidationError("'tolerance' must be a valid number.")

            return data
        except ma.ValidationError as e:
            raise e
        except Exception as e:
            raise ma.ValidationError(f"Unexpected validation error: {str(e)}")
