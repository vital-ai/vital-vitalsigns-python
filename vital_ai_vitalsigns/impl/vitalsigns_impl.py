import pkgutil
import importlib
# from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


class VitalSignsImpl:

    @classmethod
    def create_property_with_trait(cls, property_class, trait_uri, value):

        trait_class = cls.get_trait_class_from_uri(trait_uri)

        if not trait_class:
            raise ValueError(f"No trait found with URI: {trait_uri}")

        class CombinedProperty(property_class, trait_class):
            def get_uri(self):
                return super().get_uri()

            def __hash__(self):
                return hash((self.get_uri(), self.value))

        return CombinedProperty(value)

    @classmethod
    def get_trait_class_from_uri(cls, uri):

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        registry = vs.get_registry()

        trait_cls = registry.vitalsigns_property_classes[uri]

        return trait_cls

