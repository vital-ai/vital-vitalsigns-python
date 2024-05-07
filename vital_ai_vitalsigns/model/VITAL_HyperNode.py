from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty


class VITAL_HyperNode(GraphObject):

    _allowed_properties = [
        # {'uri': 'http://vital.ai/ontology/vital-core#URIProp', 'prop_class': URIProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#isActive', 'prop_class': BooleanProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#hasVersionIRI', 'prop_class': URIProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#hasUpdateTime', 'prop_class': LongProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#hasTimestamp', 'prop_class': LongProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#hasProvenance', 'prop_class': URIProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#hasOntologyIRI', 'prop_class': URIProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#hasName', 'prop_class': StringProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#vitaltype', 'prop_class': URIProperty},
        {'uri': 'http://vital.ai/ontology/vital-core#types', 'prop_class': URIProperty}
    ]

    @classmethod
    def get_allowed_properties(cls):
        return super().get_allowed_properties() + VITAL_HyperNode._allowed_properties

    @classmethod
    def get_class_uri(cls) -> str:
        return 'http://vital.ai/ontology/vital-core#VITAL_HyperNode'
