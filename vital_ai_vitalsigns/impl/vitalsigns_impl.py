import pkgutil
import importlib
from datetime import datetime
from typing import TypeVar, Type
from urllib.parse import urlparse
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
from vital_ai_vitalsigns.model.properties.MultiValueProperty import MultiValueProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait

# from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait

T = TypeVar('T', bound=PropertyTrait)


class VitalSignsImpl:

    @classmethod
    def create_property_with_trait(cls, property_class, trait_uri, value):

        trait_class = cls.get_trait_class_from_uri(trait_uri)

        if not trait_class:
            raise ValueError(f"No trait found with URI: {trait_uri}")

        multiple_values = trait_class.multiple_values

        if not multiple_values:

            class CombinedProperty(property_class, trait_class):
                def get_uri(self):
                    return super().get_uri()

                def __hash__(self):
                    return hash((self.get_uri(), self.value))

            return CombinedProperty(value)
        else:
            class CombinedProperty(MultiValueProperty, trait_class):
                def get_uri(self):
                    return super().get_uri()

                def __hash__(self):
                    return hash((self.get_uri(), self.value))

            return CombinedProperty(value, property_class)

    @classmethod
    def create_extern_property(cls, value):

        property_class = cls.get_property_class_from_value(value)

        if property_class is None:
            return None

        property_instance = property_class(value)

        return property_instance

    @classmethod
    def get_trait_class_from_uri(cls, uri) -> Type[T]:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        registry = vs.get_registry()

        trait_cls = registry.vitalsigns_property_classes[uri]

        return trait_cls

    @classmethod
    def get_property_class_from_value(cls, value):

        if isinstance(value, str):
            if cls.is_parseable_as_uri(value):
                return URIProperty

        if isinstance(value, str):
            return StringProperty

        if isinstance(value, bool):
            return BooleanProperty

        if isinstance(value, float):
            return DoubleProperty

        if isinstance(value, int):
            return IntegerProperty

        if isinstance(value, datetime):
            return DateTimeProperty

    @classmethod
    def is_parseable_as_uri(cls, uri):
        try:
            result = urlparse(uri)
            # A valid URI must have a scheme and either a netloc or a path
            if not result.scheme:
                return False
            if result.scheme in ('http', 'https', 'ftp', 'ftps', 'mailto', 'file'):
                # These schemes require a netloc
                return bool(result.netloc)
            elif result.scheme in ('urn', 'data'):
                # These schemes do not require a netloc but should have a path
                return bool(result.path)
            else:
                # For other schemes, require at least a path
                return bool(result.path)
        except ValueError:
            return False

        return None


