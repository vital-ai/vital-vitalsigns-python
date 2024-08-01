from __future__ import annotations
import sys
from abc import ABC, abstractmethod
import json
from datetime import datetime
from typing import TypeVar, List, Generator, Tuple, Optional, Set
from urllib.parse import urlparse
import rdflib
from rdflib import Graph, Literal, URIRef, RDF, Dataset
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.properties.IProperty import IProperty
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from functools import wraps
from functools import lru_cache
from rdflib.term import _is_valid_uri

from vital_ai_vitalsigns.model.utils.class_utils import ClassUtils


def cacheable_method(method):
    @lru_cache(None)
    @wraps(method)
    def cached_method(*args, **kwargs):
        return method(*args, **kwargs)
    cached_method._is_cacheable = True
    return cached_method


class VitalSignsEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class AttributeComparisonProxy:
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

    def __eq__(self, value):
        print(f"Comparing {self.cls.__name__}.{self.name} with {value}")
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
        print(f"Setting class attribute {name} to {value}")
        super().__setattr__(name, value)

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            print(f"Getting internal class attribute: {name}")
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

    def __del__(self):
        # print(f"deleting: {self}")

        if sys.meta_path is None or not hasattr(sys, 'modules'):
            # Python is shutting down, skip cleanup
            # print("shutting down")
            return

        try:
            from vital_ai_vitalsigns.vitalsigns import VitalSigns
            # print(f"deleting: {self.URI}")
            vs = VitalSigns()
            vs.remove_graph_object(self)
        except Exception as ex:
            # print(ex)
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

        domain_prop_list = self.get_allowed_domain_properties()

        for d in domain_prop_list:
            print(f"Domain Prop: {d}")

        prop_list = self.get_allowed_properties()

        # for prop_info in prop_list:

        for prop_info in domain_prop_list:

            uri = prop_info['uri']
            prop_class = prop_info['prop_class']
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)

            # full uri case
            # print(f"uri: {uri} :: name: {name}")

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
                            print(f"Exception: {e}")
                            pass
                return value
            return None
        return NotImplemented

    def get_property_value(self, property_uri):
        if property_uri == 'http://vital.ai/ontology/vital-core#URIProp':
            return self._properties['http://vital.ai/ontology/vital-core#URIProp']
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

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        serializable_dict = {}

        for uri, prop in self._properties.items():
            prop_value = prop.to_json()["value"]
            if uri == 'http://vital.ai/ontology/vital-core#URIProp':
                serializable_dict['URI'] = prop_value
            else:
                serializable_dict[uri] = prop_value

        if isinstance(self, VITAL_GraphContainerObject):
            for name, prop in self._extern_properties.items():
                prop_value = prop.to_json()["value"]
                uri = "urn:extern:" + name
                serializable_dict[uri] = prop_value

        class_uri = self.get_class_uri()

        serializable_dict['type'] = class_uri

        serializable_dict['types'] = [class_uri]

        return serializable_dict

    def to_json(self, pretty_print=True) -> str:

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        serializable_dict = {}

        for uri, prop in self._properties.items():
            prop_value = prop.to_json()["value"]
            if uri == 'http://vital.ai/ontology/vital-core#URIProp':
                serializable_dict['URI'] = prop_value
            else:
                serializable_dict[uri] = prop_value

        if isinstance(self, VITAL_GraphContainerObject):
            for name, prop in self._extern_properties.items():
                prop_value = prop.to_json()["value"]
                uri = "urn:extern:" + name
                serializable_dict[uri] = prop_value

        class_uri = self.get_class_uri()

        serializable_dict['type'] = class_uri

        serializable_dict['types'] = [class_uri]

        if pretty_print:
            json_string = json.dumps(serializable_dict, indent=2, cls=VitalSignsEncoder)
        else:
            json_string = json.dumps(serializable_dict, indent=None, cls=VitalSignsEncoder)

        return json_string

    def add_to_dataset(self, dataset: Dataset, graph_uri: str):

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        subject = URIRef(str(self._properties['http://vital.ai/ontology/vital-core#URIProp']))

        triples = []

        class_uri = self.get_class_uri()

        triples.append((subject, URIRef(RDF.type), URIRef(class_uri)))

        # graph.add((subject, URIRef(RDF.type), URIRef(class_uri)))

        for prop_uri, prop_instance in self._properties.items():

            rdf_data = prop_instance.to_rdf()

            if rdf_data["datatype"] == list:

                value_list = rdf_data["value"]
                data_class = rdf_data["data_class"]

                for v in value_list:
                    if data_class == URIRef:
                        # graph.add((subject, URIRef(prop_uri), URIRef(v)))
                        triples.append((subject, URIRef(prop_uri), URIRef(v)))
                    else:
                        if data_class == datetime:
                            datatype = rdflib.XSD.dateTime
                        elif data_class == int:
                            datatype = rdflib.XSD.integer
                        elif data_class == float:
                            datatype = rdflib.XSD.float
                        elif data_class == bool:
                            datatype = rdflib.XSD.boolean
                        else:
                            datatype = rdflib.XSD.string

                        # graph.add((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))
                        triples.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

            elif rdf_data["datatype"] == URIRef:
                # graph.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                triples.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
            else:
                # graph.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))
                triples.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if isinstance(self, VITAL_GraphContainerObject):
            for name, prop_instance in self._extern_properties.items():

                prop_uri = "urn:extern:" + name

                rdf_data = prop_instance.to_rdf()

                if rdf_data["datatype"] == list:

                    value_list = rdf_data["value"]
                    data_class = rdf_data["data_class"]

                    for v in value_list:
                        if data_class == URIRef:
                            # graph.add((subject, URIRef(prop_uri), URIRef(v)))
                            triples.append((subject, URIRef(prop_uri), URIRef(v)))
                        else:
                            if data_class == datetime:
                                datatype = rdflib.XSD.dateTime
                            elif data_class == int:
                                datatype = rdflib.XSD.integer
                            elif data_class == float:
                                datatype = rdflib.XSD.float
                            elif data_class == bool:
                                datatype = rdflib.XSD.boolean
                            else:
                                datatype = rdflib.XSD.string

                            # graph.add((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))
                            triples.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

                elif rdf_data["datatype"] == URIRef:
                    # graph.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                    triples.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                else:
                    # graph.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))
                    triples.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if len(triples) > 0:
            triples_with_context = [(s, p, o, URIRef(graph_uri)) for s, p, o in triples]
            # print(f"Adding: {triples_with_context}")
            dataset.addN(triples_with_context)
            # print(f"Added {len(triples_with_context)} triples to graph with triple count: {len(graph)}")

    def add_to_list(self, triple_list: list):

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        subject = URIRef(str(self._properties['http://vital.ai/ontology/vital-core#URIProp']))

        class_uri = self.get_class_uri()

        triple_list.append((subject, URIRef(RDF.type), URIRef(class_uri)))

        for prop_uri, prop_instance in self._properties.items():

            rdf_data = prop_instance.to_rdf()

            if rdf_data["datatype"] == list:

                value_list = rdf_data["value"]
                data_class = rdf_data["data_class"]

                for v in value_list:
                    if data_class == URIRef:
                        # graph.add((subject, URIRef(prop_uri), URIRef(v)))
                        triple_list.append((subject, URIRef(prop_uri), URIRef(v)))
                    else:
                        if data_class == datetime:
                            datatype = rdflib.XSD.dateTime
                        elif data_class == int:
                            datatype = rdflib.XSD.integer
                        elif data_class == float:
                            datatype = rdflib.XSD.float
                        elif data_class == bool:
                            datatype = rdflib.XSD.boolean
                        else:
                            datatype = rdflib.XSD.string

                        # graph.add((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))
                        triple_list.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

            elif rdf_data["datatype"] == URIRef:
                # graph.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                triple_list.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
            else:
                # graph.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))
                triple_list.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if isinstance(self, VITAL_GraphContainerObject):
            for name, prop_instance in self._extern_properties.items():

                prop_uri = "urn:extern:" + name

                rdf_data = prop_instance.to_rdf()

                if rdf_data["datatype"] == list:

                    value_list = rdf_data["value"]
                    data_class = rdf_data["data_class"]

                    for v in value_list:
                        if data_class == URIRef:
                            # graph.add((subject, URIRef(prop_uri), URIRef(v)))
                            triple_list.append((subject, URIRef(prop_uri), URIRef(v)))
                        else:
                            if data_class == datetime:
                                datatype = rdflib.XSD.dateTime
                            elif data_class == int:
                                datatype = rdflib.XSD.integer
                            elif data_class == float:
                                datatype = rdflib.XSD.float
                            elif data_class == bool:
                                datatype = rdflib.XSD.boolean
                            else:
                                datatype = rdflib.XSD.string

                            # graph.add((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))
                            triple_list.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

                elif rdf_data["datatype"] == URIRef:
                    # graph.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                    triple_list.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                else:
                    # graph.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))
                    triple_list.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

    def to_rdf(self, format='nt', graph_uri: str = None) -> str:

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        # change to a Dataset for quads?
        g = Graph(identifier=URIRef(graph_uri) if graph_uri else None)

        subject = URIRef(str(self._properties['http://vital.ai/ontology/vital-core#URIProp']))

        class_uri = self.get_class_uri()

        g.add((subject, URIRef(RDF.type), URIRef(class_uri)))

        for prop_uri, prop_instance in self._properties.items():

            rdf_data = prop_instance.to_rdf()

            if rdf_data["datatype"] == list:

                value_list = rdf_data["value"]
                data_class = rdf_data["data_class"]

                for v in value_list:
                    if data_class == URIRef:
                        g.add((subject, URIRef(prop_uri), URIRef(v)))
                    else:
                        if data_class == datetime:
                            datatype = rdflib.XSD.dateTime
                        elif data_class == int:
                            datatype = rdflib.XSD.integer
                        elif data_class == float:
                            datatype = rdflib.XSD.float
                        elif data_class == bool:
                            datatype = rdflib.XSD.boolean
                        else:
                            datatype = rdflib.XSD.string

                        g.add((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

            elif rdf_data["datatype"] == URIRef:
                g.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
            else:
                g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if isinstance(self, VITAL_GraphContainerObject):
            for name, prop_instance in self._extern_properties.items():

                prop_uri = "urn:extern:" + name

                rdf_data = prop_instance.to_rdf()

                if rdf_data["datatype"] == list:

                    value_list = rdf_data["value"]
                    data_class = rdf_data["data_class"]

                    for v in value_list:
                        if data_class == URIRef:
                            g.add((subject, URIRef(prop_uri), URIRef(v)))
                        else:
                            if data_class == datetime:
                                datatype = rdflib.XSD.dateTime
                            elif data_class == int:
                                datatype = rdflib.XSD.integer
                            elif data_class == float:
                                datatype = rdflib.XSD.float
                            elif data_class == bool:
                                datatype = rdflib.XSD.boolean
                            else:
                                datatype = rdflib.XSD.string

                            g.add((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

                elif rdf_data["datatype"] == URIRef:
                    g.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                else:
                    g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        return g.serialize(format=format)

    @staticmethod
    @lru_cache(maxsize=1000)
    def valid_uri(uri_string: str) -> bool:
        return _is_valid_uri(uri_string)

    @classmethod
    def from_json_triples(cls, json_string: str) -> list:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        triple_list = []

        # print(json_string)

        object_map = json.loads(json_string)

        subject = URIRef(object_map['URI'])

        type_uri = object_map['type']

        type_uri_ref = URIRef(type_uri)

        triple_list.append((subject, RDF.type, type_uri_ref))

        triple_list.append((subject, URIRef('http://vital.ai/ontology/vital-core#URIProp'), subject))

        registry = vs.get_registry()

        graph_object_cls = registry.get_vitalsigns_class(type_uri)

        allowed_prop_list = graph_object_cls.get_allowed_properties()

        # TODO
        # handle types
        # handle vitaltype
        # handle lists or prop values?

        for property_uri, value in object_map.items():

            if property_uri == 'type':
                continue
            if property_uri == 'types':
                continue
            if property_uri == 'URI':
                continue

            triple_prop_class = None

            for prop_info in allowed_prop_list:
                p_uri = prop_info['uri']
                if p_uri == property_uri:
                    prop_class = prop_info['prop_class']
                    triple_prop_class = prop_class
                    break

            prop_uri = URIRef(property_uri)

            try:
                if isinstance(value, dict):
                    continue

                if triple_prop_class == URIProperty:
                    triple = (subject, prop_uri, URIRef(value))
                elif triple_prop_class is not None:
                    datatype = IProperty.get_rdf_datatype(value)
                    literal_value = Literal(value, datatype=datatype)
                    triple = (subject, prop_uri, literal_value)
                elif cls.valid_uri(value):
                    triple = (subject, prop_uri, URIRef(value))
                else:
                    datatype = IProperty.get_rdf_datatype(value)
                    literal_value = Literal(value, datatype=datatype)
                    triple = (subject, prop_uri, literal_value)

                triple_list.append(triple)
            except ValueError as e:
                print(f"Error creating triple for {property_uri}: {e}")

        return triple_list

    @classmethod
    def from_json(cls, json_map: str, *, modified=False) -> G:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        data = json.loads(json_map)

        type_uri = data['type']

        vs = VitalSigns()

        registry = vs.get_registry()

        # graph_object_cls = registry.vitalsigns_classes[type_uri]

        graph_object_cls = registry.get_vitalsigns_class(type_uri)

        graph_object = graph_object_cls(modified=modified)

        for key, value in data.items():
            if key == 'type':
                continue
            if key == 'types':
                continue
            if key == 'http://vital.ai/ontology/vital-core#URIProp':
                graph_object.URI = value
                continue

            setattr(graph_object, key, value)

        return graph_object

    @classmethod
    def from_json_list(cls, json_map_list: str, *, modified=False) -> List[G]:

        graph_object_list = []

        data_list = json.loads(json_map_list)

        for data in data_list:
            graph_object = cls.from_json(data, modified=modified)
            graph_object_list.append(graph_object)

        return graph_object_list

    @classmethod
    def from_rdf(cls, rdf_string: str, *, modified=False) -> G:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        g = Graph()

        g.parse(data=rdf_string, format='nt')

        type_uri = None

        subject_uri = None

        for subject, predicate, obj in g.triples((None, RDF.type, None)):
            type_uri = str(obj)
            subject_uri = subject
            break

        if not type_uri:
            raise ValueError("Type URI not found in RDF data.")

        if not subject_uri:
            raise ValueError("Subject URI not found in RDF data.")

        vs = VitalSigns()

        registry = vs.get_registry()

        graph_object_cls = registry.vitalsigns_classes[type_uri]

        graph_object = graph_object_cls(modified=modified)

        graph_object.URI = subject_uri

        multi_valued_props = []

        for subject, predicate, obj_value in g:

            if predicate == RDF.type:
                continue

            predicate = str(predicate)

            if predicate == 'http://vital.ai/ontology/vital-core#URIProp':
                continue

            trait_cls = registry.vitalsigns_property_classes[predicate]

            multiple_values = trait_cls.multiple_values

            if multiple_values is True:

                if predicate in multi_valued_props:
                    continue

                value_list = []

                for multi_value_subject, multi_value_predicate, multi_obj_value in g.triples((subject, URIRef(predicate), None)):
                    value_list.append(multi_obj_value)

                setattr(graph_object, predicate, value_list)

                multi_valued_props.append(predicate)

                continue

            if isinstance(obj_value, Literal):
                value = obj_value.toPython()
            elif isinstance(obj_value, URIRef):
                value = str(obj_value)

            setattr(graph_object, predicate, value)

        if modified is False:
            graph_object.mark_serialized()

        return graph_object

    @classmethod
    def from_triples(cls, triples: Generator[Tuple, None, None], *, modified=False) -> 'G':

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        type_uri = None
        subject_uri = None

        generated_triples = []

        # copy the generated triples into a list for repeat processing
        for subject, predicate, obj in triples:
            generated_triples.append((subject, predicate, obj))

        for subject, predicate, obj in generated_triples:
            # print(f"Triple: {subject}, {predicate}, {obj}")
            if predicate == RDF.type:
                type_uri = str(obj)
                subject_uri = str(subject)
                break

        if not type_uri:
            raise ValueError("Type URI not found in RDF data.")

        if not subject_uri:
            raise ValueError("Subject URI not found in RDF data.")

        vs = VitalSigns()

        registry = vs.get_registry()

        graph_object_cls = registry.vitalsigns_classes[type_uri]

        graph_object = graph_object_cls(modified=modified)

        graph_object.URI = subject_uri

        for subject, predicate, obj_value in generated_triples:

            if predicate == RDF.type:
                continue

            predicate = str(predicate)

            # skip
            if predicate == 'http://vital.ai/ontology/vital-core#URIProp':
                continue

            if isinstance(obj_value, Literal):
                value = obj_value.toPython()
            elif isinstance(obj_value, URIRef):
                value = str(obj_value)

            setattr(graph_object, predicate, value)

        if modified is False:
            graph_object.mark_serialized()

        return graph_object

    @classmethod
    def from_rdf_list(cls, rdf_string: str, *, modified=False) -> List[G]:

        g = Graph()

        g.parse(data=rdf_string, format='nt')

        subjects = set(g.subjects())

        split_rdf_strings = []

        for subj in subjects:

            subj_graph = Graph()

            for s, p, o in g.triples((subj, None, None)):
                subj_graph.add((s, p, o))

            split_rdf_strings.append(subj_graph.serialize(format='nt').decode('utf-8'))

        graph_object_list = []

        for rdf_split in split_rdf_strings:
            graph_object = cls.from_rdf(rdf_split, modified=modified)
            graph_object_list.append(graph_object)

        return graph_object_list
