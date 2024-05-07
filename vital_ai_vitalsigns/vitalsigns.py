from vital_ai_vitalsigns.impl.vitalsigns_registry import VitalSignsRegistry


class VitalSignsMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class VitalSigns(metaclass=VitalSignsMeta):
    def __init__(self):
        self._registry = VitalSignsRegistry()
        self._embedding_model_registry = {}
        self._registry.build_registry()

    def get_registry(self):
        return self._registry

    def put_embedding_model(self, name, model):
        """Add a model instance to the registry."""
        self._embedding_model_registry[name] = model

    def get_embedding_model(self, name):
        """Retrieve a model instance from the registry by its name."""
        return self._embedding_model_registry.get(name)




