from .IProperty import IProperty


class OtherProperty(IProperty):
    def __init__(self, value: str):
        super().__init__(value)

    def __bool__(self):
        return bool(self.value)

    def __getattr__(self, attr):
        return getattr(self.value, attr)

    def __str__(self):
        return str(self.value)

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}
