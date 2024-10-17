from typing import Literal
from typing_extensions import TypedDict


# constraint across query given values determined at query time

ARC_CONSTRAINT_TYPE = Literal[
    "EXISTS",
    "NOT_EXISTS",
    "COMPARATOR",
]


ARC_COMPARATOR_TYPE = Literal[
    "EQUAL_TO",
    "NOT_EQUAL_TO",
    "GREATER_THAN",
    "LESS_THAN",
    "GREATER_THAN_EQUAL_TO",
    "LESS_THAN_EQUAL_TO",
    "EXISTS",
    "NOT_EXISTS",
    "LIST_CONTAINS",
    "LIST_NOT_CONTAINS",
    "STRING_CONTAINS",
    "STRING_NOT_CONTAINS",
    "ONE_OF_LIST",
    "NONE_OF_LIST"
]


class MetaQLArcConstraint(TypedDict):

    metaql_class: str

    arc_constraint_type: ARC_CONSTRAINT_TYPE
    source_provides_name: str


class ExistsArcConstraint(MetaQLArcConstraint):
    pass


class NotExistsArcConstraint(MetaQLArcConstraint):
    pass


class ComparatorArcConstraint(MetaQLArcConstraint):

    comparator_type: ARC_COMPARATOR_TYPE
    target_provides_name: str


