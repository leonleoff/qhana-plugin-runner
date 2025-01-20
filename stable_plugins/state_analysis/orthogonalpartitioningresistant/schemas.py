import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS, TOLERANCE, NullAbleFileUrl
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class OrthogonalPartitioningResistantParametersSchema(FrontendFormBaseSchema):
    """
    Validates input for the plugin that checks if all vectors form one connected component via orthogonality edges.
    Either multiple vectors or a .qcd circuit descriptor can be used.
    """

    vectors = SETOFCOMPLEXVECTORS(
        required=False,
        metadata={
            "label": "Input Vectors",
            "description": "A set of complex vectors. Each vector is a list of [re, im].",
            "input_type": "textarea",
        },
    )

    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": "Optional threshold. Defaults to 1e-10.",
            "input_type": "text",
        },
    )

    circuit = NullAbleFileUrl(
        required=False,
        allow_none=True,
        data_input_type="application/x-qcd",
        data_content_types="application/json",
        metadata={
            "label": "Circuit Descriptor (.qcd)",
            "description": "If provided, we decode vectors from QASM. Tolerance for BFS might be separate or the same.",
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": "Min probability for decoding bits from circuit. Default ~1e-5.",
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        if data.get("tolerance") in ("", None):
            data["tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        if data.get("vectors") and data.get("circuit"):
            raise ValueError("Either 'vectors' or 'circuit' can be provided, not both.")
        if not data.get("vectors") and not data.get("circuit"):
            raise ValueError("Must provide either 'vectors' or 'circuit'.")

        if data.get("vectors"):
            data["circuit"] = None
            data["probability_tolerance"] = None
        else:
            data["vectors"] = None
            data["tolerance"] = None

        return data
