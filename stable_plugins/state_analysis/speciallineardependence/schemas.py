import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisSpeciallineardependenceParametersSchema(
    FrontendFormBaseSchema
):
    input_json = ma.fields.String(
        required=True,
        allow_none=False,
        metadata={
            "label": "Input JSON",
            "description": (
                "Provide a JSON object with the keys 'state', 'dim_A', 'dim_B', and optionally 'tolerance'. "
                'Example: {"state": ["0.7071067811865475+0j", "0+0j", "0+0j", "0.7071067811865475+0j"], "dim_A": 2, "dim_B": 2, "tolerance": 1e-10}'
            ),
            "input_type": "textarea",
        },
    )

    @ma.post_load
    def parse_json(self, data, **kwargs):
        """Parse the JSON input into a Python dictionary."""
        try:
            parsed_data = ma.utils.json.loads(data["input_json"])

            # Validate required keys
            if (
                "state" not in parsed_data
                or "dim_A" not in parsed_data
                or "dim_B" not in parsed_data
            ):
                raise ma.ValidationError(
                    "Keys 'state', 'dim_A', and 'dim_B' are required in the JSON."
                )

            # Validate state (must be a list with complex numbers as strings)

            def try_parse_complex(value: str):
                try:
                    complex(value)
                    return True
                except ValueError:
                    return False

            def try_parse_float(value: str):
                try:
                    float(value)
                    return True
                except ValueError:
                    return False

            if not (
                isinstance(parsed_data["state"], list)
                and all(
                    isinstance(val, str)
                    and (try_parse_complex(val) or try_parse_float(val))
                    for val in parsed_data["state"]
                )
            ):
                raise ma.ValidationError(
                    "'state' must be a list containing complex numbers as strings."
                )

            # Validate dim_A and dim_B (must be integers)
            if not (
                isinstance(parsed_data["dim_A"], int)
                and isinstance(parsed_data["dim_B"], int)
            ):
                raise ma.ValidationError("'dim_A' and 'dim_B' must be integers.")

            # Validate tolerance (optional, must be a number if provided)
            if "tolerance" in parsed_data and not isinstance(
                parsed_data["tolerance"], (int, float)
            ):
                raise ma.ValidationError("'tolerance' must be a number if provided.")

            # Validate that dim_A * dim_B equals the length of the state
            if len(parsed_data["state"]) != parsed_data["dim_A"] * parsed_data["dim_B"]:
                raise ma.ValidationError(
                    "The product of 'dim_A' and 'dim_B' must match the length of 'state'."
                )

            return parsed_data

        except Exception as e:
            raise ma.ValidationError(f"Invalid JSON format: {str(e)}")
