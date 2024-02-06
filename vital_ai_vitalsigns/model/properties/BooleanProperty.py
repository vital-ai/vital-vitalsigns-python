from .IProperty import IProperty


class BooleanProperty(IProperty):
    def __init__(self, value: bool):
        super().__init__(value)

