import traceback
from vital_ai_vitalsigns.model.properties.IProperty import IProperty

class FloatProperty(IProperty):
    def __init__(self, value: float):
        float_value = float(value)
        super().__init__(float_value)

    @classmethod
    def get_data_class(cls):
        return float

    def __bool__(self) -> bool:
        return bool(self.value)

    def __getattr__(self, attr):

        if attr == 'value':
            traceback.print_exc()
            raise AttributeError(f"'FloatProperty' accessing value '{attr}'")

        return getattr(self.value, attr)

    def __float__(self):
        return float(self.value)

    def __eq__(self, other) -> bool:
        if isinstance(other, float):
            return self.value == other
        elif isinstance(other, FloatProperty):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, float):
            return self.value < other
        elif isinstance(other, FloatProperty):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> bool:
        if isinstance(other, float):
            return self.value <= other
        elif isinstance(other, FloatProperty):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, float):
            return self.value > other
        elif isinstance(other, FloatProperty):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other) -> bool:
        if isinstance(other, float):
            return self.value >= other
        elif isinstance(other, FloatProperty):
            return self.value >= other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}
