from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod
import json
from datetime import datetime
from typing import TypeVar, List, Generator, Tuple, Optional, Set
import rdflib
from rdflib import Graph, Literal, URIRef, RDF, Dataset
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.vital_constants import VitalConstants
from vital_ai_vitalsigns.model.properties.IProperty import IProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from functools import wraps
from functools import lru_cache
from rdflib.term import _is_valid_uri
from vital_ai_vitalsigns.model.utils.class_utils import ClassUtils
from vital_ai_vitalsigns.model.utils.graphobject_triples_utils import GraphObjectTriplesUtils
from vital_ai_vitalsigns.model.utils.graphobject_rdf_utils import GraphObjectRdfUtils
from vital_ai_vitalsigns.model.utils.graphobject_json_utils import GraphObjectJsonUtils
from vital_ai_vitalsigns.model.utils.graphobject_dict_utils import GraphObjectDictUtils
from vital_ai_vitalsigns.model.utils.graphobject_jsonld_utils import GraphObjectJsonldUtils
from collections import defaultdict

# Pydantic v2 imports (optional)
try:
    from vital_ai_vitalsigns.model.utils.graphobject_pydanticv2_utils import GraphObjectPydanticUtils
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import core_schema
    from typing import Type, Any, Dict
    PYDANTIC_V2_AVAILABLE = True
except ImportError:
    PYDANTIC_V2_AVAILABLE = False
    GraphObjectPydanticUtils = None
    GetCoreSchemaHandler = None
    core_schema = None

# Create logger for this module
logger = logging.getLogger(__name__)

def cacheable_method(method):
    @lru_cache(None)
    @wraps(method)
    def cached_method(*args, **kwargs):
        return method(*args, **kwargs)
    cached_method._is_cacheable = True
    return cached_method

class AttributeComparisonProxy:
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

    def __eq__(self, value):
        logger.info(f"Comparing {self.cls.__name__}.{self.name} with {value}")
        # TODO Add logic here
        return False  # Placeholder for the example
    
    def __getitem__(self, key):
        # Make proxy subscriptable to avoid Pydantic errors
        # Return None or raise KeyError for missing items
        raise KeyError(f"'{self.name}' has no key '{key}'")
    
    def __iter__(self):
        # Make proxy iterable (returns empty iterator)
        return iter([])
    
    def __len__(self):
        # Make proxy support len()
        return 0

class GraphObjectMeta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        for base in bases:
            for attr_name, attr_value in base.__dict__.items():
                if callable(attr_value) and getattr(attr_value, '_is_cacheable', False):
                    if attr_name in dct and callable(dct[attr_name]):
                        setattr(cls, attr_name, cacheable_method(dct[attr_name]))

    def __setattr__(self, name, value):
        logger.info(f"Setting class attribute {name} to {value}")
        super().__setattr__(name, value)

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            logger.info(f"Getting internal class attribute: {name}")
        return AttributeComparisonProxy(self, name)

G = TypeVar('G', bound=Optional['GraphObject'])
GC = TypeVar('GC', bound='GraphCollection')

class GraphObject(metaclass=GraphObjectMeta):
    _allowed_properties = []

    @classmethod
    @cacheable_method
    def get_allowed_properties(cls):
        return GraphObject._allowed_properties

    @classmethod
    @cacheable_method
    def get_allowed_domain_properties(cls):

        property_list = []

        parent_list = ClassUtils.get_class_hierarchy(cls, GraphObject)

        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        vs = VitalSigns()

        ont_manager = vs.get_ontology_manager()

        for p in parent_list:
            prop_list = ont_manager.get_domain_property_list(p)
            property_list.extend(prop_list)

        return property_list

    def __init__(self, *, modified=True):
        super().__setattr__('_properties', {})
        super().__setattr__('_extern_properties', {})
        super().__setattr__('_graph_collection_set', set())
        super().__setattr__('_graph_uri_set', set())
        super().__setattr__('_modified', modified)
        super().__setattr__('_object_hash', "")

        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        vs = VitalSigns()
        vs.include_graph_object(self)

    def __repr__(self):
        go_json = self.to_json(False)
        clazz=type(self)
        return f"GraphObject(class={clazz}, json={go_json})"

    def __del__(self):
        # logger.debug(f"deleting: {self}")

        if sys.meta_path is None or not hasattr(sys, 'modules'):
            # Python is shutting down, skip cleanup
            # logger.debug("shutting down")
            return

        try:
            from vital_ai_vitalsigns.vitalsigns import VitalSigns
            # logger.debug(f"deleting: {self.URI}")
            vs = VitalSigns()
            vs.remove_graph_object(self)
        except Exception as ex:
            # logger.debug(ex)
            pass

    def __setattr__(self, name, value):

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        if name == 'URI':
            if value is None:
                self._properties.pop('http://vital.ai/ontology/vital-core#URIProp', None)
            else:
                self._properties['http://vital.ai/ontology/vital-core#URIProp'] = VitalSignsImpl.create_property_with_trait(URIProperty, 'http://vital.ai/ontology/vital-core#URIProp', value)
            
            super().__setattr__('_modified', True)

            return

        # this list should be the general all-inclusive list
        # including properties added to classes after the
        # class was defined
        # this list is built using all OWL ontologies
        # currently loaded
        domain_prop_list = self.get_allowed_domain_properties()

        # for d in domain_prop_list:
        #    logger.debug(f"Domain Prop: {d}")

        # this includes properties defined when the class was defined
        # including properties associated with parent classes when
        # those were defined
        # if an extending ontology adds a property to an existing class
        # this list will not include it
        # prop_list = self.get_allowed_properties()
        # for prop_info in prop_list:

        for prop_info in domain_prop_list:

            uri = prop_info['uri']
            prop_class = prop_info['prop_class']
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)

            # full uri case
            # logger.debug(f"uri: {uri} :: name: {name}")

            if trait_class and uri == name:
                if value is None:
                    self._properties.pop(uri, None)
                else:
                    self._properties[uri] = VitalSignsImpl.create_property_with_trait(prop_class, uri, value)
                super().__setattr__('_modified', True)
                return

            # short name case
            if trait_class and trait_class.get_short_name() == name:
                if value is None:
                    self._properties.pop(uri, None)
                else:
                    self._properties[uri] = VitalSignsImpl.create_property_with_trait(prop_class, uri, value)
                super().__setattr__('_modified', True)
                return

        if isinstance(self, VITAL_GraphContainerObject):
            # arbitrary properties are allowed
            if value is None:
                self._extern_properties.pop(name, None)
            else:
                prop_name = name.removeprefix('urn:extern:')
                self._extern_properties[prop_name] = VitalSignsImpl.create_extern_property(value)
            super().__setattr__('_modified', True)
            return

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def my_getattr(self, name):

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        from vital_ai_vitalsigns_core.model.GraphMatch import GraphMatch
        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        if name == 'URI':
            if VitalConstants.uri_prop_uri in self._properties:
                return self._properties[VitalConstants.uri_prop_uri]
            else:
                return None
        if name == 'vitaltype':
            return self.get_class_uri()
        
        # Check if name is a full URI first
        if name in self._properties:
            return self._properties[name]
            
        # Then check for short names
        for prop_info in self.get_allowed_domain_properties():
            uri = prop_info['uri']
            # logger.debug(uri)
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)
            # logger.debug(trait_class)
            if trait_class and trait_class.get_short_name() == name:
                if uri in self._properties:
                    return self._properties[uri]
                else:
                    return None
        if isinstance(self, VITAL_GraphContainerObject):
            if name in self._extern_properties:
                value = self._extern_properties[name]
                # GraphMatch case of expanding embedded objects
                if isinstance(self, GraphMatch):
                    if VitalSignsImpl.is_parseable_as_uri(name):
                        try:
                            parsed_json = json.loads(str(value))
                            if isinstance(parsed_json, dict):
                                go = vs.from_json(str(value))
                                if go:
                                    return go
                        except Exception as e:
                            logger.info(f"Exception: {e}")
                            pass
                return value
            return None
        return NotImplemented

    def get_property_value(self, property_uri):
        if property_uri == VitalConstants.uri_prop_uri:
            return self._properties[VitalConstants.uri_prop_uri]
        trait_class = VitalSignsImpl.get_trait_class_from_uri(property_uri)
        if not trait_class:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute with uri'{property_uri}'")
        name = trait_class.get_short_name()
        return self.__getattr__(name)

    def __getattr__(self, name):
        value = self.my_getattr(name)
        if value is NotImplemented:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return value

    def set_property(self, prop, value):
        prop_string = str(prop)
        setattr(self, prop_string, value)

    def get_property(self, prop):
        prop_string = str(prop)
        return getattr(self, prop_string)

    def __getitem__(self, key):
        return self.get_property(key)

    def __setitem__(self, key, value):
        self.set_property(key, value)

    def __delitem__(self, key):
        self.set_property(key, None)

    def keys(self):
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        keys = list(self._properties.keys())

        if isinstance(self, VITAL_GraphContainerObject):
            extern_keys = list(self._extern_properties.keys())
            keys = keys + extern_keys

        return keys

    def values(self):
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        values = list(self._properties.values())

        if isinstance(self, VITAL_GraphContainerObject):
            extern_values = list(self._extern_properties.values())
            values = values + extern_values

        return values

    def items(self):

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        go_map = {}

        for key, value in self._properties.items():
            go_map[key] = value

        if isinstance(self, VITAL_GraphContainerObject):
            for key, value in self._extern_properties.items():
                go_map[key] = value

        return go_map.items()

    def graph_uri_set(self) -> Set[str]:
        return self._graph_uri_set.copy()

    def add_graph_uri(self, uri: str):
        self._graph_uri_set.add(uri)

    def remove_graph_uri(self, uri: str):
        self._graph_uri_set.remove(uri)

    def clear_graph_uri(self):
        self._graph_uri_set.clear()

    def include_on_graph(self, graph_collection: GC):
        self._graph_collection_set.add(graph_collection)

    def remove_from_graph(self, graph_collection: GC):
        self._graph_collection_set.remove(graph_collection)

    def graph_locations(self) -> Set[G]:
        return self._graph_collection_set.copy()

    def is_modified(self) -> bool:
        return self._modified

    def mark_serialized(self):
        super().__setattr__('_modified', False)

    def get_hash(self) -> str:
        return self._object_hash

    def calc_hash(self) -> str:
        # TODO define real function
        # we don't override the __hash__ function
        # because objects may be instantiated using different
        # queries over time and be included in different graphs
        # as separate instances (or just directly instantiated)
        # when serializing a graph, we want to detect
        # which objects are already serialized via a different graph
        # this may occur by the same object instance being serialized
        # or by an object with an identical hash already serialized
        # so, for the moment, we want to keep separate the concept
        # of the hash of an object instance and the hash of
        # all the properties and value of the object which make it unique
        # so if we have:
        # Graph 1: { A1, B1 }
        # Graph 2: { A2, C1 }
        # with A1 and A2 being different instances but identical object hashes
        # and we store Graph 1
        # if we store Graph 2 it can not serialize A2 since it already
        # has been serialized and is unchanged

        super().__setattr__('_object_hash', "")
        return self._object_hash

    @classmethod
    def is_top_level_class(cls):
        return cls.__bases__ == (object,)

    @classmethod
    @cacheable_method
    @abstractmethod
    def get_class_uri(cls) -> str:
        pass

    def to_dict(self) -> dict:
        return GraphObjectDictUtils.to_dict_impl(self)

    @staticmethod
    def to_dict_list(graph_object_list) -> List[dict]:
        return GraphObjectDictUtils.to_dict_list_impl(graph_object_list)

    def to_json(self, pretty_print=True) -> str:
        return GraphObjectJsonUtils.to_json_impl(self, pretty_print)

    def to_jsonld(self) -> dict:
        return GraphObjectJsonldUtils.to_jsonld_impl(self)

    @staticmethod
    def to_jsonld_list(graph_object_list) -> dict:
        return GraphObjectJsonldUtils.to_jsonld_list_impl(graph_object_list)

    def add_to_dataset(self, dataset: Dataset, graph_uri: str):
        GraphObjectTriplesUtils.add_to_dataset_impl(self, dataset, graph_uri)

    def add_to_list(self, triple_list: list):
        GraphObjectTriplesUtils.add_to_list_impl(self, triple_list)

    def to_triples(self) -> list:
        return GraphObjectTriplesUtils.to_triples_impl(self)

    @staticmethod
    def to_triples_list(graph_object_list: List) -> list:
        return GraphObjectTriplesUtils.to_triples_list_impl(graph_object_list)

    def to_rdf(self, format='nt', graph_uri: str = None) -> str:
        return GraphObjectRdfUtils.to_rdf_impl(self, format, graph_uri)

    @staticmethod
    @lru_cache(maxsize=1000)
    def valid_uri(uri_string: str) -> bool:
        return _is_valid_uri(uri_string)

    @classmethod
    def from_json_triples(cls, json_string: str) -> list:
        return GraphObjectTriplesUtils.from_json_triples_impl(cls, json_string)

    @classmethod
    def from_json(cls, json_map: str, *, modified=False) -> G:
        return GraphObjectJsonUtils.from_json_impl(cls, json_map, modified=modified)

    @classmethod
    def from_json_map(cls, json_map: dict, *, modified=False) -> G:
        return GraphObjectJsonUtils.from_json_map_impl(cls, json_map, modified=modified)

    @classmethod
    def from_dict(cls, dict_map: dict, *, modified=False) -> G:
        return GraphObjectDictUtils.from_dict_impl(cls, dict_map, modified=modified)

    @classmethod
    def from_dict_list(cls, dict_list: List[dict], *, modified=False) -> List[G]:
        return GraphObjectDictUtils.from_dict_list_impl(cls, dict_list, modified=modified)

    @classmethod
    def from_jsonld(cls, jsonld_data: dict, *, modified=False) -> G:
        return GraphObjectJsonldUtils.from_jsonld_impl(cls, jsonld_data, modified=modified)

    @classmethod
    def from_jsonld_list(cls, jsonld_doc, *, modified=False) -> List[G]:
        return GraphObjectJsonldUtils.from_jsonld_list_impl(cls, jsonld_doc, modified=modified)

    @classmethod
    def from_json_list(cls, json_map_list: str, *, modified=False) -> List[G]:
        return GraphObjectJsonUtils.from_json_list_impl(cls, json_map_list, modified=modified)

    @classmethod
    def from_rdf(cls, rdf_string: str, *, modified=False) -> G:
        return GraphObjectRdfUtils.from_rdf_impl(cls, rdf_string, modified=modified)

    @classmethod
    def from_triples(cls, triples: Generator[Tuple, None, None], *, modified=False) -> G:
        return GraphObjectTriplesUtils.from_triples_impl(cls, triples, modified=modified)

    @classmethod
    def from_triples_list(cls, triples_list: Generator[Tuple, None, None], *, modified=False) -> List[G]:
        return GraphObjectTriplesUtils.from_triples_list_impl(cls, triples_list, modified=modified)

    @classmethod
    def from_rdf_list(cls, rdf_string: str, *, modified=False) -> List[G]:
        return GraphObjectRdfUtils.from_rdf_list_impl(cls, rdf_string, modified=modified)

    # Pydantic v2 compatibility methods
    @classmethod
    def __get_pydantic_core_schema__(
        cls, 
        source_type: Type[Any], 
        handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Pydantic v2 core schema generation for GraphObject classes."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality. Install with: pip install pydantic>=2.0")
        return GraphObjectPydanticUtils.get_pydantic_core_schema_impl(cls, source_type, handler)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Pydantic-compatible serialization method."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality. Install with: pip install pydantic>=2.0")
        return GraphObjectPydanticUtils.pydantic_serialize_impl(self)

    @classmethod
    def model_validate(cls, data: Any, **kwargs) -> 'GraphObject':
        """Pydantic-compatible validation method."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality. Install with: pip install pydantic>=2.0")
        return GraphObjectPydanticUtils.pydantic_validate_impl(cls, data)

    def model_dump_json(self, **kwargs) -> str:
        """Pydantic-compatible JSON serialization."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality. Install with: pip install pydantic>=2.0")
        import json
        return json.dumps(self.model_dump(**kwargs))

    @classmethod
    def model_validate_json(cls, json_data: str, **kwargs) -> 'GraphObject':
        """Pydantic-compatible JSON validation."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality. Install with: pip install pydantic>=2.0")
        import json
        data = json.loads(json_data)
        return cls.model_validate(data, **kwargs)
