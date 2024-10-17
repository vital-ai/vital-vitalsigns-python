from typing import Literal, List
from typing_extensions import TypedDict
from vital_ai_vitalsigns.metaql.arc.metaql_arc import Arc

AND_ARC_LIST_TYPE = "AND_ARC_LIST_TYPE"
OR_ARC_LIST_TYPE = "OR_ARC_LIST_TYPE"

ARC_LIST_TYPE = Literal[
    "AND_ARC_LIST_TYPE",
    "OR_ARC_LIST_TYPE"
]


class MetaQLArcList(TypedDict):

    metaql_class: str

    arc_list: List["Arc"]

    # make this recursive or use ARC as the container?
    # arclist_list: List["MetaQLArcList"]

    arc_list_type: ARC_LIST_TYPE


class AndArcList(MetaQLArcList):
    pass


class OrArcList(MetaQLArcList):
    pass


