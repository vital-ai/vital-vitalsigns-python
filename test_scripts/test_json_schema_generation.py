#!/usr/bin/env python3
"""
Test script for JSON Schema generation from VitalSigns ontologies.

This script demonstrates how to use the VitalSignsJSONSchemaGenerator
to generate JSON schemas for loaded ontologies.
"""

import os
import json
import logging
from pathlib import Path
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_generate.generate.json_schema_generator import VitalSignsJSONSchemaGenerator


def main():
    """Test JSON schema generation for loaded ontologies."""
    
    print("=== VitalSigns JSON Schema Generation Test ===")
    
    # Initialize VitalSigns (loads all discovered ontologies)
    print("Initializing VitalSigns...")
    vs = VitalSigns()
    
    # Get ontology manager to see what's loaded
    ontology_manager = vs.get_ontology_manager()
    loaded_ontologies = ontology_manager.get_ontology_iri_list()
    
    print(f"Found {len(loaded_ontologies)} loaded ontologies:")
    for i, iri in enumerate(loaded_ontologies, 1):
        print(f"  {i}. {iri}")
    
    # Create output directory
    output_dir = Path("/Users/hadfield/Local/vital-git/vital-vitalsigns-python/domain_schema")
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir.absolute()}")
    
    # Initialize JSON Schema Generator
    generator = VitalSignsJSONSchemaGenerator()
    
    # Generate schemas for all loaded ontologies
    generated_files = []
    
    for ontology_iri in loaded_ontologies:
        try:
            print(f"\nGenerating schema for: {ontology_iri}")
            
            schema_path = generator.generate_json_schema_for_ontology(
                ontology_iri, 
                str(output_dir)
            )
            
            generated_files.append(schema_path)
            print(f"  ✓ Generated: {schema_path}")
            
            # Validate the generated schema
            validate_generated_schema(schema_path)
            
        except Exception as e:
            print(f"  ✗ Error generating schema for {ontology_iri}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n=== Generation Complete ===")
    print(f"Successfully generated {len(generated_files)} schema files:")
    for file_path in generated_files:
        file_size = Path(file_path).stat().st_size
        print(f"  - {file_path} ({file_size:,} bytes)")
    
    # Test specific ontology (if vital-core is available)
    test_specific_ontology(generator, output_dir, loaded_ontologies)


def validate_generated_schema(schema_path: str):
    """Validate that the generated schema is valid JSON and has expected structure."""
    
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Check required top-level fields
        required_fields = ['$schema', 'domainURI', 'vitalsignsVersion', '$defs']
        for field in required_fields:
            if field not in schema:
                print(f"    ⚠ Warning: Missing required field '{field}'")
            else:
                print(f"    ✓ Has required field '{field}'")
        
        # Check schema definitions
        if '$defs' in schema and schema['$defs']:
            class_count = len(schema['$defs'])
            print(f"    ✓ Contains {class_count} class definitions")
            
            # Check first class structure
            if class_count > 0:
                first_class = next(iter(schema['$defs'].values()))
                if 'type' in first_class and first_class['type'] == 'object':
                    print(f"    ✓ Classes have proper object structure")
                if 'properties' in first_class:
                    prop_count = len(first_class['properties'])
                    print(f"    ✓ First class has {prop_count} properties")
        else:
            print(f"    ⚠ Warning: No class definitions found")
        
    except json.JSONDecodeError as e:
        print(f"    ✗ Invalid JSON: {e}")
    except Exception as e:
        print(f"    ✗ Validation error: {e}")


def test_specific_ontology(generator, output_dir, loaded_ontologies):
    """Test generation for a specific ontology with detailed output."""
    
    # Look for vital-core ontology
    vital_core_iri = "http://vital.ai/ontology/vital-core#"
    
    if vital_core_iri in loaded_ontologies:
        print(f"\n=== Detailed Test: {vital_core_iri} ===")
        
        try:
            schema_path = generator.generate_json_schema_for_ontology(
                vital_core_iri,
                str(output_dir)
            )
            
            # Load and inspect the schema
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            print(f"Schema details:")
            print(f"  - Domain URI: {schema.get('domainURI', 'N/A')}")
            print(f"  - Name: {schema.get('name', 'N/A')}")
            print(f"  - Version: {schema.get('version', 'N/A')}")
            print(f"  - VitalSigns Version: {schema.get('vitalsignsVersion', 'N/A')}")
            print(f"  - Parents: {schema.get('parents', [])}")
            
            if '$defs' in schema:
                print(f"  - Class Definitions: {len(schema['$defs'])}")
                
                # Show first few classes
                class_names = list(schema['$defs'].keys())[:3]
                for class_name in class_names:
                    class_def = schema['$defs'][class_name]
                    prop_count = len(class_def.get('properties', {}))
                    print(f"    - {class_name}: {prop_count} properties")
                    
                    # Show first few properties
                    if prop_count > 0:
                        prop_names = list(class_def['properties'].keys())[:2]
                        for prop_name in prop_names:
                            prop_def = class_def['properties'][prop_name]
                            prop_type = prop_def.get('type', 'unknown')
                            ts_name = prop_def.get('tsPropertyName', 'N/A')
                            print(f"      - {prop_name}: {prop_type} (TS: {ts_name})")
            
        except Exception as e:
            print(f"  ✗ Detailed test failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n=== Detailed Test Skipped ===")
        print(f"vital-core ontology not found in loaded ontologies")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
