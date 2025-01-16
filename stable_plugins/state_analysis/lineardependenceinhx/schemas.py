import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS, TOLERANCE
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisLineardependenceInHXParametersSchema(FrontendFormBaseSchema):
    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": (
                "A set of complex vectors. "
                "Example: [[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]],[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]],[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]]]"
            ),
            "input_type": "textarea",
        },
    )

    dimA = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim A",
            "description": ("A number specifying the dimension of A. " "Example: 2"),
            "input_type": "number",
        },
    )

    dimB = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim B",
            "description": ("A number specifying the dimension of B. " "Example: 2"),
            "input_type": "number",
        },
    )

    singularValueTolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Singular Value Tolerance",
            "description": (
                "Optional tolerance value for filtering singular values. "
                "Default: 1e-10."
            ),
            "input_type": "text",
        },
    )

    linearDependenceTolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Linear Dependence Tolerance",
            "description": (
                "Optional tolerance value for determining matrix rank. " "Default: 1e-10."
            ),
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        # transform 'tolerance'
        if data["singularValueTolerance"] == "":
            data["singularValueTolerance"] = None

        if data["linearDependenceTolerance"] == "":
            data["linearDependenceTolerance"] = None

        return data
