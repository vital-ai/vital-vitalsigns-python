from vital_ai_vitalsigns.model.properties.IProperty import IProperty


# TODO add in implementation

class TruthProperty(IProperty):
    def __init__(self, value: str):
        str_value = str(value)
        super().__init__(str_value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        elif isinstance(other, TruthProperty):
            return self.value == other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}
