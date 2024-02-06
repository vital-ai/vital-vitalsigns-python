from datetime import datetime
from .IProperty import IProperty


class DateTimeProperty(IProperty):
    def __init__(self, value: datetime):
        super().__init__(value)

    def __str__(self):
        return self.value.strftime('%Y-%m-%d')
