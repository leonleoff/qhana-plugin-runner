import marshmallow as ma
from qhana_plugin_runner.api.util import (
    FrontendFormBaseSchema,
    
)


class HelloWorldParametersSchema(FrontendFormBaseSchema):
    input_str = ma.fields.String(
        required=True,
        allow_none=False,
        metadata={
            "label": "Input String",
            "description": "A simple string input.",
            "input_type": "textarea",
        },
    )