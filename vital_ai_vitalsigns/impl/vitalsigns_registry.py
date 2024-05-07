from importlib.metadata import entry_points
import importlib
import pkgutil
import logging

# these are not imported here to remove a circular dependency on start-up
# from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
# from vital_ai_vitalsigns.model.VITAL_GraphContainerObject import VITAL_GraphContainerObject
# from vital_ai_vitalsigns.model.VITAL_HyperEdge import VITAL_HyperEdge
# from vital_ai_vitalsigns.model.VITAL_HyperNode import VITAL_HyperNode
# from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
# from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait


class VitalSignsRegistry:

    def __init__(self):
        self.vitalsigns_packages = []
        self.vitalsigns_classes = {}
        self.vitalsigns_property_classes = {}
        self.vitalsigns_ontologies = []

    def build_registry(self):
        self.vitalsigns_packages = []
        self.vitalsigns_ontologies = []

        self.vitalsigns_classes = {}

        logging.info('building vitalsigns class and property registry...')

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

        for ep in entry_points().get('vitalsigns_packages', []):
            try:
                module = importlib.import_module(ep.value)
                self.vitalsigns_packages.append(module)
                logging.info('Discovered Module: ' + str(module))
            except ImportError as e:
                logging.info(f"Could not import {ep.value}: {e}")
        for p in self.vitalsigns_packages:
            self.scan_vitalsigns_classes(p)

        logging.info('completed build of vitalsigns class and property registry.')

    def _scan_module(self, module_name):
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            logging.info(f"Error importing {module_name}: {e}")
            return

        for cls_name, cls in vars(module).items():
            if isinstance(cls, type):
                if self.is_vitalsigns_ontology_class(cls):
                    logging.info(f"Found VitalSigns Domain Ontology Class {cls_name} URI: {cls.OntologyURI}")
                    self.vitalsigns_ontologies.append(cls)
                if self.is_vitalsigns_class(cls):
                    class_uri = cls.get_class_uri()
                    logging.info(f"Found VitalSigns Graph Class {cls_name} URI: {class_uri}")
                    self.vitalsigns_classes[class_uri] = cls
                if self.is_vitalsigns_property_class(cls):
                    property_trait_uri = cls.get_uri()
                    logging.info(f"Found VitalSigns Property Class {cls_name} URI: {property_trait_uri}")
                    self.vitalsigns_property_classes[property_trait_uri] = cls

    def scan_vitalsigns_classes(self, package):
        for finder, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            self._scan_module(name)
            if is_pkg:
                self._scan_module(name)

    def is_vitalsigns_ontology_class(self, cls):

        from vital_ai_vitalsigns.model.BaseDomainOntology import BaseDomainOntology

        if cls is BaseDomainOntology:
            return False
        if issubclass(cls, BaseDomainOntology):
            return True

    def is_vitalsigns_class(self, cls):

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

    def is_vitalsigns_property_class(self, cls):

        from vital_ai_vitalsigns.model.trait.PropertyTrait import PropertyTrait

        if cls is PropertyTrait:
            return False
        if issubclass(cls, PropertyTrait):
            return True
        return False
