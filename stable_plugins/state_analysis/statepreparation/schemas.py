import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS
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

    # falls du sonstige Parameter brauchst, hier hinzufügen.

    @ma.post_load
    def fix_data(self, data, **kwargs):
        # Evtl. Abhängigkeiten oder Defaults
        return data
