from vital_ai_vitalsigns.model.properties.IProperty import IProperty


class BooleanProperty(IProperty):
    def __init__(self, value: bool):
        bool_value = bool(value)
        super().__init__(bool_value)

    @classmethod
    def get_data_class(cls):
        return bool

    def __bool__(self) -> bool:
        return bool(self.value)

    def __eq__(self, other) -> bool:
        if isinstance(other, bool):
            return self.value == other
        elif isinstance(other, BooleanProperty):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, bool):
            return self.value < other
        elif isinstance(other, BooleanProperty):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> bool:
        if isinstance(other, bool):
            return self.value <= other
        elif isinstance(other, BooleanProperty):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, bool):
            return self.value > other
        elif isinstance(other, BooleanProperty):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other) -> bool:
        if isinstance(other, bool):
            return self.value >= other
        elif isinstance(other, BooleanProperty):
            return self.value >= other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}

