from vital_ai_vitalsigns.metaql.constraint.metaql_property_constraint import OTHER_PROPERTY_DATA_CONSTRAINT_TYPE, \
    STRING_PROPERTY_DATA_CONSTRAINT_TYPE, BOOLEAN_PROPERTY_DATA_CONSTRAINT_TYPE, DATETIME_PROPERTY_DATA_CONSTRAINT_TYPE, \
    DOUBLE_PROPERTY_DATA_CONSTRAINT_TYPE, FLOAT_PROPERTY_DATA_CONSTRAINT_TYPE, \
    GEOLOCATION_PROPERTY_DATA_CONSTRAINT_TYPE, INTEGER_PROPERTY_DATA_CONSTRAINT_TYPE, \
    LONG_PROPERTY_DATA_CONSTRAINT_TYPE, TRUTH_PROPERTY_DATA_CONSTRAINT_TYPE, URI_PROPERTY_DATA_CONSTRAINT_TYPE
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


class PropertyDataConstraintUtils:

    @staticmethod
    def lookup(prop_class):
        property_constraint_type = OTHER_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == StringProperty:
            property_constraint_type = STRING_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == BooleanProperty:
            property_constraint_type = BOOLEAN_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == DateTimeProperty:
            property_constraint_type = DATETIME_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == DoubleProperty:
            property_constraint_type = DOUBLE_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == FloatProperty:
            property_constraint_type = FLOAT_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == GeoLocationProperty:
            property_constraint_type = GEOLOCATION_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == IntegerProperty:
            property_constraint_type = INTEGER_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == LongProperty:
            property_constraint_type = LONG_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == OtherProperty:
            property_constraint_type = OTHER_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == TruthProperty:
            property_constraint_type = TRUTH_PROPERTY_DATA_CONSTRAINT_TYPE

        if prop_class == URIProperty:
            property_constraint_type = URI_PROPERTY_DATA_CONSTRAINT_TYPE

        return property_constraint_type

