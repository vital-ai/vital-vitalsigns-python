import json
from typing import List, TypeVar, Generator, Tuple
from vital_ai_vitalsigns.impl.vitalsigns_registry import VitalSignsRegistry
from vital_ai_vitalsigns.model.GraphObject import GraphObject


class VitalSignsMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


G = TypeVar('G', bound='GraphObject')


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

    def from_json(self, json_map: str) -> G:
        return GraphObject.from_json(json_map)

    def from_json_list(self, json_map_list: str) -> List[G]:
        return GraphObject.from_json_list(json_map_list)

    def from_rdf(self, rdf_string: str) -> G:
        return GraphObject.from_rdf(rdf_string)

    def from_rdf_list(self, rdf_string_list: str) -> List[G]:
        return GraphObject.from_rdf_list(rdf_string_list)

    def from_triples(self, triples: Generator[Tuple, None, None]) -> G:
        return GraphObject.from_triples(triples)

    def to_json(self, graph_object_list: List[G]) -> str:
        json_list = []

        for obj in graph_object_list:
            json_data = obj.to_json()
            json_list.append(json.loads(json_data))

        return json.dumps(json_list, indent=2)

    def to_rdf(self, graph_object_list: List[G]) -> str:
        rdf_strings = []

        for obj in graph_object_list:
            rdf_data = obj.to_rdf()
            rdf_strings.append(rdf_data)

        return "\n".join(rdf_strings)
