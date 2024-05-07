
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


class DomainModel(VITAL_Node):
    _allowed_properties = [
        {'uri': 'http://vital.ai/ontology/vital-core#hasAppID', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasBackwardCompVersion', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasDefaultPackageValue', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasDomainOWL', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasDomainOWLHash', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasOrganizationID', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasPreferredImportVersions', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasVersionInfo', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#isPreferred', 'prop_class': BooleanProperty}, 
    ]

    @classmethod
    def get_allowed_properties(cls):
        return super().get_allowed_properties() + DomainModel._allowed_properties

    @classmethod
    def get_class_uri(self) -> str:
        return 'http://vital.ai/ontology/vital-core#DomainModel'

