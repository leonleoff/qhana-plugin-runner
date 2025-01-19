import marshmallow as ma
from common.marshmallow_util import SETOFTWOCOMPLEXVECTORS, TOLERANCE

from qhana_plugin_runner.api.util import FileUrl, FrontendFormBaseSchema


class ClassicalStateAnalysisOrthogonalityParametersSchema(FrontendFormBaseSchema):
    """Schema for classical state analysis of orthogonality."""

    vectors = SETOFTWOCOMPLEXVECTORS(
        required=False,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A set of two complex vectors"
                "Example: [[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]],[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]]"
            ),
            "input_type": "textarea",
        },
    )

    innerproduct_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Tolerance",
            "description": (
                "Provide an optional tolerance value for the analysis. "
                "If not provided, the default value: `1e-10` will be used."
            ),
            "input_type": "text",
        },
    )

    # TODO: Text
    circuit = FileUrl(
        required=False,
        allow_none=False,
        data_input_type="executable/circuit",
        data_content_types="text/x-qasm",
        metadata={
            "label": "OpenQASM Circuit",
            "description": "URL to a quantum circuit in the OpenQASM format mit dem map wo steht von wo bis wo die vectoren und so gehen .",
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Tolerance",
            "description": (
                "Die warhscheinlichkeit die ein wert mindestens haben muss bei dem decoding von den quantenzuständen dass er als bit mit dem wert 1 und nicht 0 interpretiert wird"
                "If not provided, the default value: `1e-5` will be used."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        # Transform 'tolerance'
        if data.get("innerproduct_tolerance") in ("", None):
            data["innerproduct_tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        # case vector
        if data.get("vectors") not in ("", None):

            # case vector and circuiturl
            if data.get("circuit") not in ("", None):
                raise Exception(
                    "Es darf nicht beides angegeben werden vectors und circuiturl es muss ein eindrutige input typ sein"
                )

            # case vector not circuiturl
            data["circuit"] = None
            data["probability_tolerance"] = None
            return data

        # case circuiturl
        if data.get("circuit") not in ("", None):
            # case vector and circuiturl
            if data.get("vectors") not in ("", None):
                raise Exception(
                    "Es darf nicht beides angegeben werden vectors und circuiturl es muss ein eindrutige input typ sein"
                )

            # case circuiturl not vector
            data["vectors"] = None
            data["innerproduct_tolerance"] = None
            return data
        raise Exception(
            "Es darf nicht nichts angegeben werden entwerder muss die url da sein doer die vectoren"
        )
