import logging
from typing import List, TypeVar, Dict, Optional

from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.metaql_result import MetaQLResult
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.service.base_service import BaseService
from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService
from vital_ai_vitalsigns.service.graph.graph_service_status import GraphServiceStatusType
from vital_ai_vitalsigns.service.vital_name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.vector.vector_collection import VitalVectorCollection
from vital_ai_vitalsigns.service.vector.vector_result import VitalVectorResult
from vital_ai_vitalsigns.service.vector.vector_service import VitalVectorService
from vital_ai_vitalsigns.service.vector.vector_status import VitalVectorStatus
from vital_ai_vitalsigns.service.vital_service_status import VitalServiceStatus, VitalServiceStatusType
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
                 vitalservice_base_uri: str = None,
                 graph_service: VitalGraphService = None,
                 vector_service: VitalVectorService = None,
                 synchronize_service=True,
                 synchronize_task=True):
        self.vitalservice_name = vitalservice_name
        self.vitalservice_namespace = vitalservice_namespace
        self.vitalservice_base_uri = vitalservice_base_uri
        self.graph_service = graph_service
        self.vector_service = vector_service
        self.graph_info_lock = threading.RLock()
        self.background_thread = None
        self.running = False
        if synchronize_service:
            self.synchronize_service()
        if synchronize_task:
            self.start()


    def is_combined_service(self) -> bool:
        if self.graph_service is not None:
            if self.vector_service is not None:
                return True

        return False

    def is_graph_service(self) -> bool:
        if self.graph_service is not None:
            return True
        return False

    def is_vector_service(self) -> bool:
        if self.vector_service is not None:
            return True
        return False

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

    def list_graph_uris(self) -> List[str]:

        graph_uri_list = self.graph_service.list_graph_uris()

        return graph_uri_list

    def get_service_status(self) -> VitalServiceStatus:

        # ensure access to graph info from background task
        with self.graph_info_lock:

            graph_status = self.graph_service.service_status()

            logging.info(f"Graph Database Status: {graph_status.get_status_type()}")

            if graph_status.get_status_type() == GraphServiceStatusType.UNINITIALIZED:

                status = VitalServiceStatus(VitalServiceStatusType.UNINITIALIZED)

                return status


            status = VitalServiceStatus()

            return status

    def destroy_service(self) -> VitalServiceStatus:

        with self.graph_info_lock:

            # TODO change to status object
            destroyed = self.graph_service.destroy_service()

            if not destroyed:
                status = VitalServiceStatus(VitalServiceStatusType.ERROR)

                return status

            if self.vector_service is not None:
                vector_status = self.vector_service.destroy_vital_vector_service()
                # TODO check for error or ok


        status = VitalServiceStatus()

        return status

    def is_graph_global(self, graph_id: str, *, account_id: str|None = None) -> bool:
        return self.graph_service.is_graph_global(graph_id, account_id=account_id)

    def initialize_service(self, delete_service:bool = False, delete_index: bool = False) -> VitalServiceStatus:

        # ensure access to graph info from background task
        with self.graph_info_lock:

            # TODO change to status object
            initialized = self.graph_service.initialize_service()

            if not initialized:

                status = VitalServiceStatus(VitalServiceStatusType.UNINITIALIZED)

                return status

            if self.vector_service is not None:
                vector_status = self.vector_service.init_vital_vector_service()
                # TODO check for error or ok


        status = VitalServiceStatus()

        return status

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

    def get_graph(self, graph_id: str, *,
                  global_graph: bool = False,
                  account_id: str|None = None) -> VitalNameGraph:

        name_graph = self.graph_service.get_graph(graph_id,
                                                  global_graph=global_graph,
                                                  account_id=account_id)

        return name_graph

    def list_graphs(self, *,
                    account_id: str | None = None,
                    include_global: bool = True,
                    include_private: bool = True
                    ) -> List[VitalNameGraph]:

        name_graph_list = self.graph_service.list_graphs(
            account_id=account_id,
            include_global=include_global,
            include_private=include_private
        )

        return name_graph_list

    # create graph
    # store name graph in vital service graph and in the graph itself
    # a graph needs to have some triples in it to exist

    def check_create_graph(self, graph_id: str, *,
                           global_graph: bool = False,
                           account_id: str|None = None) -> bool:
        return self.graph_service.check_create_graph(graph_id,
                                                     global_graph=global_graph,
                                                     account_id=account_id)

    def create_graph(self, graph_id: str, *,
                     global_graph: bool = False,
                     account_id: str|None = None) -> bool:
        return self.graph_service.create_graph(graph_id,
                                               global_graph=global_graph,
                                               account_id=account_id)

    # delete graph
    # delete graph itself plus record in vital service graph

    def delete_graph(self, graph_id: str, *,
                     global_graph: bool = False,
                     account_id: str | None = None,
                     update_index: bool = True) -> bool:
        return self.graph_service.delete_graph(graph_id,
                                               global_graph=global_graph,
                                               account_id=account_id)

    # purge graph (delete all but name graph)

    def purge_graph(self, graph_id: str, *,
                    global_graph: bool = False,
                    account_id: str | None = None,
                    update_index: bool = True) -> bool:
        return self.graph_service.purge_graph(graph_id,
                                              global_graph=global_graph,
                                              account_id=account_id)

    def get_graph_all_objects(self, graph_id: str, *,
                              global_graph: bool = False,
                              account_id: str | None = None,
                              limit: int = 100, offset: int = 0) -> ResultList:
        return self.graph_service.get_graph_all_objects(graph_id,
                                                        global_graph=global_graph,
                                                        account_id=account_id,
                                                        limit=limit, offset=offset)

    #################################################
    # Graph and Vector combined functions

    def insert_object(self, graph_id: str, graph_object: G, *,
                      global_graph: bool = False,
                      account_id: str | None = None,
                      update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.insert_object(graph_id, graph_object,
                                                        global_graph=global_graph,
                                                        account_id=account_id)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())
        service_status.set_changes(graph_status.get_changes())

        return service_status

    def insert_object_list(self, graph_id: str, graph_object_list: List[G], *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.insert_object_list(graph_id, graph_object_list,
                                                             global_graph=global_graph,
                                                             account_id=account_id)
        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())
        service_status.set_changes(graph_status.get_changes())

        return service_status

    def update_object(self, graph_object: G, graph_id: str, *,
                      global_graph: bool = False,
                      account_id: str | None = None,
                      upsert: bool = False, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.update_object(graph_object,
                                                        graph_id=graph_id,
                                                        global_graph=global_graph,
                                                        account_id=account_id,
                                                        upsert=upsert)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status

    def update_object_list(self, graph_object_list: List[G], graph_id: str, *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           upsert: bool = False, update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.update_object_list(graph_object_list,
                                                             graph_id=graph_id,
                                                             account_id=account_id,
                                                             global_graph=global_graph, upsert=upsert)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status

    def get_object(self, object_uri: str, graph_id: str, *,
                   account_id: str | None = None,
                   global_graph: bool = False) -> G:

        graph_object = self.graph_service.get_object(object_uri,
                                                     graph_id=graph_id,
                                                     account_id=account_id,
                                                     global_graph=global_graph)

        return graph_object

    def get_object_list(self, object_uri_list: List[str], graph_id: str, *,
                        global_graph: bool = False,
                        account_id: str | None = None
                        ) -> ResultList:

        return self.graph_service.get_object_list(object_uri_list,
                                                  graph_id=graph_id,
                                                  account_id=account_id,
                                                  global_graph=global_graph)

    def delete_object(self, object_uri: str, graph_id: str, *,
                      global_graph: bool = False,
                      account_id: str | None = None,
                      update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.delete_object(object_uri,
                                                        graph_id=graph_id,
                                                        account_id=account_id,
                                                        global_graph=global_graph)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status

    def delete_object_list(self, object_uri_list: List[str], graph_id: str, *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           update_index: bool = True) -> VitalServiceStatus:

        graph_status = self.graph_service.delete_object_list(object_uri_list,
                                                             graph_id=graph_id,
                                                             account_id=account_id,
                                                             global_graph=global_graph)

        service_status = VitalServiceStatus(graph_status.get_status(), graph_status.get_message())

        service_status.set_changes(graph_status.get_changes())

        return service_status


    # query graph

    def query(self, sparql_query: str, graph_id: str, uri_binding='uri', *,
              account_id: str | None = None,
              global_graph: bool = False,
              resolve_objects=True) -> ResultList:
        return self.graph_service.query(sparql_query, graph_id, uri_binding,
                                        global_graph=global_graph,
                                        account_id=account_id,
                                        resolve_objects=resolve_objects)

    #################################################
    # Vector functions

    # TODO check if indexed
    def is_indexed(self) -> bool:

        return False

    def init_vector_collections(self) -> VitalVectorStatus:
        return self.vector_service.init_vital_vector_collections()

    def remove_vector_collections(self) -> VitalVectorStatus:
        return self.vector_service.remove_vital_vector_collections()

    def get_vector_collection_identifiers(self) -> List[str]:

        collection_list = []

        vector_col_list = self.vector_service.get_collection_identifiers()

        for col in vector_col_list:
            collection_list.append(col)

        return collection_list

    def get_vital_vector_collections(self) -> VitalVectorResult:
        pass

    def add_vital_vector_collection(self, collection_class: VitalVectorCollection) -> VitalVectorStatus:
        pass

    def delete_vital_vector_collection(self, collection_class_id) -> VitalVectorStatus:
        pass

    def index_vital_vector_collection(self, collection_class_id, delete_index=False) -> VitalVectorStatus:
        pass

    def index_vital_vector_all_collections(self, delete_indexes=False) -> VitalVectorStatus:
        pass

    #################################################
    # MetaQL Functions

    def metaql_select_query(self, *,
                            select_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology]) -> MetaQLResult:

        # check query to decide to send to vector or graph store

        return self.graph_service.metaql_select_query(
            select_query=select_query,
            namespace_list=namespace_list)

    def metaql_graph_query(self, *,
                           graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology] = None) -> MetaQLResult:

        # avoid circular dependency
        from vital_ai_vitalsigns.vitalsigns import VitalSigns

        vs = VitalSigns()

        namespace = self.vitalservice_namespace

        if namespace_list is None:

            namespace_list = [
                Ontology("owl", "http://www.w3.org/2002/07/owl#"),
                Ontology("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
                Ontology("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
            ]

            iri_list = vs.get_ontology_manager().get_ontology_iri_list()

            ont_prefix_map = {}

            for iri in iri_list:

                if iri.startswith("http://vital.ai/ontology/"):
                    prefix = iri[len("http://vital.ai/ontology/"):]

                    prefix = prefix.removesuffix("#")

                    # logger.info(f"Vital Prefix: {prefix} IRI: {iri}")

                    ont_prefix_map[prefix] = iri

            for k in ont_prefix_map.keys():
                # print(f"Ont Prefix: {k} IRI: {ont_prefix_map[k]}")
                ont = Ontology(k, ont_prefix_map[k])
                namespace_list.append(ont)

        # check query to decide to send to vector or graph store

        return self.graph_service.metaql_graph_query(
            graph_query=graph_query,
            namespace_list=namespace_list)

    #################################################
    # Import Functions

    def import_graph_batch(self, graph_id: str, object_generator: GraphObjectGenerator,
                           *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           purge_first: bool = True, batch_size: int = 10_000):
        pass


    def index_graph_batch(self, graph_id: str, object_generator: GraphObjectGenerator,
                          *,
                          global_graph: bool = False,
                          account_id: str | None = None,
                          tenant_id: str | None = None,
                          purge_first: bool = True, batch_size: int = 10_000):

        self.vector_service.index_batch(tenant_id, object_generator,
                                        graph_id=graph_id,
                                        account_id=account_id,
                                        global_graph=global_graph)

    def import_graph_batch_file(self, graph_id: str, file_path: str, *,
                                global_graph: bool = False,
                                account_id: str | None = None,
                                purge_first: bool = True, batch_size: int = 10_000):
        pass

    def import_multi_graph_batch(self, object_generator: GraphObjectGenerator,
                                 *, purge_first: bool = True, batch_size: int = 10_000):

        pass

    def import_multi_graph_batch_file(self, file_path: str,
                                     *, purge_first: bool = True, batch_size: int = 10_000):

        pass

