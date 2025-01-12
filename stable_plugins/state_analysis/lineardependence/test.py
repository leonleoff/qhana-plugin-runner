from marshmallow_util import COMPLEXNUMBER, COMPLEXVECTOR
import marshmallow as ma

# Tests for COMPLEXNUMBER

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

# Tests for COMPLEXVECTOR

def test_complexvector_field_valid():
    """Test a valid complex vector."""
    class MySchema(ma.Schema):
        complex_vector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {
    "complex_vector": [
        [1.0, -2.0],
        [3.5, 4.0],
        [-1.5, 0.0]
    ]
    }

    output_data = {
    "complex_vector": [
        complex(1.0, -2.0),
        complex(3.5, 4.0),
        complex(-1.5, 0.0)
    ]
    }
    
    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

def test_complexvector_field_invalid_element():
    """Test a complex vector with an invalid element."""
    class MySchema(ma.Schema):
        complex_vector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {
        "complex_vector": [
            [1.0, -2.0],
            "invalid_element"  # Not a list or tuple
        ]
    }

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"

def test_complexvector_field_empty():
    """Test an empty complex vector."""
    class MySchema(ma.Schema):
        complex_vector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {"complex_vector": []}  # Empty list

    result = schema.load(input_data)
    assert result == {"complex_vector": []}, f"Unexpected result: {result}"

def test_complexvector_field_missing():
    """Test missing complex vector field."""
    class MySchema(ma.Schema):
        complex_vector = COMPLEXVECTOR(required=True)

    schema = MySchema()

    input_data = {}  # Missing 'complex_vector'
    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Missing data for required field." in str(e), f"Unexpected error: {e}"

# Run tests
if __name__ == "__main__":
    
    # Tests for COMPLEXNUMBER
    test_complexnumber_field_valid()
    test_complexnumber_field_invalid_structure()
    test_complexnumber_field_invalid_types()
    test_complexnumber_field_missing_field()

    # Tests for COMPLEXVECTOR
    test_complexvector_field_valid()
    test_complexvector_field_invalid_element()
    test_complexvector_field_empty()
    test_complexvector_field_missing()
    print("All tests passed.")
