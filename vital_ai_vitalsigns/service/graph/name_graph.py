
class VitalNameGraph:
    def __init__(self, graph_uri):
        self.graph_uri = graph_uri

    def get_graph_uri(self):
        return self.graph_uri

    def __repr__(self):
        return f"VitalNameGraph(graph_uri={self.graph_uri})"

