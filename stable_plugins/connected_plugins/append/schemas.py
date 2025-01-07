import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema

class AppendPluginParametersSchema(FrontendFormBaseSchema):
    input_text = ma.fields.String(
        required=True,
        allow_none=False,
        metadata={
            "label": "Input Text",
            "description": (
                "Provide a text input that will be appended with 'world'. "
                "Example: 'Hello'"
            ),
            "input_type": "text",
        },
    )
