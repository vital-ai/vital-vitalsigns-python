import os
import threading
from typing import List, TypeVar
from rdflib import Dataset, URIRef, Graph, Literal
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution import Solution
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding, BindingValueType
from vital_ai_vitalsigns.service.vital_name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus
from vital_ai_vitalsigns.service.graph.graph_service_constants import VitalGraphServiceConstants
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns_core.model.RDFStatement import RDFStatement
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment

G = TypeVar('G', bound='GraphObject')

# TODO switch to using graph_id in place of graph_uri
# to match service definition?

# handle case when graph_id (and account, etc) are None
# to use the global (default) graph

# Note: RDF collection makes direct calls to the graph
# to update the global graph which we may or may not want to continue

class RDFlibSparqlImpl:

    def __init__(self, *, multigraph=False):

        self._multigraph = multigraph

        if multigraph:
            self.graph = Dataset()
        else:
            self.graph = Graph()

        self.lock = threading.Lock()

    def _list_graphs_impl(self) -> List[VitalNameGraph]:

        name_graph_list = []

        # only handle multigraph case
        if self._multigraph:
            if isinstance(self.graph, Dataset):
                for c in self.graph.graphs():
                    graph_uri = str(c.identifier)
                    name_graph = VitalNameGraph(graph_uri)
                    name_graph_list.append(name_graph)
        else:
            # uni-graph case
            return []

        return name_graph_list

    def _get_graph_impl(self, *, graph_uri: str) -> VitalNameGraph | None:

        # only handle multigraph case
        if self._multigraph:
            if isinstance(self.graph, Dataset):
                for c in self.graph.graphs():
                    context_graph_uri = str(c.identifier)
                    if context_graph_uri == graph_uri:
                        name_graph = VitalNameGraph(graph_uri)
                        return name_graph
        else:
            # uni-graph case
            return None

    def _check_create_graph_impl(self, *, graph_uri: str) -> bool:

        if self._multigraph:
            name_graph = self._get_graph_impl(graph_uri=graph_uri)

            if name_graph:
                return False

            return self._create_graph_impl(graph_uri=graph_uri)
        else:
            # uni-graph case
            return False

    def _create_graph_impl(self, *, graph_uri: str, enforce_segment: bool = True) -> bool:

        if not self._multigraph:
            # uni-graph case
            return False

        if not isinstance(self.graph, Dataset):
            # enforce multi-graph case
            return False

        if not enforce_segment:
            try:
                new_graph = Graph(identifier=URIRef(graph_uri))
                self.graph.add_graph(new_graph)
            except Exception as e:
                # log exception
                return False
            return True

        if enforce_segment:
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
                # log exception
                return False

        return True

    def _delete_graph_impl(self, *, graph_uri: str, enforce_segment: bool = True) -> bool:

        if not self._multigraph:
            # uni-graph case
            self.graph = Graph()
            return True

        if not enforce_segment:
            # TODO should this leave the graph but just erase all triples?

            if isinstance(self.graph, Dataset):
                self.graph.remove_graph(URIRef(graph_uri))
                return True

        try:
            if isinstance(self.graph, Dataset):
                service_graph = self.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

                # for triple in service_graph.triples((None, None, None)):
                #    print(triple)

                # print(f"Deleting Graph URI: {graph_uri}")

                query = f"""
                   SELECT ?subject
                   WHERE {{
                     ?subject <http://vital.ai/ontology/vital-core#hasSegmentID> "{graph_uri}"^^<http://www.w3.org/2001/XMLSchema#string> .
                   }}
                   """

                # print(query)

                result = service_graph.query(query)

                subject_to_remove = None

                for row in result:
                    # print(row)
                    subject_to_remove = row.subject

                # print(f"Subject to Remove: {subject_to_remove}")

                if subject_to_remove:
                    triples_to_remove = list(service_graph.triples((subject_to_remove, None, None)))
                    for triple in triples_to_remove:
                        print(f"deleting: {triple}")
                        service_graph.remove(triple)

                self.graph.remove_graph(URIRef(graph_uri))

        except Exception as e:
            # log exception
            return False

        return True

    def _purge_graph_impl(self, *, graph_uri: str, enforce_segment: bool = True) -> bool:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        if not self._multigraph:
            # uni-graph case
            self.graph = Graph()
            return True

        if not enforce_segment:
            if isinstance(self.graph, Dataset):
                self.graph.remove_graph(URIRef(graph_uri))
                return True

        try:

            if isinstance(self.graph, Dataset):

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
            # log exception
            return False

        return True

    def _get_graph_all_objects_impl(self, *, graph_uri: str, limit=100, offset=0, enforce_segment: bool = True, safety_check: bool = True) -> ResultList:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        # include limit, offset
        # sort by subject uri
        # count total unique subjects and throw exception if over some number?

        # TODO this should be "not" ?

        if self._multigraph:
            graph = self.graph
        else:
            graph = self.graph.get_graph(URIRef(graph_uri))

        filter_term = ""

        if enforce_segment:

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

            filter_term = f"FILTER(?s != <{subject}>)"

        query = f"""
                CONSTRUCT {{
                    ?s ?p ?o .
                }}
                WHERE {{
                    {{
                        SELECT DISTINCT ?s WHERE {{
                                ?s ?p ?o .
                                {filter_term}
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

    def _insert_object_impl(self, *, graph_object: G, graph_uri: str, enforce_segment: bool = True, safety_check: bool = True) -> VitalGraphStatus:

        # TODO this should be "not" ?

        if self._multigraph:
            graph = self.graph
        else:
            graph = self.graph.get_graph(URIRef(graph_uri))

        graph_object_rdf_data = graph_object.to_rdf()

        graph.parse(data=graph_object_rdf_data, format="nt")

        status = VitalGraphStatus()

        return status

    def _insert_object_list_impl(self, *, graph_object_list: List[G], graph_uri: str, safety_check: bool = True) -> VitalGraphStatus:

        # for graph_object in graph_object_list:
        #    graph_object_rdf_data = graph_object.to_rdf()
        #    graph.parse(data=graph_object_rdf_data, format="nt")

        # combined_rdf_data = ""
        # for graph_object in graph_object_list:
        #    graph_object_rdf_data = graph_object.to_rdf()
        #    combined_rdf_data += graph_object_rdf_data + "\n"

        # Parse the combined RDF data string once
        # graph.parse(data=combined_rdf_data, format="nt")

        if not self._multigraph:
            # todo, confirm this works
            insert_graph = Graph()

            for graph_object in graph_object_list:
                graph_object.add_to_graph(insert_graph)

            with self.lock:
                graph = self.graph
                graph += insert_graph

            status = VitalGraphStatus()
            return status
        else:
            insert_graph = Graph(identifier=URIRef(graph_uri))

            for graph_object in graph_object_list:
                graph_object.add_to_graph(insert_graph)

            with self.lock:

                if isinstance(self.graph, Dataset):
                    graph = self.graph.get_graph(URIRef(graph_uri))
                    graph += insert_graph

            status = VitalGraphStatus()
            return status

    def _update_object_impl(self, *, graph_object: G, graph_uri: str = None, upsert: bool = False, safety_check: bool = True) -> VitalGraphStatus:

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph

        object_uri = str(graph_object.URI)

        # TODO is this right?
        service_graph_object = self._get_object_impl(object_uri=object_uri, graph_uri=graph_uri)

        if service_graph_object is None:
            if upsert is False:
                status = VitalGraphStatus(status=-1, message="Object Not Found")
                return status
        else:
            self._delete_object_impl(object_uri=object_uri, graph_uri=graph_uri)

        self._insert_object_impl(graph_uri=graph_uri, graph_object=graph_object)

        status = VitalGraphStatus()
        return status

    def _update_object_list_impl(self, *, graph_object_list: List[G], graph_uri: str = None, upsert: bool = False,
                                 safety_check: bool = True) -> VitalGraphStatus:

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph

        # check if all objects exist
        if upsert is False:
            all_found = True
            for graph_object in graph_object_list:
                object_uri = str(graph_object.URI)
                service_graph_object = self._get_object_impl(object_uri=object_uri, graph_uri=graph_uri)
                if service_graph_object is None:
                    all_found = False
                    break
            if all_found is False:
                status = VitalGraphStatus(status=-1, message="Not all objects found")
                return status

        for graph_object in graph_object_list:
            object_uri = str(graph_object.URI)
            self._delete_object_impl(object_uri=object_uri, graph_uri=graph_uri)
            self._insert_object_impl(graph_uri=graph_uri, graph_object=graph_object)

        status = VitalGraphStatus()
        return status

    def _get_object_impl(self, *, object_uri: str, graph_uri: str = None, safety_check: bool = True) -> G:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph

        # print(f"Graph URI {graph_uri}")
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
            # log
            print(f"get_object Exception {e}")

        return None

    def _get_object_list_impl(self, *, object_uri_list: List[str], graph_uri: str = None, safety_check: bool = True) -> ResultList:

        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph

        result_list = ResultList()

        for object_uri in object_uri_list:

            subject = URIRef(object_uri)
            triples = graph.triples((subject, None, None))
            graph_object = vs.from_triples(triples)
            result_list.add_result(graph_object)

        return result_list

    def _delete_object_impl(self, *, object_uri: str, graph_uri: str = None, safety_check: bool = True) -> VitalGraphStatus:

        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph

        triples_to_remove = list(graph.triples((URIRef(object_uri), None, None)))

        if len(triples_to_remove) == 0:
            status = VitalGraphStatus(status=-1, message="Object Not Found and Not Deleted")
            return status

        for t in triples_to_remove:
            graph.remove(t)

        status = VitalGraphStatus()

        return status

    def _delete_object_list_impl(self, *, object_uri_list: List[str], graph_uri: str = None, safety_check: bool = True) -> VitalGraphStatus:

        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph

        for object_uri in object_uri_list:

            triples_to_remove = list(graph.triples((URIRef(object_uri), None, None)))

            for t in triples_to_remove:
                graph.remove(t)

        status = VitalGraphStatus()
        return status

    def _filter_query_impl(self, *, graph_uri: str, sparql_query: str, uri_binding='uri', limit: int = 100, offset: int = 0,
                           resolve_objects: bool = True, safety_check: bool = True) -> ResultList:

        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph

        # TODO implement

        result_list = ResultList()
        return result_list

    def _query_impl(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit=100, offset=0, resolve_objects=True,
                    safety_check: bool = True) -> ResultList:

        name_graph = None
        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                name_graph = self.get_graph(graph_uri)
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            graph = self.graph
            # TODO
            result_list = ResultList()
            return result_list

        # if graph_uri is None:
        #    return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # TODO handle uni-graph case, this is for multi-graph:

        # TODO get namespaces dynamically

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
            return self._get_object_list_impl(object_uri_list=object_uri_list, graph_uri=graph_uri)
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

    def _query_construct_impl(self, *, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                              binding_list: List[Binding], limit=100, offset=0, safety_check: bool = True,
                              ) -> ResultList:

        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
                # exception if graph doesn't exist
                name_graph = self._get_graph_impl(graph_uri=graph_uri)
        else:
            graph = self.graph

        # TODO handle uni-graph case

        if graph_uri is None:
            result_list = ResultList()
            result_list.set_status(-1)
            result_list.set_message("Error: graph_uri is not set.")
            return result_list

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

        # TODO clean up query, adjust ordering, limit/offset

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
            ORDER BY {order_by_section}
            LIMIT {limit}
            OFFSET {offset}
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

    def _query_construct_solution_impl(self, *, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                                       binding_list: List[Binding], root_binding: str | None = None, limit=100, offset=0,
                                       resolve_objects: bool = True,
                                       safety_check: bool = True) -> SolutionList:

        from vital_ai_vitalsigns.collection.graph_collection import GraphCollection

        graph = None

        if self._multigraph:
            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))
        else:
            # TODO handle uni-graph case
            graph = self.graph
            solution_list = SolutionList([], limit, offset)
            return solution_list

        # object cache to use during query
        graph_collection = GraphCollection(use_rdfstore=False, use_vectordb=False)

        result_list = self._query_construct_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            namespace_list=namespace_list,
            binding_list=binding_list,
            limit=limit, offset=offset)

        result_graph = Graph()

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
                    result_graph.add((URIRef(str(s)), URIRef(str(p)), URIRef(str(o))))
                else:
                    result_graph.add((URIRef(str(s)), URIRef(str(p)), Literal(str(o))))

        solutions = []

        unique_subjects = set(result_graph.subjects())

        for subject in unique_subjects:

            uri_map = {}
            obj_map = {}

            root_binding_obj = None

            triples = set(result_graph.triples((subject, None, None)))

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
                            binding_obj = self._get_object_impl(object_uri=str(o), graph_uri=graph_uri)
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

    def _export_ntriples_impl(self, file_path: str, *,
                              graph_uri=None,
                              enforce_segment=True,
                              overwrite=True) -> bool:

        # TODO MemoryGraphService not switched to use multi-graph yet
        # so triples end up in the global graph and not the per segment graph


        # TODO temp override for testing
        enforce_segment = False

        print(f"Exporting: graph_uri {graph_uri}")
        print(f"Exporting: enforce_segment {enforce_segment}")
        print(f"Exporting: overwrite {overwrite}")

        print(f"Exporting: into {file_path}")

        if os.path.exists(file_path):
            if overwrite is False:
                print(f"Exporting canceled. File path exists and overwrite is false.")
                return False

        if enforce_segment:

            if not graph_uri:
                print(f"Exporting canceled. Segment is enforced but graph_uri is not set.")
                return False

            try:

                # TODO do this without copying graph
                # Exclude triples from the segment

                graph = self.graph.get_graph(URIRef(graph_uri))

                source_graph_triple_count = len(graph)

                print(f"Exporting: source_graph_triple_count {source_graph_triple_count}")

                # for s, p, o in graph:
                #    print(f"Exporting: s {s} p {p} o {o}")

                query = f"""
                        SELECT ?subject
                            WHERE {{
                                ?subject <http://vital.ai/ontology/vital-core#hasSegmentID> "{graph_uri}"^^<http://www.w3.org/2001/XMLSchema#string> .
                            }}
                """

                result = graph.query(query)

                subject = None

                # should be exactly one

                for row in result:
                    # print(row)
                    subject = row.subject

                    if not subject:
                        print(f"Exporting: failed.  Segment not found in source graph.")
                        return False

                    original_triples = graph.triples

                    # temp patch to skip the segment triples
                    def filtered_triples(pattern=None):
                        # If no pattern is provided, use the default (None, None, None).
                        if pattern is None:
                            pattern = (None, None, None)
                        # Iterate over all triples using the original method.
                        for triple in original_triples(pattern):
                            # If the subject matches the one to ignore, skip this triple.
                            if triple[0] == subject:
                                continue
                            yield triple

                    graph.triples = filtered_triples

                    # new_graph = Graph()
                    # for s, p, o in graph:
                    #    if s != subject:
                    #        new_graph.add((s, p, o))

                    triple_count = len(graph)

                    print(f"Exporting: triple_count {triple_count}")

                    with open(file_path, 'wb') as f:
                        graph.serialize(destination=f, format='nt', encoding='utf-8')

                    graph.triples = original_triples

                    return True

            except Exception as e:
                print(f"Export Exception {e}")

        else:

            if self._multigraph:
                if graph_uri is not None:
                    if isinstance(self.graph, Dataset):
                        graph = self.graph.get_graph(URIRef(graph_uri))
                else:
                    print(f"Export canceled. Multigraph but graph_uri is not set.")
                    return False
            else:
                graph = self.graph


            # TODO temp override for test

            graph = self.graph

            triple_count = len(graph)

            print(f"Exporting: triple_count {triple_count}")

            with open(file_path, 'wb') as f:
                graph.serialize(destination=f, format='nt', encoding='utf-8')
            return True

        print(f"Exporting failed.")

        return False

    def _import_ntriples_impl(self, file_path: str, *,
                              graph_uri=None,
                              enforce_segment=True) -> bool:

        graph = None

        if enforce_segment:

            if not graph_uri:
                print(f"Importing canceled. Segment is enforced but graph_uri is not set.")
                return False

            print(f"Importing: {graph_uri}")

            print(f"Purging: {graph_uri}")

            self._purge_graph_impl(graph_uri=graph_uri)

            print(f"Importing: {graph_uri} from file: {file_path}")

            if isinstance(self.graph, Dataset):
                graph = self.graph.get_graph(URIRef(graph_uri))

            try:
                graph.parse(source=file_path, format='nt')
                print(f"Imported: {graph_uri} with Triple Count: {len(graph)}")
                return True
            except Exception as e:
                print(f"Import Exception {e}")
        else:
            if self._multigraph:
                if graph_uri is not None:
                    if isinstance(self.graph, Dataset):
                        graph = self.graph.get_graph(URIRef(graph_uri))
                else:
                    print(f"Importing canceled. Multigraph but graph_uri is not set.")
                    return False
            else:
                graph = self.graph

            graph.remove((None, None, None))
            graph.parse(source=file_path, format='nt')
            print(f"File Path: {file_path} with Triple Count: {len(graph)}")
            return True

        print(f"Importing: {graph_uri} failed.")

        return False
