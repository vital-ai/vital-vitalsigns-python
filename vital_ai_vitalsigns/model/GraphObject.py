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
from vital_ai_vitalsigns.model.annotation import AnnotationValue
from vital_ai_vitalsigns.impl.annotation_registry import is_annotation_property
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

def _parse_annotation_value(v):
    """Convert various value formats to AnnotationValue.

    Accepts:
      - AnnotationValue — returned as-is
      - dict with 'value' and optional 'lang' keys
      - rdflib Literal (has .language attribute)
      - str — plain string, no language tag
    """
    if isinstance(v, AnnotationValue):
        return v
    if isinstance(v, dict):
        return AnnotationValue(v["value"], lang=v.get("lang"))
    if hasattr(v, 'language'):
        return AnnotationValue(str(v), lang=v.language)
    return AnnotationValue(str(v))


class AttributeComparisonProxy:
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

    def __eq__(self, value):
        logger.info(f"Comparing {self.cls.__name__}.{self.name} with {value}")
        # TODO Add logic here
        return False  # Placeholder for the example
    
    

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
        
        # Prevent Pydantic from encountering AttributeComparisonProxy objects
        # by raising AttributeError for Pydantic-specific attributes
        pydantic_attrs = {
            '__get_pydantic_json_schema__',
            '__pydantic_generic_metadata__',
            '__pydantic_core_schema__',
            '__pydantic_serializer__',
            '__pydantic_validator__',
            '__pydantic_decorators__',
            '__pydantic_fields__',
            '__pydantic_config__',
            '__pydantic_complete__',
            '__pydantic_custom_init_subclass_params__',
            '__pydantic_init_subclass__',
            '__pydantic_post_init__',
            '__pydantic_private__',
            '__pydantic_extra__',
            '__pydantic_fields_set__',
            '__pydantic_parent_namespace__',
            '__args__',  # Used by Pydantic for generic type checking
            '__origin__',  # Used by Pydantic for generic type checking
            '__parameters__'  # Used by Pydantic for generic type checking
        }
        
        if name in pydantic_attrs:
            raise AttributeError(f"'{self.__name__}' has no attribute '{name}'")
        
        return AttributeComparisonProxy(self, name)

G = TypeVar('G', bound=Optional['GraphObject'])
GC = TypeVar('GC', bound='GraphCollection')

class GraphObject(metaclass=GraphObjectMeta):
    _allowed_properties = []

    _ANNOTATION_SHORT_NAMES = {
        'rdfs_label': 'http://www.w3.org/2000/01/rdf-schema#label',
        'rdfs_comment': 'http://www.w3.org/2000/01/rdf-schema#comment',
        'rdfs_seeAlso': 'http://www.w3.org/2000/01/rdf-schema#seeAlso',
        'rdfs_isDefinedBy': 'http://www.w3.org/2000/01/rdf-schema#isDefinedBy',
        'owl_versionInfo': 'http://www.w3.org/2002/07/owl#versionInfo',
        'owl_deprecated': 'http://www.w3.org/2002/07/owl#deprecated',
    }

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

    @classmethod
    @cacheable_method
    def _get_property_lookup_dicts(cls):
        uri_dict = {}
        short_name_dict = {}
        for prop_info in cls.get_allowed_domain_properties():
            uri = prop_info['uri']
            prop_class = prop_info['prop_class']
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)
            if trait_class:
                entry = {'uri': uri, 'prop_class': prop_class, 'trait_class': trait_class}
                uri_dict[uri] = entry
                short_name = trait_class.get_short_name()
                short_name_dict[short_name] = entry
        return uri_dict, short_name_dict

    def __init__(self, *, modified=True):
        super().__setattr__('_properties', {})
        super().__setattr__('_extern_properties', {})
        super().__setattr__('_annotations', {})
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

        ann_uri = self._ANNOTATION_SHORT_NAMES.get(name)
        if ann_uri is not None:
            self.set_annotation(ann_uri, value)
            return

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

        # this includes properties defined when the class was defined
        # including properties associated with parent classes when
        # those were defined
        # if an extending ontology adds a property to an existing class
        # this list will not include it

        uri_dict, short_name_dict = self._get_property_lookup_dicts()

        # O(1) lookup by full URI
        entry = uri_dict.get(name)
        if entry is None:
            # O(1) lookup by short name
            entry = short_name_dict.get(name)

        if entry:
            uri = entry['uri']
            if value is None:
                self._properties.pop(uri, None)
            else:
                self._properties[uri] = VitalSignsImpl.create_property_with_trait_from_classes(
                    entry['prop_class'], entry['trait_class'], value)
            super().__setattr__('_modified', True)
            return

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
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

        if name == 'URI':
            if VitalConstants.uri_prop_uri in self._properties:
                return self._properties[VitalConstants.uri_prop_uri]
            else:
                return None
        if name == 'vitaltype':
            return self.get_class_uri()

        ann_uri = self._ANNOTATION_SHORT_NAMES.get(name)
        if ann_uri is not None:
            return self.get_annotation(ann_uri)

        # Check if name is a full URI first
        if name in self._properties:
            return self._properties[name]

        # O(1) short name lookup using cached dict
        _, short_name_dict = self._get_property_lookup_dicts()
        entry = short_name_dict.get(name)
        if entry:
            uri = entry['uri']
            if uri in self._properties:
                return self._properties[uri]
            else:
                return None

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        if isinstance(self, VITAL_GraphContainerObject):
            if name in self._extern_properties:
                value = self._extern_properties[name]
                # GraphMatch case of expanding embedded objects
                from vital_ai_vitalsigns_core.model.GraphMatch import GraphMatch
                if isinstance(self, GraphMatch):
                    if VitalSignsImpl.is_parseable_as_uri(name):
                        try:
                            from vital_ai_vitalsigns.vitalsigns import VitalSigns
                            vs = VitalSigns()
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
        if property_uri in self._properties:
            return self._properties[property_uri]
        return None

    def __getattr__(self, name):
        value = self.my_getattr(name)
        if value is NotImplemented:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return value

    def set_property(self, prop, value, lang=None):
        if lang is not None:
            from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
            value = StringProperty(value, lang=lang)
        prop_string = str(prop)
        setattr(self, prop_string, value)

    def get_property(self, prop):
        prop_string = str(prop)
        return getattr(self, prop_string)

    # --- Annotation API ---

    def get_annotations(self, uri: str) -> list:
        return list(self._annotations.get(uri, []))

    def get_annotation(self, uri: str, lang=None):
        values = self._annotations.get(uri, [])
        if not values:
            return None
        if lang is not None:
            for av in values:
                if av.lang == lang:
                    return str(av)
            return None
        return str(values[0])

    def set_annotation(self, uri: str, value, lang=None):
        if value is None:
            self._annotations.pop(uri, None)
        else:
            if isinstance(value, AnnotationValue):
                av = value
            else:
                av = AnnotationValue(str(value), lang=lang)
            self._annotations[uri] = [av]
        super().__setattr__('_modified', True)

    def add_annotation(self, uri: str, value, lang=None):
        if isinstance(value, AnnotationValue):
            av = value
        else:
            av = AnnotationValue(str(value), lang=lang)
        if uri not in self._annotations:
            self._annotations[uri] = []
        self._annotations[uri].append(av)
        super().__setattr__('_modified', True)

    def remove_annotation(self, uri: str, value=None, lang=None):
        if uri not in self._annotations:
            return
        if value is None and lang is None:
            del self._annotations[uri]
        else:
            self._annotations[uri] = [
                av for av in self._annotations[uri]
                if not (
                    (value is None or str(av) == str(value)) and
                    (lang is None or av.lang == lang)
                )
            ]
            if not self._annotations[uri]:
                del self._annotations[uri]
        super().__setattr__('_modified', True)

    # --- Convenience annotation accessors with lang ---

    def get_rdfs_label(self, lang=None):
        return self.get_annotation('http://www.w3.org/2000/01/rdf-schema#label', lang=lang)

    def set_rdfs_label(self, value, lang=None):
        if lang is not None:
            self.remove_annotation('http://www.w3.org/2000/01/rdf-schema#label', lang=lang)
            if value is not None:
                self.add_annotation('http://www.w3.org/2000/01/rdf-schema#label', value, lang=lang)
        else:
            self.set_annotation('http://www.w3.org/2000/01/rdf-schema#label', value)

    def get_rdfs_comment(self, lang=None):
        return self.get_annotation('http://www.w3.org/2000/01/rdf-schema#comment', lang=lang)

    def set_rdfs_comment(self, value, lang=None):
        if lang is not None:
            self.remove_annotation('http://www.w3.org/2000/01/rdf-schema#comment', lang=lang)
            if value is not None:
                self.add_annotation('http://www.w3.org/2000/01/rdf-schema#comment', value, lang=lang)
        else:
            self.set_annotation('http://www.w3.org/2000/01/rdf-schema#comment', value)

    def set_rdfs_labels(self, lang_map: dict):
        """Replace all rdfs:label annotations with the given language map.

        Args:
            lang_map: dict mapping language tag to label string,
                      e.g. {"en": "Cat", "fr": "Chat", "de": "Katze"}.
                      Use None key for a label with no language tag.
        """
        self.set_annotations_by_lang('http://www.w3.org/2000/01/rdf-schema#label', lang_map)

    def set_rdfs_comments(self, lang_map: dict):
        """Replace all rdfs:comment annotations with the given language map.

        Args:
            lang_map: dict mapping language tag to comment string.
                      Use None key for a comment with no language tag.
        """
        self.set_annotations_by_lang('http://www.w3.org/2000/01/rdf-schema#comment', lang_map)

    def set_annotations_by_lang(self, uri: str, lang_map: dict):
        """Replace all annotations for a URI with the given language map.

        Args:
            uri: The annotation URI
            lang_map: dict mapping language tag (or None) to value string.
        """
        self._annotations.pop(uri, None)
        for lang, value in lang_map.items():
            self.add_annotation(uri, value, lang=lang)
        super().__setattr__('_modified', True)

    def __getitem__(self, key):
        return self.get_property(key)

    def __setitem__(self, key, value):
        self.set_property(key, value)

    def __delitem__(self, key):
        self.set_property(key, None)

    def keys(self):
        keys = list(self._properties.keys())

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        if isinstance(self, VITAL_GraphContainerObject):
            extern_keys = list(self._extern_properties.keys())
            keys = keys + extern_keys

        return keys

    def values(self):
        values = list(self._properties.values())

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        if isinstance(self, VITAL_GraphContainerObject):
            extern_values = list(self._extern_properties.values())
            values = values + extern_values

        return values

    def items(self):
        go_map = {}

        for key, value in self._properties.items():
            go_map[key] = value

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
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

    def to_property_map(self) -> dict:
        """Serialize to a property map — the fastest outbound path, no rdflib.

        Returns: {'subject_uri': str, 'type_uri': str, 'properties': {uri: value}}
        Multi-value properties are returned as lists.
        """
        properties = {}
        subject_uri = None

        for uri, prop in self._properties.items():
            if uri == VitalConstants.uri_prop_uri:
                subject_uri = prop.get_value()
                continue
            properties[uri] = prop.get_value()

        result = {
            'subject_uri': subject_uri,
            'type_uri': self.get_class_uri(),
            'properties': properties
        }

        if self._annotations:
            ann_dict = {}
            for ann_uri, ann_values in self._annotations.items():
                ann_dict[ann_uri] = [av.to_json() for av in ann_values]
            result['annotations'] = ann_dict

        return result

    @staticmethod
    def to_property_maps(graph_object_list: list) -> list:
        """Serialize a list of GraphObjects to property maps (batch).

        Returns list of {'subject_uri': str, 'type_uri': str, 'properties': {uri: value}}
        """
        uri_prop = VitalConstants.uri_prop_uri
        results = []
        for graph_object in graph_object_list:
            properties = {}
            subject_uri = None
            for uri, prop in graph_object._properties.items():
                if uri == uri_prop:
                    subject_uri = prop.get_value()
                    continue
                properties[uri] = prop.get_value()
            entry = {
                'subject_uri': subject_uri,
                'type_uri': graph_object.get_class_uri(),
                'properties': properties
            }
            if graph_object._annotations:
                ann_dict = {}
                for ann_uri, ann_values in graph_object._annotations.items():
                    ann_dict[ann_uri] = [av.to_json() for av in ann_values]
                entry['annotations'] = ann_dict
            results.append(entry)
        return results

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

    @staticmethod
    def from_property_map(subject_uri: str, type_uri: str,
                          properties: dict, *, modified=False, **kwargs) -> 'GraphObject':
        """Create a GraphObject directly from a property map.

        Bypasses rdflib and __setattr__ — the fastest deserialization path.

        Args:
            subject_uri: The URI of the graph object
            type_uri: The RDF type URI of the graph object
            properties: Dict mapping predicate URI strings to Python values.
                        Multi-value properties should map to a list of values.
            modified: Whether to mark the object as modified (default False)
        """
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl

        vs = VitalSigns()
        registry = vs.get_registry()

        graph_object_cls = registry.get_vitalsigns_class(type_uri)
        graph_object = graph_object_cls(modified=modified)
        graph_object.URI = subject_uri

        uri_dict, _ = graph_object_cls._get_property_lookup_dicts()

        for prop_uri, value in properties.items():
            if value is None:
                continue
            entry = uri_dict.get(prop_uri)
            if entry:
                graph_object._properties[prop_uri] = \
                    VitalSignsImpl.create_property_with_trait_from_classes(
                        entry['prop_class'], entry['trait_class'], value)
            elif is_annotation_property(prop_uri):
                if isinstance(value, list):
                    for v in value:
                        graph_object.add_annotation(prop_uri, _parse_annotation_value(v))
                else:
                    graph_object.add_annotation(prop_uri, _parse_annotation_value(value))

        annotations = kwargs.get('annotations')
        if annotations and isinstance(annotations, dict):
            for ann_uri, ann_list in annotations.items():
                for av_data in ann_list:
                    av = AnnotationValue.from_json(av_data)
                    graph_object.add_annotation(ann_uri, av)

        if not modified:
            graph_object.mark_serialized()

        return graph_object

    @staticmethod
    def from_property_maps(entries: list, *, modified=False) -> list:
        """Create GraphObjects from a list of property maps (batch).

        Each entry: {'subject_uri': str, 'type_uri': str, 'properties': {uri: value}}
        Multi-value properties should map to a list of values.
        """
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl

        vs = VitalSigns()
        registry = vs.get_registry()

        results = []
        for entry_map in entries:
            subject_uri = entry_map['subject_uri']
            type_uri = entry_map['type_uri']
            properties = entry_map['properties']

            graph_object_cls = registry.get_vitalsigns_class(type_uri)
            graph_object = graph_object_cls(modified=modified)
            graph_object.URI = subject_uri

            uri_dict, _ = graph_object_cls._get_property_lookup_dicts()

            for prop_uri, value in properties.items():
                if value is None:
                    continue
                entry = uri_dict.get(prop_uri)
                if entry:
                    graph_object._properties[prop_uri] = \
                        VitalSignsImpl.create_property_with_trait_from_classes(
                            entry['prop_class'], entry['trait_class'], value)
                elif is_annotation_property(prop_uri):
                    if isinstance(value, list):
                        for v in value:
                            graph_object.add_annotation(prop_uri, _parse_annotation_value(v))
                    else:
                        graph_object.add_annotation(prop_uri, _parse_annotation_value(value))

            annotations = entry_map.get('annotations')
            if annotations and isinstance(annotations, dict):
                for ann_uri, ann_list in annotations.items():
                    for av_data in ann_list:
                        av = AnnotationValue.from_json(av_data)
                        graph_object.add_annotation(ann_uri, av)

            if not modified:
                graph_object.mark_serialized()

            results.append(graph_object)

        return results

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

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        """Pydantic v2 JSON schema generation method with enhanced property structure."""
        if not PYDANTIC_V2_AVAILABLE:
            raise ImportError("Pydantic v2 is required for this functionality. Install with: pip install pydantic>=2.0")
        
        # Use enhanced schema generation that shows VitalSigns property structure
        return GraphObjectPydanticUtils.get_pydantic_json_schema_impl(cls, core_schema, handler)
