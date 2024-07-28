from owlready2 import get_ontology, onto_path, set_log_level, IRIS, default_world
import os
from rdflib import Graph

from vital_ai_vitalsigns_generate.vitalsigns_domain_list_generator import VitalSignsDomainListGenerator


class VitalSignsGenerator:

    def __init__(self):
        pass

    # special case of vitalsigns core
    # location of input and output

    def generate_vital_core(self):

        onto_path.append("../vital_home_test/vital-ontology/")

        main_ontology = get_ontology("file://../vital_home_test/vital-ontology/vital-core-0.2.304.owl").load()

        for imported_ontology in main_ontology.imported_ontologies:
            print(f"Imported ontology: {imported_ontology}")

        for cls in main_ontology.classes():
            print(cls)

        for prop in main_ontology.properties():
            print(prop)

        for individual in main_ontology.individuals():
            print(individual)

    # special case of vitalsigns domain
    # location of input, output, path to core owl ontology

    def generate_vital_domain(self):

        # set_log_level(2)

        onto_path.append("../vital_home_test/vital-ontology/")

        vital_ontology_path = "../vital_home_test/vital-ontology/"

        domain_ontology_path = "../vital_home_test/domain-ontology/"

        iri_to_file_map = self.get_iri_to_file_map([vital_ontology_path, domain_ontology_path])

        print(iri_to_file_map)

        original_get_ontology = default_world.get_ontology

        def custom_resolver(iri, iri_to_file_map):
            """Custom resolver function for mapping IRIs to local files."""
            return iri_to_file_map.get(iri, iri)

        def get_ontology_with_resolver(iri):
            resolved_iri = custom_resolver(iri, iri_to_file_map)
            return original_get_ontology(resolved_iri)

        default_world.get_ontology = get_ontology_with_resolver

        main_ontology = get_ontology("file://../vital_home_test/vital-ontology/vital-0.2.304.owl").load()

        for imported_ontology in main_ontology.imported_ontologies:
            print(f"Imported ontology: {imported_ontology}")

        for cls in main_ontology.classes():
            print(cls)

        for prop in main_ontology.properties():
            print(prop)

        for individual in main_ontology.individuals():
            print(individual)

    # case of a domain list
    # path to vital core owl
    # path to vital domain owl
    # path to domain list
    # directories to use for resolving ontologies
    # path to output

    def generate_domain_list(self):

        onto_path.append("../vital_home_test/vital-ontology/")

        vital_ontology_path = "../vital_home_test/vital-ontology/"

        domain_ontology_path = "../vital_home_test/domain-ontology/"

        iri_to_file_map = self.get_iri_to_file_map([vital_ontology_path, domain_ontology_path])

        print(iri_to_file_map)

        generator = VitalSignsDomainListGenerator()

        generator.generate(iri_to_file_map)

    def get_iri_to_file_map(self, directories):
        """Get a dictionary mapping IRIs to file paths for OWL files in a list of directories."""
        iri_to_file_map = {}
        for directory in directories:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if file_path.endswith('.owl'):
                    iri = self.extract_iri_from_owl(file_path)
                    if iri:
                        iri_to_file_map[iri] = "file://" + os.path.abspath(file_path)
        return iri_to_file_map

    def extract_iri_from_owl(self, file_path):
        """Extract the IRI from an OWL RDF/XML file."""
        g = Graph()
        g.parse(file_path, format='application/rdf+xml')

        query = """
        SELECT ?iri WHERE {
            ?iri a <http://www.w3.org/2002/07/owl#Ontology> .
        }
        """

        result = g.query(query)
        for row in result:
            return str(row[0])
        return None
