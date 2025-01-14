import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema

from .marshmallow_util import SETOFTWOCOMPLEXVECTORS, TOLERANCE


class ClassicalStateAnalysisOrthogonalityParametersSchema(FrontendFormBaseSchema):
    """Schema for classical state analysis of orthogonality."""

    vectors = SETOFTWOCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A set of two complex vectors"
                "Example: [[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]],[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]]"
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
    try:
        # Check if the input is a dictionary and contains the required keys
        if not isinstance(data, dict):
            raise ma.ValidationError("The input data must be a dictionary.")

        # Check if 'vectors' is present in the dictionary
        if "vectors" not in data:
            raise ma.ValidationError("The input data must contain a 'vectors' key.")

        # Check if 'tolerance' is present in the dictionary
        if "tolerance" not in data:
            raise ma.ValidationError("The input data must contain a 'tolerance' key.")

        # Extract the vectors
        vectors = data["vectors"]

        # Convert each list of vectors into complex numbers
        processed_data = [
            [complex(real, imag) for real, imag in vector] for vector in vectors
        ]

        # Optionally, include the tolerance in the output
        tolerance = data["tolerance"]
        return {"processed_vectors": processed_data, "tolerance": tolerance}

    except ValueError as e:
        raise ma.ValidationError(f"Invalid vector format in the data: {data}. Error: {e}")
    except Exception as e:
        raise ma.ValidationError(f"An unexpected error occurred: {e}")
