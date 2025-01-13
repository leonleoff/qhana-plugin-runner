import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisOrthogonalityParametersSchema(FrontendFormBaseSchema):
    input_json = ma.fields.String(
        required=True,
        allow_none=False,
        metadata={
            "label": "Input JSON",
            "description": (
                "Provide a JSON object with the keys 'vector1', 'vector2', and optionally 'tolerance'. "
                'Example: {"vector1": [1.0, 0.0, 3.5], "vector2": [0.0, 1.0, -3.5], "tolerance": 1e-10}'
            ),
            "input_type": "textarea",
        },
    )

    @ma.post_load
    def parse_json(self, data, **kwargs):
        """Parse the JSON input into a Python dictionary."""
        try:
            parsed_data = ma.utils.json.loads(data["input_json"])
            if "vector1" not in parsed_data or "vector2" not in parsed_data:
                raise ma.ValidationError(
                    "Both 'vector1' and 'vector2' are required in the JSON."
                )

            # Optionally validate vectors and tolerance
            if not isinstance(parsed_data["vector1"], list) or not isinstance(
                parsed_data["vector2"], list
            ):
                raise ma.ValidationError(
                    "'vector1' and 'vector2' must be lists of numbers."
                )

            if "tolerance" in parsed_data and not isinstance(
                parsed_data["tolerance"], (int, float)
            ):
                raise ma.ValidationError("'tolerance' must be a number if provided.")

            return parsed_data
        except Exception as e:
            raise ma.ValidationError(f"Invalid JSON format: {str(e)}")
