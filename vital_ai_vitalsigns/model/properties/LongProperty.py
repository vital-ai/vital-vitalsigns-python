import traceback
from vital_ai_vitalsigns.model.properties.IProperty import IProperty

class LongProperty(IProperty):
    def __init__(self, value: int):
        long_value = int(value)
        super().__init__(long_value)

    @classmethod
    def get_data_class(cls):
        return int

    def __bool__(self) -> bool:
        return bool(self.value)

    def __getattr__(self, attr):

        if attr == 'value':
            traceback.print_exc()
            raise AttributeError(f"'LongProperty' accessing value '{attr}'")

        return getattr(self.value, attr)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other) -> bool:
        if isinstance(other, int):
            return self.value == other
        elif isinstance(other, LongProperty):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, int):
            return self.value < other
        elif isinstance(other, LongProperty):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> bool:
        if isinstance(other, int):
            return self.value <= other
        elif isinstance(other, LongProperty):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, int):
            return self.value > other
        elif isinstance(other, LongProperty):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other) -> bool:
        if isinstance(other, int):
            return self.value >= other
        elif isinstance(other, LongProperty):
            return self.value >= other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}