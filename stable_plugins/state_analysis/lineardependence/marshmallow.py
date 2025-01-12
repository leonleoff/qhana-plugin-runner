import marshmallow as ma

class TOLERANCE(ma.fields.Float):

    default_tolerance = 0
    def __init__(self, *,default_tolerance: float, allow_nan: bool = False, as_string: bool = False, **kwargs):
        self.default_tolerance = default_tolerance
        self.allow_nan = allow_nan
        super().__init__(as_string=as_string, **kwargs)

    def _validated(self, value):
        if value == "":
            value = self.default_tolerance
        return super()._validated(value)


# Exportierbar machen für andere Module
__all__ = ["TOLERANCE"]