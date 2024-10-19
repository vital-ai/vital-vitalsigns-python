from typing import List


class MetaQLSparqlImpl:

    def __init__(self):

        self._filter_list: List[str] = []
        self._constraint_list: List[str] = []

    def get_filter_list(self) -> List[str]:
        return self._filter_list

    def get_constraint_list(self) -> List[str]:
        return self._constraint_list

    def add_filter(self, filter_term: str):
        self._filter_list.append(filter_term)

    def add_constraint(self, constraint_term: str):
        self._constraint_list.append(constraint_term)

