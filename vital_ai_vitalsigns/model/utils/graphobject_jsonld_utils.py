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
    def _validate_single_object(data):
        """Validate that input is a single JSON-LD object, not a list or @graph document."""
        if isinstance(data, list):
            raise ValueError("Expected single JSON-LD object, got list. Use from_jsonld_list() instead.")
        if isinstance(data, dict) and "@graph" in data:
            raise ValueError("Expected single JSON-LD object, got @graph document. Use from_jsonld_list() instead.")
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data).__name__}")

    @staticmethod
    def _validate_document_or_list(data):
        """Validate that input is a dict or list for list operations."""
        if not isinstance(data, (dict, list)):
            raise ValueError(f"Expected dict or list, got {type(data).__name__}")

    @staticmethod
    def _normalize_identifier_to_jsonld(graph_object, jsonld_obj):
        """Convert VitalSigns URI to JSON-LD @id."""
        # Check if URI property exists in _properties
        if VitalConstants.uri_prop_uri not in graph_object._properties:
            raise ValueError("Cannot convert GraphObject to JSON-LD - missing URI property")
        
        try:
            # Use my_getattr to properly access URI property
            uri_value = graph_object.my_getattr('URI')
            if uri_value is not NotImplemented and uri_value is not None:
                # URI property should be a string, cast the CombinedProperty to string
                jsonld_obj['@id'] = str(uri_value)
            else:
                raise ValueError("Cannot convert GraphObject to JSON-LD - missing URI property")
        except (KeyError, AttributeError):
            # No URI property set - this is an error
            raise ValueError("Cannot convert GraphObject to JSON-LD - missing URI property")

    @staticmethod
    def _normalize_identifier_from_jsonld(jsonld_obj, graph_object):
        """Convert JSON-LD @id to VitalSigns URI property."""
        if '@id' in jsonld_obj:
            # Use my_getattr to properly set the URI property
            graph_object.URI = jsonld_obj['@id']
        else:
            raise ValueError("Cannot create GraphObject from JSON-LD - missing @id property")

    @staticmethod
    def _get_default_context():
        """Get default JSON-LD context with built-in and ontology-managed namespaces."""
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        
        # Start with built-in W3C namespaces (no aliases for @id/@type)
        context = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
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
    def _build_dynamic_context(graph_objects):
        """Build context dynamically based on URIs found in the data.
        
        Args:
            graph_objects: Single GraphObject or list of GraphObjects
            
        Returns:
            dict: Context with namespaces needed for the data
        """
        # Start with base JSON-LD context (no aliases for @id/@type)
        context = {}
        
        # Extract all URIs from the objects
        uris_found = set()
        objects_to_scan = [graph_objects] if not isinstance(graph_objects, list) else graph_objects
        
        for obj in objects_to_scan:
            # Scan object properties for URIs
            uris_found.update(GraphObjectJsonldUtils._extract_uris_from_object(obj))
        
        # Map URIs to known ontology prefixes using VitalSigns OntologyManager
        try:
            from vital_ai_vitalsigns.vitalsigns import VitalSigns
            vs = VitalSigns()
            ontology_manager = vs.get_ontology_manager()
            
            for uri in uris_found:
                namespace = GraphObjectJsonldUtils._get_namespace_from_uri(uri)
                if namespace:
                    prefix = GraphObjectJsonldUtils._get_prefix_for_namespace(ontology_manager, namespace)
                    if prefix:
                        context[prefix] = namespace
        except Exception as e:
            # Fallback to static context if dynamic fails
            return GraphObjectJsonldUtils._get_default_context()
        
        return context

    @staticmethod
    def _extract_uris_from_object(graph_object):
        """Extract all URIs from a GraphObject (types, properties, values)."""
        uris = set()
        
        # Add object URI using proper property access - URI is required
        if VitalConstants.uri_prop_uri not in graph_object._properties:
            raise ValueError("Cannot extract URIs from GraphObject - missing URI property")
        
        try:
            uri_value = graph_object.my_getattr('URI')
            if uri_value is not NotImplemented and uri_value is not None:
                uris.add(str(uri_value))
            else:
                raise ValueError("Cannot extract URIs from GraphObject - missing URI property")
        except (KeyError, AttributeError):
            raise ValueError("Cannot extract URIs from GraphObject - missing URI property")
        
        # Add type URIs using my_getattr method
        vitaltype = graph_object.my_getattr('vitaltype')
        if vitaltype is not NotImplemented and vitaltype is not None:
            uris.add(str(vitaltype))
        
        # Add property URIs by scanning _properties dictionary
        for property_uri in graph_object._properties.keys():
            uris.add(property_uri)
        
        return uris

    @staticmethod
    def _get_namespace_from_uri(uri):
        """Extract namespace from full URI."""
        if '#' in uri:
            return uri.rsplit('#', 1)[0] + '#'
        elif '/' in uri:
            return uri.rsplit('/', 1)[0] + '/'
        return None

    @staticmethod
    def _get_prefix_for_namespace(ontology_manager, namespace):
        """Get prefix for namespace from ontology manager."""
        try:
            ontology_list = ontology_manager.get_ontology_list()
            for ontology in ontology_list:
                if hasattr(ontology, 'ontology_iri') and hasattr(ontology, 'prefix'):
                    if ontology.ontology_iri == namespace:
                        return ontology.prefix
        except Exception:
            pass
        return None

    @staticmethod
    def to_jsonld_impl(graph_object) -> dict:
        """Convert single GraphObject to complete JSON-LD object with @context.
        
        Returns a single JSON-LD object (not a document with @graph).
        For multiple objects, use to_jsonld_list_impl().
        """
        from vital_ai_vitalsigns.model.utils.graphobject_rdf_utils import GraphObjectRdfUtils
        
        # Get RDF representation
        rdf_string = GraphObjectRdfUtils.to_rdf_impl(graph_object, format='turtle')
        
        # Parse RDF with rdflib
        g = Graph()
        g.parse(data=rdf_string, format='turtle')
        
        # Convert to JSON-LD without context first
        jsonld_string = g.serialize(format='json-ld')
        jsonld_data = json.loads(jsonld_string)
        
        # Extract single object from RDF serialization
        if isinstance(jsonld_data, list) and len(jsonld_data) == 1:
            jsonld_data = jsonld_data[0]
        elif isinstance(jsonld_data, list) and len(jsonld_data) == 0:
            raise ValueError("No JSON-LD data generated from GraphObject")
        elif isinstance(jsonld_data, list):
            raise ValueError("Multiple subjects found in JSON-LD output - expected single subject")
        
        # Ensure proper identifier normalization
        GraphObjectJsonldUtils._normalize_identifier_to_jsonld(graph_object, jsonld_data)
        
        # Add proper context with namespaces based on actual data
        context = GraphObjectJsonldUtils._build_dynamic_context(graph_object)
        
        # Create final JSON-LD object with context (NOT a document)
        jsonld_obj = {
            "@context": context,
            **jsonld_data  # Merge the object data
        }
        
        # Return without compaction to preserve @id and @type
        return jsonld_obj

    @staticmethod
    def from_jsonld_impl(cls, jsonld_data: dict, *, modified=False) -> G:
        """Convert single JSON-LD object to GraphObject.
        
        Args:
            jsonld_data: JSON-LD object (NOT document with @graph)
            cls: Class hint for object creation
            modified: Whether to mark object as modified
            
        Returns:
            GraphObject: Single VitalSigns object
            
        Raises:
            ValueError: If input is @graph document or list
        """
        from vital_ai_vitalsigns.model.utils.graphobject_rdf_utils import GraphObjectRdfUtils
        
        # Strict single object validation
        GraphObjectJsonldUtils._validate_single_object(jsonld_data)
        
        # Convert JSON-LD to RDF triples using PyLD
        try:
            # Handle empty dictionary case - cannot create GraphObject without type
            if not jsonld_data or (isinstance(jsonld_data, dict) and len(jsonld_data) == 0):
                raise ValueError("Cannot create GraphObject from empty JSON-LD - missing @type information")
            
            # Check for required @type information
            if isinstance(jsonld_data, dict) and '@type' not in jsonld_data:
                # Check if there's a type after context processing
                expanded_check = jsonld.expand(jsonld_data)
                if len(expanded_check) == 0 or not any('@type' in item for item in expanded_check if isinstance(item, dict)):
                    raise ValueError("Cannot create GraphObject from JSON-LD - missing @type information")
            
            # Expand the JSON-LD to normalize it
            expanded = jsonld.expand(jsonld_data)
            
            if len(expanded) == 0:
                raise ValueError("Cannot create GraphObject from JSON-LD - no valid data after expansion")
            elif len(expanded) > 1:
                raise ValueError("Multiple subjects found in expanded JSON-LD")
            
            # Convert to N-Quads format
            nquads = jsonld.to_rdf(jsonld_data, {'format': 'application/n-quads'})
            
            # Parse with rdflib and convert to turtle for consistency
            g = Graph()
            g.parse(data=nquads, format='nquads')
            rdf_string = g.serialize(format='nt')
            
            # Use existing RDF functionality to create GraphObject
            graph_object = GraphObjectRdfUtils.from_rdf_impl(cls, rdf_string, modified=modified)
            
            # Ensure proper identifier normalization from JSON-LD to VitalSigns
            GraphObjectJsonldUtils._normalize_identifier_from_jsonld(jsonld_data, graph_object)
            
            return graph_object
            
        except Exception as e:
            raise ValueError(f"Error processing JSON-LD: {str(e)}")

    @staticmethod
    def to_jsonld_list_impl(graph_object_list) -> dict:
        """Convert list of GraphObjects to complete JSON-LD document.
        
        Returns:
            dict: Complete JSON-LD document with @context and @graph
        """
        # Create a proper JSON-LD document with @graph structure
        context = GraphObjectJsonldUtils._build_dynamic_context(graph_object_list)
        
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
                # Ensure proper identifier normalization
                GraphObjectJsonldUtils._normalize_identifier_to_jsonld(graph_object, obj_data)
                objects_data.append(obj_data)
            elif isinstance(jsonld_data, dict):
                # Remove any @context from individual objects
                if "@context" in jsonld_data:
                    del jsonld_data["@context"]
                # Ensure proper identifier normalization
                GraphObjectJsonldUtils._normalize_identifier_to_jsonld(graph_object, jsonld_data)
                objects_data.append(jsonld_data)
        
        # Create the final JSON-LD document with shared context and @graph
        jsonld_doc = {
            "@context": context,
            "@graph": objects_data
        }
        
        # Return without compaction to preserve @id and @type
        return jsonld_doc

    @staticmethod
    def from_jsonld_list_impl(cls, jsonld_doc, *, modified=False) -> List[G]:
        """Convert JSON-LD document or list to list of GraphObjects.
        
        Args:
            jsonld_doc: JSON-LD document with @graph, or list of objects
            cls: Optional class hint for object creation
            modified: Whether to mark objects as modified
            
        Returns:
            List[GraphObject]: List of VitalSigns objects
            
        Handles:
            - {"@context": {...}, "@graph": [...]} documents
            - [...] lists of objects  
            - {...} single objects (returns list with one item)
        """
        # Validate input type
        GraphObjectJsonldUtils._validate_document_or_list(jsonld_doc)
        
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
            # Single JSON-LD object - convert to list with one item
            graph_object = GraphObjectJsonldUtils.from_jsonld_impl(cls, jsonld_doc, modified=modified)
            graph_object_list.append(graph_object)

        return graph_object_list