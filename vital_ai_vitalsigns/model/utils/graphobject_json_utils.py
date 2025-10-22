from __future__ import annotations

import json
from typing import TypeVar, List, Optional
from vital_ai_vitalsigns.model.vital_constants import VitalConstants

G = TypeVar('G', bound=Optional['GraphObject'])


class VitalSignsEncoder(json.JSONEncoder):
    """JSON encoder for VitalSigns objects."""
    def default(self, o):
        from datetime import datetime
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class GraphObjectJsonUtils:
    """Utility class containing JSON-related functionality for GraphObject."""

    @staticmethod
    def to_json_impl(graph_object, pretty_print=True) -> str:
        """Implementation of to_json functionality."""
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        serializable_dict = {}

        for uri, prop in graph_object._properties.items():
            prop_value = prop.to_json()["value"]
            if uri == VitalConstants.uri_prop_uri:
                serializable_dict['URI'] = prop_value
            else:
                serializable_dict[uri] = prop_value

        if isinstance(graph_object, VITAL_GraphContainerObject):
            for name, prop in graph_object._extern_properties.items():
                prop_value = prop.to_json()["value"]
                uri = "urn:extern:" + name
                serializable_dict[uri] = prop_value

        class_uri = graph_object.get_class_uri()

        serializable_dict['type'] = class_uri

        serializable_dict[VitalConstants.vitaltype_uri] = class_uri

        serializable_dict['types'] = [class_uri]

        if pretty_print:
            json_string = json.dumps(serializable_dict, indent=2, cls=VitalSignsEncoder)
        else:
            json_string = json.dumps(serializable_dict, indent=None, cls=VitalSignsEncoder)

        return json_string

    @staticmethod
    def from_json_impl(cls, json_map: str, *, modified=False) -> G:
        """Implementation of from_json functionality."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        data = json.loads(json_map)

        type_uri = data['type']

        vitaltype_class_uri = data.get(VitalConstants.vitaltype_uri)

        vs = VitalSigns()

        registry = vs.get_registry()

        # graph_object_cls = registry.vitalsigns_classes[type_uri]

        graph_object_cls = registry.get_vitalsigns_class(type_uri)

        # TODO switch to this
        # graph_object_cls = registry.get_vitalsigns_class(vitaltype_class_uri)

        graph_object = graph_object_cls(modified=modified)

        for key, value in data.items():
            if key == 'type':
                continue
            if key == 'types':
                continue
            if key == 'vitaltype':  # is this used?
                continue
            if key == VitalConstants.vitaltype_uri:
                continue
            if key == VitalConstants.uri_prop_uri:
                graph_object.URI = value
                continue

            setattr(graph_object, key, value)

        return graph_object

    @staticmethod
    def from_json_map_impl(cls, json_map: dict, *, modified=False) -> G:
        """Implementation of from_json_map functionality."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        data = json_map

        type_uri = data['type']

        vitaltype_class_uri = data.get(VitalConstants.vitaltype_uri)

        vs = VitalSigns()

        registry = vs.get_registry()

        # graph_object_cls = registry.vitalsigns_classes[type_uri]

        graph_object_cls = registry.get_vitalsigns_class(type_uri)

        # TODO switch to this
        # graph_object_cls = registry.get_vitalsigns_class(vitaltype_class_uri)

        graph_object = graph_object_cls(modified=modified)

        for key, value in data.items():
            if key == 'type':
                continue
            if key == 'types':
                continue
            if key == 'vitaltype':  # is this used?
                continue
            if key == VitalConstants.vitaltype_uri:
                continue
            if key == VitalConstants.uri_prop_uri:
                graph_object.URI = value
                continue

            setattr(graph_object, key, value)

        return graph_object

    @staticmethod
    def from_json_list_impl(cls, json_map_list: str, *, modified=False) -> List[G]:
        """Implementation of from_json_list functionality."""
        graph_object_list = []

        data_list = json.loads(json_map_list)

        for data in data_list:
            graph_object = cls.from_json_map(data, modified=modified)
            graph_object_list.append(graph_object)

        return graph_object_list