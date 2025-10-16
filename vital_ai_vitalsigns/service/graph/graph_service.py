from abc import abstractmethod, ABC
from typing import TypeVar, List

from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery

from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.metaql_result import MetaQLResult
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator
from vital_ai_vitalsigns.service.graph.graph_service_status import GraphServiceStatus
from vital_ai_vitalsigns.service.vital_name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus

from vital_ai_vitalsigns.config.vitalsigns_config import GraphDatabaseConfig

G = TypeVar('G', bound='GraphObject')


class VitalGraphService(ABC):
    def __init__(self, config: GraphDatabaseConfig, **kwargs):
        self.config = config
        self.base_uri = kwargs.get('base_uri')
        self.namespace = kwargs.get('namespace')
        super().__init__()

    def get_graph_uri(self, *,
                      name_graph: VitalNameGraph = None,
                      graph_id: str|None = None,
                      account_id: str|None = None,
                      is_global: bool = False) -> str | None:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = None

        if name_graph:
            graph_id = name_graph.get_graph_id()
            account_id = name_graph.get_account_id()
            is_global = name_graph.is_global()

        # print(f"is_global: {is_global}")

        if is_global is True or is_global == 1:
            if account_id:
                graph_uri = f"{base_uri}/{namespace}/GLOBAL/{account_id}/{graph_id}"
            else:
                graph_uri = f"{base_uri}/{namespace}/GLOBAL/{graph_id}"
        else:
            if account_id:
                graph_uri = f"{base_uri}/{namespace}/{account_id}/{graph_id}"
            else:
                graph_uri = f"{base_uri}/{namespace}/{graph_id}"

        return graph_uri

    def get_name_graph(self, graph_uri: str) -> VitalNameGraph:

        base_uri = self.base_uri
        namespace = self.namespace

        print(f"graph_uri: {graph_uri}")
        print(f"base_uri: {base_uri}")
        print(f"namespace: {namespace}")

        if not graph_uri.startswith(f"{base_uri}/{namespace}"):
            raise ValueError("The URI does not match the given base_uri and namespace.")

        components = graph_uri[len(f"{base_uri}/{namespace}/"):].split('/')

        result = {
            "base_uri": base_uri,
            "namespace": namespace,
            "graph_id": None,
            "account_id": None,
            "global_symbol": None,
        }

        if len(components) == 1:
            # Pattern: base_uri / namespace / graph_id
            result["graph_id"] = components[0]
        elif len(components) == 2 and components[0] == "GLOBAL":
            # Pattern: base_uri / namespace / GLOBAL / graph_id
            result["global_symbol"] = components[0]
            result["graph_id"] = components[1]
        elif len(components) == 2:
            # Pattern: base_uri / namespace / account_id / graph_id
            result["account_id"] = components[0]
            result["graph_id"] = components[1]
        elif len(components) == 3 and components[0] == "GLOBAL":
            # Pattern: base_uri / namespace / GLOBAL / account_id / graph_id
            result["global_symbol"] = components[0]
            result["account_id"] = components[1]
            result["graph_id"] = components[2]
        else:
            raise ValueError("The URI does not match any known pattern.")

        is_global = False
        graph_id = None
        account_id = None

        if result["global_symbol"]:
            is_global = True

        if result["graph_id"]:
            graph_id = result["graph_id"]

        if result["account_id"]:
            account_id = result["account_id"]

        name_graph = VitalNameGraph(
            graph_uri,
            graph_id=graph_id,
            account_id=account_id,
            is_global=is_global,
        )

        return name_graph

    @abstractmethod
    def list_graph_uris(self, *,
                        safety_check: bool = True) -> List[str]:
        pass

    @abstractmethod
    def service_info(self) -> dict:
        pass

    @abstractmethod
    def service_status(self) -> GraphServiceStatus:
        pass


    # initialize, create vital service graph
    @abstractmethod
    def initialize_service(self) -> bool:
        pass

    # destroy vital service graph and all associated graphs
    @abstractmethod
    def destroy_service(self) -> bool:
        pass

    @abstractmethod
    def is_graph_global(self, graph_id: str, *,
                        account_id: str|None = None) -> bool:
        pass

    @abstractmethod
    def get_graph(self, graph_id: str, *,
                  global_graph: bool = False,
                  account_id: str|None = None,
                  safety_check: bool = True) -> VitalNameGraph:
        pass

    @abstractmethod
    def list_graphs(self, *,
                    account_id: str | None = None,
                    include_global: bool = True,
                    include_private: bool = True,
                    safety_check: bool = True) -> List[VitalNameGraph]:
        pass

    # create graph
    # store name graph in vital service graph and in the graph itself
    # a graph needs to have some triples in it to exist

    @abstractmethod
    def check_create_graph(self, graph_id: str, *,
                           global_graph: bool = False,
                           account_id: str|None = None,
                           safety_check: bool = True) -> bool:
        pass

    @abstractmethod
    def create_graph(self, graph_id: str, *,
                     global_graph: bool = False,
                     account_id: str|None = None,
                     safety_check: bool = True) -> bool:
        pass

    # delete graph
    # delete graph itself plus record in vital service graph

    @abstractmethod
    def delete_graph(self, graph_id: str, *,
                     global_graph: bool = False,
                     account_id: str|None = None,
                     safety_check: bool = True) -> bool:
        pass

    # purge graph (delete all but name graph)

    @abstractmethod
    def purge_graph(self, graph_id: str, *,
                    global_graph: bool = False,
                    account_id: str|None = None,
                    safety_check: bool = True) -> bool:
        pass

    @abstractmethod
    def get_graph_all_objects(self, graph_id: str, *,
                              global_graph: bool = False,
                              account_id: str|None = None,
                              limit=100,
                              offset=0,
                              safety_check: bool = True) -> ResultList:
        pass

    # insert object into graph (scoped to vital service graph uri, which must exist)

    # insert object list into graph (scoped to vital service graph uri, which must exist)

    @abstractmethod
    def insert_object(self, graph_id: str, graph_object: G, *,
                      global_graph: bool = False,
                      account_id: str|None = None,
                      safety_check: bool = True) -> VitalGraphStatus:
        pass

    @abstractmethod
    def insert_object_list(self, graph_id: str, graph_object_list: List[G], *,
                           global_graph: bool = False,
                           account_id: str|None = None,
                           safety_check: bool = True) -> VitalGraphStatus:
        pass

    # update object into graph (scoped to vital service graph uri, which must exist)
    # delete old, replace with new

    # update object list into graph (scoped to vital service graph uri, which must exist)
    # delete old, replace with new

    @abstractmethod
    def update_object(self, graph_object: G, *,
                      graph_id: str = None,
                      global_graph: bool = False,
                      account_id: str|None = None,
                      upsert: bool = False,
                      safety_check: bool = True) -> VitalGraphStatus:
        pass

    @abstractmethod
    def update_object_list(self, graph_object_list: List[G], *,
                           graph_id: str = None,
                           global_graph: bool = False,
                           account_id: str|None = None,
                           upsert: bool = False,
                           safety_check: bool = True) -> VitalGraphStatus:
        pass

    # get object (scoped to all vital service graphs)

    # get object (scoped to specific graph, or graph list)

    # get objects by uri list (scoped to all vital service graphs)

    # get objects by uri list (scoped to specific graph, or graph list)

    @abstractmethod
    def get_object(self, object_uri: str, *,
                   graph_id: str = None,
                   global_graph: bool = False,
                   account_id: str|None = None,
                   safety_check: bool = True) -> G:
        pass

    @abstractmethod
    def get_object_list(self, object_uri_list: List[str], *,
                        graph_id: str = None,
                        global_graph: bool = False,
                        account_id: str|None = None,
                        safety_check: bool = True) -> ResultList:
        pass

    # delete uri (scoped to all vital service graphs)

    # delete uri list (scoped to all vital service graphs)

    # delete uri (scoped to graph or graph list)

    # delete uri list (scoped to graph or graph list)

    @abstractmethod
    def delete_object(self, object_uri: str, *,
                      graph_id: str = None,
                      global_graph: bool = False,
                      account_id: str|None = None,
                      safety_check: bool = True) -> VitalGraphStatus:
        pass

    @abstractmethod
    def delete_object_list(self, object_uri_list: List[str], *,
                           graph_id: str = None,
                           global_graph: bool = False,
                           account_id: str|None = None,
                           safety_check: bool = True) -> VitalGraphStatus:
        pass

    # filter graph

    @abstractmethod
    def filter_query(self, graph_id: str, sparql_query: str, uri_binding='uri', *,
                     limit: int = 100,
                     offset: int = 0,
                     global_graph: bool = False,
                     account_id: str|None = None,
                     resolve_objects: bool = True,
                     safety_check: bool = True) -> ResultList:
        pass

    # query graph

    @abstractmethod
    def query(self, graph_id: str, sparql_query: str, uri_binding='uri', *,
              limit=100,
              offset=0,
              global_graph: bool = False,
              account_id: str|None = None,
              resolve_objects=True,
              safety_check: bool = True) -> ResultList:
        pass

    @abstractmethod
    def query_construct(self, graph_id: str, sparql_query: str,
                        namespace_list: List[Ontology],
                        binding_list: List[Binding], *,
                        limit=100, offset=0,
                        global_graph: bool = False,
                        account_id: str|None = None,
                        safety_check: bool = True) -> ResultList:
        pass

    @abstractmethod
    def query_construct_solution(self,
                                 graph_id: str,
                                 sparql_query: str,
                                 namespace_list: List[Ontology],
                                 binding_list: List[Binding],
                                 root_binding: str | None = None, *,
                                 limit=100, offset=0,
                                 global_graph: bool = False,
                                 account_id: str|None = None,
                                 resolve_objects: bool = True,
                                 safety_check: bool = True) -> SolutionList:
        pass

    @abstractmethod
    def metaql_select_query(self, *,
                            select_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology],
                            account_id: str|None = None, is_global: bool = False) -> MetaQLResult:
        pass

    @abstractmethod
    def metaql_graph_query(self, *,
                           graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology],
                           account_id: str|None = None, is_global: bool = False) -> MetaQLResult:
        pass

    #################################################
    # Import Functions

    @abstractmethod
    def import_graph_batch(self, graph_id: str, object_generator: GraphObjectGenerator,
                           *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           purge_first: bool = True, batch_size: int = 10_000):
        pass

    @abstractmethod
    def import_graph_batch_file(self, graph_id: str, file_path: str,
                                *,
                                global_graph: bool = False,
                                account_id: str | None = None,
                                purge_first: bool = True, batch_size: int = 10_000):
        pass


    # multi-graph cases use graph id from the objects
    # optionally use account id in objects also
    @abstractmethod
    def import_multi_graph_batch(self, object_generator: GraphObjectGenerator,
                                 *,
                                 use_account_id: bool = True,
                                 purge_first: bool = True, batch_size: int = 10_000):
        pass

    @abstractmethod
    def import_multi_graph_batch_file(self, file_path: str,
                                     *,
                                     use_account_id: bool = True,
                                     purge_first: bool = True, batch_size: int = 10_000):
        pass



