import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema

class ClassicalStateAnalysisLineardependenceParametersSchema(FrontendFormBaseSchema):
    input_json = ma.fields.String(
        required=True,
        allow_none=False,
        metadata={
            "label": "Input JSON",
            "description": (
                "Provide a JSON object with the key 'vectors' containing a list of vectors, and optionally 'tolerance'. "
                "Example: {\"vectors\": [[1.0, 0.0, 3.5], [0.0, 1.0, -3.5], [2.0, 1.0, 0.0]], \"tolerance\": 1e-10}"
            ),
            "input_type": "textarea",
        },
    )

    @ma.post_load
    def parse_json(self, data, **kwargs):
        """Parse the JSON input into a Python dictionary."""
        try:
            parsed_data = ma.utils.json.loads(data["input_json"])

            # Validate the presence of 'vectors'
            if "vectors" not in parsed_data:
                raise ma.ValidationError("The key 'vectors' is required in the JSON.")

            # Validate that 'vectors' is a list of lists
            if not isinstance(parsed_data["vectors"], list) or not all(
                isinstance(vec, list) and all(isinstance(num, (int, float)) for num in vec)
                for vec in parsed_data["vectors"]
            ):
                raise ma.ValidationError("'vectors' must be a list of lists of numbers.")

            # Optionally validate 'tolerance'
            if "tolerance" in parsed_data and not isinstance(parsed_data["tolerance"], (int, float)):
                raise ma.ValidationError("'tolerance' must be a number if provided.")

            return parsed_data
        except Exception as e:
            raise ma.ValidationError(f"Invalid JSON format: {str(e)}")
