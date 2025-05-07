import os
from typing import List
from rdflib import Dataset, URIRef, Graph, Literal
from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.impl.rdflib.rdflib_sparql_impl import RDFlibSparqlImpl
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery, SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.metaql_result import MetaQLResult
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution import Solution
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding, BindingValueType
from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService, G
from vital_ai_vitalsigns.service.graph.graph_service_status import GraphServiceStatus, GraphServiceStatusType
from vital_ai_vitalsigns.service.graph.name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus
from vital_ai_vitalsigns.service.graph.graph_service_constants import VitalGraphServiceConstants
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.RDFStatement import RDFStatement
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment


class MemoryGraphService(VitalGraphService, RDFlibSparqlImpl):

    def __init__(self, **kwargs):

        super().__init__(multigraph=True, **kwargs)

        # init service graph, domain ontology graph

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

    def service_status(self) -> GraphServiceStatus:

        status_type = GraphServiceStatusType.READY

        status = GraphServiceStatus(status_type)

        return status

    def service_info(self) -> dict:

        service_info = {}

        return service_info

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

        return self._export_ntriples_impl(graph_uri=graph_uri, file_path=file_path, overwrite=overwrite)

    def import_ntriples(self, graph_uri: str, file_path: str) -> bool:

        return self._import_ntriples_impl(graph_uri=graph_uri, file_path=file_path)

    def list_graph_uris(self, *,
                    safety_check: bool = True) -> List[str]:
        return []

    def initialize_service(self) -> bool:
        return True

    def destroy_service(self) -> bool:
        return True

    def list_graphs(self, *,
                    account_id: str | None = None,
                    include_global: bool = True,
                    include_private: bool = True,
                    safety_check: bool = True) -> List[VitalNameGraph]:

        return self._list_graphs_impl()

    def get_graph(self, graph_uri: str, *,
                  account_id: str | None = None,
                  include_global: bool = True,
                  include_private: bool = True,
                  safety_check: bool = True) -> VitalNameGraph:

        return self._get_graph_impl(graph_uri=graph_uri)

    def check_create_graph(self, graph_uri: str, *,
                           account_id: str | None = None,
                           include_global: bool = True,
                           include_private: bool = True,
                           safety_check: bool = True) -> bool:

        return self._check_create_graph_impl(graph_uri=graph_uri)

    def create_graph(self, graph_uri: str, *, global_graph: bool = False,
                     account_id: str|None = None, safety_check: bool = True) -> bool:

        return self._create_graph_impl(graph_uri=graph_uri)

    def delete_graph(self, graph_uri: str, *,
                     account_id: str | None = None,
                     include_global: bool = True,
                     include_private: bool = True,
                     safety_check: bool = True) -> bool:

        return self._delete_graph_impl(graph_uri=graph_uri)

    def purge_graph(self, graph_uri: str, *,
                    account_id: str | None = None,
                    global_graph: bool = False,
                    include_private: bool = True,
                    safety_check: bool = True) -> bool:

        return self._purge_graph_impl(graph_uri=graph_uri)

    def get_graph_all_objects(self, graph_uri: str, *,
                              account_id: str | None = None,
                              global_graph: bool = False,
                              include_private: bool = True,
                              limit=100, offset=0, safety_check: bool = True) -> ResultList:

        return self._get_graph_all_objects_impl(graph_uri=graph_uri, limit=limit, offset=offset, safety_check=safety_check)

    def insert_object(self, graph_uri: str, graph_object: G, *,
                      account_id: str | None = None,
                      include_global: bool = True,
                      include_private: bool = True,
                      safety_check: bool = True) -> VitalGraphStatus:

        return self._insert_object_impl(graph_uri=graph_uri, graph_object=graph_object, safety_check=safety_check)

    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], *,
                           account_id: str | None = None,
                           include_global: bool = True,
                           include_private: bool = True,
                           safety_check: bool = True) -> VitalGraphStatus:

        return self._insert_object_list_impl(graph_uri=graph_uri, graph_object_list=graph_object_list, safety_check=safety_check)

    def update_object(self, graph_object: G, *,
                      graph_id: str = None, upsert: bool = False,
                      account_id: str | None = None,
                      global_graph: bool = False,
                      include_private: bool = True,
                      safety_check: bool = True) -> VitalGraphStatus:

        return self._update_object_impl(graph_object=graph_object, graph_uri=graph_id, upsert=upsert, safety_check=safety_check)

    def update_object_list(self, graph_object_list: List[G], *,
                           graph_id: str = None, upsert: bool = False,
                           account_id: str | None = None,
                           global_graph: bool = False,
                           include_private: bool = True,
                           safety_check: bool = True) -> VitalGraphStatus:

        return self._update_object_list_impl(graph_object_list=graph_object_list, graph_uri=graph_id, upsert=upsert, safety_check=safety_check)

    def get_object(self, object_uri: str, *, graph_uri: str = None,
                   account_id: str | None = None,
                   include_global: bool = True,
                   include_private: bool = True,
                   safety_check: bool = True) -> G:

        return self._get_object_impl(object_uri=object_uri, graph_uri=graph_uri, safety_check=safety_check)

    def get_object_list(self, object_uri_list: List[str], *,
                        account_id: str | None = None,
                        include_global: bool = True,
                        include_private: bool = True,
                        graph_uri: str = None, safety_check: bool = True) -> ResultList:

        return self._get_object_list_impl(object_uri_list=object_uri_list, graph_uri=graph_uri, safety_check=safety_check)

    def delete_object(self, object_uri: str, *, graph_uri: str = None,
                      account_id: str | None = None,
                      include_global: bool = True,
                      include_private: bool = True,
                      safety_check: bool = True) -> VitalGraphStatus:

        return self._delete_object_impl(object_uri=object_uri, graph_uri=graph_uri, safety_check=safety_check)

    def delete_object_list(self, object_uri_list: List[str], *, graph_uri: str = None,
                           account_id: str | None = None,
                           include_global: bool = True,
                           include_private: bool = True,
                           safety_check: bool = True) -> VitalGraphStatus:

        return self._delete_object_list_impl(object_uri_list=object_uri_list, graph_uri=graph_uri, safety_check=safety_check)

    def filter_query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit: int = 100, offset: int = 0,
                     resolve_objects: bool = True,
                     account_id: str | None = None,
                     include_global: bool = True,
                     include_private: bool = True,
                     safety_check: bool = True) -> ResultList:

        return self._filter_query_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            uri_binding=uri_binding,
            limit=limit,
            offset=offset,
            resolve_objects=resolve_objects,
            safety_check=safety_check)

    def query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *,
              account_id: str | None = None,
              include_global: bool = True,
              include_private: bool = True,
              limit=100, offset=0, resolve_objects=True,
              safety_check: bool = True) -> ResultList:

        return self._query_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            uri_binding=uri_binding,
            limit=limit,
            offset=offset,
            resolve_objects=resolve_objects,
            safety_check=safety_check)

    def query_construct(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                        binding_list: List[Binding], *,
                        account_id: str | None = None,
                        include_global: bool = True,
                        include_private: bool = True,
                        limit=100, offset=0, safety_check: bool = True) -> ResultList:

        return self._query_construct_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            namespace_list=namespace_list,
            binding_list=binding_list,
            limit=limit,
            offset=offset,
            safety_check=safety_check)

    def query_construct_solution(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                                 binding_list: List[Binding], root_binding: str | None = None, *,
                                 account_id: str | None = None,
                                 include_global: bool = True,
                                 include_private: bool = True,
                                 limit=100, offset=0,
                                 resolve_objects: bool = True,
                                 safety_check: bool = True) -> SolutionList:

        return self._query_construct_solution_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            namespace_list=namespace_list,
            binding_list=binding_list,
            root_binding=root_binding,
            limit=limit,
            offset=offset,
            resolve_objects=resolve_objects,
            safety_check=safety_check)

    def metaql_select_query(self, *, namespace: str = None, select_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology]) -> MetaQLResult:
        pass

    def metaql_graph_query(self, *, namespace: str = None, graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology]) -> MetaQLResult:
        pass

    def is_graph_global(self, graph_id: str, *,
                        account_id: str | None = None) -> bool:

        pass

    def import_graph_batch(self, graph_id: str, object_generator: GraphObjectGenerator,
                           *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           purge_first: bool = True, batch_size: int = 10_000):
        pass

    def import_graph_batch_file(self, graph_id: str, file_path: str,
                                *,
                                global_graph: bool = False,
                                account_id: str | None = None,
                                purge_first: bool = True, batch_size: int = 10_000):
        pass

    def import_multi_graph_batch(self, object_generator: GraphObjectGenerator,
                                 *,
                                 purge_first: bool = True,
                                 use_account_id: bool = True,
                                 batch_size: int = 10_000):
        pass

    def import_multi_graph_batch_file(self, file_path: str,
                                     *,
                                     purge_first: bool = True,
                                     use_account_id: bool = True,
                                     batch_size: int = 10_000):
        pass

