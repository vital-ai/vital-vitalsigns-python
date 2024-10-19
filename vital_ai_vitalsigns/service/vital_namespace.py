

class VitalNamespace:
    def __init__(self, graph_uri: str = None):
        self._graph_uri: str = graph_uri

    def get_namespace(self) -> str:
        return self._graph_uri

    def to_dict(self) -> dict:
        return {
            "vital_class": "VitalNamespace",
            "graph_uri": self._graph_uri
        }

    def from_dict(self, dict: dict) -> None:
        self._graph_uri = dict.get("graph_uri")

    def __repr__(self):
        return f"VitalNamespace(graph_uri={self._graph_uri})"
