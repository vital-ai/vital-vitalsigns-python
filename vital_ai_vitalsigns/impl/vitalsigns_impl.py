import pkgutil
import importlib
# from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalSignsImpl:

    """
    @staticmethod
    def import_submodules(package_name):
        try:
            package = importlib.import_module(package_name)
            package_path = package.__path__
            for loader, name, is_pkg in pkgutil.walk_packages(path=package_path):
                full_name = f"{package_name}.{name}"
                # print(full_name)
                try:
                    importlib.import_module(full_name)
                    if is_pkg:
                        VitalSignsImpl.import_submodules(full_name)
                except ImportError as e:
                    pass  # print(f"Error importing {full_name}: {e}")
        except ImportError as e:
            pass  # print(f"Error importing package {package_name}: {e}")

    @staticmethod
    def find_all_subclasses(base_class):
        return base_class.__subclasses__()
    
    """

    @classmethod
    def create_property_with_trait(cls, property_class, trait_uri, value):

        # VitalSignsImpl.import_submodules('vital_ai_vitalsigns_core')
        # VitalSignsImpl.import_submodules('vital_ai_vitalsigns')

        # trait_classes = [cls for cls in PropertyTrait.__subclasses__() if cls.get_uri() == trait_uri]

        # if not trait_classes:
        #    raise ValueError(f"No trait found with URI: {trait_uri}")

        # trait_class = trait_classes[0]

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

        vs = VitalSigns()

        registry = vs.get_registry()

        trait_cls = registry.vitalsigns_property_classes[uri]

        return trait_cls

        # VitalSignsImpl.import_submodules('vital_ai_vitalsigns_core')
        # for subclass in PropertyTrait.__subclasses__():
        #   if subclass.get_uri() == uri:
        #        return subclass
        # return None
