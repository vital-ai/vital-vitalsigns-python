from vital_ai_vitalsigns.query.vital_query import VitalQuery


class VitalGraphQuery(VitalQuery):
    def __init__(self):
        self.segments = []
        self.arcs = []

    def add_segment(self, segment):
        self.segments.append(segment)
        return self

    def add_arc(self, arc):
        self.arcs.append(arc)
        return self

    def __repr__(self):
        return f"GraphQuery(segments={self.segments}, arcs={self.arcs})"


class Assignment:
    def __init__(self, variable):
        self.variable = variable

    def to(self, value):
        if isinstance(value, type):
            value = value.__name__
        return f"{self.variable} = {value}"


def bind(variable):
    return Assignment(variable)


def ref(variable):
    return f"?{variable}"


class Arc:
    def __init__(self):
        self.node_constraints = []
        self.edge_constraints = []
        self.constraints = []
        self.provisions = []
        self.arcs = []

    def node_constraint(self, constraint):
        if isinstance(constraint, type):
            constraint = f"{constraint.__name__}"
        self.node_constraints.append(constraint)
        return self

    def edge_constraint(self, constraint):
        if isinstance(constraint, type):
            constraint = constraint().__repr__()
        self.edge_constraints.append(constraint)
        return self

    def constraint(self, constraint):
        self.constraints.append(constraint)
        return self

    def provides(self, provision):
        self.provisions.append(provision)
        return self

    def add_arc(self, arc):
        self.arcs.append(arc)
        return self

    def __repr__(self):
        return (f"Arc(node_constraints={self.node_constraints}, "
                f"edge_constraints={self.edge_constraints}, "
                f"constraints={self.constraints}, "
                f"provisions={self.provisions}, arcs={self.arcs})")

    def to_sparql(self):
        sparql = ""
        return sparql


class ArcGroup:
    pass


class ArcOr(ArcGroup):
    def __init__(self):
        self.arcs = []

    def add_arc(self, arc):
        self.arcs.append(arc)
        return self

    def __repr__(self):
        return f"ArcOr(arcs={self.arcs})"


class ArcAnd(ArcGroup):
    def __init__(self):
        self.arcs = []

    def add_arc(self, arc):
        self.arcs.append(arc)
        return self

    def __repr__(self):
        return f"ArcAnd(arcs={self.arcs})"

