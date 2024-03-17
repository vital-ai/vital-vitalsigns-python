from vital_ai_vitalsigns.model.GraphObject import GraphObject


class VITAL_Edge(GraphObject):
    # URIProp: str
    URI: str
    active: bool
    versionIRI: str
    updateTime: int
    timestamp: int
    provenance: str
    ontologyIRI: str
    name: str
    vitaltype: str
    types: str

    edgeSource: str
    edgeDestination: str
