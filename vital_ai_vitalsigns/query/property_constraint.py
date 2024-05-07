
class PropertyConstraint:
    def __init__(self, expression):
        self.expression = expression

    def __repr__(self):
        return self.expression

    def __eq__(self, other):
        return PropertyConstraint(f"{self.expression} == {other}")

    def __ne__(self, other):
        return PropertyConstraint(f"{self.expression} != {other}")

