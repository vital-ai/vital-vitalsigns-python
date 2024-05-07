
class VitalQuery:
    pass


class Constraint:
    def __init__(self, expression):
        self.expression = expression

    def __repr__(self):
        return self.expression

    def __eq__(self, other):
        return Constraint(f"{self.expression} == {other}")

    def __ne__(self, other):
        return Constraint(f"{self.expression} != {other}")


class Field:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"?{self.name}"

    def __getattr__(self, item):
        return Constraint(f"?{self.name}.{item}")
