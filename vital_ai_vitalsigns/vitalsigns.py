import gc
import weakref
import json
import logging
from typing import List, TypeVar, Generator, Tuple, Optional, Set
from vital_ai_vitalsigns.impl.vitalsigns_registry import VitalSignsRegistry
from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.model.GraphObject import GraphObject
import threading
import time
from vital_ai_vitalsigns.ontology.vitalsigns_ontology_manager import VitalSignsOntologyManager
from vital_ai_vitalsigns.service.vitalservice_manager import VitalServiceManager
from vital_ai_vitalsigns.utils.background_task import BackgroundTaskMixin
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome
from vital_ai_vitalsigns.config.vitalsigns_config import VitalSignsConfigLoader, VitalSignsConfig
import os

logger = logging.getLogger(__name__)

# seconds between periodic gc.collect() passes in the background thread
GC_INTERVAL_SECONDS = 60

# granularity of the background thread's sleep, so stop() returns promptly
GC_SLEEP_SLICE_SECONDS = 1

# how long stop() waits for the background thread before giving up on the join
STOP_JOIN_TIMEOUT_SECONDS = 30

# The object registry is opt-in: see planning/issues/
# protocol-support-lifecycle-and-registry-optin.md. It exists for planned
# ontology inference over live objects, which is not in regular use, so every
# GraphObject construction should not pay for it by default.
OBJECT_REGISTRY_ENV_VAR = 'VITALSIGNS_OBJECT_REGISTRY'
_TRUTHY = {'1', 'true', 'yes', 'on'}


def _object_registry_default() -> bool:
    return os.environ.get(OBJECT_REGISTRY_ENV_VAR, '').strip().lower() in _TRUTHY


class VitalSignsMeta(type):
    """Singleton metaclass, safe against re-entrant construction.

    The naive double-checked-locking form runs __init__ inside the critical
    section and only publishes the instance once __init__ returns. Anything that
    calls VitalSigns() during VitalSigns.__init__ (GraphObject.__init__ does, as
    does get_allowed_domain_properties) therefore re-enters, fails the
    "already built?" check, and blocks forever on a lock its own thread holds.

    Two changes prevent that:
      - _lock is an RLock, so the nested acquire succeeds.
      - the in-progress instance is published to a thread-local while __init__
        runs, so the re-entrant call gets the partially-built instance instead of
        recursing into a second __init__. It is deliberately NOT published to
        _instances until __init__ completes, so other threads keep blocking on
        the lock and can never observe a half-built singleton.
    """

    _instances = {}
    _lock = threading.RLock()
    _building = threading.local()

    def __call__(cls, *args, **kwargs):
        instance = cls._instances.get(cls)
        if instance is not None:
            if args or kwargs:
                logger.warning(
                    "%s is already constructed; ignoring arguments %r / %r. "
                    "Construction arguments only apply to the first call.",
                    cls.__name__, args, kwargs)
            return instance

        with cls._lock:
            instance = cls._instances.get(cls)
            if instance is not None:
                return instance

            building = getattr(cls._building, 'map', None)
            if building is None:
                building = {}
                cls._building.map = building

            # re-entrant call from inside this thread's __init__
            if cls in building:
                return building[cls]

            instance = cls.__new__(cls)
            building[cls] = instance
            try:
                instance.__init__(*args, **kwargs)
            finally:
                # on failure the instance is never published, so a later call
                # retries construction rather than returning a broken singleton
                building.pop(cls, None)

            cls._instances[cls] = instance
            return instance


G = TypeVar('G', bound=Optional['GraphObject'])


class VitalSigns(BackgroundTaskMixin, metaclass=VitalSignsMeta):

    BG_INTERVAL_SECONDS = GC_INTERVAL_SECONDS
    BG_SLEEP_SLICE_SECONDS = GC_SLEEP_SLICE_SECONDS
    BG_JOIN_TIMEOUT_SECONDS = STOP_JOIN_TIMEOUT_SECONDS

    def __init__(self, *, background_task=True, object_registry=None):

        os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'

        self._ont_manager = VitalSignsOntologyManager()
        self._registry = VitalSignsRegistry(ontology_manager=self._ont_manager)
        self._embedding_model_registry = {}
        self._registry.build_registry()
        # Registries of live objects, keyed by id(). WeakValueDictionary entries
        # self-evict when the referent is collected, so there is no sweep to race
        # against and no finalizer needed on GraphObject/GraphCollection.
        self._graph_collection_map = weakref.WeakValueDictionary()
        self._graph_object_map = weakref.WeakValueDictionary()

        # Guards iteration of _graph_collection_map (see graph_collection_set).
        # _graph_object_map is never iterated, so its writes stay lock-free.
        self._vitalsigns_lock = threading.RLock()

        # Lifecycle state (_bg_running/_bg_thread/_lifecycle_lock) lives in
        # BackgroundTaskMixin. Its lock is separate from _vitalsigns_lock so
        # shutdown never waits behind registry work, and vice versa.
        self._init_background_task()

        # Opt-in object registry (default off). Publishing to GraphObject lets
        # its __init__ skip the import + singleton lookup + map write entirely.
        self.set_object_registry_enabled(self._resolve_object_registry(object_registry))

        vital_home = find_vitalhome()

        self._vital_home = vital_home

        self._vitalsigns_config = VitalSignsConfigLoader.vitalsigns_load_config(vital_home)

        # Use the new VitalServiceManager constructor with full config
        self._vitalservice_manager = VitalServiceManager(vitalsigns_config=self._vitalsigns_config)

        self._vitalservice_manager._initialize()

        if background_task:
            self.start()

    def _background_tick(self):
        self.cleanup_task()

    def _background_task_name(self):
        return 'VitalSigns'

    # legacy attribute names, preserved for callers that touch them directly
    @property
    def _running(self):
        return self._bg_running

    @_running.setter
    def _running(self, value):
        self._bg_running = value

    @property
    def _background_thread(self):
        return self._bg_thread

    @_background_thread.setter
    def _background_thread(self, value):
        self._bg_thread = value

    @staticmethod
    def _resolve_object_registry(argument) -> bool:
        """Resolve the object-registry setting, most specific source winning.

            1. explicit constructor argument
            2. VITALSIGNS_OBJECT_REGISTRY environment variable
            3. off

        Deliberately not read from vitalsigns_config.yaml: that file is not
        tracked in the repo (vitalhome/**/*.yaml is gitignored), so a value set
        there does not travel with a deployment and a fresh checkout has no
        config file at all. An environment variable is the reliable lever.
        """
        if argument is not None:
            return bool(argument)
        return _object_registry_default()

    def is_object_registry_enabled(self) -> bool:
        return self._object_registry_enabled

    def set_object_registry_enabled(self, enabled: bool):
        """Turn the object registry on or off at runtime.

        Only affects objects constructed afterwards -- there is no backfill, so
        objects built while it was off are not retroactively registered.
        """
        self._object_registry_enabled = bool(enabled)
        GraphObject._registry_enabled = self._object_registry_enabled

    def cleanup_task(self):
        # The registry maps self-evict, so nothing to sweep. The periodic collect
        # remains: GraphObject/GraphCollection form reference cycles, which would
        # otherwise wait on CPython's infrequent gen-2 collector. Deliberately not
        # under _vitalsigns_lock -- a full collect can take hundreds of ms and
        # nothing in the collect path touches the maps.
        self.gc()

    def get_vitalhome(self):
        return self._vital_home

    def get_config(self) -> VitalSignsConfig:
        return self._vitalsigns_config

    def parse_config(self, yaml_config: str) -> VitalSignsConfig:

        vitalsigns_config = VitalSignsConfigLoader.parse_yaml_config(yaml_config)

        self._vitalsigns_config = vitalsigns_config

        return vitalsigns_config

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
        # Opt-in: off by default, so direct callers are safe either way.
        if not self._object_registry_enabled:
            return
        # Hot path: one atomic __setitem__, no lock. The entry evicts itself when
        # graph_object is collected, so no explicit removal is required.
        #
        # NOTE: lock-free ONLY because nothing iterates _graph_object_map. The
        # planned ontology-inference feature iterates it by design; re-add a
        # guard here before building that. See the planning docs.
        self._graph_object_map[id(graph_object)] = graph_object

    def remove_graph_object(self, graph_object: G):
        # Retained for API compatibility; eviction is automatic. Idempotent.
        self._graph_object_map.pop(id(graph_object), None)

    def graph_object_count(self) -> int:
        return len(self._graph_object_map)

    def clean_graph_object_map(self):
        # Deprecated no-op: the registry self-evicts.
        return 0

    def include_graph_collection(self, graph_collection: GraphCollection):
        with self._vitalsigns_lock:
            self._graph_collection_map[id(graph_collection)] = graph_collection

    def remove_graph_collection(self, graph_collection: GraphCollection):
        # Retained for API compatibility; eviction is automatic. Idempotent.
        with self._vitalsigns_lock:
            self._graph_collection_map.pop(id(graph_collection), None)

    def graph_collection_set(self) -> Set[GraphCollection]:
        # Locked because a concurrent include_graph_collection during iteration
        # would raise "dictionary changed size during iteration". The weakref
        # eviction case is already handled by WeakValueDictionary's iteration guard.
        with self._vitalsigns_lock:
            return set(self._graph_collection_map.values())

    def graph_collection_count(self) -> int:
        return len(self._graph_collection_map)

    def clean_graph_collection_map(self):
        # Deprecated no-op: the registry self-evicts.
        return 0

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

    def from_property_map(self, subject_uri: str, type_uri: str,
                          properties: dict, *, modified=False) -> G:
        return GraphObject.from_property_map(subject_uri, type_uri, properties, modified=modified)

    def from_property_maps(self, entries: list, *, modified=False) -> list:
        return GraphObject.from_property_maps(entries, modified=modified)

    def to_property_maps(self, graph_object_list: list) -> list:
        return GraphObject.to_property_maps(graph_object_list)

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
