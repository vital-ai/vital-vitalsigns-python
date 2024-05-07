from .IProperty import IProperty


class DoubleProperty(IProperty):
    def __init__(self, value: float):
        super().__init__(value)

    def __eq__(self, other):
        if isinstance(other, float):
            return self.value == other
        elif isinstance(other, DoubleProperty):
            return self.value == other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}

