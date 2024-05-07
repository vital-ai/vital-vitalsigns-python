from .IProperty import IProperty


class GeoLocationProperty(IProperty):
    def __init__(self, value: str):
        super().__init__(value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        elif isinstance(other, GeoLocationProperty):
            return self.value == other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}
