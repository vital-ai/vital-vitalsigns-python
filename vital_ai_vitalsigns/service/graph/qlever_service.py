from typing import List

from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery, SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.metaql_result import MetaQLResult
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService, G
from vital_ai_vitalsigns.service.graph.name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus


class QLeverGraphService(VitalGraphService):

    # TODO implement when name graph functionality in QLever is complete
    # TODO and when sparql update implementation is merged in

    def __init__(self, username: str | None = None, password: str | None = None, endpoint: str | None = None, **kwargs):
        self.username = username
        self.password = password
        self.endpoint = endpoint.rstrip('/')
        super().__init__(**kwargs)

    def list_graph_uris(self, *,
                    safety_check: bool = True) -> List[str]:
        return []

    def initialize_service(self) -> bool:
        return True

    def destroy_service(self) -> bool:
        return True

    def get_graph(self, graph_uri: str, *, safety_check: bool = True) -> VitalNameGraph:
        pass

    def list_graphs(self, *, safety_check: bool = True) -> List[VitalNameGraph]:
        pass

    def check_create_graph(self, graph_uri: str, *, safety_check: bool = True) -> bool:
        pass

    def create_graph(self, graph_uri: str, *, safety_check: bool = True) -> bool:
        pass

    def delete_graph(self, graph_uri: str, *, safety_check: bool = True) -> bool:
        pass

    def purge_graph(self, graph_uri: str, *, safety_check: bool = True) -> bool:
        pass

    def get_graph_all_objects(self, graph_uri: str, *, limit=100, offset=0, safety_check: bool = True,
                              vital_managed=True) -> ResultList:
        pass

    def insert_object(self, graph_uri: str, graph_object: G, *, safety_check: bool = True) -> VitalGraphStatus:
        pass

    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], *, safety_check: bool = True) -> VitalGraphStatus:
        pass

    def update_object(self, graph_object: G, *, graph_uri: str = None, upsert: bool = False, safety_check: bool = True) -> VitalGraphStatus:
        pass

    def update_object_list(self, graph_object_list: List[G], *, graph_uri: str = None, upsert: bool = False,
                           safety_check: bool = True) -> VitalGraphStatus:
        pass

    def get_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True) -> G:
        pass

    def get_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True) -> ResultList:
        pass

    def delete_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True) -> VitalGraphStatus:
        pass

    def delete_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True) -> VitalGraphStatus:
        pass

    def filter_query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit: int = 100, offset: int = 0,
                     resolve_objects: bool = True, safety_check: bool = True) -> ResultList:
        pass

    def query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit=100, offset=0, resolve_objects=True,
              safety_check: bool = True) -> ResultList:
        pass

    def query_construct(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                        binding_list: List[Binding], *, limit=100, offset=0, safety_check: bool = True) -> ResultList:
        pass

    def query_construct_solution(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                                 binding_list: List[Binding], root_binding: str | None = None, *, limit=100, offset=0,
                                 resolve_objects: bool = True,
                                 safety_check: bool = True) -> SolutionList:
        pass

    def metaql_select_query(self, *, namespace: str = None, select_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology]) -> MetaQLResult:
        pass

    def metaql_graph_query(self, *, namespace: str = None, graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology]) -> MetaQLResult:
        pass
