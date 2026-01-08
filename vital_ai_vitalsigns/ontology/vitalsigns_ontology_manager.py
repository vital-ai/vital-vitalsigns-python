import logging
from collections import deque, defaultdict
from pathlib import Path
from typing import List
from owlready2 import get_ontology, onto_path, default_world, PREDEFINED_ONTOLOGIES
from rdflib import Graph, URIRef, Namespace, RDF, BNode, OWL, RDFS
from vital_ai_vitalsigns.model.properties.URIProperty import URIProperty
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.ontology.vitalsigns_ontology import VitalSignsOntology
from concurrent.futures import ThreadPoolExecutor, as_completed


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
        self._domain_property_map = {}
        self._data_prop_results_dict = {}
        self._ont_prop_results_dict = {}
        self._range_property_map = {}

    # TODO adding single ontology to check if imports are already
    # loaded, and don't import if not

    def get_property_info(self, property_uri: str):
        return self._range_property_map.get(property_uri, {})

    def get_domain_property_list(self, clazz):

        prop_list = []

        prop_set = set()

        if clazz.get_class_uri():

            clazz_uri = str(clazz.get_class_uri())

            # print(f"Class URI: {clazz_uri}")

            # print(domain_property_map.keys())
            # print(len(domain_property_map.keys()))

            class_map = self._domain_property_map.get(clazz_uri)

            if class_map:
                class_prop_set = class_map["prop_set"]
                prop_set.update(class_prop_set)

        for p in prop_set:
            prop_map = self._range_property_map[p]
            prop_class = prop_map["prop_class"]

            # print(f"Property: {p} : {prop_class.__name__}")
            # {'uri': 'http://vital.ai/ontology/vital-aimp#hasAccountEventAccountURI', 'prop_class': URIProperty},

            prop_map = {
                "uri": p,
                "prop_class": prop_class,
            }
            prop_list.append(prop_map)

        return prop_list

    def add_ontology(self, package_name: str, path: str):

        # TODO update this, currently just using the list case upon init
        # and not this function
        logging.info(f"Adding Ontology: {package_name} : {path}")

        vitalsigns_ontology = VitalSignsOntology(package_name, path)

        self._ont_map[vitalsigns_ontology.get_ontology_iri()] = vitalsigns_ontology

        ont_graph = vitalsigns_ontology.get_ontology_graph()

        for triple in ont_graph:
            self._domain_graph.add(triple)

    def extract_classes(self, expression, graph):
        classes = set()
        if isinstance(expression, BNode):
            for s, p, o in graph.triples((expression, None, None)):
                if p == OWL.unionOf or p == OWL.intersectionOf:
                    for item in graph.items(o):
                        classes.update(self.extract_classes(item, graph))
                else:
                    classes.update(self.extract_classes(o, graph))
        else:
            if (expression, RDF.type, OWL.Class) in graph or (expression, RDF.type, RDFS.Class) in graph:
                classes.add(expression)
        return classes

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

        def load_ontology(ont_module, owl_file):
            logging.info(f"Ont Module: {ont_module} : OWL File: {owl_file}")

            file_path = Path(owl_file)

            if not file_path.exists():
                logging.error(f'File not found: {file_path}')
                return None

            try:
                ont_graph = Graph()
                ont_graph.parse(file_path, format='xml')
                ont_iri = self.get_ontology_iri(ont_graph)
                imports = self.find_imports(ont_graph)
                return (ont_module, file_path, ont_iri, imports)
            except Exception as e:
                logging.error(f"Failed to load ontology {owl_file}: {e}")
                return None

        with ThreadPoolExecutor() as executor:
            future_to_ontology = {
                executor.submit(load_ontology, ont_module, owl_file): (ont_module, owl_file)
                for ont_module, owl_file in ontology_list
            }

            for future in as_completed(future_to_ontology):
                result = future.result()
                if result is None:
                    continue

                ont_module, file_path, ont_iri, imports = result
                file_paths.append(str(file_path))
                file_path_map[str(file_path)] = ont_iri
                ont_mod_map[ont_iri] = ont_module

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

            self.build_domain_property_map()

        else:
            logging.error('Failed to load ontology metadata.')

    def get_domain_graph(self) -> Graph:
        return self._domain_graph

    def get_subclass_uri_list(self, class_uri: str) -> List[str]:

        domain_graph = self.get_domain_graph()

        class_query = f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX vital: <http://vital.ai/ontology/vital-core#>

                SELECT ?subclass ?label ?parent
                WHERE {{
                    ?subclass rdfs:subClassOf*  <{class_uri}> .

                    OPTIONAL {{ ?subclass rdfs:label ?label }}
                    OPTIONAL {{ ?subclass rdfs:subClassOf ?parent }}
                }}
                """

        results = domain_graph.query(class_query)

        subclass_list: List[str] = []

        for row in results:
            subclass_uri = str(row['subclass'])
            label = str(row['label']) if row['label'] else subclass_uri.split('#')[-1]
            parent_uri = str(row['parent']) if row['parent'] else None

            # print(f"Subclass URI: {subclass_uri}, Label: {label}, Parent URI: {parent_uri}")

            subclass_list.append(subclass_uri)

        return subclass_list

    def get_ontology_list(self) -> List[Ontology]:

        domain_graph = self.get_domain_graph()

        namespaces = { prefix: str(namespace) for prefix, namespace in domain_graph.namespace_manager.namespaces()}

        ontology_list = []

        for prefix in namespaces.keys():
            ontology = Ontology(prefix, namespaces[prefix])
            ontology_list.append(ontology)

        return ontology_list


    def build_domain_property_map(self):

        from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl

        data_property_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?classExpression ?dataProperty ?dataType
            WHERE {
                ?dataProperty rdf:type owl:DatatypeProperty .
                ?dataProperty rdfs:domain ?classExpression .
                ?dataProperty rdfs:range ?dataType .
            }
            """

        results = self._domain_graph.query(data_property_query)

        for row in results:
            class_expression = row['classExpression']
            data_property_uri = str(row['dataProperty'])
            data_type_uri = str(row['dataType'])

            # Extract all classes from the class expression
            domain_classes = list(self.extract_classes(class_expression, self._domain_graph))

            # Add to results dictionary
            if data_property_uri not in self._data_prop_results_dict:
                self._data_prop_results_dict[data_property_uri] = {"domain": set(), "dataType": data_type_uri}

            self._data_prop_results_dict[data_property_uri]["domain"].update(domain_classes)

        object_property_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?classExpression ?objectProperty ?rangeExpression
            WHERE {
                ?objectProperty rdf:type owl:ObjectProperty .
                ?objectProperty rdfs:domain ?classExpression .
                OPTIONAL { ?objectProperty rdfs:range ?rangeExpression . }
            }
            """

        results = self._domain_graph.query(object_property_query)

        for row in results:
            class_expression = row['classExpression']
            object_property_uri = str(row['objectProperty'])
            range_expression = row['rangeExpression']

            # Extract all classes from the class expression and range expression
            domain_classes = list(self.extract_classes(class_expression, self._domain_graph))
            range_classes = list(self.extract_classes(range_expression, self._domain_graph)) if range_expression else []

            # Add to results dictionary
            if object_property_uri not in self._ont_prop_results_dict:
                self._ont_prop_results_dict[object_property_uri] = {"domain": set(), "range": set()}

            self._ont_prop_results_dict[object_property_uri]["domain"].update(domain_classes)
            self._ont_prop_results_dict[object_property_uri]["range"].update(range_classes)

        for prop_uri, domain_and_type in self._data_prop_results_dict.items():

            class_list = list(domain_and_type["domain"])

            data_type = domain_and_type["dataType"]

            prop_class = VitalSignsImpl.get_property_class_from_rdf_type(data_type)

            if prop_class is None:
                # print(f"No property class found for {data_type}")
                pass

            property_range_map = {
                "property_uri": prop_uri,
                "property_type": "DataProperty",
                "data_type": data_type,
                "prop_class": prop_class
            }

            self._range_property_map[prop_uri] = property_range_map

            # print(f"Data Prop: {class_list} {prop_uri} {data_type}")

            for clz in class_list:
                clz = str(clz)
                if clz in self._domain_property_map.keys():
                    class_map = self._domain_property_map[clz]
                    class_prop_set = class_map["prop_set"]
                else:
                    class_map = {}
                    self._domain_property_map[clz] = class_map
                    class_prop_set = set()
                    class_map["prop_set"] = class_prop_set
                class_prop_set.add(prop_uri)

        for prop_uri, domains_and_ranges in self._ont_prop_results_dict.items():

            class_list = list(domains_and_ranges["domain"])

            range_list = list(domains_and_ranges["range"])

            property_range_map = {
                "property_uri": prop_uri,
                "property_type": "ObjectProperty",
                "range_class_list": range_list,
                "prop_class": URIProperty
            }

            self._range_property_map[prop_uri] = property_range_map

            # print(f"Ont Prop: {class_list} {prop_uri} {range_list}")

            for clz in class_list:
                clz = str(clz)
                if clz in self._domain_property_map.keys():
                    class_map = self._domain_property_map[clz]
                    class_prop_set = class_map["prop_set"]
                else:
                    class_map = {}
                    self._domain_property_map[clz] = class_map
                    class_prop_set = set()
                    class_map["prop_set"] = class_prop_set

                class_prop_set.add(prop_uri)

            # exceptional case, used to get property type for query builder
            # should this be added into class info?
            uri_prop_uri = str("http://vital.ai/ontology/vital-core#URIProp")

            uri_property_range_map = {
                "property_uri": uri_prop_uri,
                "property_type": "ObjectProperty",
                "range_class_list": [],
                "prop_class": URIProperty
            }

            self._range_property_map[uri_prop_uri] = uri_property_range_map

    def get_ontology_iri_list(self) -> List[str]:
        return list(self._ont_map.keys())

    def get_vitalsigns_ontology(self, ontology_iri: str) -> VitalSignsOntology:
        return self._ont_map[ontology_iri]

    # dict of ontology uri to VitalSignsOntology instance
    # note: this means one version of an ontology in the manager at a time
    # potentially incorporate multi-versions

