import hashlib
import logging
from typing import List
from rdflib import Graph, Namespace
from owlready2 import get_ontology, default_world


class VitalSignsOntology:
    def __init__(self, package_name: str, path: str, *, ontology=None):
        self._load_ontology(package_name, path, ontology=ontology)

    def _load_ontology(self, package_name: str, path: str, *, ontology=None):
        try:
            self._package_name = package_name
            self._ontology_path = path
            self._graph = Graph()
            self._ontology_hash = ""

            if ontology is None:
                ontology = get_ontology(path).load(only_local=True)

            ontology_iri = str(ontology.base_iri)

            self._ontology_iri = ontology_iri

            logging.info(f"Loading Ontology IRI: {ontology_iri}")

            imports = []

            # for imp in ontology.imported_ontologies:
            #    logging.info(f"Import: {imp.base_iri}")

            # set
            if ontology.imported_ontologies:
                imports = {imp.base_iri for imp in ontology.imported_ontologies}

            logging.info(f"Ontology Imports: {imports}")

            self._import_list = imports

            self._graph.parse(path, format='xml')

            logging.info(f"Ontology Triple Count: { len(self._graph)}")

            self._namespace_map = {}

            if self._graph.namespace_manager.namespaces():
                self._namespace_map = {prefix: str(namespace) for prefix, namespace in self._graph.namespace_manager.namespaces()}

            logging.info(f"Ontology Namespaces: {self._namespace_map}")

            with open(path, 'rb') as f:
                file_data = f.read()

            md5_hash = hashlib.md5(file_data).hexdigest()

            self._ontology_hash = md5_hash

        except Exception as ex:
            logging.error(f"{ex}")

    def get_import_list(self) -> List[str]:
        return self._import_list

    def get_package_name(self) -> str:
        return self._package_name

    def get_ontology_iri(self) -> str:
        return self._ontology_iri

    def get_ontology_path(self) -> str:
        return self._ontology_path

    def get_ontology_graph(self) -> Graph:
        return self._graph
