import traceback
from datetime import datetime
from vital_ai_vitalsigns.model.properties.IProperty import IProperty


class DateTimeProperty(IProperty):
    def __init__(self, value):

        if isinstance(value, datetime):
            datetime_value = value
            super().__init__(datetime_value)
        elif isinstance(value, int):
            datetime_value = datetime.fromtimestamp(value / 1000)
            super().__init__(datetime_value )
        elif isinstance(value, str):
            try:
                datetime_value = datetime.fromisoformat(value)
                super().__init__(datetime_value)
            except ValueError:
                raise TypeError(f"Unsupported string {value} for datetime property: {type(value).__name__}")
        else:
            raise TypeError(f"Unsupported type in value {value} for datetime property: {type(value).__name__}")

    @classmethod
    def get_data_class(cls):
        return datetime

    def __bool__(self) -> bool:
        return self.value is not None

    def __getattr__(self, attr):

        if attr == 'value':
            traceback.print_exc()
            raise AttributeError(f"'DateTimeProperty' accessing value '{attr}'")

        return getattr(self.value, attr)

    def __str__(self):
        return self.value.strftime('%Y-%m-%d')

    def __eq__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.value == other
        elif isinstance(other, DateTimeProperty):
            return self.value == other.value
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.value < other
        elif isinstance(other, DateTimeProperty):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.value <= other
        elif isinstance(other, DateTimeProperty):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.value > other
        elif isinstance(other, DateTimeProperty):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.value >= other
        elif isinstance(other, DateTimeProperty):
            return self.value >= other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}

