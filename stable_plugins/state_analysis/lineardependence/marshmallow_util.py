import marshmallow as ma

class TOLERANCE(ma.fields.Float):
    """A Float field with a default value when an empty string is provided."""

    def __init__(self, *, default_tolerance: float, allow_nan: bool = False, as_string: bool = False, **kwargs):
        self.default_tolerance = default_tolerance
        super().__init__(as_string=as_string, **kwargs  ,missing = default_tolerance )

    def _deserialize(self, value, attr, data, **kwargs):
        # Replace empty string or None with the default tolerance value
        if value == "" or value is None:
            value = self.default_tolerance
        return super()._validated(value)


class COMPLEXNUMBER(ma.fields.Field):
    
    def _deserialize(self, value, attr, data, **kwargs):
        # Überprüfen, ob der Wert ein Array (Liste oder Tupel) ist
        if not isinstance(value, (list, tuple)):
            raise ma.ValidationError(
                f"Invalid input. Expected a list or tuple with two elements: [real, imag]. But the input was {value}"
            )
        # Sicherstellen, dass das Array genau zwei Elemente hat
        if len(value) != 2:
            raise ma.ValidationError(
                f"Invalid input length. Expected two elements: [real, imag]. But the input was {value}"
            )
        try:
            # Versuche, die Werte in Floats zu konvertieren
            real, imag = float(value[0]), float(value[1])
            return complex(real, imag)
        except (ValueError, TypeError):
            raise ma.ValidationError(
                f"Invalid numbers provided. Real and imaginary parts must be valid floats. But the input was {value}"
            )


class COMPLEXVECTOR(ma.fields.List):
    """Field for vectors of complex numbers."""
    def __init__(self, **metadata):
        super().__init__(COMPLEXNUMBER(), **metadata)


class SETOFCOMPLEXVECTORS(ma.fields.List):
    """Field for a set of vectors of complex numbers."""
    def __init__(self, **metadata):
        super().__init__(COMPLEXVECTOR(), **metadata)

# Tests for TOLERANCE

def test_tolerance_valid():
    """Test valid tolerance values."""
    class MySchema(ma.Schema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {"tolerance": 0.01}
    output_data = {"tolerance": 0.01}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

def test_tolerance_empty_string():
    """Test tolerance with an empty string."""
    class MySchema(ma.Schema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {"tolerance": ""}
    output_data = {"tolerance": 1e-5}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

def test_tolerance_invalid_type():
    """Test tolerance with invalid input type."""
    class MySchema(ma.Schema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {"tolerance": "invalid"}

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Not a valid number." in str(e), f"Unexpected error: {e}"

def test_tolerance_missing_field():
    """Test when tolerance field is missing."""
    class MySchema(ma.Schema):
        tolerance = TOLERANCE(default_tolerance=1e-5)

    schema = MySchema()

    input_data = {}
    output_data = {"tolerance": 1e-5}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

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

def test_setcomplexvectors_field_valid():
    """Test a valid set of complex vectors."""
    class MySchema(ma.Schema):
        complex_vectors = SETOFCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complex_vectors": [
            [
                [1.0, -2.0],
                [3.5, 4.0],
                [-1.5, 0.0]
            ],
            [
                [3.0, -2.0],
                [5.5, 6.0],
                [-1.5, 9.0]
            ],
            [
                [11.0, -2.0],
                [36.5, 0.0],
                [-1.5, -3.0]
            ]
        ]
    }

    output_data = {
        "complex_vectors": [
            [
                complex(1.0, -2.0),
                complex(3.5, 4.0),
                complex(-1.5, 0.0)
            ],
            [
                complex(3.0, -2.0),
                complex(5.5, 6.0),
                complex(-1.5, 9.0)
            ],
            [
                complex(11.0, -2.0),
                complex(36.5, 0.0),
                complex(-1.5, -3.0)
            ]
        ]
    }

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

def test_setcomplexvectors_field_empty():
    """Test an empty set of complex vectors."""
    class MySchema(ma.Schema):
        complex_vectors = SETOFCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {"complex_vectors": []}
    output_data = {"complex_vectors": []}

    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

def test_setcomplexvectors_field_invalid_element():
    """Test a set of complex vectors with an invalid element."""
    class MySchema(ma.Schema):
        complex_vectors = SETOFCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complex_vectors": [
            [
                [1.0, -2.0],
                "invalid_element",  # Not a list or tuple
                [-1.5, 0.0]
            ]
        ]
    }

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"

def test_setcomplexvectors_field_missing():
    """Test missing complex vectors field."""
    class MySchema(ma.Schema):
        complex_vectors = SETOFCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {}  # Missing 'complex_vectors'

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Missing data for required field." in str(e), f"Unexpected error: {e}"

def test_setcomplexvectors_field_invalid_structure():
    """Test a set of complex vectors with an invalid structure."""
    class MySchema(ma.Schema):
        complex_vectors = SETOFCOMPLEXVECTORS(required=True)

    schema = MySchema()

    input_data = {
        "complex_vectors": [
            [
                [1.0],  # Missing imaginary part
                [3.5, 4.0]
            ]
        ]
    }

    try:
        schema.load(input_data)
    except ma.ValidationError as e:
        assert "Invalid input" in str(e), f"Unexpected error: {e}"


# Run tests
if __name__ == "__main__":

    # Tests for TOLERANCE
    test_tolerance_missing_field()
    test_tolerance_valid()
    test_tolerance_empty_string()
    test_tolerance_invalid_type()
    

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

    # Tests for SETOFCOMPLEXVECTORS
    test_setcomplexvectors_field_valid()
    test_setcomplexvectors_field_empty()
    test_setcomplexvectors_field_invalid_element()
    test_setcomplexvectors_field_missing()
    test_setcomplexvectors_field_invalid_structure()

    print("All tests passed.")
