import marshmallow as ma
from qhana_plugin_runner.api.extra_fields import EnumField
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class VectorsToQasmParametersSchema(FrontendFormBaseSchema):
    """
    Validates parameters to encode a set of complex vectors into QASM.
    """

    qasmCode = ma.fields.String(
        required=True,
        metadata={
            "label": "qasmCode",
            "description": ("QASM code that will be then stored with in a file"),
            "input_type": "textarea",
        },
    )

    metaData = ma.fields.String(
        required=True,
        metadata={
            "label": "metadata",
            "description": (" Metadata that will be stored in a file"),
            "input_type": "textarea",
        },
    )
