from vital_ai_vitalsigns.impl import VitalSignsImpl
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


class VITALNode:
    allowed_properties = []

    def __init__(self):
        super().__setattr__('_properties', {})

    def __setattr__(self, name, value):
        print(name)
        for prop_info in self.allowed_properties:
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

    def __getattr__(self, name):
        for prop_info in self.allowed_properties:
            uri = prop_info['uri']
            # print(uri)
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)
            # print(trait_class)
            if trait_class and trait_class.get_short_name() == name:
                if uri in self._properties:
                    return self._properties[uri]
                else:
                    return None
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

