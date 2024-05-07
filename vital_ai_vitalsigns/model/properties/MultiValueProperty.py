from vital_ai_vitalsigns.model.properties.IProperty import IProperty


class MultiValueProperty(IProperty):
    def __init__(self, value: str):
        super().__init__(value)

    def __str__(self):
        return str(self.value)

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}
