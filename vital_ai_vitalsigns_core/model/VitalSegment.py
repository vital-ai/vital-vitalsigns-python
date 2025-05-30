
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
from vital_ai_vitalsigns.model.properties.FloatProperty import FloatProperty
from vital_ai_vitalsigns.model.properties.GeoLocationProperty import GeoLocationProperty
from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.OtherProperty import OtherProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.TruthProperty import TruthProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


class VitalSegment(VITAL_Node):
    _allowed_properties = [
        {'uri': 'http://vital.ai/ontology/vital-core#hasSegmentGraphURI', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasSegmentID', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasSegmentNamespace', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasSegmentStateJSON', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasSegmentTenantID', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#isReadOnly', 'prop_class': BooleanProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#isSegmentGlobal', 'prop_class': BooleanProperty}, 
    ]

    @classmethod
    def get_allowed_properties(cls):
        return super().get_allowed_properties() + VitalSegment._allowed_properties

    @classmethod
    def get_class_uri(cls) -> str:
        return 'http://vital.ai/ontology/vital-core#VitalSegment'

