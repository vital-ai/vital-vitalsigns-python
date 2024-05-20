from __future__ import annotations
from abc import ABC, abstractmethod
import json
from datetime import datetime
from typing import TypeVar, List

import rdflib
from rdflib import Graph, Literal, URIRef, RDF
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait
from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty


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
    def __setattr__(self, name, value):
        print(f"Setting class attribute {name} to {value}")
        super().__setattr__(name, value)

    def __getattr__(self, name):
        return AttributeComparisonProxy(self, name)


G = TypeVar('G', bound='GraphObject')


class GraphObject(metaclass=GraphObjectMeta):
    _allowed_properties = []

    @classmethod
    def get_allowed_properties(cls):
        return GraphObject._allowed_properties

    def __init__(self):
        super().__setattr__('_properties', {})

    def __setattr__(self, name, value) -> bool:
        # print(name)
        if name == 'URI':
            if value is None:
                self._properties.pop('http://vital.ai/ontology/vital-core#URIProp', None)
            else:
                self._properties['http://vital.ai/ontology/vital-core#URIProp'] = VitalSignsImpl.create_property_with_trait(URIProperty, 'http://vital.ai/ontology/vital-core#URIProp', value)
            return
        for prop_info in self.get_allowed_properties():
            uri = prop_info['uri']
            prop_class = prop_info['prop_class']
            trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)

            # full uri case
            if trait_class and uri == name:
                if value is None:
                    self._properties.pop(uri, None)
                else:
                    self._properties[uri] = VitalSignsImpl.create_property_with_trait(prop_class, uri, value)
                return

            # short name case
            if trait_class and trait_class.get_short_name() == name:
                if value is None:
                    self._properties.pop(uri, None)
                else:
                    self._properties[uri] = VitalSignsImpl.create_property_with_trait(prop_class, uri, value)
                return

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def my_getattr(self, name):
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

    @classmethod
    def is_top_level_class(cls):
        return cls.__bases__ == (object,)

    @classmethod
    @abstractmethod
    def get_class_uri(cls) -> str:
        pass

    def to_json(self) -> str:

        serializable_dict = {}

        for uri, prop in self._properties.items():
            prop_value = prop.to_json()["value"]
            if uri == 'http://vital.ai/ontology/vital-core#URIProp':
                serializable_dict['URI'] = prop_value
            else:
                serializable_dict[uri] = prop_value

        class_uri = self.get_class_uri()

        serializable_dict['type'] = class_uri

        serializable_dict['types'] = [class_uri]

        return json.dumps(serializable_dict, indent=2, cls=VitalSignsEncoder)

    def to_rdf(self, format='nt', graph_uri: str = None) -> str:

        g = Graph(identifier=URIRef(graph_uri) if graph_uri else None)

        subject = URIRef(str(self._properties['http://vital.ai/ontology/vital-core#URIProp']))

        class_uri = self.get_class_uri()

        g.add((subject, URIRef(RDF.type), URIRef(class_uri)))

        for prop_uri, prop_instance in self._properties.items():

            rdf_data = prop_instance.to_rdf()

            if rdf_data["datatype"] == URIRef:
                g.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
            else:
                g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        return g.serialize(format=format)

    @classmethod
    def from_json(cls, json_map: str) -> G:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        data = json.loads(json_map)

        type_uri = data['type']

        vs = VitalSigns()

        registry = vs.get_registry()

        graph_object_cls = registry.vitalsigns_classes[type_uri]

        graph_object = graph_object_cls()

        for key, value in data.items():
            if key == 'type':
                continue
            if key == 'types':
                continue

            setattr(graph_object, key, value)

        return graph_object

    @classmethod
    def from_json_list(cls, json_map_list: str) -> List[G]:

        graph_object_list = []

        data_list = json.loads(json_map_list)

        for data in data_list:
            graph_object = cls.from_json(data)
            graph_object_list.append(graph_object)

        return graph_object_list

    @classmethod
    def from_rdf(cls, rdf_string: str) -> G:

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

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        registry = vs.get_registry()

        graph_object_cls = registry.vitalsigns_classes[type_uri]

        graph_object = graph_object_cls()

        graph_object.URI = subject_uri

        for subject, predicate, obj_value in g:

            if predicate == RDF.type:
                continue

            if isinstance(obj_value, Literal):
                value = obj_value.toPython()
            elif isinstance(obj_value, URIRef):
                value = str(obj_value)
            setattr(obj, predicate, value)

        return graph_object

    @classmethod
    def from_rdf_list(cls, rdf_string: str) -> List[G]:

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
            graph_object = cls.from_rdf(rdf_split)
            graph_object_list.append(graph_object)

        return graph_object_list

