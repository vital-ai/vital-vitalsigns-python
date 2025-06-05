import sys
from datetime import datetime
from functools import lru_cache
from importlib.metadata import entry_points, distribution
import importlib
import pkgutil
import logging
from pathlib import Path
import importlib.resources as resources
import concurrent.futures
from typing import Type, Dict
from importlib.metadata import entry_points
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.ontology.vitalsigns_ontology_manager import VitalSignsOntologyManager


# these are not imported here to remove a circular dependency on start-up
# from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
# from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
# from vital_ai_vitalsigns.model.VITAL_HyperEdge import VITAL_HyperEdge
# from vital_ai_vitalsigns.model.VITAL_HyperNode import VITAL_HyperNode
# from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
# from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


def is_vitalsigns_ontology_class(cls):
    from vital_ai_vitalsigns.model.BaseDomainOntology import BaseDomainOntology

    if cls is BaseDomainOntology:
        return False
    if issubclass(cls, BaseDomainOntology):
        return True


def is_vitalsigns_class(cls):
    from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
    from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
    from vital_ai_vitalsigns.model.VITAL_HyperEdge import VITAL_HyperEdge
    from vital_ai_vitalsigns.model.VITAL_HyperNode import VITAL_HyperNode
    from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node

    if cls is VITAL_Node:
        return False
    if cls is VITAL_Edge:
        return False
    if cls is VITAL_HyperNode:
        return False
    if cls is VITAL_HyperEdge:
        return False
    if cls is VITAL_GraphContainerObject:
        return False
    if issubclass(cls, VITAL_Node):
        return True
    if issubclass(cls, VITAL_Edge):
        return True
    if issubclass(cls, VITAL_HyperNode):
        return True
    if issubclass(cls, VITAL_HyperEdge):
        return True
    if issubclass(cls, VITAL_GraphContainerObject):
        return True
    return False


def is_vitalsigns_property_class(cls):
    from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait

    if cls is PropertyTrait:
        return False
    if issubclass(cls, PropertyTrait):
        return True
    return False


def scan_module_parallel(module_name):
    try:
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            module = importlib.import_module(module_name)
    except ImportError as e:
        logging.info(f"Error importing {module_name}: {e}")
        return [], {}, {}

    # logging.info(f"Scanning {module_name}")

    ontologies = set()
    classes = {}
    properties = {}

    for cls_name, cls in vars(module).items():
        if isinstance(cls, type):
            if is_vitalsigns_ontology_class(cls):
                logging.info(f"Found VitalSigns Domain Ontology Class {cls_name} URI: {cls.OntologyURI}")
                ontologies.add(cls)
            if is_vitalsigns_class(cls):
                class_uri = cls.get_class_uri()
                logging.info(f"Found VitalSigns Graph Class {cls_name} URI: {class_uri}")
                classes[class_uri] = cls
            if is_vitalsigns_property_class(cls):
                property_trait_uri = cls.get_uri()
                logging.info(f"Found VitalSigns Property Class {cls_name} URI: {property_trait_uri}")
                properties[property_trait_uri] = cls

    return ontologies, classes, properties


def scan_vitalsigns_package_parallel(package_path, package_name):
    ontology_set = set()
    classes_map = {}
    properties_map = {}

    for finder, name, is_pkg in pkgutil.walk_packages(package_path, package_name + '.'):
        # logging.info(f"Scanning path: {name}")
        ontologies, classes, properties = scan_module_parallel(name)
        ontology_set.update(ontologies)
        classes_map.update(classes)
        properties_map.update(properties)

    return ontology_set, classes_map, properties_map


def scan_package(package_path, package_name):
    try:
        return package_name, scan_vitalsigns_package_parallel(package_path, package_name)
    except Exception as e:
        return package_name, e


def scan_vitalsigns_classes_parallel(vitalsigns_packages):

    results = {}

    with concurrent.futures.ProcessPoolExecutor() as executor:

        future_to_package = {}

        for p in vitalsigns_packages:
            package_path = p.__path__
            package_name = p.__name__

            future = executor.submit(scan_package, package_path, package_name)

            future_to_package[future] = package_name

        for future in concurrent.futures.as_completed(future_to_package):
            package_name = future_to_package[future]
            try:
                result = future.result()
                results[package_name] = result
            except Exception as e:
                results[package_name] = e

    return results


class VitalSignsRegistry:

    from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait

    def __init__(self, *, ontology_manager: VitalSignsOntologyManager):
        self.vitalsigns_packages = []
        self.vitalsigns_classes: Dict[str, Type[GraphObject]] = {}
        self.vitalsigns_property_classes = {}
        self.vitalsigns_ontologies = set()
        self.ontology_manager = ontology_manager

    def get_package_root(self):
        # Get the root of the current package
        package_name = __name__.split('.')[0]
        dist = distribution(package_name)
        package_root = Path(dist.locate_file('')) / package_name
        return package_root

    @lru_cache(maxsize=None)
    def get_vitalsigns_class(self, class_uri: str) -> Type[GraphObject]:
        return self.vitalsigns_classes[class_uri]

    @lru_cache(maxsize=None)
    def get_vitalsigns_property_class(self, property_uri: str) -> Type[PropertyTrait]:
        return self.vitalsigns_property_classes[property_uri]

    def build_registry(self):
        self.vitalsigns_packages = []
        self.vitalsigns_ontologies = set()
        self.vitalsigns_classes = {}

        logging.info('building vitalsigns class and property registry...')

        package_root = self.get_package_root()
        logging.info(f'Package root: {package_root}')

        from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
        from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
        from vital_ai_vitalsigns.model.VITAL_HyperEdge import VITAL_HyperEdge
        from vital_ai_vitalsigns.model.VITAL_HyperNode import VITAL_HyperNode
        from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node

        self.vitalsigns_classes[VITAL_Node.get_class_uri()] = VITAL_Node
        self.vitalsigns_classes[VITAL_Edge.get_class_uri()] = VITAL_Edge
        self.vitalsigns_classes[VITAL_HyperNode.get_class_uri()] = VITAL_HyperNode
        self.vitalsigns_classes[VITAL_HyperEdge.get_class_uri()] = VITAL_HyperEdge
        self.vitalsigns_classes[VITAL_GraphContainerObject.get_class_uri()] = VITAL_GraphContainerObject

        self.vitalsigns_property_classes = {}

        ont_tuple_list = []

        # for ep in entry_points().get('vitalsigns_packages', []):
        for ep in entry_points(group='vitalsigns_packages'):

            try:
                module = importlib.import_module(ep.value)
                self.vitalsigns_packages.append(module)

                logging.info('Discovered Module: ' + str(module))

                module_path = Path(module.__file__).parent

                ont_tuples = self.check_ontology_files(module_path, module.__name__)

                # TODO confirm that a module only provides a single ontology
                if len(ont_tuples) > 0:
                    ont_tuple_list.extend(ont_tuples)

            except ImportError as e:
                logging.info(f"Could not import {ep.value}: {e}")

        logging.info('completed vitalsigns entry point scan.')

        current_time = datetime.now()

        # print(f"Scan: Before Time: {current_time}")

        logging.info(f"Scan: Before Time: {current_time}")

        logging.info(f"Package Length: {len(self.vitalsigns_packages)}")

        for p in self.vitalsigns_packages:
            self.scan_vitalsigns_classes(p)

        # disable spawning new processes for now until that is more stable

        """
        results = scan_vitalsigns_classes_parallel(self.vitalsigns_packages)

        for k, v in results.items():
            # logging.info(f"V: {v}")
            [package_name, [ontologies, classes, properties]] = v
            logging.info(f"Package: {package_name}")

            self.vitalsigns_ontologies.update(ontologies)
            self.vitalsigns_classes.update(classes)
            self.vitalsigns_property_classes.update(properties)

        """

        current_time = datetime.now()

        # print(f"Scan: After Time: {current_time}")

        logging.info(f"Scan: After Time: {current_time}")

        logging.info('completed build of vitalsigns class and property registry.')

        logging.info(f"Ontology Tuple List: {ont_tuple_list}")

        if len(ont_tuple_list) > 0:

            self.ontology_manager.add_ontology_list(ont_tuple_list)

            current_time = datetime.now()

            logging.info(f"Scan: After Ontology Load: {current_time}")

            # print(f"Scan: After Ontology Load: {current_time}")

    def _scan_module(self, module_name):
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                module = importlib.import_module(module_name)
        except ImportError as e:
            logging.info(f"Error importing {module_name}: {e}")
            return [], {}, {}

        # logging.info(f"Scanning {module_name}")

        for cls_name, cls in vars(module).items():
            if isinstance(cls, type):
                if is_vitalsigns_ontology_class(cls):
                    # logging.info(f"Found VitalSigns Domain Ontology Class {cls_name} URI: {cls.OntologyURI}")
                    self.vitalsigns_ontologies.add(cls)
                if is_vitalsigns_class(cls):
                    class_uri = cls.get_class_uri()
                    # logging.info(f"Found VitalSigns Graph Class {cls_name} URI: {class_uri}")
                    self.vitalsigns_classes[class_uri] = cls
                if is_vitalsigns_property_class(cls):
                    property_trait_uri = cls.get_uri()
                    # logging.info(f"Found VitalSigns Property Class {cls_name} URI: {property_trait_uri}")
                    self.vitalsigns_property_classes[property_trait_uri] = cls

    def scan_vitalsigns_classes(self, package):
        for finder, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):

            # logging.info(f"Scanning path: {name}")

            self._scan_module(name)

            # if is_pkg:
            #    self._scan_module(name)

            # add further recursion?
            # self.scan_vitalsigns_classes(name)

    def check_ontology_files(self, base_path, module_name):

        ontology_list = []

        for ontology_dir in ['vital-ontology', 'domain-ontology']:
            ontology_path = base_path / ontology_dir

            # logging.info(f"Ontology check: {ontology_path}")

            if ontology_path.exists() and ontology_path.is_dir():

                # logging.info(f"Ontology Listing files: {ontology_path}")

                # should be at most one
                for owl_file in ontology_path.glob('*.owl'):

                    owl_file_str = str(owl_file)

                    # logging.info(f"Discovered OWL File {owl_file_str}")
                    # one-to-one relationship between module name and owl file
                    # self.ontology_manager.add_ontology(module_name, owl_file_str)
                    ontology_list.append([module_name, owl_file_str])

        return ontology_list
