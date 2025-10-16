import json
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from rdflib import XSD, OWL
from owlready2 import ObjectPropertyClass, default_world
from vital_ai_vitalsigns_generate.vitalsigns_ontology_generator import VitalSignsOntologyGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalSignsJSONSchemaGenerator(VitalSignsOntologyGenerator):
    """
    Generator for JSON Schema files from VitalSigns ontologies.
    
    This generator creates self-contained JSON Schema files that include
    all properties from the inheritance chain, optimized for TypeScript
    code generation.
    """
    
    def __init__(self):
        super().__init__()
        self.vitalsigns = VitalSigns()
        self.ontology_manager = self.vitalsigns.get_ontology_manager()
    
    def generate_json_schema_for_ontology(self, ontology_uri: str, output_directory: str) -> str:
        """
        Generate JSON Schema file for a specific ontology URI.
        
        Args:
            ontology_uri (str): The URI of the ontology to generate schema for 
                               (e.g., "http://vital.ai/ontology/vital-core#")
            output_directory (str): Directory path where the schema file will be written
            
        Returns:
            str: Path to the generated schema file
            
        Raises:
            ValueError: If ontology_uri is not found in loaded ontologies
            IOError: If output_directory is not writable
        """
        
        logging.info(f"Generating JSON schema for ontology: {ontology_uri}")
        
        # Get all loaded ontologies
        all_ontology_iris = self.ontology_manager.get_ontology_iri_list()
        all_ontologies = []
        for iri in all_ontology_iris:
            try:
                vs_ont = self.ontology_manager.get_vitalsigns_ontology(iri)
                all_ontologies.append(vs_ont)
            except Exception as e:
                logging.warning(f"Could not load ontology {iri}: {e}")
        
        # Generate metadata
        metadata = self.generate_metadata(ontology_uri, all_ontologies)
        
        # Generate class schemas for this ontology
        class_schemas = self.generate_class_schemas_for_ontology(ontology_uri)
        
        # Add ALL classes from parent ontologies to make schema completely self-contained
        parent_classes = self.get_all_parent_ontology_classes(ontology_uri)
        for parent_class_uri, parent_class_schema in parent_classes.items():
            class_name = parent_class_uri.split('#')[-1]
            if class_name not in class_schemas:
                class_schemas[class_name] = parent_class_schema
                logging.debug(f"Added parent ontology class: {class_name}")
        
        logging.info(f"Added {len(parent_classes)} classes from parent ontologies")
        
        # Build complete schema
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"VitalSigns {metadata['name']} Domain Schema",
            **metadata,
            "$defs": class_schemas
        }
        
        # Write to file
        schema_filename = f"{metadata['name']}-schema.json"
        output_path = os.path.join(output_directory, schema_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Generated self-contained JSON schema: {output_path}")
        logging.info(f"Total classes in schema: {len(class_schemas)} (includes external references)")
        return output_path
    
    def generate_json_instances_for_ontology(self, ontology_uri: str, output_directory: str) -> str:
        """
        Generate JSONL file containing JSON instances from OWL individuals.
        
        Args:
            ontology_uri (str): The URI of the ontology to extract individuals from
            output_directory (str): Directory path where the JSONL file will be written
            
        Returns:
            str: Path to the generated JSONL file
            
        Raises:
            ValueError: If ontology_uri is not found in loaded ontologies
            IOError: If output_directory is not writable
        """
        
        logging.info(f"Generating JSON instances for ontology: {ontology_uri}")
        
        # Get all loaded ontologies
        all_ontology_iris = self.ontology_manager.get_ontology_iri_list()
        all_ontologies = []
        for iri in all_ontology_iris:
            try:
                vs_ont = self.ontology_manager.get_vitalsigns_ontology(iri)
                all_ontologies.append(vs_ont)
            except Exception as e:
                logging.warning(f"Could not load ontology {iri}: {e}")
        
        # Generate metadata for file naming
        metadata = self.generate_metadata(ontology_uri, all_ontologies)
        
        # Extract all individuals from ontology and its imports
        all_individuals = self.extract_individuals_from_ontology(ontology_uri)
        
        logging.info(f"Found {len(all_individuals)} individuals to process")
        
        # Convert individuals to JSON instances
        json_instances = []
        for individual in all_individuals:
            try:
                json_instance = self.convert_individual_to_json(individual)
                json_instances.append(json_instance)
                logging.debug(f"Converted individual: {json_instance.get('@id', 'Unknown')}")
            except Exception as e:
                logging.error(f"Error converting individual to JSON: {e}")
        
        # Write JSONL file
        instances_filename = f"{metadata['name']}-instances.jsonl"
        output_path = os.path.join(output_directory, instances_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for instance in json_instances:
                json.dump(instance, f, ensure_ascii=False)
                f.write('\n')
        
        logging.info(f"Generated JSON instances file: {output_path}")
        logging.info(f"Total instances written: {len(json_instances)}")
        return output_path
    
    def generate_metadata(self, ontology_uri: str, all_ontologies: List) -> Dict[str, Any]:
        """Generate metadata for the JSON schema."""
        
        # Find the specific ontology
        target_ontology = None
        target_iri = ontology_uri.rstrip('#')
        
        for ontology in all_ontologies:
            ontology_iri = ontology.get_ontology_iri()
            # Try exact match and also with/without trailing #
            if (ontology_iri == target_iri or 
                ontology_iri == ontology_uri or
                ontology_iri.rstrip('#') == target_iri):
                target_ontology = ontology
                break
        
        if not target_ontology:
            available_iris = [ont.get_ontology_iri() for ont in all_ontologies]
            raise ValueError(f"Ontology {ontology_uri} not found in loaded ontologies. Available: {available_iris}")
        
        # Extract version from path or URI
        ontology_path = target_ontology.get_ontology_path()
        version = self.extract_version(ontology_path, ontology_uri)
        
        # Generate domain name from URI
        domain_name = self.extract_domain_name(ontology_uri, version)
        
        # Calculate OWL file hash
        owl_hash = self.calculate_owl_hash(ontology_path)
        
        # Get parent ontologies (imports)
        parents = self.get_parent_ontologies(ontology_uri)
        
        # Get VitalSigns version
        vitalsigns_version = "0.2.304"  # TODO: Get from config
        
        # Generate TypeScript namespace
        namespace = self.generate_typescript_namespace(domain_name)
        
        return {
            "domainURI": ontology_uri.rstrip('#'),
            "name": domain_name,
            "version": version,
            "domainOWLHash": owl_hash,
            "vitalsignsVersion": vitalsigns_version,
            "parents": parents,
            "typeScriptConfig": {
                "namespace": namespace,
                "exportFormat": "interface",
                "dateTimeFormat": "iso8601",
                "generateUnionTypes": True,
                "unionTypeStrategy": "branded-strings",
                "cardinalityValidation": True
            }
        }
    
    def extract_version(self, ontology_path: str, ontology_uri: str) -> str:
        """Extract version from ontology path or URI."""
        
        # Try to extract from filename (e.g., vital-core-0.2.304.owl)
        path = Path(ontology_path)
        filename = path.stem
        
        version_match = re.search(r'-(\d+\.\d+\.\d+)', filename)
        if version_match:
            return version_match.group(1)
        
        # Try to extract from URI
        version_match = re.search(r'(\d+\.\d+\.\d+)', ontology_uri)
        if version_match:
            return version_match.group(1)
        
        # Default version
        return "1.0.0"
    
    def extract_domain_name(self, ontology_uri: str, version: str) -> str:
        """Extract domain name from URI and version."""
        
        # Extract the last part of the URI
        uri_clean = ontology_uri.rstrip('#/')
        domain_part = uri_clean.split('/')[-1]
        
        return f"{domain_part}-{version}"
    
    def calculate_owl_hash(self, ontology_path: str) -> str:
        """Calculate MD5 hash of the OWL file."""
        
        try:
            with open(ontology_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logging.warning(f"Could not calculate hash for {ontology_path}: {e}")
            return "unknown"
    
    def get_parent_ontologies(self, ontology_uri: str) -> List[str]:
        """Get parent ontology URIs (imports)."""
        
        try:
            # Use simplified approach based on known relationships
            if 'haley-ai-kg' in ontology_uri:
                return ['http://vital.ai/ontology/haley-ai-question#']
            elif 'haley-ai-question' in ontology_uri:
                return ['http://vital.ai/ontology/haley#']
            elif 'haley' in ontology_uri and 'haley-ai' not in ontology_uri:
                return ['http://vital.ai/ontology/vital-core#']
            else:
                return []
                
        except Exception as e:
            logging.warning(f"Could not determine parent ontologies for {ontology_uri}: {e}")
            return []
    
    def generate_typescript_namespace(self, domain_name: str) -> str:
        """Generate TypeScript namespace from domain name."""
        
        # Convert domain-name-1.0.0 to DomainName100
        parts = domain_name.replace('-', ' ').replace('.', '').split()
        namespace = ''.join(word.capitalize() for word in parts if word)
        return namespace
    
    def generate_filename(self, metadata: Dict[str, Any]) -> str:
        """Generate filename for the schema file."""
        
        name = metadata.get("name", "unknown")
        # Sanitize filename
        safe_name = re.sub(r'[^\w\-.]', '-', name)
        return f"{safe_name}-schema.json"
    
    def generate_json_schema(self, vitalsigns_ontology, ontology_uri: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the complete JSON schema."""
        
        # Base schema structure
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"VitalSigns {metadata['name']} Domain Schema",
            "domainURI": metadata["domainURI"],
            "name": metadata["name"],
            "version": metadata["version"],
            "domainOWLHash": metadata["domainOWLHash"],
            "vitalsignsVersion": metadata["vitalsignsVersion"],
            "parents": metadata["parents"],
            "typeScriptConfig": {
                "namespace": self.generate_typescript_namespace(metadata["name"]),
                "exportFormat": "interface",
                "dateTimeFormat": "iso8601",
                "generateUnionTypes": True,
                "unionTypeStrategy": "branded-strings",
                "cardinalityValidation": True,
                "phase2Features": True
            },
            "$defs": {}
        }
        
        # Generate class schemas
        class_schemas = self.generate_class_schemas_for_ontology(ontology_uri)
        schema["$defs"].update(class_schemas)
        
        return schema
    
    def generate_typescript_namespace(self, domain_name: str) -> str:
        """Generate TypeScript namespace from domain name."""
        
        # Convert to PascalCase
        parts = re.split(r'[-_.]', domain_name)
        namespace = ''.join(word.capitalize() for word in parts if word)
        return namespace
    
    def generate_class_schemas_for_ontology(self, ontology_uri: str) -> Dict[str, Any]:
        """Generate JSON schemas for all classes in the ontology."""
        
        class_schemas = {}
        
        # Get all loaded ontologies for property resolution
        all_ontologies = []
        loaded_iris = self.ontology_manager.get_ontology_iri_list()
        
        for iri in loaded_iris:
            try:
                vs_ont = self.ontology_manager.get_vitalsigns_ontology(iri)
                all_ontologies.append(vs_ont)
            except Exception as e:
                logging.warning(f"Could not load ontology {iri}: {e}")
        
        # Get registry for class information
        registry = self.vitalsigns.get_registry()
        
        # Find classes that belong to this ontology
        target_classes = []
        ontology_base = ontology_uri.rstrip('#')
        
        logging.debug(f"Looking for classes matching ontology base: {ontology_base}")
        logging.debug(f"Total classes in registry: {len(registry.vitalsigns_classes)}")
        
        for class_uri, class_type in registry.vitalsigns_classes.items():
            if class_uri.startswith(ontology_base):
                target_classes.append((class_uri, class_type))
                logging.debug(f"Found matching class: {class_uri}")
        
        logging.info(f"Found {len(target_classes)} classes for ontology {ontology_uri}")
        
        # If no classes found, show some sample class URIs for debugging
        if len(target_classes) == 0:
            sample_uris = list(registry.vitalsigns_classes.keys())[:5]
            logging.warning(f"No classes found for {ontology_uri}. Sample class URIs: {sample_uris}")
        
        # Sort classes by dependency order (base classes first)
        sorted_classes = self.sort_classes_by_dependency(target_classes, ontology_uri)
        
        # Generate schema for each class
        for class_uri, class_type in sorted_classes:
            try:
                class_name = class_uri.split('#')[-1]
                class_schema = self.generate_class_schema(class_uri, class_type, all_ontologies)
                class_schemas[class_name] = class_schema
                logging.debug(f"Generated schema for class: {class_name}")
            except Exception as e:
                logging.error(f"Error generating schema for class {class_uri}: {e}")
        
        return class_schemas
    
    def sort_classes_by_dependency(self, target_classes: List[tuple], ontology_uri: str) -> List[tuple]:
        """Sort classes so that base classes are processed before derived classes."""
        
        # Create a map of class URI to class tuple
        class_map = {class_uri: (class_uri, class_type) for class_uri, class_type in target_classes}
        
        # Track processed classes
        processed = set()
        result = []
        
        def process_class(class_uri, class_type):
            if class_uri in processed:
                return
            
            # Find immediate parent within this ontology
            parent_uri = self.find_immediate_parent_in_ontology(class_type, ontology_uri, class_map)
            
            # If parent exists in this ontology, process it first
            if parent_uri and parent_uri in class_map:
                parent_class_uri, parent_class_type = class_map[parent_uri]
                process_class(parent_class_uri, parent_class_type)
            
            # Now process this class
            result.append((class_uri, class_type))
            processed.add(class_uri)
        
        # Process all classes
        for class_uri, class_type in target_classes:
            process_class(class_uri, class_type)
        
        logging.debug(f"Sorted {len(target_classes)} classes by dependency")
        return result
    
    def find_immediate_parent_in_ontology(self, class_type: type, ontology_uri: str, class_map: Dict) -> str:
        """Find the immediate parent class that exists in the same ontology."""
        
        registry = self.vitalsigns.get_registry()
        
        # Look through MRO for immediate parent
        for parent_class in class_type.__mro__[1:]:
            # Find URI for this parent class
            for uri, reg_cls in registry.vitalsigns_classes.items():
                if reg_cls == parent_class:
                    # Check if this parent is in the same ontology
                    if uri.startswith(ontology_uri.rstrip('#')):
                        return uri
                    # If not in same ontology, this is the boundary - stop here
                    else:
                        return None
        
        return class_schemas
    
    def get_all_parent_ontology_classes(self, ontology_uri: str) -> Dict[str, Any]:
        """Get all classes from all parent ontologies and ALL loaded ontologies (complete inclusion)."""
        
        all_parent_classes = {}
        registry = self.vitalsigns.get_registry()
        processed_ontologies = set()
        
        # Get parent ontology URIs from import hierarchy
        parent_ontology_uris = self.get_parent_ontology_uris_recursive(ontology_uri)
        
        # Get ALL loaded ontologies to ensure complete coverage (like FileNode from vital domain)
        all_loaded_ontologies = self.ontology_manager.get_ontology_iri_list()
        
        # Combine parent ontologies with all loaded ontologies
        all_ontology_uris = parent_ontology_uris + [uri for uri in all_loaded_ontologies if uri not in parent_ontology_uris]
        
        logging.info(f"Including all classes from complete ontology set: {all_ontology_uris}")
        
        # Generate schemas for all classes in all ontologies
        for ont_uri in all_ontology_uris:
            ont_base = ont_uri.rstrip('#')
            if ont_base not in processed_ontologies:
                parent_classes_count = 0
                
                for class_uri, class_type in registry.vitalsigns_classes.items():
                    if class_uri.startswith(ont_base):
                        try:
                            class_schema = self.generate_class_schema(class_uri, class_type, [])
                            all_parent_classes[class_uri] = class_schema
                            parent_classes_count += 1
                        except Exception as e:
                            logging.error(f"Error generating schema for class {class_uri}: {e}")
                
                processed_ontologies.add(ont_base)
                logging.info(f"Added {parent_classes_count} classes from {ont_uri}")
        
        return all_parent_classes
    
    def get_parent_ontology_uris_recursive(self, ontology_uri: str) -> List[str]:
        """Get all parent ontology URIs recursively (including parents of parents)."""
        
        all_parents = set()
        to_process = [ontology_uri]
        processed = set()
        
        while to_process:
            current_uri = to_process.pop(0)
            if current_uri in processed:
                continue
            
            processed.add(current_uri)
            direct_parents = self.get_parent_ontologies(current_uri)
            
            for parent_uri in direct_parents:
                if parent_uri not in all_parents:
                    all_parents.add(parent_uri)
                    to_process.append(parent_uri)
        
        return list(all_parents)
    
    def generate_class_schema(self, class_uri: str, class_type: type, all_ontologies: List) -> Dict[str, Any]:
        """Generate JSON schema for a single class with proper inheritance using allOf."""
        
        # Determine inheritance strategy
        base_classes = self.get_base_classes(class_type)
        own_properties = self.get_own_properties(class_uri, class_type)
        
        # Extract cardinality constraints for this class
        cardinality_map = self.extract_cardinality_constraints(class_uri)
        
        class_name = class_uri.split('#')[-1]
        
        # If this class has base classes, use allOf inheritance
        if base_classes:
            return self.generate_inheritance_schema(class_uri, class_name, base_classes, own_properties, cardinality_map)
        else:
            # This is a base class, generate full schema
            return self.generate_full_class_schema(class_uri, class_name, own_properties, cardinality_map)
    
    def get_referenced_external_classes(self, class_schemas: Dict[str, Any], ontology_uri: str) -> Dict[str, Any]:
        """Find and generate schemas for external classes referenced by this ontology."""
        
        referenced_classes = {}
        registry = self.vitalsigns.get_registry()
        processed_classes = set()
        
        def collect_and_generate_refs(schemas_to_check: Dict[str, Any]):
            """Recursively collect and generate external references."""
            external_refs = set()
            
            def collect_refs(obj):
                if isinstance(obj, dict):
                    if '$ref' in obj:
                        ref_path = obj['$ref']
                        if ref_path.startswith('#/$defs/'):
                            class_name = ref_path.split('/')[-1]
                            # Check if this class is not in our current schema and not already processed
                            if (class_name not in class_schemas and 
                                class_name not in referenced_classes and
                                class_name not in processed_classes):
                                external_refs.add(class_name)
                    for value in obj.values():
                        collect_refs(value)
                elif isinstance(obj, list):
                    for item in obj:
                        collect_refs(item)
            
            collect_refs(schemas_to_check)
            
            # Generate schemas for external classes
            new_external_schemas = {}
            for class_name in external_refs:
                # Find the full URI for this class
                for class_uri, class_type in registry.vitalsigns_classes.items():
                    if class_uri.split('#')[-1] == class_name:
                        # Only include if it's from a different ontology
                        if not class_uri.startswith(ontology_uri.rstrip('#')):
                            try:
                                class_schema = self.generate_class_schema(class_uri, class_type, [])
                                new_external_schemas[class_name] = class_schema
                                referenced_classes[class_uri] = class_schema
                                processed_classes.add(class_name)
                                logging.debug(f"Generated schema for external class: {class_name}")
                            except Exception as e:
                                logging.error(f"Error generating schema for external class {class_name}: {e}")
                        break
            
            # If we found new external classes, check if they reference other external classes
            if new_external_schemas:
                collect_and_generate_refs(new_external_schemas)
        
        # Start the recursive collection
        collect_and_generate_refs(class_schemas)
        
        logging.info(f"Added {len(referenced_classes)} external classes to make schema self-contained")
        return referenced_classes
    
    def extract_individuals_from_ontology(self, ontology_uri: str) -> List:
        """Extract all individuals from ontology and ALL its imports (complete hierarchy)."""
        
        all_individuals = []
        processed_ontologies = set()
        
        # Get ALL ontology URIs in the import hierarchy
        all_ontology_uris = [ontology_uri]
        parent_ontology_uris = self.get_parent_ontology_uris_recursive(ontology_uri)
        all_ontology_uris.extend(parent_ontology_uris)
        
        logging.info(f"Processing individuals from complete import hierarchy: {all_ontology_uris}")
        
        # Get individuals from ALL ontologies in the hierarchy
        for ont_uri in all_ontology_uris:
            if ont_uri not in processed_ontologies:
                individuals = self.get_ontology_individuals(ont_uri)
                all_individuals.extend(individuals)
                processed_ontologies.add(ont_uri)
                logging.info(f"Added {len(individuals)} individuals from {ont_uri}")
        
        # Also get individuals from ALL loaded ontologies to ensure complete coverage
        all_loaded_ontologies = self.ontology_manager.get_ontology_iri_list()
        for loaded_uri in all_loaded_ontologies:
            if loaded_uri not in processed_ontologies:
                individuals = self.get_ontology_individuals(loaded_uri)
                if len(individuals) > 0:
                    all_individuals.extend(individuals)
                    processed_ontologies.add(loaded_uri)
                    logging.info(f"Added {len(individuals)} additional individuals from {loaded_uri}")
        
        logging.info(f"Total individuals collected from complete hierarchy: {len(all_individuals)}")
        return all_individuals
    
    def get_ontology_individuals(self, ontology_uri: str) -> List:
        """Get all individuals defined in a specific ontology."""
        
        individuals = []
        ontology_base = ontology_uri.rstrip('#')
        
        try:
            # Try to get the VitalSigns ontology - handle both with and without trailing #
            vs_ontology = None
            for uri_variant in [ontology_base, ontology_uri, ontology_base + '#']:
                try:
                    vs_ontology = self.ontology_manager.get_vitalsigns_ontology(uri_variant)
                    break
                except:
                    continue
            
            if vs_ontology is None:
                logging.warning(f"Could not find VitalSigns ontology for {ontology_uri}")
                return individuals
            
            ontology_path = vs_ontology.get_ontology_path()
            logging.debug(f"Loading ontology from path: {ontology_path}")
            
            # Load the ontology using owlready2 to access individuals
            from owlready2 import get_ontology
            owl_ontology = get_ontology(f"file://{ontology_path}").load()
            
            # Extract individuals from this ontology
            for individual in owl_ontology.individuals():
                # Check if individual belongs to this ontology (not imported)
                individual_iri = str(individual.iri)
                if individual_iri.startswith(ontology_base):
                    individuals.append(individual)
                    logging.debug(f"Found individual: {individual.iri}")
            
            logging.info(f"Found {len(individuals)} individuals in {ontology_uri}")
            
        except Exception as e:
            logging.error(f"Error extracting individuals from {ontology_uri}: {e}")
            import traceback
            logging.debug(f"Full traceback: {traceback.format_exc()}")
        
        return individuals
    
    def convert_individual_to_json(self, individual) -> Dict[str, Any]:
        """Convert OWL individual to JSON instance."""
        
        # Start with basic structure
        json_instance = {
            "@id": str(individual.iri)
        }
        
        # Get the class type(s)
        if hasattr(individual, 'is_a') and individual.is_a:
            # Use the first class as the primary type
            primary_class = individual.is_a[0]
            if hasattr(primary_class, 'iri'):
                json_instance["@type"] = str(primary_class.iri)
            else:
                json_instance["@type"] = str(primary_class)
        
        # Extract all properties
        try:
            # Get all properties for this individual
            for prop in individual.get_properties():
                prop_uri = str(prop.iri)
                values = getattr(individual, prop.python_name, None)
                
                if values is not None:
                    if isinstance(values, list):
                        if len(values) == 1:
                            json_instance[prop_uri] = self.convert_owl_value_to_json(values[0])
                        elif len(values) > 1:
                            json_instance[prop_uri] = [self.convert_owl_value_to_json(v) for v in values]
                    else:
                        json_instance[prop_uri] = self.convert_owl_value_to_json(values)
        
        except Exception as e:
            logging.debug(f"Error extracting properties for individual {individual.iri}: {e}")
            # Try alternative approach - iterate through individual's attributes
            try:
                for attr_name in dir(individual):
                    if not attr_name.startswith('_') and attr_name not in ['is_a', 'iri', 'name']:
                        attr_value = getattr(individual, attr_name)
                        if attr_value is not None and not callable(attr_value):
                            # Try to find the property URI
                            prop_uri = f"http://vital.ai/ontology/{attr_name}"  # Fallback URI
                            json_instance[prop_uri] = self.convert_owl_value_to_json(attr_value)
            except Exception as e2:
                logging.debug(f"Alternative property extraction also failed: {e2}")
        
        return json_instance
    
    def convert_owl_value_to_json(self, owl_value):
        """Convert OWL property value to JSON-compatible type."""
        
        if owl_value is None:
            return None
        elif isinstance(owl_value, str):
            return owl_value
        elif isinstance(owl_value, (int, float)):
            return owl_value
        elif isinstance(owl_value, bool):
            return owl_value
        elif hasattr(owl_value, 'iri'):  # Object property reference
            return str(owl_value.iri)
        elif hasattr(owl_value, '__iter__') and not isinstance(owl_value, str):
            # Handle collections
            return [self.convert_owl_value_to_json(item) for item in owl_value]
        else:
            # Fallback to string representation
            return str(owl_value)
    
    def get_base_classes(self, class_type: type) -> List[str]:
        """Get immediate parent class URI for proper inheritance hierarchy."""
        
        registry = self.vitalsigns.get_registry()
        
        # Look for the immediate parent class in the MRO
        for base_class in class_type.__mro__[1:]:  # Skip self
            # Find the URI for this base class
            for uri, cls in registry.vitalsigns_classes.items():
                if cls == base_class:
                    logging.debug(f"Found immediate parent class: {uri} for {class_type}")
                    return [uri]  # Return only the immediate parent
        
        return []
    
    def get_own_properties(self, class_uri: str, class_type: type) -> List[Dict[str, Any]]:
        """Get properties that belong specifically to this class (not inherited)."""
        
        try:
            # Get all properties for this class
            all_properties = self.ontology_manager.get_domain_property_list(class_type)
            
            # Get parent class properties to filter out inherited ones
            parent_classes = self.get_base_classes(class_type)
            inherited_properties = set()
            
            if parent_classes:
                registry = self.vitalsigns.get_registry()
                for parent_uri in parent_classes:
                    parent_class = registry.vitalsigns_classes.get(parent_uri)
                    if parent_class:
                        parent_properties = self.ontology_manager.get_domain_property_list(parent_class)
                        for prop in parent_properties:
                            inherited_properties.add(prop.get('uri'))
            
            # Filter out inherited properties
            own_properties = []
            for prop in all_properties:
                prop_uri = prop.get('uri')
                if prop_uri not in inherited_properties:
                    own_properties.append(prop)
            
            logging.debug(f"Class {class_uri}: {len(all_properties)} total, {len(own_properties)} own properties")
            return own_properties
            
        except Exception as e:
            logging.error(f"Error getting own properties for {class_uri}: {e}")
            return []
    
    def generate_inheritance_schema(self, class_uri: str, class_name: str, base_classes: List[str], 
                                  own_properties: List[Dict[str, Any]], cardinality_map: Dict) -> Dict[str, Any]:
        """Generate schema using allOf inheritance pattern with immediate parent."""
        
        # Build allOf array starting with immediate parent reference
        all_of = []
        
        # Add reference to immediate parent class (should be only one)
        if base_classes:
            parent_uri = base_classes[0]  # Only immediate parent
            parent_name = parent_uri.split('#')[-1]
            all_of.append({"$ref": f"#/$defs/{parent_name}"})
            logging.debug(f"Class {class_name} inherits from {parent_name}")
        
        # Add own properties if any
        if own_properties:
            own_property_schemas = {}
            required_properties = []
            
            for prop_info in own_properties:
                prop_uri = prop_info["uri"]
                prop_class = prop_info["prop_class"]
                
                cardinality = cardinality_map.get(prop_uri, {})
                union_types = self.detect_union_types(prop_uri)
                
                prop_schema = self.generate_enhanced_property_schema(
                    prop_uri, prop_class, cardinality, union_types
                )
                own_property_schemas[prop_uri] = prop_schema
                
                if self.is_property_required(cardinality):
                    required_properties.append(prop_uri)
            
            if own_property_schemas:
                own_schema = {
                    "type": "object",
                    "properties": own_property_schemas,
                    "additionalProperties": False
                }
                
                if required_properties:
                    own_schema["required"] = required_properties
                
                all_of.append(own_schema)
                logging.debug(f"Class {class_name} has {len(own_property_schemas)} own properties")
        
        return {
            "title": class_name,
            "description": f"VitalSigns class: {class_uri}",
            "classURI": class_uri,
            "allOf": all_of
        }
    
    def generate_full_class_schema(self, class_uri: str, class_name: str, 
                                 properties: List[Dict[str, Any]], cardinality_map: Dict) -> Dict[str, Any]:
        """Generate full schema for base classes."""
        
        property_schemas = {}
        required_properties = []
        
        for prop_info in properties:
            prop_uri = prop_info["uri"]
            prop_class = prop_info["prop_class"]
            
            cardinality = cardinality_map.get(prop_uri, {})
            union_types = self.detect_union_types(prop_uri)
            
            prop_schema = self.generate_enhanced_property_schema(
                prop_uri, prop_class, cardinality, union_types
            )
            property_schemas[prop_uri] = prop_schema
            
            if self.is_property_required(cardinality):
                required_properties.append(prop_uri)
        
        class_schema = {
            "type": "object",
            "title": class_name,
            "description": f"VitalSigns class: {class_uri}",
            "classURI": class_uri,
            "properties": property_schemas,
            "additionalProperties": False
        }
        
        if required_properties:
            class_schema["required"] = required_properties
        
        return class_schema
    
    def is_base_class_property(self, prop_uri: str, base_classes: List[str]) -> bool:
        """Check if a property belongs to a base class."""
        
        # Simple heuristic: if property is from vital-core, it's likely a base property
        return 'vital-core#' in prop_uri
    
    def get_class_properties(self, class_uri: str) -> List[Dict[str, Any]]:
        """Get all properties for a class, including inherited ones."""
        
        try:
            # Get the class from registry
            registry = self.vitalsigns.get_registry()
            class_type = registry.vitalsigns_classes.get(class_uri)
            
            if not class_type:
                logging.warning(f"Class not found in registry: {class_uri}")
                return []
            
            logging.debug(f"Getting properties for class: {class_uri}")
            
            # Try the standard method first
            properties = self.ontology_manager.get_domain_property_list(class_type)
            
            # If we get no properties or very few, use comprehensive inheritance resolution
            if len(properties) == 0 or (len(properties) < 5 and ("Edge_" in class_uri or "VITAL_" in class_uri)):
                logging.debug(f"Using comprehensive inheritance resolution for {class_uri} (found {len(properties)} properties)")
                properties = self.get_comprehensive_inherited_properties(class_type)
            
            logging.debug(f"Final property count for {class_uri}: {len(properties)}")
            return properties
            
        except Exception as e:
            logging.error(f"Error getting properties for class {class_uri}: {e}")
            return []
    
    def get_comprehensive_inherited_properties(self, class_type: type) -> List[Dict[str, Any]]:
        """Comprehensively resolve inherited properties by walking the class hierarchy and registry."""
        
        all_properties = []
        registry = self.vitalsigns.get_registry()
        
        try:
            # Method 1: Walk up the class hierarchy (MRO - Method Resolution Order)
            for base_class in class_type.__mro__:
                if hasattr(base_class, '__module__') and 'vital' in base_class.__module__.lower():
                    logging.debug(f"Checking MRO base class: {base_class.__name__}")
                    
                    # Try to get properties for this base class
                    base_properties = self.ontology_manager.get_domain_property_list(base_class)
                    
                    if base_properties:
                        logging.debug(f"Found {len(base_properties)} properties in MRO class {base_class.__name__}")
                        all_properties.extend(base_properties)
            
            # Method 2: Check registry for base class URIs and get their properties
            for uri, cls in registry.vitalsigns_classes.items():
                if cls in class_type.__mro__ and cls != class_type:
                    logging.debug(f"Checking registry base class: {uri}")
                    base_props = self.ontology_manager.get_domain_property_list(cls)
                    if base_props:
                        logging.debug(f"Found {len(base_props)} properties for registry class {uri}")
                        all_properties.extend(base_props)
            
            # Method 3: For edge classes, explicitly check VITAL_Edge
            if "Edge_" in str(class_type):
                vital_edge_uri = "http://vital.ai/ontology/vital-core#VITAL_Edge"
                vital_edge_class = registry.vitalsigns_classes.get(vital_edge_uri)
                if vital_edge_class:
                    logging.debug(f"Explicitly checking VITAL_Edge for edge class")
                    edge_props = self.ontology_manager.get_domain_property_list(vital_edge_class)
                    if edge_props:
                        logging.debug(f"Found {len(edge_props)} properties from VITAL_Edge")
                        all_properties.extend(edge_props)
            
            # Remove duplicates based on property URI
            unique_properties = []
            seen_uris = set()
            
            for prop in all_properties:
                prop_uri = prop.get('uri')
                if prop_uri and prop_uri not in seen_uris:
                    seen_uris.add(prop_uri)
                    unique_properties.append(prop)
            
            logging.debug(f"Comprehensive inheritance resolution found {len(unique_properties)} unique properties")
            return unique_properties
            
        except Exception as e:
            logging.error(f"Error in comprehensive inheritance resolution: {e}")
            return []
    
    def generate_property_schema(self, prop_uri: str, prop_class: type) -> Dict[str, Any]:
        """Generate JSON schema for a property."""
        
        # Get property info from ontology manager
        prop_info = self.ontology_manager.get_property_info(prop_uri)
        
        # Determine if multi-value
        is_multi_value = False  # TODO: Extract from ontology annotations
        
        # Map property class to JSON Schema type
        json_type = self.map_property_class_to_json_type(prop_class, is_multi_value)
        
        # Add description
        prop_name = prop_uri.split('#')[-1] if '#' in prop_uri else prop_uri.split('/')[-1]
        json_type["description"] = f"Property: {prop_name}"
        
        # Add TypeScript property name hint
        ts_prop_name = self.generate_typescript_property_name(prop_name)
        json_type["tsPropertyName"] = ts_prop_name
        
        return json_type
    
    def map_property_class_to_json_type(self, prop_class: type, is_multi_value: bool = False) -> Dict[str, Any]:
        """Map VitalSigns property class to JSON Schema type."""
        
        # Import property classes
        from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
        from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
        from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
        from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
        from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
        from vital_ai_vitalsigns.model.properties.FloatProperty import FloatProperty
        from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
        from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
        
        # Type mapping
        if prop_class == StringProperty:
            base_type = {"type": "string"}
        elif prop_class == BooleanProperty:
            base_type = {"type": "boolean"}
        elif prop_class in [IntegerProperty, LongProperty]:
            base_type = {"type": "number"}
        elif prop_class in [DoubleProperty, FloatProperty]:
            base_type = {"type": "number"}
        elif prop_class == DateTimeProperty:
            base_type = {"type": "string", "format": "date-time"}
        elif prop_class == URIProperty:
            base_type = {"type": "string", "format": "uri"}
        else:
            # Default to string
            base_type = {"type": "string"}
        
        # Handle multi-value properties
        if is_multi_value:
            return {
                "type": "array",
                "items": base_type,
                "description": f"Array of {base_type['type']} values"
            }
        else:
            return base_type
    
    def generate_typescript_property_name(self, prop_name: str) -> str:
        """Generate TypeScript-friendly property name."""
        
        # Remove common prefixes
        name = prop_name
        if name.startswith("has"):
            name = name[3:]
        elif name.startswith("is"):
            name = name[2:]
        
        # Convert to camelCase
        if name:
            return name[0].lower() + name[1:]
        return prop_name.lower()
    
    # ========== Phase 2: Advanced Features ==========
    
    def extract_cardinality_constraints(self, class_uri: str) -> Dict[str, Dict[str, int]]:
        """Extract cardinality constraints for properties of a class."""
        
        cardinality_map = {}
        
        try:
            # Get the domain graph for SPARQL queries
            domain_graph = self.ontology_manager.get_domain_graph()
            
            # SPARQL query to find cardinality restrictions
            cardinality_query = f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?property ?restrictionType ?value WHERE {{
                <{class_uri}> rdfs:subClassOf ?restriction .
                ?restriction a owl:Restriction .
                ?restriction owl:onProperty ?property .
                
                {{
                    ?restriction owl:cardinality ?value .
                    BIND("exact" AS ?restrictionType)
                }} UNION {{
                    ?restriction owl:minCardinality ?value .
                    BIND("min" AS ?restrictionType)  
                }} UNION {{
                    ?restriction owl:maxCardinality ?value .
                    BIND("max" AS ?restrictionType)
                }}
            }}
            """
            
            results = domain_graph.query(cardinality_query)
            
            for row in results:
                prop_uri = str(row['property'])
                restriction_type = str(row['restrictionType'])
                value = int(row['value'])
                
                if prop_uri not in cardinality_map:
                    cardinality_map[prop_uri] = {}
                
                cardinality_map[prop_uri][restriction_type] = value
                
                logging.debug(f"Found cardinality constraint: {prop_uri} {restriction_type}={value}")
        
        except Exception as e:
            logging.warning(f"Could not extract cardinality constraints for {class_uri}: {e}")
        
        return cardinality_map
    
    def detect_union_types(self, prop_uri: str) -> Optional[List[str]]:
        """Detect if a property has union range types."""
        
        try:
            # Get property info from ontology manager
            prop_info = self.ontology_manager.get_property_info(prop_uri)
            
            if not prop_info:
                return None
            
            # Check if this is an object property with multiple range classes
            if prop_info.get("property_type") == "ObjectProperty":
                range_classes = prop_info.get("range_class_list", [])
                
                if len(range_classes) > 1:
                    # Multiple range classes indicate a union type
                    union_classes = [str(cls) for cls in range_classes]
                    logging.debug(f"Found union types for {prop_uri}: {union_classes}")
                    return union_classes
            
            # TODO: Add more sophisticated union detection using OWL graph analysis
            # This would involve parsing blank nodes and owl:unionOf constructs
            
        except Exception as e:
            logging.warning(f"Could not detect union types for {prop_uri}: {e}")
        
        return None
    
    def is_property_required(self, cardinality: Dict[str, int]) -> bool:
        """Determine if a property is required based on cardinality constraints."""
        
        # Required if minCardinality >= 1 or exact cardinality >= 1
        min_card = cardinality.get("min", 0)
        exact_card = cardinality.get("exact")
        
        if exact_card is not None and exact_card >= 1:
            return True
        elif min_card >= 1:
            return True
        
        return False
    
    def is_multi_value_property(self, cardinality: Dict[str, int]) -> bool:
        """Determine if property should be multi-value based on cardinality."""
        
        # If max cardinality is 1, it's single value
        if cardinality.get("max") == 1 or cardinality.get("exact") == 1:
            return False
        
        # If max cardinality > 1 or no max specified, it's multi-value
        max_card = cardinality.get("max")
        exact_card = cardinality.get("exact")
        
        if exact_card is not None and exact_card > 1:
            return True
        elif max_card is not None and max_card > 1:
            return True
        elif max_card is None and cardinality.get("min", 0) > 1:
            return True
        
        # Default to single value
        return False
    
    def generate_enhanced_property_schema(self, prop_uri: str, prop_class: type, 
                                        cardinality: Dict[str, int], 
                                        union_types: Optional[List[str]]) -> Dict[str, Any]:
        """Generate enhanced property schema with union types, cardinality, and multiple values support."""
        
        # Base schema from property class
        base_schema = self.get_property_schema_from_class(prop_class)
        
        # Check for hasMultipleValues annotation
        has_multiple_values = self.check_property_has_multiple_values(prop_uri)
        
        # If property has multiple values, wrap in array
        if has_multiple_values:
            base_schema = {
                "type": "array",
                "items": base_schema
            }
        
        # Add union types if present
        if union_types:
            if has_multiple_values:
                # Union types go in the items schema for arrays
                base_schema["items"]["unionTypes"] = union_types
                
                # Generate TypeScript union type names
                ts_union_names = []
                for union_type in union_types:
                    class_name = union_type.split('#')[-1]
                    ts_union_names.append(f"{class_name}URI")
                
                base_schema["items"]["tsUnionTypeNames"] = ts_union_names
                
                # Update description to include union information
                union_class_names = [ut.split('#')[-1] for ut in union_types]
                base_schema["items"]["description"] = f"URI reference to one of: {', '.join(union_class_names)}"
            else:
                # Union types go directly in the schema for single values
                base_schema["unionTypes"] = union_types
                
                # Generate TypeScript union type names
                ts_union_names = []
                for union_type in union_types:
                    class_name = union_type.split('#')[-1]
                    ts_union_names.append(f"{class_name}URI")
                
                base_schema["tsUnionTypeNames"] = ts_union_names
                
                # Update description to include union information
                union_class_names = [ut.split('#')[-1] for ut in union_types]
                base_schema["description"] = f"URI reference to one of: {', '.join(union_class_names)}"
                if "max" in cardinality or "exact" in cardinality:
                    max_items = cardinality.get("exact", cardinality.get("max"))
                    if max_items is not None:
                        base_schema["maxItems"] = max_items
        
        # Add TypeScript property name
        prop_name = prop_uri.split('#')[-1] if '#' in prop_uri else prop_uri.split('/')[-1]
        base_schema["tsPropertyName"] = self.generate_typescript_property_name(prop_name)
        
        return base_schema
    
    def check_property_has_multiple_values(self, prop_uri: str) -> bool:
        """Check if a property has the hasMultipleValues annotation set to true."""
        
        try:
            # Get the ontology that contains this property
            ontology_uri = None
            for ont_uri in self.ontology_manager.get_ontology_iri_list():
                ont_base = ont_uri.rstrip('#')
                if prop_uri.startswith(ont_base):
                    ontology_uri = ont_uri  # Keep the full URI with #
                    break
            
            if not ontology_uri:
                logging.debug(f"Could not find ontology for property: {prop_uri}")
                return False
            
            # Get the VitalSigns ontology and load with owlready2
            vs_ontology = self.ontology_manager.get_vitalsigns_ontology(ontology_uri)
            ontology_path = vs_ontology.get_ontology_path()
            
            from owlready2 import get_ontology
            owl_ontology = get_ontology(f"file://{ontology_path}").load()
            
            # Find the property in the ontology by name
            prop_name = prop_uri.split('#')[-1] if '#' in prop_uri else prop_uri.split('/')[-1]
            
            # Search for the property by name
            for prop in owl_ontology.properties():
                if prop.name == prop_name:
                    # Check if the property has the hasMultipleValues annotation
                    if hasattr(prop, 'hasMultipleValues'):
                        annotation_value = getattr(prop, 'hasMultipleValues')
                        if annotation_value:
                            multi_values = annotation_value[0]  # Get the boolean value
                            logging.debug(f"Property {prop_uri} hasMultipleValues: {multi_values}")
                            return bool(multi_values)
                    break
            
            return False
            
        except Exception as e:
            logging.debug(f"Error checking hasMultipleValues for property {prop_uri}: {e}")
            return False
    
    def get_property_schema_from_class(self, prop_class: type) -> Dict[str, Any]:
        """Generate base JSON schema from property class type."""
        
        from vital_ai_vitalsigns.model.properties.StringProperty import StringProperty
        from vital_ai_vitalsigns.model.properties.IntegerProperty import IntegerProperty
        from vital_ai_vitalsigns.model.properties.FloatProperty import FloatProperty
        from vital_ai_vitalsigns.model.properties.DoubleProperty import DoubleProperty
        from vital_ai_vitalsigns.model.properties.BooleanProperty import BooleanProperty
        from vital_ai_vitalsigns.model.properties.DateTimeProperty import DateTimeProperty
        from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
        from vital_ai_vitalsigns.model.properties.LongProperty import LongProperty
        
        # Map property classes to JSON schema types
        if prop_class == StringProperty:
            return {"type": "string"}
        elif prop_class == IntegerProperty:
            return {"type": "integer"}
        elif prop_class == LongProperty:
            return {"type": "integer", "format": "int64"}
        elif prop_class == FloatProperty:
            return {"type": "number", "format": "float"}
        elif prop_class == DoubleProperty:
            return {"type": "number", "format": "double"}
        elif prop_class == BooleanProperty:
            return {"type": "boolean"}
        elif prop_class == DateTimeProperty:
            return {"type": "string", "format": "date-time"}
        elif prop_class == URIProperty:
            return {"type": "string", "format": "uri"}
        else:
            # Default to string for unknown property types
            logging.debug(f"Unknown property class: {prop_class}, defaulting to string")
            return {"type": "string"}
    
    def generate_typescript_property_name(self, prop_name: str) -> str:
        """Generate TypeScript-friendly property name from OWL property name."""
        
        # Remove common prefixes
        if prop_name.startswith('has'):
            prop_name = prop_name[3:]
        elif prop_name.startswith('is'):
            prop_name = prop_name[2:]
        
        # Convert to camelCase
        return self.convert_to_camel_case(prop_name)
    
    def convert_to_camel_case(self, name: str) -> str:
        """Convert a name to camelCase."""
        
        if not name:
            return name
        
        # Handle names that are already camelCase or PascalCase
        if name[0].islower():
            return name
        
        # Convert first character to lowercase
        return name[0].lower() + name[1:] if len(name) > 1 else name.lower()
