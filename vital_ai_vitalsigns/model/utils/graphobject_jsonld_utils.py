from __future__ import annotations

import json
from typing import TypeVar, List, Optional
from pyld import jsonld
from rdflib import Graph
from vital_ai_vitalsigns.model.vital_constants import VitalConstants

G = TypeVar('G', bound=Optional['GraphObject'])


class GraphObjectJsonldUtils:
    """Utility class containing JSON-LD related functionality for GraphObject."""

    @staticmethod
    def _get_default_context():
        """Get default JSON-LD context with built-in and ontology-managed namespaces."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        
        # Start with built-in W3C namespaces
        context = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            # Common JSON-LD properties
            "type": "@type",
            "id": "@id"
        }
        
        # Get ontology namespaces from the ontology manager
        try:
            vs = VitalSigns()
            ont_manager = vs.get_ontology_manager()
            
            # Get all loaded ontologies
            ontology_list = ont_manager.get_ontology_list()
            
            # Add ontology namespaces to context
            for ontology in ontology_list:
                if hasattr(ontology, 'prefix') and hasattr(ontology, 'ontology_iri'):
                    context[ontology.prefix] = ontology.ontology_iri
                
        except Exception as e:
            # Fallback: if ontology manager is not available, continue with built-ins only
            pass
        
        return context

    @staticmethod
    def to_jsonld_impl(graph_object) -> dict:
        """Implementation of to_jsonld functionality."""
        # Convert GraphObject to RDF, then RDF to JSON-LD with proper context
        from vital_ai_vitalsigns.model.utils.graphobject_rdf_utils import GraphObjectRdfUtils
        
        # Get RDF representation
        rdf_string = GraphObjectRdfUtils.to_rdf_impl(graph_object, format='turtle')
        
        # Parse RDF with rdflib
        g = Graph()
        g.parse(data=rdf_string, format='turtle')
        
        # Convert to JSON-LD without context first
        jsonld_string = g.serialize(format='json-ld')
        jsonld_data = json.loads(jsonld_string)
        
        # If it's a list with one item, extract the item
        if isinstance(jsonld_data, list) and len(jsonld_data) == 1:
            jsonld_data = jsonld_data[0]
        elif isinstance(jsonld_data, list) and len(jsonld_data) == 0:
            raise ValueError("No JSON-LD data generated from GraphObject")
        elif isinstance(jsonld_data, list):
            raise ValueError("Multiple subjects found in JSON-LD output - expected single subject")
        
        # Add proper context with common namespaces
        context = GraphObjectJsonldUtils._get_default_context()
        
        # Create final JSON-LD document with context
        jsonld_doc = {
            "@context": context,
            **jsonld_data  # Merge the object data
        }
        
        # Use PyLD to compact with the context for cleaner output
        try:
            compacted = jsonld.compact(jsonld_doc, context)
            return compacted
        except Exception as e:
            # If compaction fails, return with basic context
            return jsonld_doc

    @staticmethod
    def from_jsonld_impl(cls, jsonld_data: dict, *, modified=False) -> G:
        """Implementation of from_jsonld functionality."""
        from vital_ai_vitalsigns.model.utils.graphobject_rdf_utils import GraphObjectRdfUtils
        
        # Ensure we have a single subject
        if isinstance(jsonld_data, list):
            if len(jsonld_data) == 0:
                raise ValueError("Empty JSON-LD list provided")
            elif len(jsonld_data) > 1:
                raise ValueError("Multiple subjects found in JSON-LD - expected single subject")
            jsonld_data = jsonld_data[0]
        
        # Convert JSON-LD to RDF triples using PyLD
        try:
            # Expand the JSON-LD to normalize it
            expanded = jsonld.expand(jsonld_data)
            
            if len(expanded) == 0:
                raise ValueError("No expanded JSON-LD data")
            elif len(expanded) > 1:
                raise ValueError("Multiple subjects found in expanded JSON-LD")
            
            # Convert to N-Quads format
            nquads = jsonld.to_rdf(jsonld_data, {'format': 'application/n-quads'})
            
            # Parse with rdflib and convert to turtle for consistency
            g = Graph()
            g.parse(data=nquads, format='nquads')
            rdf_string = g.serialize(format='nt')
            
            # Use existing RDF functionality to create GraphObject
            return GraphObjectRdfUtils.from_rdf_impl(cls, rdf_string, modified=modified)
            
        except Exception as e:
            raise ValueError(f"Error processing JSON-LD: {str(e)}")

    @staticmethod
    def to_jsonld_list_impl(graph_object_list) -> dict:
        """Implementation of to_jsonld_list functionality."""
        # Create a proper JSON-LD document with @graph structure
        context = GraphObjectJsonldUtils._get_default_context()
        
        # Convert each GraphObject to its data (without individual contexts)
        objects_data = []
        
        for graph_object in graph_object_list:
            # Get RDF representation
            from vital_ai_vitalsigns.model.utils.graphobject_rdf_utils import GraphObjectRdfUtils
            rdf_string = GraphObjectRdfUtils.to_rdf_impl(graph_object, format='turtle')
            
            # Parse RDF with rdflib
            g = Graph()
            g.parse(data=rdf_string, format='turtle')
            
            # Convert to JSON-LD without context
            jsonld_string = g.serialize(format='json-ld')
            jsonld_data = json.loads(jsonld_string)
            
            # Extract the object data (without @context)
            if isinstance(jsonld_data, list) and len(jsonld_data) == 1:
                obj_data = jsonld_data[0]
                # Remove any @context from individual objects
                if "@context" in obj_data:
                    del obj_data["@context"]
                objects_data.append(obj_data)
            elif isinstance(jsonld_data, dict):
                # Remove any @context from individual objects
                if "@context" in jsonld_data:
                    del jsonld_data["@context"]
                objects_data.append(jsonld_data)
        
        # Create the final JSON-LD document with shared context and @graph
        jsonld_doc = {
            "@context": context,
            "@graph": objects_data
        }
        
        # Use PyLD to compact for cleaner output
        try:
            compacted = jsonld.compact(jsonld_doc, context)
            return compacted
        except Exception as e:
            # If compaction fails, return with basic structure
            return jsonld_doc

    @staticmethod
    def from_jsonld_list_impl(cls, jsonld_doc, *, modified=False) -> List[G]:
        """Implementation of from_jsonld_list functionality."""
        graph_object_list = []

        # Handle both list of objects and @graph document structure
        if isinstance(jsonld_doc, list):
            # List of individual JSON-LD objects
            for jsonld_data in jsonld_doc:
                graph_object = GraphObjectJsonldUtils.from_jsonld_impl(cls, jsonld_data, modified=modified)
                graph_object_list.append(graph_object)
        elif isinstance(jsonld_doc, dict) and "@graph" in jsonld_doc:
            # JSON-LD document with @graph structure
            context = jsonld_doc.get("@context", {})
            graph_items = jsonld_doc["@graph"]
            
            for item in graph_items:
                # Add context to each item if it doesn't have one
                if "@context" not in item and context:
                    item_with_context = {
                        "@context": context,
                        **item
                    }
                else:
                    item_with_context = item
                
                graph_object = GraphObjectJsonldUtils.from_jsonld_impl(cls, item_with_context, modified=modified)
                graph_object_list.append(graph_object)
        else:
            # Single JSON-LD object
            graph_object = GraphObjectJsonldUtils.from_jsonld_impl(cls, jsonld_doc, modified=modified)
            graph_object_list.append(graph_object)

        return graph_object_list