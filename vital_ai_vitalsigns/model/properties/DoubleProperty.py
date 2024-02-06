from .IProperty import IProperty


class DoubleProperty(IProperty):
    def __init__(self, value: float):
        super().__init__(value)
