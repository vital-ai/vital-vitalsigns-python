from vital_ai_vitalsigns.model.properties.IProperty import IProperty


class BooleanProperty(IProperty):
    def __init__(self, value: bool):
        bool_value = bool(value)
        super().__init__(bool_value)

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

