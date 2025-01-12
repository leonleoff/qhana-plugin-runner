import marshmallow as ma

class TOLERANCE(ma.fields.Float):
    """A Float field with a default value when an empty string or None is provided."""

    def __init__(self, *, default_tolerance: float, allow_nan: bool = False, as_string: bool = False, **kwargs):
        self.default_tolerance = default_tolerance
        self.allow_nan = allow_nan
        super().__init__(as_string=as_string, **kwargs)

    def _validated(self, value):
        # Replace empty string or None with the default tolerance value
        if value == "" or value is None:
            value = self.default_tolerance
        return super()._validated(value)


class COMPLEXNUMBER(ma.fields.Field):
    def _validated(self, value):
        raise ma.ValidationError("LOL")
        # Replace empty string or None with the default tolerance value
        if value == "" or value is None:
            value = self.default_tolerance
        return super()._validated(value)
    

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


class COMPLEXVECTORSField(ma.fields.List):
    """Field for vectors of complex numbers."""
    def __init__(self, **metadata):
        super().__init__(COMPLEXNUMBERField(), **metadata)


class SETOFCOMPLEXVECTORSField(ma.fields.List):
    """Field for a set of vectors of complex numbers."""
    def __init__(self, **metadata):
        super().__init__(COMPLEXVECTORSField(), **metadata)