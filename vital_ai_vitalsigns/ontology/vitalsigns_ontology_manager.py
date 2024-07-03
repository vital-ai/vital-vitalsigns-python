import logging
from collections import deque, defaultdict
from pathlib import Path
from typing import List
from owlready2 import get_ontology, onto_path, default_world, PREDEFINED_ONTOLOGIES
from rdflib import Graph, URIRef, Namespace, RDF
from vital_ai_vitalsigns.ontology.vitalsigns_ontology import VitalSignsOntology


class VitalSignsOntologyManager:

    OWL_IMPORTS = URIRef("http://www.w3.org/2002/07/owl#imports")
    OWL = Namespace("http://www.w3.org/2002/07/owl#")

    # TODO cleanup adding list to create a Graph
    # for each, extract metadata from the Graph
    # without reloading the file
    # and then import using owlready2 to get the rest
    # of the metadata

    def __init__(self):
        self._domain_graph = Graph()
        self._ont_map = {}

    # TODO adding single ontology to check if imports are already
    # loaded, and don't import if not

    def add_ontology(self, package_name: str, path: str):

        # TODO update this, currently just using the list case upon init
        # and not this function
        logging.info(f"Adding Ontology: {package_name} : {path}")

        vitalsigns_ontology = VitalSignsOntology(package_name, path)

        self._ont_map[vitalsigns_ontology.get_ontology_iri()] = vitalsigns_ontology

        ont_graph = vitalsigns_ontology.get_ontology_graph()

        for triple in ont_graph:
            self._domain_graph.add(triple)

    def get_ontology_iri(self, graph):

        # Query the graph to find the ontology IRI
        ontology_iri = None

        for s in graph.subjects(RDF.type, VitalSignsOntologyManager.OWL.Ontology):
            ontology_iri = str(s)
            break

        return ontology_iri

    def find_imports(self, graph):
        imports = set()
        for _, _, o in graph.triples((None, VitalSignsOntologyManager.OWL_IMPORTS, None)):
            imports.add(str(o))
        return imports

    def topological_sort(self, file_paths, import_graph):
        # we end up reversing this list, should this change?

        in_degree = {file: 0 for file in file_paths}

        for deps in import_graph.values():
            for dep in deps:
                in_degree[dep] += 1

        queue = deque([file for file in file_paths if in_degree[file] == 0])

        sorted_files = []

        while queue:
            current = queue.popleft()
            sorted_files.append(current)
            for neighbor in import_graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_files) != len(file_paths):
            raise Exception("Cycle detected in ontology imports!")

        return sorted_files

    def load_ontologies(self, ontology_list):

        ont_iri_list = []

        file_paths = []

        file_path_map = {}

        ont_mod_map = {}

        import_graph = defaultdict(list)

        for [ont_module, owl_file] in ontology_list:

            logging.info(f"Ont Module: {ont_module} : OWL File: {owl_file}")

            file_path = Path(owl_file)

            file_paths.append(str(file_path))

            if not file_path.exists():
                logging.error(f'File not found: {file_path}')
                continue

            # logging.info(f"Adding Ontology: {ont_module} : {file_path}")

            ont_graph = Graph()

            ont_graph.parse(file_path, format='xml')

            ont_iri = self.get_ontology_iri(ont_graph)

            file_path_map[str(file_path)] = ont_iri

            ont_mod_map[ont_iri] = ont_module

            imports = self.find_imports(ont_graph)

            # logging.info(f"{file_path}: imports: {imports}")

            for imp in imports:
                import_file_path = Path(imp).resolve()
                if import_file_path.exists():
                    import_graph[file_path].append(import_file_path)

        try:
            sorted_files = self.topological_sort(file_paths, import_graph)
        except Exception as e:
            logging.error(f'Error sorting ontologies: {e}')
            return None, None, None, None

        ontologies = []

        graph = Graph()

        directories = [str(Path(file).parent) for file in sorted_files]

        for d in directories:
            onto_path.append(d)

        # logging.info(f"OntoPath: {onto_path}")

        for file in sorted_files:

            # ont_iri = self.get_ontology_iri(file)
            # ont_iri = file_path_map[file]

            # ont_graph = Graph()
            # ont_graph.parse(file, format='xml')
            # ont_iri = self.get_ontology_iri(ont_graph)

            ont_iri = file_path_map[file]

            PREDEFINED_ONTOLOGIES[ont_iri] = file

        # Load each ontology in the correct order
        # reversing to start with vital-core, should the function sort differently?
        for file_path in reversed(sorted_files):
            try:

                file_path_str = str(file_path)

                # logging.info(f"Ontology File Path: {file_path_str}")

                ontology = get_ontology(file_path_str).load(only_local=True)

                # logging.info(f"After Ontology File Path: {file_path_str}")

                ontologies.append(ontology)

                ontology_iri = str(ontology.base_iri)

                # logging.info(f"Ontology IRI: {ontology_iri}")

                # logging.info(f"Ont Mod Map: {ont_mod_map}")

                # some cases have the IRI ending with # and other cases it does not
                ont_module = ont_mod_map[ontology_iri.rstrip('#')]

                logging.info(f"Ont Module: {ontology_iri}")

                vitalsigns_ontology = VitalSignsOntology(ont_module, file_path_str, ontology=ontology)

                ont_iri = vitalsigns_ontology.get_ontology_iri()

                # logging.info(f"Ont IRI: {ontology_iri}")

                ont_iri_list.append(ont_iri)

                self._ont_map[ont_iri] = vitalsigns_ontology

                # add to combined graph
                graph.parse(str(file_path), format='xml')

            except Exception as e:
                logging.error(f'Error loading ontology: {e}')

        # Extract ontology metadata
        ontology_metadata = []

        for ontology in ontologies:

            # logging.info(f"Ontology: {ontology}")

            ontology_iri = str(ontology.base_iri)

            imports = [imp.base_iri for imp in ontology.imported_ontologies]

            # logging.info(f"Ontology Imports: {imports}")

            ontology_metadata.append((ontology_iri, imports))

        # Get namespaces from the RDFLib graph
        namespaces = {prefix: str(namespace) for prefix, namespace in graph.namespace_manager.namespaces()}

        # Count the number of triples in the graph
        triple_count = len(graph)

        return ontology_metadata, namespaces, graph, triple_count

    # TODO check that the IRIs are unique

    def add_ontology_list(self, ontology_list):

        logging.info(f"Ontology List: {ontology_list}")

        file_paths = []

        for [ont_module, owl_file] in ontology_list:
            # logging.info(f"Ont Module: {ont_module} : OWL File: {owl_file}")
            file_paths.append(owl_file)

        ontology_metadata, namespaces, graph, triple_count = self.load_ontologies(ontology_list)

        if ontology_metadata and namespaces and graph:

            # for ontology_iri, imports in ontology_metadata:
            #    logging.info(f'Ontology IRI: {ontology_iri}')
            #    logging.info('Imports:')
            #    for imp in imports:
            #        logging.info(f'  {imp}')

            # logging.info('Namespaces:')
            # for prefix, iri in namespaces.items():
            #    logging.info(f'  {prefix}: {iri}')

            logging.info(f'The combined ontologies contain {triple_count} triples.')

            for triple in graph:
                self._domain_graph.add(triple)

            for k in self._ont_map.keys():
                logging.info(f"Ontology Loaded: {k}")

            logging.info(f"Domain Graph Triple Count: {len(graph)}")

        else:
            logging.error('Failed to load ontology metadata.')

    def get_domain_graph(self) -> Graph:
        return self._domain_graph

    def get_ontology_iri_list(self) -> List[str]:
        return list(self._ont_map.keys())

    def get_vitalsigns_ontology(self, ontology_iri: str) -> VitalSignsOntology:
        return self._ont_map[ontology_iri]

    # dict of ontology uri to VitalSignsOntology instance
    # note: this means one version of an ontology in the manager at a time
    # potentially incorporate multi-versions

