import json

import marshmallow as ma


class TOLERANCE(ma.fields.Float):
    """A Float field with a default value when an empty string is provided."""

    def __init__(
        self,
        *,
        default_tolerance: float,
        allow_nan: bool = False,
        as_string: bool = False,
        **kwargs,
    ):
        self.default_tolerance = default_tolerance
        super().__init__(as_string=as_string, **kwargs, missing=default_tolerance)

    def _deserialize(self, value, attr, data, **kwargs):
        # Replace empty string or None with the default tolerance value
        if value == "" or value is None:
            value = self.default_tolerance
        return super()._validated(value)


class COMPLEXNUMBER(ma.fields.Field):

    def _deserialize(self, value, attr, data, **kwargs):
        # Check if the value is a string and try to parse it into a list or tuple
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ma.ValidationError(
                    f"Invalid input. Expected a JSON string representing a list or tuple, but the input string could not be parsed: {value}"
                )

        # Check if the value is an array (list or tuple)
        if not isinstance(value, (list, tuple)):
            raise ma.ValidationError(
                f"Invalid input. Expected a list or tuple with two elements: [real, imag]. But the input was {value}"
            )
        # Ensure the array has exactly two elements
        if len(value) != 2:
            raise ma.ValidationError(
                f"Invalid input length. Expected two elements: [real, imag]. But the input was {value}"
            )
        try:
            # Attempt to convert the values to floats
            real, imag = float(value[0]), float(value[1])
            return [real, imag]
        except (ValueError, TypeError):
            raise ma.ValidationError(
                f"Invalid numbers provided. Real and imaginary parts must be valid floats. But the input was {value}"
            )


class COMPLEXVECTOR(ma.fields.Field):
    """Field for deserializing a vector of complex numbers."""

    def _deserialize(self, value, attr, data, **kwargs):
        # Check if the value is a string and try to parse it into a list or tuple
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ma.ValidationError(
                    f"Invalid input. Expected a JSON string representing a list or tuple, but the input string could not be parsed: {value}"
                )

        # Validate that the value is a list
        if not isinstance(value, list):
            raise ma.ValidationError(
                f"Invalid input. Expected a list of complex number representations, but the input was: {value}"
            )

        # Validate that the list is not empty
        if not value:
            raise ma.ValidationError(
                "Invalid input. The list of complex number representations cannot be empty."
            )

        # Deserialize each complex number in the vector
        output = []
        for comp_num in value:
            try:
                deserialized_num = COMPLEXNUMBER().deserialize(comp_num)
                output.append(deserialized_num)
            except ma.ValidationError as e:
                raise ma.ValidationError(
                    f"Invalid complex number in vector: {comp_num}. Error: {e.messages}"
                )

        return output


class SETOFTWOCOMPLEXVECTORS(ma.fields.Field):

    def _deserialize(self, value, attr, data, **kwargs):
        # Check if the value is a string and try to parse it into a list or tuple
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ma.ValidationError(
                    f"Invalid input. Expected a JSON string representing a list or tuple, but the input string could not be parsed: {value}"
                )

        # Validate that the value is a list
        if not isinstance(value, list):
            raise ma.ValidationError(
                f"Invalid input. Expected a list of complex vector representations. But the input was {value}"
            )

        # Validate that there are exactly two vectors in the set
        if not len(value) == 2:
            raise ma.ValidationError(
                f"Invalid input. Expected a list of exactly 2 vectors, but the input was {value}."
            )

        # Deserialize each complex number in the vector
        output = []
        for comp_vec in value:
            try:
                deserialized_vec = COMPLEXVECTOR().deserialize(comp_vec)
                output.append(deserialized_vec)
            except ma.ValidationError as e:
                raise ma.ValidationError(
                    f"Invalid complex vector in set: {comp_vec}. Error: {e.messages}"
                )

        return output
