from marshmallow_util import COMPLEXNUMBER
import marshmallow as ma

# Tests for Schemas

def test_complexnumber_field_valid():
    """Test a valid complex number."""
    class MySchema(ma.Schema):
        complex_number = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {"complex_number": [2.0, 1.0]}
    output_data = {"complex_number": complex(2.0, 1.0)}
    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

def test_complexnumber_field_invalid_structure():
    """Test an invalid structure for the complex number."""
    class MySchema(ma.Schema):
        complex_number = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {"complex_number": [2.0]}  # Missing imaginary part
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input length. Expected two elements: [real, imag]." in str(e), f"Unexpected error: {e}"


def test_complexnumber_field_invalid_types():
    """Test invalid types for the real and imaginary parts."""
    class MySchema(ma.Schema):
        complex_number = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {"complex_number": ["real", 1.0]}  # Invalid real part
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid numbers provided. Real and imaginary parts must be valid floats." in str(e), f"Unexpected error: {e}"


def test_complexnumber_field_missing_field():
    """Test missing complex number field."""
    class MySchema(ma.Schema):
        complex_number = COMPLEXNUMBER(required=True)

    schema = MySchema()

    input_data = {}  # Missing 'complex_number'
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Missing data for required field." in str(e), f"Unexpected error: {e}"

# Run tests
if __name__ == "__main__":
    test_complexnumber_field_valid()
    test_complexnumber_field_invalid_structure()
    test_complexnumber_field_invalid_types()
    test_complexnumber_field_missing_field()
    print("All tests passed.")
