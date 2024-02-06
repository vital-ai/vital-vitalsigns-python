from .IProperty import IProperty


class StringProperty(IProperty):
    def __init__(self, value: str):
        super().__init__(value)

    def __str__(self):
        return str(self.value)
