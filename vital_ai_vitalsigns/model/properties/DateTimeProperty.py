from datetime import datetime
from .IProperty import IProperty


class DateTimeProperty(IProperty):
    def __init__(self, value: datetime):
        super().__init__(value)

    def __bool__(self):
        return self.value is not None

    def __getattr__(self, attr):
        return getattr(self.value, attr)

    def __str__(self):
        return self.value.strftime('%Y-%m-%d')

    def __eq__(self, other):
        if isinstance(other, datetime):
            return self.value == other
        elif isinstance(other, DateTimeProperty):
            return self.value == other.value
        return NotImplemented

    def __rshift__(self, other):
        return self == other

    def to_json(self):
        return {"value": self.value}

