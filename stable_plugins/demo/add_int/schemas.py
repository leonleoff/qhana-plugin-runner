import marshmallow as ma
from qhana_plugin_runner.api.util import (
    FrontendFormBaseSchema,
    MaBaseSchema,
)


class DemoResponseSchema(MaBaseSchema):
    name = ma.fields.String(required=True, allow_none=False, dump_only=True)
    version = ma.fields.String(required=True, allow_none=False, dump_only=True)
    identifier = ma.fields.String(required=True, allow_none=False, dump_only=True)


class AddIntParametersSchema(FrontendFormBaseSchema):
    input_int1 = ma.fields.Integer(
        required=True,
        allow_none=False,
        metadata={
            "label": "First Integer Input",
            "description": "Enter the first integer.",
            "input_type": "number",
        },
    )
    input_int2 = ma.fields.Integer(
        required=True,
        allow_none=False,
        metadata={
            "label": "Second Integer Input",
            "description": "Enter the second integer.",
            "input_type": "number",
        },
    )
    
