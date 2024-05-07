from vital_ai_vitalsigns.query.vital_query import VitalQuery


class VitalSelectQuery(VitalQuery):
    def __init__(self):
        self.segments = []
        self.node_constraints = []
        self.edge_constraints = []

    def add_segment(self, segment):
        self.segments.append(segment)
        return self

    def __repr__(self):
        return f"SelectQuery(segments={self.segments}, node_constraints={self.node_constraints}, edge_constraints={self.edge_constraints})"

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


