import os
import re
import shutil
import sys

from owlready2 import get_ontology, onto_path, set_log_level, IRIS, default_world, ObjectProperty, DataProperty, \
    AnnotationProperty, Or, owl, ThingClass, ObjectPropertyClass
from rdflib import XSD, RDF, OWL, URIRef, RDFS
from vital_ai_vitalsigns_generate.generate.class_generator import VitalSignsClassGenerator
from vital_ai_vitalsigns_generate.generate.domain_ontology_class_generator import DomainOntologyClassGenerator
from vital_ai_vitalsigns_generate.generate.property_trait_generator import VitalSignsPropertyTraitGenerator
from vital_ai_vitalsigns_generate.vitalsigns_ontology_generator import VitalSignsOntologyGenerator


class VitalSignsDomainListGenerator(VitalSignsOntologyGenerator):

    def __init__(self):
        pass

    def add_init_py(self, directory):
        # Ensure the directory exists
        # os.makedirs(directory, exist_ok=True)

        # Define the path for the __init__.py file
        init_file_path = os.path.join(directory, '__init__.py')

        # Create an empty __init__.py file
        with open(init_file_path, 'w') as f:
            pass

        print(f"Empty __init__.py file created in: {directory}")

    def generate(self, iri_to_file_map: dict):

        # base_dir = '../vital_home_test/domain-python/'

        project_dir = '/Users/hadfield/Local/vital-git/vital-vitalsigns-python'

        vital_home_dir = project_dir + '/vital_home_test/'

        vital_home_python_dir = vital_home_dir + 'domain-python/'

        domain_list_file_path = vital_home_python_dir + 'domain-config.yaml'

        generate_ontology_iri = "http://vital.ai/ontology/vital-aimp"

        generate_ontology_file_name = "vital-aimp-0.1.0.owl"

        ontology_package_dir = "vital-aimp-python"

        ontology_model, ontology_list = self.load_ontologies(generate_ontology_iri, iri_to_file_map, domain_list_file_path)

        for ont in ontology_list:
            print(f"- {ont.base_iri}")

        print(f"Main ontology base IRI: {ontology_model.base_iri}")

        # check if ontology_package_path exists, exit if not
        # setup.py should exist within this

        ontology_package_path = vital_home_python_dir + ontology_package_dir

        if not os.path.isdir(ontology_package_path):
            print(f"Directory does not exist: {ontology_package_path}")
            sys.exit(1)
        else:
            print(f"Directory exists: {ontology_package_path}")

        # package_name = "com_vitalai_aimp_domain"

        # determine package name
        # delete if exists
        # create directory: com_vitalai_aimp_domain

        package_name = self.get_default_package(ontology_model)[0]

        package_name = package_name.replace('.', '_')

        print(f"Package name: {package_name}")

        package_dir_path = ontology_package_path + '/' + package_name

        if os.path.isdir(package_dir_path):
            print(f"Directory exists, deleting: {package_dir_path}")
            shutil.rmtree(package_dir_path)
        os.makedirs(package_dir_path)
        print(f"Directory created: {package_dir_path}")

        # add file __init__.py
        self.add_init_py(package_dir_path)

        # create directory domain-ontology
        # copy owl file into it from domain-ontology

        domain_ont_dir_path = package_dir_path + '/' + 'domain-ontology'

        os.makedirs(domain_ont_dir_path)

        dest_domain_ont_path = domain_ont_dir_path + '/' + generate_ontology_file_name

        source_domain_ont_path = vital_home_dir + 'domain-ontology/' + generate_ontology_file_name

        shutil.copy(source_domain_ont_path, dest_domain_ont_path)

        # create model directory, add __init__.py
        # create properties directory, add __init__.py

        model_dir = package_dir_path + '/' + 'model'
        os.makedirs(model_dir)
        self.add_init_py(model_dir)

        properties_dir = model_dir + '/' + 'properties'
        os.makedirs(properties_dir)
        self.add_init_py(properties_dir)


        # generate DomainOntology.py into model directory

        domain_ontology_class = DomainOntologyClassGenerator.generate(generate_ontology_iri)

        # print(domain_ontology_class)

        domain_ontology_file_name = 'DomainOntology.py'

        domain_ontology_file_path = model_dir + '/' + domain_ontology_file_name

        with open(domain_ontology_file_path, 'w') as file:
            file.write(domain_ontology_class)

        for ont_prop in ontology_model.properties():

            # print(f"Ont Prop: {ont_prop.name}")

            prop_trait_code = self.generate_property_code(ontology_model, ont_prop)

            # print(prop_trait_code)

            # write file, using name like: Property_hasAccountEventAccountURI.py

            property_trait_file_name = 'Property_' + ont_prop.name + '.py'

            print(f"PropertyTrait File: {property_trait_file_name}")

            property_trait_file_path = properties_dir + '/' + property_trait_file_name

            with open(property_trait_file_path, 'w') as file:
                file.write(prop_trait_code)

        for ont_class in ontology_model.classes():
            # print(f"Class: {ont_class.namespace.base_iri} {ont_class.name}")
            class_code = self.generate_class_code(ontology_list, ontology_model, ont_class)
            # print(class_code)

            # write file, name like AccountAction.py

            class_file_name = ont_class.name + '.py'

            print(f"Class File: {class_file_name}")

            class_file_path = model_dir + '/' + class_file_name

            with open(class_file_path, 'w') as file:
                file.write(class_code)

            class_interface_code = self.generate_class_interface_code(ontology_list, ontology_model, ont_class)
            # print(class_interface_code)

            # write file, name like: AccountAction.pyi

            class_interface_file_name = ont_class.name + '.pyi'

            print(f"Class Interface File: {class_interface_file_name}")

            class_interface_file_path = model_dir + '/' + class_interface_file_name

            with open(class_interface_file_path, 'w') as file:
                file.write(class_interface_code)

        for ont_individual in ontology_model.individuals():
            # print(f"Individual: {ont_individual.name}")
            pass
