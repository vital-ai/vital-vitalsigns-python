from typing import Any, List, TypeVar
from vital_ai_vitalsigns.query.result_element import ResultElement


G = TypeVar('G', bound='GraphObject')


class ResultList(List[ResultElement]):
    def __init__(self, *args, limit: int = None, offset: int = None, status: int = 0, message: str = None):
        super().__init__(*args)
        self.limit = limit
        self.offset = offset
        self.message = message
        self.status = status

    def add_result(self, graph_object: G, score: float = 1.0):
        """
        Adds a ResultElement to the list.
        :param graph_object: The associated object (e.g., a document or data structure).
        :param score: The similarity score.
        """
        self.append(ResultElement(graph_object, score))

    def set_status(self, status: int):
        self.status = status

    def set_message(self, message: str):
        self.message = message

    def set_limit(self, limit: int):
        self.limit = limit

    def set_offset(self, offset: int):
        self.offset = offset

    def get_status(self):
        return self.status

    def get_message(self):
        return self.message

    def get_limit(self):
        return self.limit

    def get_offset(self):
        return self.offset

    def is_ok(self) -> bool:
        return self.status == 0








