import marshmallow as ma

# Note: To make this import work, you may need to set the PYTHONPATH environment variable.
# Example (in PowerShell): $env:PYTHONPATH="Path/to/qhana-plugin-runner"
from qhana_plugin_runner.api.util import FrontendFormBaseSchema
from stable_plugins.state_analysis.orthogonality.marshmallow_util import (
    COMPLEXNUMBER,
    COMPLEXVECTOR,
    SETOFTWOCOMPLEXVECTORS,
    TOLERANCE,
)

# Tests for TOLERANCE


def test_tolerance_valid():
    """Test valid tolerance values."""

    class MySchema(FrontendFormBaseSchema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {"tolerance": 0.01}
    output_data = {"tolerance": 0.01}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


def test_tolerance_empty_string():
    """Test tolerance with an empty string."""

    class MySchema(FrontendFormBaseSchema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {"tolerance": ""}
    output_data = {"tolerance": 1e-5}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


def test_tolerance_invalid_type():
    """Test tolerance with invalid input type."""

    class MySchema(FrontendFormBaseSchema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {"tolerance": "invalid"}

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Not a valid number." in str(e), f"Unexpected error: {e}"


def test_tolerance_missing_field():
    """Test when tolerance field is missing."""

    class MySchema(FrontendFormBaseSchema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {}
    output_data = {"tolerance": 1e-5}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


# Tests for COMPLEXNUMBER


def test_complexnumber_field_valid():
    """Test a valid complex number."""

    class MySchema(FrontendFormBaseSchema):
        complexNumber = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {"complexNumber": [2.0, 1.0]}
    output_data = {"complexNumber": [2.0, 1.0]}
    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


# Test for COMPLEXNUMBER
def test_complexnumber_field_string_input():
    """Test a valid complex number provided as a JSON string."""

    class MySchema(ma.Schema):
        complexNumber = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {"complexNumber": "[2.0, 1.0]"}
    output_data = {"complexNumber": [2.0, 1.0]}
    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


def test_complexnumber_field_invalid_structure():
    """Test an invalid structure for the complex number."""

    class MySchema(FrontendFormBaseSchema):
        complexNumber = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {"complexNumber": [2.0]}  # Missing imaginary part
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input length. Expected two elements: [real, imag]." in str(
            e
        ), f"Unexpected error: {e}"


def test_complexnumber_field_invalid_types():
    """Test invalid types for the real and imaginary parts."""

    class MySchema(FrontendFormBaseSchema):
        complexNumber = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {"complexNumber": ["real", 1.0]}  # Invalid real part
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert (
            "Invalid numbers provided. Real and imaginary parts must be valid floats."
            in str(e)
        ), f"Unexpected error: {e}"


def test_complexnumber_field_missing_field():
    """Test missing complex number field."""

    class MySchema(FrontendFormBaseSchema):
        complexNumber = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {}  # Missing 'complexNumber'
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Missing data for required field." in str(e), f"Unexpected error: {e}"


# Tests for COMPLEXVECTOR


def test_complexvector_field_valid():
    """Test a valid complex vector."""

    class MySchema(FrontendFormBaseSchema):
        complexVector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {"complexVector": [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]]}

    output_data = {"complexVector": [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]]}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


def test_complexvector_field_invalid_element():
    """Test a complex vector with an invalid element."""

    class MySchema(FrontendFormBaseSchema):
        complexVector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {
        "complexVector": [[1.0, -2.0], "invalid_element"]  # Not a list or tuple
    }

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


def test_complexvector_field_empty():
    """Test an empty complex vector."""

    class MySchema(FrontendFormBaseSchema):
        complexVector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {"complexVector": []}  # Empty list

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


def test_complexvector_field_missing():
    """Test missing complex vector field."""

    class MySchema(FrontendFormBaseSchema):
        complexVector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {}  # Missing 'complexVector'
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Missing data for required field." in str(e), f"Unexpected error: {e}"


def test_settwocomplexvectors_field_valid():
    """Test a valid set of complex vectors."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complexVectors": [
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
            [[3.0, -2.0], [5.5, 6.0], [-1.5, 9.0]],
        ]
    }

    output_data = {
        "complexVectors": [
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
            [[3.0, -2.0], [5.5, 6.0], [-1.5, 9.0]],
        ]
    }

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


def test_settwocomplexvectors_field_valid():
    """Test a valid set of complex vectors."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complexVectors": [
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
            [[3.0, -2.0], [5.5, 6.0], [-1.5, 9.0]],
        ]
    }

    output_data = {
        "complexVectors": [
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
            [[3.0, -2.0], [5.5, 6.0], [-1.5, 9.0]],
        ]
    }

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"


def test_settwocomplexvectors_field_tosmall():
    """Test a to small set of complex vectors."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complexVectors": [
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
        ]
    }

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


def test_settwocomplexvectors_field_tobig():
    """Test a to small set of complex vectors."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complexVectors": [
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
            [[1.0, -2.0], [3.5, 4.0], [-1.5, 0.0]],
        ]
    }

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


def test_settwocomplexvectors_field_empty():
    """Test an empty set of complex vectors."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {"complexVectors": []}
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


def test_settwocomplexvectors_field_invalid_element():
    """Test a set of complex vectors with an invalid element."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complexVectors": [
            [[1.0, -2.0], "invalid_element", [-1.5, 0.0]]  # Not a list or tuple
        ]
    }

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


def test_settwocomplexvectors_field_missing():
    """Test missing complex vectors field."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {}  # Missing 'complexVectors'

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Missing data for required field." in str(e), f"Unexpected error: {e}"


def test_settwocomplexvectors_field_invalid_structure():
    """Test a set of complex vectors with an invalid structure."""

    class MySchema(FrontendFormBaseSchema):
        complexVectors = SETOFTWOCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {"complexVectors": [[[1.0], [3.5, 4.0]]]}  # Missing imaginary part

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


# Run tests
if __name__ == "__main__":

    # Tests for TOLERANCE
    # TODO: test_tolerance_missing_field()
    test_tolerance_valid()
    test_tolerance_empty_string()
    test_tolerance_invalid_type()

    # Tests for COMPLEXNUMBER
    test_complexnumber_field_valid()
    test_complexnumber_field_invalid_structure()
    test_complexnumber_field_invalid_types()
    test_complexnumber_field_missing_field()
    test_complexnumber_field_string_input()

    # Tests for COMPLEXVECTOR
    test_complexvector_field_valid()
    test_complexvector_field_invalid_element()
    test_complexvector_field_empty()
    test_complexvector_field_missing()

    # Tests for SETOFTWOCOMPLEXVECTORS
    test_settwocomplexvectors_field_valid()
    test_settwocomplexvectors_field_empty()
    test_settwocomplexvectors_field_invalid_element()
    test_settwocomplexvectors_field_missing()
    test_settwocomplexvectors_field_invalid_structure()
    test_settwocomplexvectors_field_tosmall()
    test_settwocomplexvectors_field_tobig()

    print("All tests passed.")
