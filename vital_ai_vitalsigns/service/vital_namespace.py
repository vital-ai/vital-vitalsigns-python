

class VitalNamespace:
    def __init__(self, graph_uri: str = None, is_global = False):
        self._graph_uri: str = graph_uri
        self._is_global: bool = is_global

    def get_namespace(self) -> str:
        return self._graph_uri

    def is_global(self) -> bool:
        return self._is_global

    def to_dict(self) -> dict:
        return {
            "vital_class": "VitalNamespace",
            "graph_uri": self._graph_uri,
            "is_global": self._is_global
        }

    def from_dict(self, namespace_dict: dict) -> None:
        self._graph_uri = namespace_dict.get("graph_uri")
        self._is_global = namespace_dict.get("is_global")

    def __repr__(self):
        return f"VitalNamespace(graph_uri={self._graph_uri}, is_global={self._is_global})"
