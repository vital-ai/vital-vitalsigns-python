import os
import re
import shutil
import sys
import yaml

from owlready2 import get_ontology, onto_path, set_log_level, IRIS, default_world, ObjectProperty, DataProperty, \
    AnnotationProperty, Or, owl, ThingClass, ObjectPropertyClass
from rdflib import XSD, RDF, OWL, URIRef, RDFS
from vital_ai_vitalsigns_generate.generate.class_generator import VitalSignsClassGenerator
from vital_ai_vitalsigns_generate.generate.domain_ontology_class_generator import DomainOntologyClassGenerator
from vital_ai_vitalsigns_generate.generate.property_trait_generator import VitalSignsPropertyTraitGenerator
from vital_ai_vitalsigns_generate.vitalsigns_ontology_generator import VitalSignsOntologyGenerator


class VitalSignsDomainListGenerator(VitalSignsOntologyGenerator):

    # ontologies with no hasDefaultPackage annotation; package names fixed by
    # convention (the legacy Groovy generator used dedicated drivers for
    # these, GenerateVitalDomainPython / GenerateVitalCoreDomainPython)
    SPECIAL_PACKAGE_NAMES = {
        "http://vital.ai/ontology/vital": "vital_ai_domain",
        "http://vital.ai/ontology/vital-core": "vital_ai_vitalsigns_core",
    }

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

        # validate before generating anything (all-or-nothing, parity spec §7)
        self.validate_ontology(ontology_model, ontology_list)

        # package_name = "com_vitalai_aimp_domain"

        # determine package name

        package_name = self.get_default_package(ontology_model)[0]

        package_name = package_name.replace('.', '_')

        print(f"Package name: {package_name}")

        # generate all file contents in memory first; only write to disk once
        # everything has been generated successfully (all-or-nothing)

        # list of (relative path within model dir, content)
        generated_files = []

        # generate DomainOntology.py

        domain_ontology_class = DomainOntologyClassGenerator.generate(generate_ontology_iri)

        generated_files.append(('DomainOntology.py', domain_ontology_class))

        # property trait files, in deterministic (property IRI) order;
        # traits are only generated for properties defined in the generated
        # ontology (parity spec §6), skipping annotation/internal properties
        # (parity spec §4)

        ont_props = sorted(ontology_model.properties(), key=lambda p: p.iri)

        for ont_prop in ont_props:

            if not self.should_generate_trait(ontology_model, ont_prop):
                print(f"Skipping property trait for: {ont_prop.iri}")
                continue

            prop_trait_code = self.generate_property_code(ontology_model, ont_prop)

            property_trait_file_name = 'Property_' + ont_prop.name + '.py'

            print(f"PropertyTrait File: {property_trait_file_name}")

            generated_files.append(('properties/' + property_trait_file_name, prop_trait_code))

        # class .py / .pyi files, in Groovy-parity order (parity spec §2):
        # ascending same-ontology ancestor count, stable for ties

        ont_classes = sorted(
            ontology_model.classes(),
            key=lambda c: self.class_sort_key(ontology_model, c))

        for ont_class in ont_classes:

            if not self.should_generate_class(ont_class):
                print(f"Skipping class: {ont_class.iri}")
                continue

            class_code = self.generate_class_code(ontology_list, ontology_model, ont_class)

            class_file_name = ont_class.name + '.py'

            print(f"Class File: {class_file_name}")

            generated_files.append((class_file_name, class_code))

            class_interface_code = self.generate_class_interface_code(ontology_list, ontology_model, ont_class)

            class_interface_file_name = ont_class.name + '.pyi'

            print(f"Class Interface File: {class_interface_file_name}")

            generated_files.append((class_interface_file_name, class_interface_code))

        for ont_individual in ontology_model.individuals():
            # print(f"Individual: {ont_individual.name}")
            pass

        # generation succeeded; now delete/create directories and write files

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

        for relative_path, content in generated_files:
            file_path = model_dir + '/' + relative_path
            with open(file_path, 'w') as file:
                file.write(content)

    def generate_domain(self, *, ontology_dirs: list, domain_config_path: str,
                        domain_name: str, output_dir: str):
        """Generate the python package for one domain listed in the domain
        config. Parameterized entry point used by the `vitalsigns generate`
        CLI. Returns the package directory path.

        ontology_dirs: directories scanned for .owl files (IRI->file map);
            the target domain's OWL may live in any of them.
        domain_config_path: domain-config.yaml listing (domain, ontology).
        domain_name: the 'domain' key of the target in the config.
        output_dir: directory the package dir is created under.
        """

        from vital_ai_vitalsigns_generate.vitalsigns_generator import VitalSignsGenerator

        with open(domain_config_path, 'r') as f:
            config = yaml.safe_load(f)

        entry = None
        for item in config['domains']:
            if item['domain'] == domain_name:
                entry = item
                break

        if entry is None:
            available = [d['domain'] for d in config['domains']]
            raise ValueError(
                f"Domain {domain_name!r} not found in {domain_config_path}; "
                f"available: {available}")

        ontology_filename = entry['ontology']

        vs_generator = VitalSignsGenerator()

        owl_path = None
        for directory in ontology_dirs:
            candidate = os.path.join(directory, ontology_filename)
            if os.path.isfile(candidate):
                owl_path = candidate
                break

        if owl_path is None:
            raise FileNotFoundError(
                f"Ontology file {ontology_filename!r} not found in any of: "
                f"{ontology_dirs}")

        ontology_iri = vs_generator.extract_iri_from_owl(owl_path)

        iri_to_file_map = vs_generator.get_iri_to_file_map(list(ontology_dirs))

        ontology_model, ontology_list = self.load_ontologies(
            ontology_iri, iri_to_file_map, domain_config_path)

        if ontology_model is None:
            raise RuntimeError(
                f"Ontology {ontology_iri} ({ontology_filename}) failed to load")

        # validate before generating anything (all-or-nothing, parity spec §7)
        self.validate_ontology(ontology_model, ontology_list)

        package_name = self.SPECIAL_PACKAGE_NAMES.get(ontology_iri.rstrip('#/'))
        if package_name is None:
            package_name = self.get_default_package(ontology_model)[0]
            package_name = package_name.replace('.', '_')

        print(f"Package name: {package_name}")

        # generate all file contents in memory first (all-or-nothing)

        generated_files = [
            ('DomainOntology.py', DomainOntologyClassGenerator.generate(ontology_iri))]

        ont_props = sorted(ontology_model.properties(), key=lambda p: p.iri)

        for ont_prop in ont_props:
            if not self.should_generate_trait(ontology_model, ont_prop):
                print(f"Skipping property trait for: {ont_prop.iri}")
                continue
            prop_trait_code = self.generate_property_code(ontology_model, ont_prop)
            generated_files.append(
                ('properties/Property_' + ont_prop.name + '.py', prop_trait_code))

        ont_classes = sorted(
            ontology_model.classes(),
            key=lambda c: self.class_sort_key(ontology_model, c))

        for ont_class in ont_classes:
            if not self.should_generate_class(ont_class):
                print(f"Skipping class: {ont_class.iri}")
                continue
            generated_files.append(
                (ont_class.name + '.py',
                 self.generate_class_code(ontology_list, ontology_model, ont_class)))
            generated_files.append(
                (ont_class.name + '.pyi',
                 self.generate_class_interface_code(ontology_list, ontology_model, ont_class)))

        # generation succeeded; now delete/create directories and write files

        package_dir_path = os.path.join(output_dir, package_name)

        if os.path.isdir(package_dir_path):
            print(f"Directory exists, deleting: {package_dir_path}")
            shutil.rmtree(package_dir_path)
        os.makedirs(package_dir_path)

        self.add_init_py(package_dir_path)

        # copy the source OWL into the package; packages built from the
        # foundation vital-ontology dir keep that dir name
        owl_parent_name = os.path.basename(os.path.dirname(os.path.abspath(owl_path)))
        owl_subdir = 'vital-ontology' if owl_parent_name == 'vital-ontology' else 'domain-ontology'

        domain_ont_dir_path = os.path.join(package_dir_path, owl_subdir)
        os.makedirs(domain_ont_dir_path)
        shutil.copy(owl_path, os.path.join(domain_ont_dir_path, ontology_filename))

        model_dir = os.path.join(package_dir_path, 'model')
        os.makedirs(model_dir)
        self.add_init_py(model_dir)

        properties_dir = os.path.join(model_dir, 'properties')
        os.makedirs(properties_dir)
        self.add_init_py(properties_dir)

        for relative_path, content in generated_files:
            with open(os.path.join(model_dir, relative_path), 'w') as file:
                file.write(content)

        return package_dir_path
