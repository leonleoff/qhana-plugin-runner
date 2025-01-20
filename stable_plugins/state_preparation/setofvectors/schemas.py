import marshmallow as ma
from common.encoding_registry import VectorEncodingEnum
from common.marshmallow_util import SETOFCOMPLEXVECTORS
from qhana_plugin_runner.api.extra_fields import EnumField
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class VectorsToQasmParametersSchema(FrontendFormBaseSchema):
    """Schema for encoding vectors into QASM code."""

    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A set (list) of complex vectors. "
                "Each vector is a list of [re, im] pairs. Example: [[[1.0,0.0],[0.0,1.0]]] "
            ),
            "input_type": "textarea",
        },
    )

    attribute_filter_strategy = EnumField(
        VectorEncodingEnum,
        required=True,
        metadata={
            "label": "Attribute Filter Setting",
            "description": "Specify attribute list as allowlist or blocklist.",
            "input_type": "select",
        },
    )

    @ma.post_load
    def fix_data(self, data, **kwargs):
        return data
