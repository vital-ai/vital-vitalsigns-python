
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
from vital_ai_vitalsigns_core.model.VitalServiceConfig import VitalServiceConfig


class VitalServiceSqlConfig(VitalServiceConfig):
    allowed_properties = [
        {'uri': 'http://vital.ai/ontology/vital-core#hasDbType', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasEndpointURL', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasPassword', 'prop_class': StringProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasPoolInitialSize', 'prop_class': IntegerProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasPoolMaxTotal', 'prop_class': IntegerProperty}, 
        {'uri': 'http://vital.ai/ontology/vital-core#hasUsername', 'prop_class': StringProperty}, 
    ]