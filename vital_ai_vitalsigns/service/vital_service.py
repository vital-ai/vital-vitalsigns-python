from typing import List, TypeVar, Dict, Optional

from vital_ai_vitalsigns.metaql.metaql_result_list import MetaQLResultList
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.metaql_result import MetaQLResult
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.base_service import BaseService
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService
from vital_ai_vitalsigns.service.vector.vector_service import VitalVectorService
from vital_ai_vitalsigns.service.vital_namespace import VitalNamespace
from vital_ai_vitalsigns.service.vital_service_status import VitalServiceStatus

from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery

import threading
import time

G = TypeVar('G', bound=Optional['GraphObject'])

# TODO
# have top-level namespace so multiple vital services can co-exist


class VitalService(BaseService):
    def __init__(self,
                 vitalservice_name: str = None,
                 vitalservice_namespace: str = None,
                 graph_service: VitalGraphService = None,
                 vector_service: VitalVectorService = None,
                 synchronize_service=True,
                 synchronize_task=True):
        self.vitalservice_name = vitalservice_name
        self.vitalservice_namespace = vitalservice_namespace
        self.graph_service = graph_service
        self.vector_service = vector_service
        self.graph_info_lock = threading.RLock()
        self.background_thread = None
        self.running = False
        if synchronize_service:
            self.synchronize_service()
        if synchronize_task:
            self.start()

    def get_vitalservice_name(self) -> str:
        return self.vitalservice_name

    def get_vitalservice_namespace(self) -> str:
        return self.vitalservice_namespace

    def query_graph_info(self):
        # put query to graph service and vector server here
        # refresh info about graphs and collections every N seconds

        # this mainly will remove access to graphs and collections
        # that no longer exist because someone else deleted them

        # if graphs are added, then we can add them into the current set
        # of graphs since no extra metadata is needed

        # if collections are added and the metadata is found in the
        # vital service collection, then these can be added into
        # the current collections as well
        # if metadata is not found, such as the case when custom schema
        # is defined but not stored into the vital service collection
        # then that collection is not accessible

        # ensure access to graph info from background task
        with self.graph_info_lock:
            pass

    def background_task(self):
        while self.running:
            self.query_graph_info()
            time.sleep(60)

    def start(self):
        if not self.running:
            self.running = True
            self.background_thread = threading.Thread(target=self.background_task, daemon=True)
            self.background_thread.start()

    def stop(self):
        if self.running:
            self.running = False
            if self.background_thread:
                self.background_thread.join()
                self.background_thread = None

    def is_running(self):
        return self.running

    # wrap combination of a vector store and graph store
    # or graph store individually or vector store individually

    # namespace primarily uses graph URI with vector namespace derived from this

    # graph store has separate graph to track the namespaces
    # vector store has separate collection to track the collections
    # each collection has its own set of tenants
    # cache the collection to tenant info to help knowing when to
    # add a tenant to a collection

    # starting from empty, get the vital managed graphs and
    # vital managed collections
    def synchronize_service(self):

        service_map = {}

        # ensure access to graph info from background task
        with self.graph_info_lock:
            return service_map

    # check for existing vital service graph, vital service collection
    # and vital managed graphs and collections
    # if delete is True, delete these
    # if delete is False and these are present, return exception
    # create new vital service graph and vital service collection

    def initialize_service(self, delete_service=False, delete_index=False):

        service_map = {}

        # ensure access to graph info from background task
        with self.graph_info_lock:
            return service_map

    def get_service_info(self):

        service_map = {}

        # ensure access to graph info from background task
        with self.graph_info_lock:
            return service_map

    # use for debugging, testing
    # check the underlying service endpoints with additional logging
    def inspect_service(self) -> Dict:

        service_map = {}

        # ensure access to graph info from background task
        with self.graph_info_lock:
            return service_map

    def get_graph(self, graph_uri: str) -> VitalNamespace:

        name_graph = self.graph_service.get_graph(graph_uri)

        namespace = VitalNamespace(name_graph.get_graph_uri())

        return namespace

    def list_graphs(self) -> List[VitalNamespace]:

        name_graph_list = self.graph_service.list_graphs()

        namespace_list = []

        for name_graph in name_graph_list:
            namespace = VitalNamespace(name_graph.get_graph_uri())
            namespace_list.append(namespace)

        return namespace_list

    # create graph
    # store name graph in vital service graph and in the graph itself
    # a graph needs to have some triples in it to exist

    def check_create_graph(self, graph_uri: str) -> bool:
        return self.graph_service.check_create_graph(graph_uri)

    def create_graph(self, graph_uri: str) -> bool:
        return self.graph_service.create_graph(graph_uri)

    # delete graph
    # delete graph itself plus record in vital service graph

    def delete_graph(self, graph_uri: str, *, update_index: bool = True) -> bool:
        return self.graph_service.delete_graph(graph_uri)

    # purge graph (delete all but name graph)

    def purge_graph(self, graph_uri: str, *, update_index: bool = True) -> bool:
        return self.graph_service.purge_graph(graph_uri)

    def get_graph_all_objects(self, graph_uri: str, limit=100, offset=0) -> ResultList:
        return self.graph_service.get_graph_all_objects(graph_uri, limit=limit, offset=offset)

    #################################################
    # Graph and Vector combined functions

    def insert_object(self, graph_uri: str, graph_object: G, *, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.insert_object(graph_uri, graph_object)
        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())
        service_status.set_changes(graph_status.get_changes())

        return service_status

    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], *, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.insert_object_list(graph_uri, graph_object_list)
        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())
        service_status.set_changes(graph_status.get_changes())

        return service_status

    def update_object(self, graph_object: G, graph_uri: str, *, upsert: bool = False, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.update_object(graph_object, graph_uri, upsert=upsert)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status

    def update_object_list(self, graph_object_list: List[G], graph_uri: str, *, upsert: bool = False, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.update_object_list(graph_object_list, graph_uri=graph_uri, upsert=upsert)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status

    def get_object(self, object_uri: str, graph_uri: str) -> G:

        graph_object = self.graph_service.get_object(object_uri, graph_uri=graph_uri)

        return graph_object

    def get_object_list(self, object_uri_list: List[str], graph_uri: str) -> ResultList:

        return self.graph_service.get_object_list(object_uri_list, graph_uri=graph_uri)

    def delete_object(self, object_uri: str, graph_uri: str, *, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.delete_object(object_uri, graph_uri=graph_uri)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status

    def delete_object_list(self, object_uri_list: List[str], graph_uri: str, *, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.delete_object_list(object_uri_list, graph_uri=graph_uri)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status

    # filter graph

    def filter_query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, resolve_objects=True) -> ResultList:

        return self.graph_service.filter_query(graph_uri, sparql_query, uri_binding, resolve_objects=resolve_objects)

    # query graph

    def query(self, sparql_query: str, graph_uri: str, uri_binding='uri', *, resolve_objects=True) -> ResultList:
        return self.graph_service.query(sparql_query, graph_uri, uri_binding, resolve_objects=resolve_objects)

    #################################################
    # Vector functions

    def get_vector_collections(self):
        pass

    def add_vector_collection(self, collection_class):
        pass

    def delete_vector_collection(self, collection_class):
        pass

    def index_vector_collection(self, collection_class, delete_index=False):
        pass

    def query_vector_service(self, graphql: str) -> List[Dict]:
        pass

    #################################################
    # MetaQL Functions

    def metaql_select_query(self, *,
                            namespace: str = None,
                            select_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology]) -> MetaQLResult:

        if namespace is None:
            namespace = self.vitalservice_namespace

        return self.graph_service.metaql_select_query(
            namespace=namespace,
            select_query=select_query,
            namespace_list=namespace_list)

    def metaql_graph_query(self, *,
                           namespace: str = None,
                           graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology]) -> MetaQLResult:

        if namespace is None:
            namespace = self.vitalservice_namespace

        return self.graph_service.metaql_graph_query(
            namespace=namespace,
            graph_query=graph_query,
            namespace_list=namespace_list)

