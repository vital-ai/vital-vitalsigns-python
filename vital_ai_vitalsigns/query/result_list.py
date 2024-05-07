from typing import Any, List

from vital_ai_vitalsigns.query.result_element import ResultElement


class ResultList(List[ResultElement]):
    def __init__(self, *args):
        super().__init__(*args)

    def add_result(self, graph_object: Any, score: float = 1.0):
        """
        Adds a ResultElement to the list.
        :param graph_object: The associated object (e.g., a document or data structure).
        :param score: The similarity score.
        """
        self.append(ResultElement(graph_object, score))
