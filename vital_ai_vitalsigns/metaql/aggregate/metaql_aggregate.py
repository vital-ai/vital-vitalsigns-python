from typing import Literal
from typing_extensions import TypedDict


AGGREGATE = Literal[
    "AVERAGE",
    "SUM",
    "MAXIMUM",
    "MINIMUM"
    ]


class MetaQLAggregate(TypedDict):

    metaql_class: str

    provides_name: str
    aggregate_type: AGGREGATE
