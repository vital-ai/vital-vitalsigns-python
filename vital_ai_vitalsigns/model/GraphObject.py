from __future__ import annotations
from abc import ABC, abstractmethod
import json
from datetime import datetime
from typing import TypeVar, List, Generator, Tuple
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
        super().__setattr__('_extern_properties', {})

    def __setattr__(self, name, value) -> bool:
        # print(f"Name: {name}")

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

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
            # print(f"uri: {uri} :: name: {name}")

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

        if isinstance(self, VITAL_GraphContainerObject):
            # arbitrary properties are allowed
            if value is None:
                self._extern_properties.pop(name, None)
            else:
                prop_name = name.removeprefix('urn:extern:')
                self._extern_properties[prop_name] = VitalSignsImpl.create_extern_property(value)
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

    @classmethod
    def is_top_level_class(cls):
        return cls.__bases__ == (object,)

    @classmethod
    @abstractmethod
    def get_class_uri(cls) -> str:
        pass

    def to_json(self) -> str:

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

        return json.dumps(serializable_dict, indent=2, cls=VitalSignsEncoder)

    def to_rdf(self, format='nt', graph_uri: str = None) -> str:

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

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

        if isinstance(self, VITAL_GraphContainerObject):
            for name, prop_instance in self._extern_properties.items():

                prop_uri = "urn:extern:" + name

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
            if key == 'http://vital.ai/ontology/vital-core#URIProp':
                graph_object.URI = value
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

        graph_object = graph_object_cls()

        graph_object.URI = subject_uri

        for subject, predicate, obj_value in g:

            if predicate == RDF.type:
                continue

            predicate = str(predicate)

            if predicate == 'http://vital.ai/ontology/vital-core#URIProp':
                continue

            if isinstance(obj_value, Literal):
                value = obj_value.toPython()
            elif isinstance(obj_value, URIRef):
                value = str(obj_value)

            setattr(graph_object, predicate, value)

        return graph_object

    @classmethod
    def from_triples(cls, triples: Generator[Tuple, None, None]) -> 'G':

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        type_uri = None
        subject_uri = None

        generated_triples = []

        # copy the generated triples into a list for repeat processing
        for subject, predicate, obj in triples:
            generated_triples.append((subject, predicate, obj))

        for subject, predicate, obj in generated_triples:
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

        graph_object = graph_object_cls()

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
