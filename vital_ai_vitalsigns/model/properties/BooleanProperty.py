from .IProperty import IProperty


class BooleanProperty(IProperty):
    def __init__(self, value: bool):
        super().__init__(value)

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        if isinstance(other, bool):
            return self.value == other
        elif isinstance(other, BooleanProperty):
            return self.value == other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}

