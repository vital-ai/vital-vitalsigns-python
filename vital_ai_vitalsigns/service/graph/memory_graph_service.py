import os
from typing import List
from rdflib import Dataset, URIRef, Graph, Literal
from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution import Solution
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding, BindingValueType
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService, G
from vital_ai_vitalsigns.service.graph.name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus
from vital_ai_vitalsigns.service.graph.graph_service_constants import VitalGraphServiceConstants
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.RDFStatement import RDFStatement
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment
import threading


class MemoryGraphService(VitalGraphService):

    def __init__(self):
        # init service graph, domain ontology graph

        self.graph = Dataset()

        # used to control access to the dataset
        self.lock = threading.Lock()

        # service_graph_uri_ref = URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI)

        service_graph = Graph(identifier=URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

        service_segment = VitalSegment()
        service_segment.URI = URIGenerator.generate_uri()
        service_segment.segmentID = VitalGraphServiceConstants.SERVICE_GRAPH_URI
        service_rdf_data = service_segment.to_rdf()

        ontology_segment = VitalSegment()
        ontology_segment.URI = URIGenerator.generate_uri()
        ontology_segment.segmentID = VitalGraphServiceConstants.SERVICE_GRAPH_URI
        ontology_rdf_data = ontology_segment.to_rdf()

        service_graph.parse(data=service_rdf_data, format="nt")
        service_graph.parse(data=ontology_rdf_data, format="nt")

        self.graph.add_graph(service_graph)

        # populate ontology graph
        # ontology_graph_uri_ref = URIRef(VitalGraphServiceConstants.ONTOLOGY_GRAPH_URI)

        ontology_graph = Graph(identifier=URIRef(VitalGraphServiceConstants.ONTOLOGY_GRAPH_URI))
        ontology_graph.parse(data=ontology_rdf_data, format="nt")

        self.graph.add_graph(ontology_graph)

        super().__init__()

    def start(self):
        pass

    def shutdown(self):
        pass

    def export_nquads(self):
        pass

    def import_nquads(self):
        pass

    def export_ntriples(self, graph_uri: str, file_path: str, *,
                        overwrite=True) -> bool:

        if os.path.exists(file_path):
            if overwrite is False:
                print(f"Exporting canceled: {graph_uri}. File path exists and overwrite is false.")
                return False

        for graph in self.graph.graphs():
            context_graph_uri = str(graph.identifier)
            if context_graph_uri == graph_uri:
                print(f"Exporting: {graph_uri}")
                print(f"Exporting: {graph_uri} into {file_path}")

                try:
                    # Exclude triples from the segment
                    query = f"""
                                SELECT ?subject
                                    WHERE {{
                                        ?subject <http://vital.ai/ontology/vital-core#hasSegmentID> "{graph_uri}"^^<http://www.w3.org/2001/XMLSchema#string> .
                                    }}
                            """

                    result = graph.query(query)

                    subject = None

                    for row in result:
                        # print(row)
                        subject = row.subject

                    if not subject:
                        print(f"Exporting: {graph_uri} failed.  Segment not found in source graph.")
                        return False

                    new_graph = Graph()

                    for s, p, o in graph:
                        if s != subject:
                            new_graph.add((s, p, o))

                    with open(file_path, 'wb') as f:
                        new_graph.serialize(destination=f, format='nt', encoding='utf-8')
                    return True

                except Exception as e:
                    print(f"Export Exception {e}")

        print(f"Exporting: {graph_uri} failed.")

        return False

    def import_ntriples(self, graph_uri: str, file_path: str) -> bool:
        for graph in self.graph.graphs():
            context_graph_uri = str(graph.identifier)
            if context_graph_uri == graph_uri:
                print(f"Importing: {graph_uri}")
                print(f"Purging: {graph_uri}")
                self.purge_graph(graph_uri)
                print(f"Importing: {graph_uri} from file: {file_path}")
                try:
                    graph.parse(source=file_path, format='nt')
                    print(f"Imported: {graph_uri} with Triple Count: {len(graph)}")
                    return True
                except Exception as e:
                    print(f"Import Exception {e}")

        print(f"Importing: {graph_uri} failed.")
        return False

    def list_graphs(self, *, vital_managed=True) -> List[VitalNameGraph]:

        name_graph_list = []

        for c in self.graph.graphs():
            graph_uri = str(c.identifier)
            name_graph = VitalNameGraph(graph_uri)
            name_graph_list.append(name_graph)

        return name_graph_list

    def get_graph(self, graph_uri: str, *, vital_managed=True) -> VitalNameGraph:

        for c in self.graph.graphs():
            context_graph_uri = str(c.identifier)
            if context_graph_uri == graph_uri:
                name_graph = VitalNameGraph(graph_uri)
                return name_graph

        return None

    def check_create_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        name_graph = self.get_graph(graph_uri)

        if name_graph:
            return False

        return self.create_graph(graph_uri)

    def create_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        graph_segment = VitalSegment()
        graph_segment.URI = URIGenerator.generate_uri()
        graph_segment.segmentID = graph_uri
        graph_rdf_data = graph_segment.to_rdf()

        try:
            # add the new graph
            new_graph = Graph(identifier=URIRef(graph_uri))
            new_graph.parse(data=graph_rdf_data, format="nt")
            self.graph.add_graph(new_graph)

            # add to the service graph
            service_graph = self.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))
            service_graph.parse(data=graph_rdf_data, format="nt")
        except Exception as e:
            return False

        return True

    def delete_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        try:
            service_graph = self.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

            for triple in service_graph.triples((None, None, None)):
                print(triple)

            print(f"Deleting Graph URI: {graph_uri}")

            query = f"""
            SELECT ?subject
            WHERE {{
              ?subject <http://vital.ai/ontology/vital-core#hasSegmentID> "{graph_uri}"^^<http://www.w3.org/2001/XMLSchema#string> .
            }}
            """

            print(query)

            result = service_graph.query(query)

            subject_to_remove = None
            for row in result:
                # print(row)
                subject_to_remove = row.subject

            print(f"Subject to Remove: {subject_to_remove}")

            if subject_to_remove:
                triples_to_remove = list(service_graph.triples((subject_to_remove, None, None)))
                for triple in triples_to_remove:
                    print(f"deleting: {triple}")
                    service_graph.remove(triple)

            self.graph.remove_graph(URIRef(graph_uri))

        except Exception as e:
            return False

        return True

    def purge_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        vs = VitalSigns()

        try:
            service_graph = self.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

            query = f"""
            SELECT ?subject
                WHERE {{
                    ?subject <http://vital.ai/ontology/vital-core#hasSegmentID> "{graph_uri}"^^<http://www.w3.org/2001/XMLSchema#string> .
                }}
            """

            result = service_graph.query(query)

            subject = None

            for row in result:
                # print(row)
                subject = row.subject

            if subject:
                # get the segment node from the service graph
                triples_gen = service_graph.triples((subject, None, None))
                segment = vs.from_triples(triples_gen)
                segment_rdf_data = segment.to_rdf()

                # delete the graph
                self.graph.remove_graph(URIRef(graph_uri))

                # recreate the graph and add the segment node
                new_graph = Graph(identifier=URIRef(graph_uri))
                new_graph.parse(data=segment_rdf_data, format="nt")
                self.graph.add_graph(new_graph)

        except Exception as e:
            return False

        return True

    def get_graph_all_objects(self, graph_uri: str, *, limit=100, offset=0, safety_check: bool = True,
                              vital_managed=True) -> ResultList:
        vs = VitalSigns()

        # include limit, offset
        # sort by subject uri
        # count total unique subjects and throw exception if over some number?

        graph = self.graph.get_graph(URIRef(graph_uri))

        query = f"""
                    SELECT ?subject
                        WHERE {{
                            ?subject <http://vital.ai/ontology/vital-core#hasSegmentID> "{graph_uri}"^^<http://www.w3.org/2001/XMLSchema#string> .
                        }}
                    """

        result = graph.query(query)

        subject = None

        for row in result:
            # print(row)
            subject = row.subject

        query = f"""
                CONSTRUCT {{
                    ?s ?p ?o .
                }} 
                WHERE {{
                    {{
                        SELECT DISTINCT ?s WHERE {{
                                ?s ?p ?o .
                                FILTER (?s != <{subject}>)
                        }}
                        ORDER BY ?s
                        LIMIT {limit}
                        OFFSET {offset}
                    }}
                   
                    ?s ?p ?o .
                    
                }}
                """

        # print(query)

        result = graph.query(query)

        # print(result)

        result_graph = Graph()

        for triple in result:
            # print(triple)
            result_graph.add(triple)

        subjects = set(result_graph.subjects())

        result_list = ResultList()

        for s in subjects:
            # print(s)
            triples = result_graph.triples((s, None, None))
            vitalsigns_object = vs.from_triples(triples)
            result_list.add_result(vitalsigns_object)

        return result_list

    def insert_object(self, graph_uri: str, graph_object: G, *, safety_check: bool = True,
                      vital_managed=True) -> VitalGraphStatus:

        graph = self.graph.get_graph(URIRef(graph_uri))

        graph_object_rdf_data = graph_object.to_rdf()

        graph.parse(data=graph_object_rdf_data, format="nt")

        status = VitalGraphStatus()
        return status

    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], *, safety_check: bool = True,
                           vital_managed=True) -> VitalGraphStatus:

        insert_graph = Graph(identifier=URIRef(graph_uri))

        for graph_object in graph_object_list:
            graph_object.add_to_graph(insert_graph)

        with self.lock:
            graph = self.graph.get_graph(URIRef(graph_uri))
            graph += insert_graph

        # for graph_object in graph_object_list:
        #    graph_object_rdf_data = graph_object.to_rdf()
        #    graph.parse(data=graph_object_rdf_data, format="nt")

        # combined_rdf_data = ""
        # for graph_object in graph_object_list:
        #    graph_object_rdf_data = graph_object.to_rdf()
        #    combined_rdf_data += graph_object_rdf_data + "\n"

        # Parse the combined RDF data string once
        # graph.parse(data=combined_rdf_data, format="nt")

        status = VitalGraphStatus()
        return status

    def update_object(self, graph_object: G, *, graph_uri: str = None, upsert: bool = False, safety_check: bool = True,
                      vital_managed: bool = True) -> VitalGraphStatus:

        graph = self.graph.get_graph(URIRef(graph_uri))

        object_uri = str(graph_object.URI)

        service_graph_object = self.get_object(object_uri, graph_uri)

        if service_graph_object is None:
            if upsert is False:
                status = VitalGraphStatus(status=-1, message="Object Not Found")
                return status
        else:
            self.delete_object(object_uri, graph_uri)

        self.insert_object(graph_uri, graph_object)

        status = VitalGraphStatus()
        return status

    def update_object_list(self, graph_object_list: List[G], *, graph_uri: str = None, upsert: bool = False,
                           safety_check: bool = True, vital_managed: bool = True) -> VitalGraphStatus:

        graph = self.graph.get_graph(URIRef(graph_uri))

        # check if all objects exist
        if upsert is False:
            all_found = True
            for graph_object in graph_object_list:
                object_uri = str(graph_object.URI)
                service_graph_object = self.get_object(object_uri, graph_uri)
                if service_graph_object is None:
                    all_found = False
                    break
            if all_found is False:
                status = VitalGraphStatus(status=-1, message="Not all objects found")
                return status

        for graph_object in graph_object_list:
            object_uri = str(graph_object.URI)
            self.delete_object(object_uri, graph_uri=graph_uri)
            self.insert_object(graph_uri, graph_object)

        status = VitalGraphStatus()
        return status

    def get_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True,
                   vital_managed: bool = True) -> G:

        vs = VitalSigns()

        # print(f"Graph URI {graph_uri}")

        graph = self.graph.get_graph(URIRef(graph_uri))

        # print(f"Graph Length: {len(graph)}")

        subject = URIRef(object_uri)

        try:
            triples = graph.triples((subject, None, None))

            if triples is None:
                return None

            vitalsigns_object = vs.from_triples(triples)

            if vitalsigns_object is None:
                return None

            return vitalsigns_object

        except Exception as e:
            print(f"get_object Exception {e}")

        return None

    def get_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True,
                        vital_managed: bool = True) -> ResultList:

        vs = VitalSigns()

        graph = self.graph.get_graph(URIRef(graph_uri))

        result_list = ResultList()

        for object_uri in object_uri_list:

            subject = URIRef(object_uri)
            triples = graph.triples((subject, None, None))
            graph_object = vs.from_triples(triples)
            result_list.add_result(graph_object)

        return result_list

    def delete_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True,
                      vital_managed: bool = True) -> VitalGraphStatus:

        graph = self.graph.get_graph(URIRef(graph_uri))

        triples_to_remove = list(graph.triples((URIRef(object_uri), None, None)))

        if len(triples_to_remove) == 0:
            status = VitalGraphStatus(status=-1, message="Object Not Found and Not Deleted")
            return status

        for t in triples_to_remove:
            graph.remove(t)

        status = VitalGraphStatus()
        return status

    def delete_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True,
                           vital_managed: bool = True) -> VitalGraphStatus:

        graph = self.graph.get_graph(URIRef(graph_uri))

        for object_uri in object_uri_list:
            triples_to_remove = list(graph.triples((URIRef(object_uri), None, None)))

            for t in triples_to_remove:
                graph.remove(t)

        status = VitalGraphStatus()
        return status

    def filter_query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit: int = 100, offset: int = 0,
                     resolve_objects: bool = True, safety_check: bool = True, vital_managed: bool = True) -> ResultList:

        graph = self.graph.get_graph(URIRef(graph_uri))


        result_list = ResultList()
        return result_list

    def query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit=100, offset=0, resolve_objects=True,
              safety_check: bool = True, vital_managed=True) -> ResultList:

        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        name_graph = self.get_graph(graph_uri)

        graph = self.graph.get_graph(URIRef(graph_uri))

        query = f"""
                PREFIX vital-core: <http://vital.ai/ontology/vital-core#>
                PREFIX vital: <http://vital.ai/ontology/vital#>
                PREFIX vital-aimp: <http://vital.ai/ontology/vital-aimp#>
                PREFIX haley: <http://vital.ai/ontology/haley#>
                PREFIX haley-ai-question: <http://vital.ai/ontology/haley-ai-question#>
                PREFIX haley-ai-kg: <http://vital.ai/ontology/haley-ai-kg#>

                SELECT DISTINCT ?{uri_binding} WHERE {{
                    GRAPH <{graph_uri}> {{
                            {sparql_query}
                        }}
                    }} ORDER BY ?{uri_binding}
                    LIMIT {limit} OFFSET {offset}
            """

        print(query)

        results = self.graph.query()

        object_uri_list = []

        for result in results:
            uri_binding = result.uri_binding
            object_uri_list.append(uri_binding)

        if not object_uri_list:
            return ResultList()

        if resolve_objects:
            return self.get_object_list(object_uri_list, graph_uri, vital_managed=vital_managed)
        else:
            result_list = ResultList()

            for uri in object_uri_list:

                rdf_triple = RDFStatement()
                rdf_triple.URI = URIGenerator.generate_uri()
                rdf_triple.rdfSubject = uri
                rdf_triple.rdfPredicate = ''
                rdf_triple.rdfObject = ''

                result_list.add_result(rdf_triple)

            return result_list

    def query_construct(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                        binding_list: List[Binding], *, limit=100, offset=0, safety_check: bool = True,
                        vital_managed: bool = True) -> ResultList:

        if graph_uri is None:
            result_list = ResultList()
            result_list.set_status(-1)
            result_list.set_message("Error: graph_uri is not set.")
            return result_list

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        graph = self.graph.get_graph(URIRef(graph_uri))

        prefix_section = "\n".join([f"PREFIX {ns.prefix}: <{ns.ontology_iri}>" for ns in namespace_list])

        order_by_section = " ".join([binding.variable for binding in binding_list])

        construct_template = "\n".join(
            [f"?bnode <{binding.property_uri}> ?{binding.variable[1:]} ." for binding in binding_list])

        select_parts = []

        for binding in binding_list:
            variable = binding.variable
            if binding.optional:
                select_parts.append(f"(COALESCE({variable}, \"{binding.unbound_symbol}\") AS {variable})")
            else:
                select_parts.append(f"{variable}")

        select_clause = "SELECT " + " ".join(select_parts)

        query = f"""
        {prefix_section}
        CONSTRUCT {{
        {construct_template}
        }}
        WHERE {{
            {{
            {select_clause} ?bnode
            WHERE {{     
            {sparql_query}
            BIND (BNODE() AS ?bnode)
            }}
            LIMIT 10  
            }}
        }}
        """

        """
        ORDER BY {order_by_section}
        LIMIT {limit}
        OFFSET {offset}
        """

        print(query)

        # results = self.graph.query(query)

        results = graph.query(query)

        print(results)

        result_graph = Graph()

        for triple in results:
            print(triple)
            result_graph.add(triple)

        subjects = set(result_graph.subjects())

        result_list = ResultList()

        triples = result_graph.triples((None, None, None))

        for s, p, o in triples:
            rdf_triple = RDFStatement()
            rdf_triple.URI = URIGenerator.generate_uri()

            rdf_triple.rdfSubject = str(s)  # blank node subject uri
            rdf_triple.rdfPredicate = str(p)  # property from binding
            rdf_triple.rdfObject = str(o)  # uri of matching object

            result_list.add_result(rdf_triple)

        return result_list

    def query_construct_solution(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                                 binding_list: List[Binding], root_binding: str | None = None, *, limit=100, offset=0,
                                 safety_check: bool = True, vital_managed: bool = True) -> SolutionList:

        graph = self.graph.get_graph(URIRef(graph_uri))

        # object cache to use during query
        graph_collection = GraphCollection(use_rdfstore=False, use_vectordb=False)

        result_list = self.query_construct(
            graph_uri,
            sparql_query,
            namespace_list,
            binding_list,
            limit, offset)

        graph = Graph()

        for result in result_list:
            rs = result.graph_object
            if isinstance(rs, RDFStatement):
                s = rs.rdfSubject
                p = rs.rdfPredicate

                value_type = BindingValueType.URIREF

                for binding in binding_list:
                    if binding.property_uri == str(p):
                        value_type = binding.value_type
                        break

                o = rs.rdfObject
                if value_type == BindingValueType.URIREF:
                    graph.add((URIRef(str(s)), URIRef(str(p)), URIRef(str(o))))
                else:
                    graph.add((URIRef(str(s)), URIRef(str(p)), Literal(str(o))))

        solutions = []

        unique_subjects = set(graph.subjects())

        for subject in unique_subjects:

            uri_map = {}
            obj_map = {}

            root_binding_obj = None

            triples = set(graph.triples((subject, None, None)))

            for s, p, o in triples:

                matching_bindings = [binding for binding in binding_list if binding.property_uri == str(p)]

                if len(matching_bindings) == 1:

                    matching_binding = matching_bindings[0]

                    binding_var = matching_binding.variable
                    binding_value = o

                    uri_map[binding_var] = binding_value

                    if matching_binding.value_type == BindingValueType.URIREF:

                        cache_obj = graph_collection.get(str(o))

                        if cache_obj is None:
                            binding_obj = self.get_object(str(o), graph_uri=graph_uri)
                            graph_collection.add(binding_obj)
                        else:
                            binding_obj = cache_obj

                        obj_map[binding_var] = binding_obj

                        if binding_var == root_binding:
                            # root_binding_uri = binding_value
                            root_binding_obj = binding_obj

            solution = Solution(uri_map, obj_map, root_binding, root_binding_obj)
            solutions.append(solution)

        solution_list = SolutionList(solutions, limit, offset)

        return solution_list

