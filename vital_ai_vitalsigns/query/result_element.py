from typing import Any, List, TypeVar

G = TypeVar('G', bound='GraphObject')


class ResultElement:
    def __init__(self, graph_object: G, score: float = 1.0):
        self.graph_object = graph_object
        self.score = score

    def __repr__(self):
        return f"ResultElement(graph_object={self.graph_object},score={self.score})"
