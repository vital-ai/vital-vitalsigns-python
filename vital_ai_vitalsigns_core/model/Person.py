from vital_ai_vitalsigns.model.VITAL_Node import VITALNode
from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty


class Person(VITALNode):
    allowed_properties = [
        {'uri': "http://vital.ai/ontology/vital-core#hasName", 'prop_class': StringProperty},
        {'uri': "http://vital.ai/ontology/vital-core#hasBirthday", 'prop_class': DateTimeProperty}
    ]

