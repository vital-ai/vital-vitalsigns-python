from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Optional
from typing_extensions import TypedDict
from vital_ai_vitalsigns.metaql.constraint_list.metaql_constraint_list import MetaQLConstraintList

# from vital_ai_vitalsigns.metaql.arc_list.metaql_arc_list import MetaQLArcList

if TYPE_CHECKING:
    # Only import the actual MetaQLArcList class for type‐checking; at runtime
    # this block is ignored, which breaks the circular dependency.
    from vital_ai_vitalsigns.metaql.arc_list.metaql_arc_list import MetaQLArcList


ARC_TYPE_ARC_ROOT = "ARC_TYPE_ARC_ROOT"
ARC_TYPE_ARC = "ARC_TYPE_ARC"

ARC_TYPE = Literal[
    "ARC_TYPE_ARC_ROOT",
    "ARC_TYPE_ARC"
]

ARC_TRAVERSE_TYPE_EDGE = "ARC_TRAVERSE_TYPE_EDGE"
ARC_TRAVERSE_TYPE_PROPERTY = "ARC_TRAVERSE_TYPE_PROPERTY"

ARC_TRAVERSE_TYPE = Literal[
    "ARC_TRAVERSE_TYPE_EDGE",
    "ARC_TRAVERSE_TYPE_PROPERTY"
]

ARC_DIRECTION_TYPE_FORWARD = "ARC_DIRECTION_TYPE_FORWARD"
ARC_DIRECTION_TYPE_REVERSE = "ARC_DIRECTION_TYPE_REVERSE"

ARC_DIRECTION_TYPE = Literal[
    "ARC_DIRECTION_TYPE_FORWARD",
    "ARC_DIRECTION_TYPE_REVERSE",
]


class MetaQLArcBinding(TypedDict):

    metaql_class: str
    binding: str


class NodeArcBinding(MetaQLArcBinding):
    pass


class EdgeArcBinding(MetaQLArcBinding):
    pass


class PathArcBinding(MetaQLArcBinding):
    pass


class SolutionArcBinding(MetaQLArcBinding):
    pass


# Later include max depth of traversing
# currently applies to a single traversal
class MetaQLPropertyPath(TypedDict):

    metaql_class: str

    class_uri: Optional[str]
    include_subclasses: Optional[bool]

    property_uri: str
    include_subproperties: Optional[bool]


# Later include depth for traversing via edge traversal type
# which may not be directly supported via SPARQL
class MetaQLArc(TypedDict):

    metaql_class: str

    constraint_list_list: List[MetaQLConstraintList]
    arc_type: ARC_TYPE
    arc_traverse_type: ARC_TRAVERSE_TYPE
    arc_direction_type: ARC_DIRECTION_TYPE

    node_binding: Optional[NodeArcBinding]

    edge_binding: Optional[EdgeArcBinding]

    path_binding: Optional[PathArcBinding]

    solution_binding: Optional[SolutionArcBinding]

    # for property traverse type, the properties used for
    # traversing are listed
    # reverse direction means other nodes traversing in to the
    # current nodes
    # forward direction means the current nodes traversing out
    # to other nodes
    property_path_list_list: Optional[List[List[MetaQLPropertyPath]]]


# use for internal ARCs either as a single path from parent arc
# or within an arc list
class Arc(MetaQLArc):
    # break circular dependency
    # arclist_list: Optional[List[TypedDict]] # List["MetaQLArcList"]
    arclist_list: Optional[List[MetaQLArcList]]

    arc: Optional["Arc"]


# use for top-level arc which may contain arc lists like AND_ARC
class ArcRoot(MetaQLArc):
    # break circular dependency
    # arclist_list: Optional[List[TypedDict]] # List["MetaQLArcList"]
    arclist_list: Optional[List["MetaQLArcList"]]

    arc: Optional[Arc]


