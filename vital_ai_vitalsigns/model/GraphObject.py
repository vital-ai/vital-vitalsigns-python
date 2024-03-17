from vital_ai_vitalsigns.impl import VitalSignsImpl
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty


class GraphObject:
    _allowed_properties = []

    @classmethod
    def get_allowed_properties(cls):
        return GraphObject._allowed_properties

    def __init__(self):
        super().__setattr__('_properties', {})

    def __setattr__(self, name, value) -> bool:
        print(name)
        if name == 'URI':
            if value is None:
                self._properties.pop('http://vital.ai/ontology/vital-core#URIProp', None)
            else:
                self._properties['http://vital.ai/ontology/vital-core#URIProp'] = VitalSignsImpl.create_property_with_trait(URIProperty, 'http://vital.ai/ontology/vital-core#URIProp', value)
            return
        for prop_info in self.get_allowed_properties():
            uri = prop_info['uri']
            prop_class = prop_info['prop_class']
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)

            if trait_class and trait_class.get_short_name() == name:
                if value is None:
                    self._properties.pop(uri, None)
                else:
                    self._properties[uri] = VitalSignsImpl.create_property_with_trait(prop_class, uri, value)
                return

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def my_getattr(self, name):
        if name == 'URI':
            return self._properties['http://vital.ai/ontology/vital-core#URIProp']
        for prop_info in self.get_allowed_properties():
            uri = prop_info['uri']
            # print(uri)
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)
            # print(trait_class)
            if trait_class and trait_class.get_short_name() == name:
                if uri in self._properties:
                    return self._properties[uri]
                else:
                    return None
        return NotImplemented

    def __getattr__(self, name):
        value = self.my_getattr(name)
        if value is NotImplemented:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return value

    @classmethod
    def is_top_level_class(cls):
        return cls.__bases__ == (object,)
