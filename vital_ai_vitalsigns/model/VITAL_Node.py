from vital_ai_vitalsigns.impl import VitalSignsImpl
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


class VITAL_Node(GraphObject):
    allowed_properties = [
        {'uri': 'http://vital.ai/ontology/vital-core#URIProp', 'prop_class': URIProperty},
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
