# schemas.py

import marshmallow as ma
from common.marshmallow_util import COMPLEXVECTOR, TOLERANCE, NullAbleFileUrl
from qhana_plugin_runner.api.util import FrontendFormBaseSchema


class ClassicalStateAnalysisSchmidtrankParametersSchema(FrontendFormBaseSchema):
    """
    Validates either:
      - one vector (COMPLEXVECTOR) plus dimA, dimB,
      - or a circuit descriptor (.qcd) from which we decode exactly one vector.
    """

    vector = COMPLEXVECTOR(
        required=False,
        metadata={
            "label": "Input Vector",
            "description": "A single bipartite state as [ [re, im], ... ].",
            "input_type": "textarea",
        },
    )

    dimA = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim A",
            "description": "Dimension of subsystem A if using direct vector.",
            "input_type": "number",
        },
    )

    dimB = ma.fields.Integer(
        required=True,
        metadata={
            "label": "Dim B",
            "description": "Dimension of subsystem B if using direct vector.",
            "input_type": "number",
        },
    )

    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": "Optional threshold for Schmidt rank. Defaults to 1e-10.",
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
            "description": "If used, we decode one vector from QASM for Schmidt rank.",
            "input_type": "text",
        },
    )

    probability_tolerance = TOLERANCE(
        required=False,
        metadata={
            "label": "Probability Tolerance",
            "description": "Min probability threshold for decoding from circuit. Default ~1e-5.",
            "input_type": "text",
        },
    )

    @ma.post_load
    def validate_data(self, data, **kwargs):
        if data.get("tolerance") in ("", None):
            data["tolerance"] = None
        if data.get("probability_tolerance") in ("", None):
            data["probability_tolerance"] = None

        vector = data.get("vector")
        circuit = data.get("circuit")

        if vector and circuit:
            raise ValueError("Either 'vector' or 'circuit' can be provided, not both.")
        if not vector and not circuit:
            raise ValueError("Must provide either 'vector' or 'circuit' input.")

        # If vector => must have dimA, dimB
        if vector:
            if data.get("dimA") is None or data.get("dimB") is None:
                raise ValueError("dimA and dimB are required if 'vector' is given.")
            data["circuit"] = None
            data["probability_tolerance"] = None
        else:
            data["vector"] = None

        return data
