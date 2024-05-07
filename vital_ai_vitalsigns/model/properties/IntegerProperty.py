from .IProperty import IProperty


class IntegerProperty(IProperty):
    def __init__(self, value: int):
        super().__init__(value)

    def __bool__(self):
        return bool(self.value)

    def __getattr__(self, attr):
        return getattr(self.value, attr)

    def __int__(self):
        return int(self.value)

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        elif isinstance(other, IntegerProperty):
            return self.value == other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}
