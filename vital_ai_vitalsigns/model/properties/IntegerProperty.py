from .IProperty import IProperty


class IntegerProperty(IProperty):
    def __init__(self, value: int):
        super().__init__(value)
