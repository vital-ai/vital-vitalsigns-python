from __future__ import annotations

import logging
from datetime import datetime
from typing import TypeVar, List, Optional
import rdflib
from rdflib import Graph, Literal, URIRef, RDF
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.vital_constants import VitalConstants
from vital_ai_vitalsigns.model.utils.rdf_utils import get_xsd_datatype
from vital_ai_vitalsigns.impl.annotation_registry import is_annotation_property
from vital_ai_vitalsigns.model.annotation import AnnotationValue

G = TypeVar('G', bound=Optional['GraphObject'])


class GraphObjectRdfUtils:
    """Utility class containing RDF-related functionality for GraphObject."""

    @staticmethod
    def to_rdf_impl(graph_object, format='nt', graph_uri: str = None) -> str:
        """Implementation of to_rdf functionality."""
        g = Graph(identifier=URIRef(graph_uri) if graph_uri else None)

        # Check if URI property exists
        if VitalConstants.uri_prop_uri not in graph_object._properties:
            raise ValueError("Cannot convert GraphObject to RDF - missing URI property")
        
        subject = URIRef(str(graph_object._properties[VitalConstants.uri_prop_uri]))

        class_uri = graph_object.get_class_uri()

        g.add((subject, URIRef(RDF.type), URIRef(class_uri)))

        g.add((subject, URIRef(VitalConstants.vitaltype_uri), URIRef(class_uri)))

        for prop_uri, prop_instance in graph_object._properties.items():

            rdf_data = prop_instance.to_rdf()

            if "lang" in rdf_data:
                g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], lang=rdf_data["lang"])))
            elif rdf_data["datatype"] == list:

                value_list = rdf_data["value"]
                data_class = rdf_data["data_class"]

                for v in value_list:
                    if data_class == URIRef:
                        g.add((subject, URIRef(prop_uri), URIRef(v)))
                    else:
                        g.add((subject, URIRef(prop_uri), Literal(v, datatype=get_xsd_datatype(data_class))))

            elif rdf_data["datatype"] == URIRef:
                g.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
            else:
                g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        if isinstance(graph_object, VITAL_GraphContainerObject):
            for name, prop_instance in graph_object._extern_properties.items():

                prop_uri = "urn:extern:" + name

                rdf_data = prop_instance.to_rdf()

                if "lang" in rdf_data:
                    g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], lang=rdf_data["lang"])))
                elif rdf_data["datatype"] == list:

                    value_list = rdf_data["value"]
                    data_class = rdf_data["data_class"]

                    for v in value_list:
                        if data_class == URIRef:
                            g.add((subject, URIRef(prop_uri), URIRef(v)))
                        else:
                            g.add((subject, URIRef(prop_uri), Literal(v, datatype=get_xsd_datatype(data_class))))

                elif rdf_data["datatype"] == URIRef:
                    g.add((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                else:
                    g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        for ann_uri, ann_values in graph_object._annotations.items():
            for av in ann_values:
                if av.lang:
                    g.add((subject, URIRef(ann_uri), Literal(str(av), lang=av.lang)))
                else:
                    g.add((subject, URIRef(ann_uri), Literal(str(av))))

        return g.serialize(format=format)

    @staticmethod
    def from_rdf_impl(cls, rdf_string: str, *, modified=False) -> G:
        """Implementation of from_rdf functionality."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        g = Graph()

        # Try to auto-detect format between supported formats
        parsed = False
        parse_error = None
        
        # First try N-Triples (most common for our use case)
        if not parsed:
            try:
                g.parse(data=rdf_string, format='nt')
                parsed = True
            except Exception as e:
                parse_error = e
        
        # Try Turtle format
        if not parsed:
            try:
                g.parse(data=rdf_string, format='turtle')
                parsed = True
            except Exception as e:
                parse_error = e
        
        # Try auto-detection as last resort
        if not parsed:
            try:
                g.parse(data=rdf_string)
                parsed = True
            except Exception as e:
                parse_error = e
        
        if not parsed:
            raise ValueError(f"Could not parse RDF data in supported formats (nt, turtle). Last error: {parse_error}")

        type_uri = None

        subject_uri = None

        vitaltype_class_uri = None

        for subject, predicate, obj in g.triples((None, RDF.type, None)):
            type_uri = str(obj)
            subject_uri = subject
            break

        for subject, predicate, obj in g.triples((None, URIRef(VitalConstants.vitaltype_uri), None)):
            vitaltype_class_uri = str(obj)
            break

        if not type_uri:
            raise ValueError("Type URI not found in RDF data.")

        if not subject_uri:
            raise ValueError("Subject URI not found in RDF data.")

        # TODO enforce: vitaltype_class_uri

        vs = VitalSigns()

        registry = vs.get_registry()

        # TODO switch to
        # graph_object_cls = registry.get_vitalsigns_class(vitaltype_class_uri)

        graph_object_cls = registry.get_vitalsigns_class(type_uri)

        graph_object = graph_object_cls(modified=modified)

        graph_object.URI = subject_uri

        uri_dict, _ = graph_object_cls._get_property_lookup_dicts()

        # Single-pass direct _properties write
        multi_value_accum = None

        for subject, predicate, obj_value in g:
            if predicate == RDF.type:
                continue
            predicate_str = str(predicate)
            if predicate_str == VitalConstants.vitaltype_uri:
                continue
            if predicate_str == VitalConstants.uri_prop_uri:
                continue

            if is_annotation_property(predicate_str):
                if isinstance(obj_value, Literal):
                    ann_lang = obj_value.language
                    ann_val = str(obj_value)
                    graph_object.add_annotation(predicate_str, ann_val, lang=ann_lang)
                continue

            entry = uri_dict.get(predicate_str)
            if not entry:
                # Fallback for unknown properties (e.g. VITAL_GraphContainerObject extern)
                if isinstance(graph_object, VITAL_GraphContainerObject):
                    value = None
                    if isinstance(obj_value, Literal):
                        value = obj_value.toPython()
                    elif isinstance(obj_value, URIRef):
                        value = str(obj_value)
                    setattr(graph_object, predicate_str, value)
                continue

            lang = None
            if isinstance(obj_value, Literal):
                value = obj_value.toPython()
                lang = obj_value.language
            elif isinstance(obj_value, URIRef):
                value = str(obj_value)
            else:
                value = obj_value

            if value is None:
                continue

            if entry['trait_class'].multiple_values:
                if multi_value_accum is None:
                    multi_value_accum = {}
                accum = multi_value_accum.get(predicate_str)
                if accum is None:
                    multi_value_accum[predicate_str] = (entry, [value])
                else:
                    accum[1].append(value)
            else:
                prop = VitalSignsImpl.create_property_with_trait_from_classes(
                    entry['prop_class'], entry['trait_class'], value)
                if lang:
                    prop.lang = lang
                graph_object._properties[predicate_str] = prop

        if multi_value_accum:
            for pred_str, (entry, value_list) in multi_value_accum.items():
                graph_object._properties[pred_str] = \
                    VitalSignsImpl.create_property_with_trait_from_classes(
                        entry['prop_class'], entry['trait_class'], value_list)

        if modified is False:
            graph_object.mark_serialized()

        return graph_object

    @staticmethod
    def from_rdf_list_impl(cls, rdf_string: str, *, modified=False) -> List[G]:
        """Implementation of from_rdf_list functionality."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        from collections import defaultdict

        g = Graph()
        g.parse(data=rdf_string, format='nt')

        # Group all triples by subject
        subject_triples = defaultdict(list)
        for s, p, o in g:
            subject_triples[s].append((p, o))

        vs = VitalSigns()
        registry = vs.get_registry()

        graph_object_list = []

        for subject, triples in subject_triples.items():
            type_uri = None
            subject_uri = str(subject)

            for predicate, obj in triples:
                if predicate == RDF.type:
                    type_uri = str(obj)
                    break

            if not type_uri:
                continue

            graph_object_cls = registry.get_vitalsigns_class(type_uri)
            graph_object = graph_object_cls(modified=modified)
            graph_object.URI = subject_uri

            uri_dict, _ = graph_object_cls._get_property_lookup_dicts()

            # Single-pass direct _properties write
            multi_value_accum = None

            for predicate, obj_value in triples:
                if predicate == RDF.type:
                    continue
                predicate_str = str(predicate)
                if predicate_str == VitalConstants.vitaltype_uri:
                    continue
                if predicate_str == VitalConstants.uri_prop_uri:
                    continue

                if is_annotation_property(predicate_str):
                    if isinstance(obj_value, Literal):
                        ann_lang = obj_value.language
                        ann_val = str(obj_value)
                        graph_object.add_annotation(predicate_str, ann_val, lang=ann_lang)
                    continue

                entry = uri_dict.get(predicate_str)
                if not entry:
                    if isinstance(graph_object, VITAL_GraphContainerObject):
                        value = None
                        if isinstance(obj_value, Literal):
                            value = obj_value.toPython()
                        elif isinstance(obj_value, URIRef):
                            value = str(obj_value)
                        setattr(graph_object, predicate_str, value)
                    continue

                lang = None
                if isinstance(obj_value, Literal):
                    value = obj_value.toPython()
                    lang = obj_value.language
                elif isinstance(obj_value, URIRef):
                    value = str(obj_value)
                else:
                    value = obj_value

                if value is None:
                    continue

                if entry['trait_class'].multiple_values:
                    if multi_value_accum is None:
                        multi_value_accum = {}
                    accum = multi_value_accum.get(predicate_str)
                    if accum is None:
                        multi_value_accum[predicate_str] = (entry, [value])
                    else:
                        accum[1].append(value)
                else:
                    prop = VitalSignsImpl.create_property_with_trait_from_classes(
                        entry['prop_class'], entry['trait_class'], value)
                    if lang:
                        prop.lang = lang
                    graph_object._properties[predicate_str] = prop

            if multi_value_accum:
                for pred_str, (entry, value_list) in multi_value_accum.items():
                    graph_object._properties[pred_str] = \
                        VitalSignsImpl.create_property_with_trait_from_classes(
                            entry['prop_class'], entry['trait_class'], value_list)

            if modified is False:
                graph_object.mark_serialized()

            graph_object_list.append(graph_object)

        return graph_object_list