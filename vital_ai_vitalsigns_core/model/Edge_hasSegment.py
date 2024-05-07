
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
from vital_ai_vitalsigns_core.model.VITAL_TaxonomyEdge import VITAL_TaxonomyEdge


class Edge_hasSegment(VITAL_TaxonomyEdge):
    _allowed_properties = [
    ]

    @classmethod
    def get_allowed_properties(cls):
        return super().get_allowed_properties() + Edge_hasSegment._allowed_properties

    @classmethod
    def get_class_uri(self) -> str:
        return 'http://vital.ai/ontology/vital-core#Edge_hasSegment'

