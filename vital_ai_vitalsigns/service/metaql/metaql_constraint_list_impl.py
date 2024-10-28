from typing import List


class MetaQLConstraintListImpl:

    def __init__(self):
        self._constraints: List[str] = []
        self._constraint_lists: List["MetaQLConstraintListImpl"] = []

    def add_constraint(self, constraint: str):
        self._constraints.append(constraint)

    def get_constraints(self):
        return self._constraints

    def add_constraint_list(self, constraint_list: "MetaQLConstraintListImpl"):
        self._constraint_lists.append(constraint_list)

    def get_constraint_lists(self) -> List["MetaQLConstraintListImpl"]:
        return self._constraint_lists


class AndConstraintListImpl(MetaQLConstraintListImpl):
    pass


class OrConstraintListImpl(MetaQLConstraintListImpl):
    pass


