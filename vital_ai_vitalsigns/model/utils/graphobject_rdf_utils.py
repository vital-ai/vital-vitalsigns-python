from __future__ import annotations

import logging
from datetime import datetime
from typing import TypeVar, List, Optional
import rdflib
from rdflib import Graph, Literal, URIRef, RDF
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.vital_constants import VitalConstants

G = TypeVar('G', bound=Optional['GraphObject'])


class GraphObjectRdfUtils:
    """Utility class containing RDF-related functionality for GraphObject."""

    @staticmethod
    def to_rdf_impl(graph_object, format='nt', graph_uri: str = None) -> str:
        """Implementation of to_rdf functionality."""
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

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
                # logging.info(f"Setting {prop_uri}: {rdf_data['value']} : {rdf_data['datatype']}")
                g.add((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if isinstance(graph_object, VITAL_GraphContainerObject):
            for name, prop_instance in graph_object._extern_properties.items():

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

        multi_valued_props = []

        for subject, predicate, obj_value in g:

            if predicate == RDF.type:
                continue

            predicate = str(predicate)

            if predicate == VitalConstants.vitaltype_uri:
                continue

            if predicate == VitalConstants.uri_prop_uri:
                continue

            trait_cls = registry.vitalsigns_property_classes.get(predicate, None)

            multiple_values = False

            # for GCO this is not set
            # need to inspect the literal to detect multiple values?
            if trait_cls:
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

            value = None
            if isinstance(obj_value, Literal):
                value = obj_value.toPython()
            elif isinstance(obj_value, URIRef):
                value = str(obj_value)

            setattr(graph_object, predicate, value)

        if modified is False:
            graph_object.mark_serialized()

        return graph_object

    @staticmethod
    def from_rdf_list_impl(cls, rdf_string: str, *, modified=False) -> List[G]:
        """Implementation of from_rdf_list functionality."""
        g = Graph()

        g.parse(data=rdf_string, format='nt')

        subjects = set(g.subjects())

        split_rdf_strings = []

        for subj in subjects:

            subj_graph = Graph()

            for s, p, o in g.triples((subj, None, None)):
                subj_graph.add((s, p, o))

            serialized = subj_graph.serialize(format='nt')
            # Handle both string and bytes return types from serialize
            if isinstance(serialized, bytes):
                split_rdf_strings.append(serialized.decode('utf-8'))
            else:
                split_rdf_strings.append(serialized)

        graph_object_list = []

        for rdf_split in split_rdf_strings:
            graph_object = cls.from_rdf(rdf_split, modified=modified)
            graph_object_list.append(graph_object)

        return graph_object_list