from typing import List
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.query.result_element import ResultElement


class MetaQLResult:

    def __init__(self, *,
                 offset: int = None,
                 limit: int = None,
                 binding_list: List[str] = None,
                 result_list: List[ResultElement] = None,
                 result_object_list: List[GraphObject] = None,
                 total_result_count: int = 0):

        self._offset: int = offset
        self._limit: int = limit

        self._binding_list: List[str] = []
        self._result_list: List[ResultElement] = []
        self._result_object_list: List[GraphObject] = []

        if binding_list:
            self._binding_list = binding_list

        if result_list:
            self._result_list = result_list

        if result_object_list:
            self._result_object_list = result_object_list

        self._result_count: int = len(self._result_list)
        self._total_result_count: int = total_result_count

    def __repr__(self):
        return f"MetaQLResult(offset={self._offset}, limit={self._limit}, binding_list={self._binding_list}, result_list={self._result_list}, result_object_list={self._result_object_list})"

    def set_offset(self, offset: int):
        self._offset = offset

    def set_limit(self, limit: int):
        self._limit = limit

    def get_offset(self) -> int:
        return self._offset

    def get_limit(self) -> int:
        return self._limit

    def get_binding_list(self) -> List[str]:
        return self._binding_list

    def set_binding_list(self, binding_list: List[str]):
        self._binding_list = binding_list

    def get_result_count(self) -> int:
        return self._result_count

    def add_result_element(self, result_element: ResultElement):
        self._result_list.append(result_element)
        self._result_count = len(self._result_list)

    def set_result_list(self, result_list: List[ResultElement]):
        self._result_list = result_list
        self._result_count = len(self._result_list)

    def get_result_list(self) -> List[ResultElement]:
        return self._result_list

    def set_result_object_list(self, result_object_list: List[GraphObject]):
        self._result_object_list = result_object_list

    def get_result_object_list(self) -> List[GraphObject]:
        return self._result_object_list

    def set_total_result_count(self, total_result_count: int):
        self._total_result_count = total_result_count

    def get_total_result_count(self) -> int:
        return self._total_result_count
