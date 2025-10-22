from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TypeVar, List, Generator, Tuple, Optional
import rdflib
from rdflib import Graph, Literal, URIRef, RDF, Dataset
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.vital_constants import VitalConstants
from vital_ai_vitalsigns.model.properties.IProperty import IProperty
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from rdflib.term import _is_valid_uri
from collections import defaultdict

G = TypeVar('G', bound=Optional['GraphObject'])

# Create logger for this module
logger = logging.getLogger(__name__)


class GraphObjectTriplesUtils:
    """Utility class containing triples-related functionality for GraphObject."""

    @staticmethod
    def from_json_triples_impl(cls, json_string: str) -> list:
        """Implementation of from_json_triples functionality."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        triple_list = []

        object_map = json.loads(json_string)

        subject = URIRef(object_map['URI'])

        type_uri = object_map['type']

        type_uri_ref = URIRef(type_uri)

        triple_list.append((subject, RDF.type, type_uri_ref))

        triple_list.append((subject, URIRef(VitalConstants.vitaltype_uri), type_uri_ref))

        triple_list.append((subject, URIRef(VitalConstants.uri_prop_uri), subject))

        registry = vs.get_registry()

        graph_object_cls = registry.get_vitalsigns_class(type_uri)

        allowed_prop_list = graph_object_cls.get_allowed_domain_properties()

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
            if property_uri == 'vitaltype':  # is this used?
                continue
            if property_uri == VitalConstants.vitaltype_uri:
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
                elif _is_valid_uri(value):
                    triple = (subject, prop_uri, URIRef(value))
                else:
                    datatype = IProperty.get_rdf_datatype(value)
                    literal_value = Literal(value, datatype=datatype)
                    triple = (subject, prop_uri, literal_value)

                triple_list.append(triple)
            except ValueError as e:
                print(f"Error creating triple for {property_uri}: {e}")

        return triple_list

    @staticmethod
    def from_triples_impl(cls, triples: Generator[Tuple, None, None], *, modified=False) -> G:
        """Implementation of from_triples functionality."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        type_uri = None
        subject_uri = None
        vitaltype_class_uri = None

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

        # TODO enforce vitaltype_class_uri

        vs = VitalSigns()

        registry = vs.get_registry()

        # TODO switch to: vitaltype_class_uri
        # graph_object_cls = registry.get_vitalsigns_class(vitaltype_class_uri)

        graph_object_cls = registry.get_vitalsigns_class(type_uri)

        graph_object = graph_object_cls(modified=modified)

        graph_object.URI = subject_uri

        for subject, predicate, obj_value in generated_triples:

            if predicate == RDF.type:
                continue

            predicate = str(predicate)

            # skip
            if predicate == VitalConstants.vitaltype_uri:
                continue

            if predicate == VitalConstants.uri_prop_uri:
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
    def from_triples_list_impl(cls, triples_list: Generator[Tuple, None, None], *, modified=False) -> List[G]:
        """Implementation of from_triples_list functionality."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        # TODO enforce vitaltype_class_uri
        registry = vs.get_registry()

        graph_object_list = []

        generated_triples = []

        grouped_triples = defaultdict(list)

        for subject, predicate, obj in triples_list:
            generated_triples.append((subject, predicate, obj))
            grouped_triples[subject].append((predicate, obj))

        for subject, triples in grouped_triples.items():

            type_uri = None
            vitaltype_class_uri = None
            subject_uri = str(subject)

            for predicate, obj in triples:

                if predicate == RDF.type:
                    type_uri = str(obj)
                    break

            if not type_uri:
                logging.info(f"subject: {subject}")
                logging.info(f"triples: {triples}")
                raise ValueError("Type URI not found in RDF data.")

            if not subject_uri:
                logging.info(f"subject: {subject}")
                logging.info(f"triples: {triples}")
                raise ValueError("Subject URI not found in RDF data.")

            # TODO switch to: vitaltype_class_uri
            # graph_object_cls = registry.get_vitalsigns_class(vitaltype_class_uri)

            graph_object_cls = registry.get_vitalsigns_class(type_uri)

            graph_object = graph_object_cls(modified=modified)

            graph_object.URI = subject_uri

            for predicate, obj_value in triples:

                if predicate == RDF.type:
                    continue

                predicate = str(predicate)

                # skip
                if predicate == VitalConstants.vitaltype_uri:
                    continue

                if predicate == VitalConstants.uri_prop_uri:
                    continue

                value = None

                if isinstance(obj_value, Literal):
                    value = obj_value.toPython()
                elif isinstance(obj_value, URIRef):
                    value = str(obj_value)

                setattr(graph_object, predicate, value)

            if modified is False:
                graph_object.mark_serialized()

            graph_object_list.append(graph_object)

        return graph_object_list

    @staticmethod
    def add_to_list_impl(graph_object, triple_list: list):
        """Implementation of add_to_list functionality."""
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        subject = URIRef(str(graph_object._properties[VitalConstants.uri_prop_uri]))

        class_uri = graph_object.get_class_uri()

        triple_list.append((subject, URIRef(RDF.type), URIRef(class_uri)))

        triple_list.append((subject, URIRef(VitalConstants.vitaltype_uri), URIRef(class_uri)))

        for prop_uri, prop_instance in graph_object._properties.items():

            rdf_data = prop_instance.to_rdf()

            if rdf_data["datatype"] == list:

                value_list = rdf_data["value"]
                data_class = rdf_data["data_class"]

                for v in value_list:
                    if data_class == URIRef:
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

                        triple_list.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

            elif rdf_data["datatype"] == URIRef:
                triple_list.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
            else:
                triple_list.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if isinstance(graph_object, VITAL_GraphContainerObject):
            for name, prop_instance in graph_object._extern_properties.items():

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

                            triple_list.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

                elif rdf_data["datatype"] == URIRef:
                    triple_list.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                else:
                    triple_list.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

    @staticmethod
    def add_to_dataset_impl(graph_object, dataset: Dataset, graph_uri: str):
        """Implementation of add_to_dataset functionality."""
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject

        subject = URIRef(str(graph_object._properties[VitalConstants.uri_prop_uri]))

        triples = []

        class_uri = graph_object.get_class_uri()

        triples.append((subject, URIRef(RDF.type), URIRef(class_uri)))

        triples.append((subject, URIRef(VitalConstants.vitaltype_uri), URIRef(class_uri)))

        for prop_uri, prop_instance in graph_object._properties.items():

            rdf_data = prop_instance.to_rdf()

            if rdf_data["datatype"] == list:

                value_list = rdf_data["value"]
                data_class = rdf_data["data_class"]

                for v in value_list:
                    if data_class == URIRef:
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

                        triples.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

            elif rdf_data["datatype"] == URIRef:
                triples.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
            else:
                triples.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if isinstance(graph_object, VITAL_GraphContainerObject):
            for name, prop_instance in graph_object._extern_properties.items():

                prop_uri = "urn:extern:" + name

                rdf_data = prop_instance.to_rdf()

                if rdf_data["datatype"] == list:

                    value_list = rdf_data["value"]
                    data_class = rdf_data["data_class"]

                    for v in value_list:
                        if data_class == URIRef:
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

                            triples.append((subject, URIRef(prop_uri), Literal(v, datatype=datatype)))

                elif rdf_data["datatype"] == URIRef:
                    triples.append((subject, URIRef(prop_uri), URIRef(rdf_data["value"])))
                else:
                    triples.append((subject, URIRef(prop_uri), Literal(rdf_data["value"], datatype=rdf_data["datatype"])))

        if len(triples) > 0:
            triples_with_context = [(s, p, o, URIRef(graph_uri)) for s, p, o in triples]
            # logger.debug(f"Adding: {triples_with_context}")
            dataset.addN(triples_with_context)
            # logger.debug(f"Added {len(triples_with_context)} triples to graph with triple count: {len(graph)}")

    @staticmethod
    def to_triples_impl(graph_object) -> list:
        """Implementation of to_triples functionality."""
        # Simple implementation that reuses existing add_to_list logic
        triple_list = []
        GraphObjectTriplesUtils.add_to_list_impl(graph_object, triple_list)
        return triple_list

    @staticmethod
    def to_triples_list_impl(graph_object_list: List) -> list:
        """Implementation of to_triples_list functionality."""
        all_triples = []
        
        for graph_object in graph_object_list:
            triples = GraphObjectTriplesUtils.to_triples_impl(graph_object)
            all_triples.extend(triples)
        
        return all_triples
