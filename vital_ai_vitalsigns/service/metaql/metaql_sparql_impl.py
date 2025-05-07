from typing import List, Set


class MetaQLSparqlImpl:

    def __init__(self):

        self._filter_list: List[str] = []
        self._constraint_list: List[str] = []
        self._binding_list: Set[str] = set()
        self._bind_constraint_list: List[str] = []
        self._limit: int = 0
        self._offset: int = 0
        self._resolve_objects: bool = False
        self._graph_uri_list: List[str] = []
        self._graph_id_list: List[str] = []
        self._root_binding: str | None = None

    def set_resolve_objects(self, resolve_objects: bool):
        self._resolve_objects = resolve_objects

    def get_resolve_objects(self) -> bool:
        return self._resolve_objects

    def set_root_binding(self, binding: str):
        self._root_binding = binding

    def get_root_binding(self) -> str:
        return self._root_binding

    def set_limit(self, limit: int):
        self._limit = limit

    def get_limit(self):
        return self._limit

    def set_offset(self, offset: int):
        self._offset = offset

    def get_offset(self):
        return self._offset

    def set_graph_uri_list(self, graph_uri_list: List[str]):
        self._graph_uri_list = graph_uri_list

    def get_graph_uri_list(self):
        return self._graph_uri_list

    def set_graph_id_list(self, graph_id_list: List[str]):
        self._graph_id_list = graph_id_list

    def get_graph_id_list(self):
        return self._graph_id_list

    def add_filter(self, filter_term: str):
        self._filter_list.append(filter_term)

    def get_filter_list(self) -> List[str]:
        return self._filter_list

    def add_arc_constraint(self, constraint_term: str):
        self._constraint_list.append(constraint_term)

    def get_arc_constraint_list(self) -> List[str]:
        return self._constraint_list

    def add_bind_constraint(self, bind_term: str):
        self._bind_constraint_list.append(bind_term)

    def get_bind_constraint_list(self) -> List[str]:
        return self._bind_constraint_list

    def add_binding(self, binding: str):
        self._binding_list.add(binding)

    def get_binding_list(self) -> Set[str]:
        return self._binding_list



