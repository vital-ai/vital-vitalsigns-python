import json
import logging
from datetime import datetime
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment


def main():

    print('Hello World')

    before_time = datetime.now()

    logging.basicConfig(level=logging.INFO)

    print(f"Initializing ontologies... ")

    vs = VitalSigns()

    after_time = datetime.now()

    delta = after_time - before_time

    delta_seconds = delta.total_seconds()

    print(f"Initialized Ontologies in: {delta_seconds} seconds.")

    vs.get_registry().build_registry()

    # Get the ontology manager from VitalSigns
    ontology_manager = vs.get_ontology_manager()
    
    print(f"\n=== Ontology Manager Information ===")
    
    # Get list of loaded domain model IRIs
    loaded_ontology_iris = ontology_manager.get_ontology_iri_list()
    
    print(f"Number of loaded ontologies: {len(loaded_ontology_iris)}")
    print(f"\nLoaded Domain Model IRIs:")
    
    for i, iri in enumerate(loaded_ontology_iris, 1):
        print(f"  {i}. {iri}")
        
        # Get detailed information about each ontology
        try:
            vitalsigns_ontology = ontology_manager.get_vitalsigns_ontology(iri)
            print(f"     Package: {vitalsigns_ontology.get_package_name()}")
            print(f"     File Path: {vitalsigns_ontology.get_ontology_path()}")
        except Exception as e:
            print(f"     Error getting details: {e}")
    
    # Get the domain graph statistics
    domain_graph = ontology_manager.get_domain_graph()
    triple_count = len(domain_graph)
    print(f"\nDomain Graph Statistics:")
    print(f"  Total triples: {triple_count}")
    
    # Get ontology list (namespace information)
    ontology_list = ontology_manager.get_ontology_list()
    print(f"\nNamespace Information:")
    for ontology in ontology_list:
        print(f"  Prefix: {ontology.prefix}, IRI: {ontology.ontology_iri}")
    
    print(f"\n=== Registry Information ===")
    
    # Get registry information
    registry = vs.get_registry()
    
    print(f"VitalSigns Classes: {len(registry.vitalsigns_classes)}")
    print(f"VitalSigns Property Classes: {len(registry.vitalsigns_property_classes)}")
    print(f"VitalSigns Ontologies: {len(registry.vitalsigns_ontologies)}")
    
    # Show some example classes
    print(f"\nExample VitalSigns Classes (first 5):")
    for i, (class_uri, class_type) in enumerate(list(registry.vitalsigns_classes.items())[:5], 1):
        print(f"  {i}. {class_uri} -> {class_type.__name__}")
    
    print(f"\nExample Property Classes (first 5):")
    for i, (prop_uri, prop_type) in enumerate(list(registry.vitalsigns_property_classes.items())[:5], 1):
        print(f"  {i}. {prop_uri} -> {prop_type.__name__}")


if __name__ == "__main__":
    main()
