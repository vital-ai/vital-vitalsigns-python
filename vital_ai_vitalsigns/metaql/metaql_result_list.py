from typing import List, Optional
from typing_extensions import TypedDict
from vital_ai_vitalsigns.metaql.metaql_result_element import MetaQLResultElement
from vital_ai_vitalsigns.model.GraphObject import GraphObject


class MetaQLResultList(TypedDict):

    metaql_class: str

    offset: int

    limit: int

    result_count: int

    total_result_count: int

    # list of binding names in results for graph queries
    binding_list: Optional[list[str]]

    # result elements are graph objects from select
    # or graph match for graph queries
    result_list: List[MetaQLResultElement]

    # in graph query, list of objects resolved if requested
    result_object_list: Optional[List[GraphObject]]


