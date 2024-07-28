from abc import abstractmethod
from typing import TypeVar, List, Tuple
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.graph.name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus

G = TypeVar('G', bound='GraphObject')


class VitalGraphService:
    def __init__(self):
        # check_create vital service graph
        pass

    # initialize, create vital service graph if necessary

    @abstractmethod
    def get_graph(self, graph_uri: str, *, vital_managed=True) -> VitalNameGraph:
        pass

    @abstractmethod
    def list_graphs(self, *, vital_managed=True) -> List[VitalNameGraph]:
        pass

    # create graph
    # store name graph in vital service graph and in the graph itself
    # a graph needs to have some triples in it to exist

    @abstractmethod
    def check_create_graph(self, graph_uri: str, *, vital_managed=True) -> bool:
        pass

    @abstractmethod
    def create_graph(self, graph_uri: str, *, vital_managed=True) -> bool:
        pass

    # delete graph
    # delete graph itself plus record in vital service graph

    @abstractmethod
    def delete_graph(self, graph_uri: str, *, vital_managed=True) -> bool:
        pass

    # purge graph (delete all but name graph)

    @abstractmethod
    def purge_graph(self, graph_uri: str, *, vital_managed=True) -> bool:
        pass

    @abstractmethod
    def get_graph_all_objects(self, graph_uri: str, *, limit=100, offset=0, safety_check: bool = True, vital_managed=True) -> ResultList:
        pass

    # insert object into graph (scoped to vital service graph uri, which must exist)

    # insert object list into graph (scoped to vital service graph uri, which must exist)

    @abstractmethod
    def insert_object(self, graph_uri: str, graph_object: G, *, safety_check: bool = True, vital_managed=True) -> VitalGraphStatus:
        pass

    @abstractmethod
    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], *, safety_check: bool = True, vital_managed=True) -> VitalGraphStatus:
        pass

    # update object into graph (scoped to vital service graph uri, which must exist)
    # delete old, replace with new

    # update object list into graph (scoped to vital service graph uri, which must exist)
    # delete old, replace with new

    @abstractmethod
    def update_object(self, graph_object: G, *, graph_uri: str = None, upsert: bool = False, safety_check: bool = True, vital_managed: bool = True) -> VitalGraphStatus:
        pass

    @abstractmethod
    def update_object_list(self, graph_object_list: List[G], *, graph_uri: str = None, upsert: bool = False, safety_check: bool = True, vital_managed: bool = True) -> VitalGraphStatus:
        pass

    # get object (scoped to all vital service graphs)

    # get object (scoped to specific graph, or graph list)

    # get objects by uri list (scoped to all vital service graphs)

    # get objects by uri list (scoped to specific graph, or graph list)

    @abstractmethod
    def get_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True, vital_managed: bool = True) -> G:
        pass

    @abstractmethod
    def get_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True, vital_managed: bool = True) -> ResultList:
        pass

    # delete uri (scoped to all vital service graphs)

    # delete uri list (scoped to all vital service graphs)

    # delete uri (scoped to graph or graph list)

    # delete uri list (scoped to graph or graph list)

    @abstractmethod
    def delete_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True, vital_managed: bool = True) -> VitalGraphStatus:
        pass

    @abstractmethod
    def delete_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True, vital_managed: bool = True) -> VitalGraphStatus:
        pass

    # filter graph

    @abstractmethod
    def filter_query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit: int = 100, offset: int = 0, resolve_objects: bool = True, safety_check: bool = True, vital_managed: bool = True) -> ResultList:
        pass

    # query graph

    @abstractmethod
    def query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit=100, offset=0, resolve_objects=True, safety_check: bool = True, vital_managed=True) -> ResultList:
        pass

    @abstractmethod
    def query_construct(self, graph_uri: str, sparql_query: str,
                        namespace_list: List[Ontology],
                        binding_list: List[Binding], *,
                        limit=100, offset=0,
                        safety_check: bool = True, vital_managed: bool = True) -> ResultList:
        pass

    @abstractmethod
    def query_construct_solution(self,
                                 graph_uri: str,
                                 sparql_query: str,
                                 namespace_list: List[Ontology],
                                 binding_list: List[Binding],
                                 root_binding: str | None = None, *,
                                 limit=100, offset=0,
                                 safety_check: bool = True, vital_managed: bool = True) -> SolutionList:
        pass







