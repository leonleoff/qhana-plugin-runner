import marshmallow as ma
from common.marshmallow_util import SETOFCOMPLEXVECTORS, TOLERANCE, NullAbleFileUrl
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisLineardependenceInHXParametersSchema(FrontendFormBaseSchema):
    """
    Validates input for lineardependenceInHX: multiple vectors or .qcd circuit,
    along with dimA, dimB, and optional tolerances.
    """

    vectors = SETOFCOMPLEXVECTORS(
        required=False,
        metadata={
            "label": "Input Vectors",
            "description": "A set of complex vectors for the bipartite space. E.g. [[[1,0],[0,1]]]",
            "input_type": "textarea",
        },
    )

    dimA = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim A",
            "description": "Dimension of subsystem A (only if vectors used).",
            "input_type": "number",
        },
    )

    dimB = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim B",
            "description": "Dimension of subsystem B (only if vectors used).",
            "input_type": "number",
        },
    )

    singularValueTolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Singular Value Tolerance",
            "description": "Optional threshold for SVD-based checks. Defaults to 1e-10.",
            "input_type": "text",
        },
    )

    linearDependenceTolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Linear Dependence Tolerance",
            "description": "Tolerance for matrix rank. Defaults to 1e-10.",
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
            "description": "If provided, vectors/dimA/dimB are ignored.",
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": "Min probability threshold for QASM decoding. Default 1e-5.",
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        if data.get("singularValueTolerance") in ("", None):
            data["singularValueTolerance"] = None
        if data.get("linearDependenceTolerance") in ("", None):
            data["linearDependenceTolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        # If circuit => ignore vectors, dimA, dimB. If vectors => require dimA, dimB
        vectors = data.get("vectors")
        circuit = data.get("circuit")

        if vectors and circuit:
            raise ValueError("Either 'vectors' or 'circuit' can be provided, not both.")
        if not vectors and not circuit:
            raise ValueError("Must provide either 'vectors' or 'circuit' input.")

        if vectors:
            # Must ensure dimA, dimB are set
            if data.get("dimA") is None or data.get("dimB") is None:
                raise ValueError("dimA and dimB are required if vectors are given.")
            # circuit-based fields not used
            data["circuit"] = None
            data["probability_tolerance"] = None
        else:
            # circuit => ignore vectors
            data["vectors"] = None

        return data
