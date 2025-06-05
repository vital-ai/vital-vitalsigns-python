import traceback
from vital_ai_vitalsigns.model.properties.IProperty import IProperty

class OtherProperty(IProperty):
    def __init__(self, value: str):
        str_value = str(value)
        super().__init__(str_value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __getattr__(self, attr):

        if attr == 'value':
            traceback.print_exc()
            raise AttributeError(f"'OtherProperty' accessing value '{attr}'")

        return getattr(self.value, attr)

    def __str__(self):
        return str(self.value)

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}
