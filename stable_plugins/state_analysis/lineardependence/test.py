from marshmallow_util import COMPLEXNUMBER
import marshmallow as ma

# Tests for Schemas

def test_complexnumber_field():
    """Test a valid set of complex vectors."""
    class MySchema(ma.Schema):
        complex_number = COMPLEXNUMBER(
            required=True
        )
    schema = MySchema()

    input_data = {"complex_number": [2.0,1.0]}
    output_data = {"complex_number": (2+1j)}
    result = schema.load(input_data)
    assert result == output_data, f"Unexpected result: {result}"

# Run tests
if __name__ == "__main__":
    test_complexnumber_field()
    print("All tests passed.")
