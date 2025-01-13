import marshmallow as ma
from qhana_plugin_runner.api.util import FrontendFormBaseSchema
from .marshmallow_util import TOLERANCE, SETOFCOMPLEXVECTORS, COMPLEXVECTOR, COMPLEXNUMBER

class ClassicalStateAnalysisLineardependenceParametersSchema(FrontendFormBaseSchema):
    """Schema for classical state analysis of linear dependence."""

    vectors = SETOFCOMPLEXVECTORS(
        required=True,
        metadata={
            "label": "Input Vectors",
            "description": (
                ""
                "Example: [[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]],[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]],[[1.0, 0.0],[1.0, 0.0],[1.0, 0.0]]]"
            ),
            "input_type": "textarea",
        },
    )

    tolerance = TOLERANCE(
        default_tolerance=1e-10,
        metadata={
            "label": "Tolerance",
            "description": (
                "Provide an optional tolerance value for the analysis. "
                "If not provided, the default value: `1e-10` will be used."
            ),
            "input_type": "text",
        },
    )

@ma.post_load
def validate_data(self, data, **kwargs):
    try:
        # Überprüfe, ob die Eingabe ein Dictionary ist und die erforderlichen Schlüssel enthält
        if not isinstance(data, dict):
            raise ma.ValidationError("Input data must be a dictionary.")

        # Überprüfe, ob 'vectors' im Dictionary enthalten ist
        if 'vectors' not in data:
            raise ma.ValidationError("Input data must contain a 'vectors' key.")

        # Überprüfe, ob 'tolerance' im Dictionary enthalten ist
        if 'tolerance' not in data:
            raise ma.ValidationError("Input data must contain a 'tolerance' key.")

        # Extrahiere die Vektoren
        vectors = data['vectors']

        # Konvertiere jede Liste von Vektoren in komplexe Zahlen
        processed_data = [
            [complex(real, imag) for real, imag in vector]
            for vector in vectors
        ]

        # Optional: Füge die Toleranz in die Rückgabe ein
        tolerance = data['tolerance']
        return {"processed_vectors": processed_data, "tolerance": tolerance}
    
    except ValueError as e:
        raise ma.ValidationError(f"Invalid vector format in data: {data}. Error: {e}")
    except Exception as e:
        raise ma.ValidationError(f"An unexpected error occurred: {e}")
