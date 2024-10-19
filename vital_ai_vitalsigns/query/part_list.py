from typing import Any, List, TypeVar, Optional
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.part.graph_part import GraphPart


G = TypeVar('G', bound=Optional[GraphObject])
GP = TypeVar('GP', bound=Optional[GraphPart])


class PartList(List[GraphPart]):
    def __init__(self, *args):
        super().__init__(*args)
        self.offset = None
        self.limit = None
        self.message = None
        self.status = None

    def add_part(self, graph_part: GP):
        """
        Adds a GraphPart to the list.
        :param graph_part: The GraphPart.
        """
        self.append(graph_part)

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

