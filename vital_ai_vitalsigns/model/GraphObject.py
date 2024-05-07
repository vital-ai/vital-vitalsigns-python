from abc import ABC, abstractmethod
import json
from datetime import datetime
import rdflib
from rdflib import Graph, Literal, URIRef
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
        # Add your custom logic here
        return False  # Placeholder for the example


class GraphObjectMeta(type):
    def __setattr__(self, name, value):
        print(f"Setting class attribute {name} to {value}")
        super().__setattr__(name, value)

    def __getattr__(self, name):
        return AttributeComparisonProxy(self, name)


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

        for prop_uri, prop_instance in self._properties.items():
            rdf_data = prop_instance.to_rdf()
            g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        return g.serialize(format=format)

