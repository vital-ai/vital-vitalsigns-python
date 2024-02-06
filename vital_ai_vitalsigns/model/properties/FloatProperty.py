from .IProperty import IProperty


class FloatProperty(IProperty):
    def __init__(self, value: float):
        super().__init__(value)
