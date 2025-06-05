from typing import Literal, List
from typing_extensions import TypedDict
from vital_ai_vitalsigns.metaql.constraint.metaql_constraint import MetaQLConstraint

# initial implementation to support flat constraint list
# to be extended with n-depth lists within lists

AND_CONSTRAINT_LIST_TYPE = "AND_CONSTRAINT_LIST_TYPE"
OR_CONSTRAINT_LIST_TYPE = "OR_CONSTRAINT_LIST_TYPE"

CONSTRAINT_LIST_TYPE = Literal[
    "AND_CONSTRAINT_LIST_TYPE",
    "OR_CONSTRAINT_LIST_TYPE"
]


class MetaQLConstraintList(TypedDict):

    metaql_class: str

    constraint_list_type: CONSTRAINT_LIST_TYPE
    constraint_list: List[MetaQLConstraint]


class AndConstraintList(MetaQLConstraintList):
    pass


class OrConstraintList(MetaQLConstraintList):
    pass
