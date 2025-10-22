import gc
import weakref
import json
from typing import List, TypeVar, Generator, Tuple, Optional, Set
from vital_ai_vitalsigns.impl.vitalsigns_registry import VitalSignsRegistry
from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.model.GraphObject import GraphObject
import threading
import time
from vital_ai_vitalsigns.ontology.vitalsigns_ontology_manager import VitalSignsOntologyManager
from vital_ai_vitalsigns.service.vitalservice_manager import VitalServiceManager
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome
from vital_ai_vitalsigns.config.vitalsigns_config import VitalSignsConfigLoader, VitalSignsConfig
import os


class VitalSignsMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


G = TypeVar('G', bound=Optional['GraphObject'])


class VitalSigns(metaclass=VitalSignsMeta):

    def __init__(self, *, background_task=True):

        os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'

        self._ont_manager = VitalSignsOntologyManager()
        self._registry = VitalSignsRegistry(ontology_manager=self._ont_manager)
        self._embedding_model_registry = {}
        self._registry.build_registry()
        self._graph_collection_map = {}
        self._graph_object_map = {}
        self._vitalsigns_lock = threading.RLock()
        self._background_thread = None
        self._running = False


        vital_home = find_vitalhome()

        self._vital_home = vital_home

        self._vitalsigns_config = VitalSignsConfigLoader.vitalsigns_load_config(vital_home)

        # Use the new VitalServiceManager constructor with full config
        self._vitalservice_manager = VitalServiceManager(vitalsigns_config=self._vitalsigns_config)

        self._vitalservice_manager._initialize()

        if background_task:
            self.start()

    def cleanup_task(self):
        with self._vitalsigns_lock:
            self.clean_graph_object_map()
            self.clean_graph_collection_map()
            self.gc()

    def background_task(self):
        while self._running:
            self.cleanup_task()
            time.sleep(60)

    def get_vitalhome(self):
        return self._vital_home

    def get_config(self) -> VitalSignsConfig:
        return self._vitalsigns_config

    def parse_config(self, yaml_config: str) -> VitalSignsConfig:

        vitalsigns_config = VitalSignsConfigLoader.parse_yaml_config(yaml_config)

        self._vitalsigns_config = vitalsigns_config

        return vitalsigns_config

    def start(self):
        if not self._running:
            self._running = True
            self._background_thread = threading.Thread(target=self.background_task, daemon=True)
            self._background_thread.start()

    def stop(self):
        if self._running:
            self._running = False
            if self._background_thread:
                self._background_thread.join()
                self._background_thread = None

    def is_running(self):
        return self._running

    def gc(self):
        # log size of graph collection and graph object map
        # before and after garbage collection
        gc.collect()

    def get_registry(self):
        return self._registry

    def get_vitalservice_manager(self):
        return self._vitalservice_manager

    def get_ontology_manager(self):
        return self._ont_manager

    def put_embedding_model(self, name, model):
        """Add a model instance to the registry."""
        self._embedding_model_registry[name] = model

    def get_embedding_model(self, name):
        """Retrieve a model instance from the registry by its name."""
        return self._embedding_model_registry.get(name)

    def include_graph_object(self, graph_object: G):
        go_id = id(graph_object)

        weak_obj = weakref.ref(graph_object)

        self._graph_object_map[go_id] = weak_obj

    def remove_graph_object(self, graph_object: G):
        go_id = id(graph_object)
        del self._graph_object_map[go_id]

    def clean_graph_object_map(self):
        try:
            dead_keys = [key for key, weak_obj in self._graph_object_map.items() if weak_obj() is None]
            for key in dead_keys:
                del self._graph_object_map[key]
        except RuntimeError as e:
            pass

    def include_graph_collection(self, graph_collection: GraphCollection):
        gc_id = id(graph_collection)
        weak_obj = weakref.ref(graph_collection)
        self._graph_collection_map[gc_id] = weak_obj

    def remove_graph_collection(self, graph_collection: GraphCollection):
        gc_id = id(graph_collection)
        del self._graph_collection_map[gc_id]

    def graph_collection_set(self) -> Set[GraphCollection]:
        gc_set = {weak_ref() for weak_ref in self._graph_collection_map.values() if weak_ref() is not None}
        return gc_set.copy()

    def clean_graph_collection_map(self):
        try:
            dead_keys = [key for key, weak_obj in self._graph_collection_map.items() if weak_obj() is None]
            for key in dead_keys:
                del self._graph_collection_map[key]
        except RuntimeError as e:
            pass

    def from_json(self, json_map: str, *, modified=False) -> G:
        return GraphObject.from_json(json_map, modified=modified)

    def from_json_list(self, json_map_list: str, *, modified=False) -> List[G]:
        return GraphObject.from_json_list(json_map_list, modified=modified)

    def from_dict(self, dict_map: dict, *, modified=False) -> G:
        return GraphObject.from_dict(dict_map, modified=modified)

    def from_dict_list(self, dict_list: List[dict], *, modified=False) -> List[G]:
        return GraphObject.from_dict_list(dict_list, modified=modified)

    def from_jsonld(self, jsonld_data: dict, *, modified=False) -> G:
        return GraphObject.from_jsonld(jsonld_data, modified=modified)

    def from_jsonld_list(self, jsonld_doc, *, modified=False) -> List[G]:
        return GraphObject.from_jsonld_list(jsonld_doc, modified=modified)

    def from_rdf(self, rdf_string: str, *, modified=False) -> G:
        return GraphObject.from_rdf(rdf_string, modified=modified)

    def from_rdf_list(self, rdf_string_list: str, *, modified=False) -> List[G]:
        return GraphObject.from_rdf_list(rdf_string_list, modified=modified)

    def from_triples(self, triples: Generator[Tuple, None, None], *, modified=False) -> G:
        return GraphObject.from_triples(triples, modified=modified)

    def from_triples_list(self, triples: Generator[Tuple, None, None], *, modified=False) -> List[G]:
        return GraphObject.from_triples_list(triples, modified=modified)


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
