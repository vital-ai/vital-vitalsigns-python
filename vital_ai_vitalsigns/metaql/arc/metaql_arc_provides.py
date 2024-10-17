from typing import Literal
from typing_extensions import TypedDict


# values set at query time which may have arc constraints applied to them
# or aggregate functions


PROVIDES_SOURCE_TYPE = Literal[
    "NODE",
    "EDGE",
    "HYPER_NODE",
    "HYPER_EDGE",
    "GRAPH_CONTAINER_OBJECT"
]


class MetaQLArcProvides(TypedDict):

    metaql_class: str

    provides_source_type: PROVIDES_SOURCE_TYPE
    provides_name: str
    property_uri: str
