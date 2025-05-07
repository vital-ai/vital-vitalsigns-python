from typing import List, Literal, Optional, Union
from typing_extensions import TypedDict
from vital_ai_vitalsigns.metaql.aggregate.metaql_aggregate import MetaQLAggregate
from vital_ai_vitalsigns.metaql.arc.metaql_arc import Arc, ArcRoot

METAQL_SELECT_QUERY = "METAQL_SELECT_QUERY"
METAQL_GRAPH_QUERY = "METAQL_GRAPH_QUERY"
METAQL_AGGREGATE_SELECT_QUERY = "METAQL_AGGREGATE_SELECT_QUERY"
METAQL_AGGREGATE_GRAPH_QUERY = "METAQL_AGGREGATE_GRAPH_QUERY"


METAQL_QUERY_TYPE = Literal[
    "METAQL_SELECT_QUERY",
    "METAQL_GRAPH_QUERY",
    "METAQL_AGGREGATE_SELECT_QUERY",
    "METAQL_AGGREGATE_GRAPH_QUERY"
]

# Notes:
# To Add:
# Optional Arcs
# provides and internal constraints
# hyper node and hyper edge
# property uri traversals


class MetaQLQuery(TypedDict):

    metaql_class: str

    query_type: METAQL_QUERY_TYPE
    graph_uri_list: Optional[List[str]]
    graph_id_list: Optional[List[str]]

    arc: Union[Arc,ArcRoot]


class SelectQuery(MetaQLQuery):

    offset: int
    limit: int


class AggregateSelectQuery(SelectQuery):

    aggregate: MetaQLAggregate


class GraphQuery(MetaQLQuery):

    resolve_objects: bool
    offset: int
    limit: int


class AggregateGraphQuery(GraphQuery):

    aggregate: MetaQLAggregate

