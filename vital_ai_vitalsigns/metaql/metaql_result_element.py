from typing_extensions import TypedDict
from vital_ai_vitalsigns.model.GraphObject import GraphObject


class MetaQLResultElement(TypedDict):

    metaql_class: str

    graph_object: GraphObject

    score: float


