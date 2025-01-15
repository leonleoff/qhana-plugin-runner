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
    try:
        # Check if the input is a dictionary and contains the required keys
        if not isinstance(data, dict):
            raise ma.ValidationError("The input data must be a dictionary.")

        # Check if 'vector' is present in the dictionary
        if "vector" not in data:
            raise ma.ValidationError("The input data must contain a 'vector' key.")

        # Extract the vector
        vector = data["vector"]

        # Convert each entry in the vector to a complex number
        processed_vector = [complex(real, imag) for real, imag in vector]

        # Validate dimensions
        dimA = data.get("dimA")
        dimB = data.get("dimB")
        if len(processed_vector) != dimA * dimB:
            raise ma.ValidationError(
                "The length of the vector must match the product of dimA and dimB."
            )

        # Optionally, include the tolerance in the output
        tolerance = data.get("tolerance", 1e-10)
        return {
            "processed_vectors": processed_vector,
            "dimA": dimA,
            "dimB": dimB,
            "tolerance": tolerance,
        }

    except ValueError as e:
        raise ma.ValidationError(f"Invalid vector format in the data: {data}. Error: {e}")
    except Exception as e:
        raise ma.ValidationError(f"An unexpected error occurred: {e}")
