from .IProperty import IProperty


class LongProperty(IProperty):
    def __init__(self, value: int):
        super().__init__(value)

    def __str__(self):
        return str(self.value)