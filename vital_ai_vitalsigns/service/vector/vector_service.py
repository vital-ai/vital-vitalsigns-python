from abc import abstractmethod
from typing import List, TypeVar
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator
from vital_ai_vitalsigns.service.vector.vector_collection import VitalVectorCollection
from vital_ai_vitalsigns.service.vector.vector_result import VitalVectorResult
from vital_ai_vitalsigns.service.vector.vector_result_list import VitalVectorResultList
from vital_ai_vitalsigns.service.vector.vector_status import VitalVectorStatus
from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery
from vital_ai_vitalsigns.service.vector.vector_query import VitalVectorQuery
from vital_ai_vitalsigns.service.vector.vector_query_result import VitalVectorQueryResult
from vital_ai_vitalsigns.config.vitalsigns_config import VectorDatabaseConfig

G = TypeVar('G', bound='GraphObject')

class VitalVectorService:
    def __init__(self, config: VectorDatabaseConfig, **kwargs):
        self.config = config
        self.base_uri = kwargs.get('base_uri')
        self.namespace = kwargs.get('namespace')
        super().__init__()

    @abstractmethod
    def get_collection_identifiers(self) -> List[str]:
        # underlying vector collection
        pass

    @abstractmethod
    def get_vector_collection(self, collection_id: str) -> VitalVectorCollection | None:
        # underlying vector collection with iterator returning dict
        pass

    @abstractmethod
    def delete_vector_collection(self, collection_id: str) -> VitalVectorStatus:
        # underlying vector collection
        pass

    @abstractmethod
    def init_vital_vector_collections(self) -> VitalVectorStatus:
        pass

    @abstractmethod
    def remove_vital_vector_collections(self) -> VitalVectorStatus:
        pass

    @abstractmethod
    def init_vital_vector_service(self) -> VitalVectorStatus:
        pass

    @abstractmethod
    def destroy_vital_vector_service(self) -> VitalVectorStatus:
        pass

    @abstractmethod
    def check_vital_collection(self, collection_class_id: str) -> VitalVectorStatus:
        pass

    @abstractmethod
    def init_vital_collection(self, collection_class_id: str, delete_vital_collection=False) -> VitalVectorStatus:
        pass

    @abstractmethod
    def add_vital_collection(self, collection_class_id: str) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_vital_collection(self, collection_class_id: str) -> VitalVectorStatus:
        pass

    @abstractmethod
    def get_vital_collections(self) -> VitalVectorResult:
        pass

    @abstractmethod
    def create_collection(self,
                          collection_class,
                          collection_schema=None,
                          vital_schema=False) -> VitalVectorStatus:

        # called by add_vital_collection
        pass

    @abstractmethod
    def list_tenants(self, collection_class_id: str, *,
                     limit: int=100, last_tenant_id: str | None = None) -> List[str]:
        pass

    @abstractmethod
    def add_tenant(self, collection_class_id: str, tenant_id: str) -> VitalVectorStatus:
        pass

    @abstractmethod
    def add_tenant_list(self, collection_class_id: str, tenant_id_list: List[str]) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_tenant(self, collection_class_id: str, tenant_id: str) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_tenant_list(self, collection_class_id: str, tenant_id_list: List[str]) -> VitalVectorStatus:
        pass

    @abstractmethod
    def is_tenant(self, collection_class_id: str, tenant: str, use_tenant_cache=True) -> bool:
        pass

    @abstractmethod
    def add_object(self, collection_class_id: str, tenant_id: str | None, graph_object) -> VitalVectorStatus:
        pass

    @abstractmethod
    def add_object_list(self, collection_class_id: str, tenant_id: str | None, graph_object_list: List) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_object(self, collection_class_id: str, tenant_id: str | None, graph_object) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_object_list(self, collection_class_id: str, tenant_id: str | None, graph_object_list: List) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_object_uri(self, collection_class_id: str, tenant_id: str | None, graph_object_uri: str):
        pass

    @abstractmethod
    def delete_object_uri_list(self, collection_class_id: str, tenant_id: str | None, graph_object_uri_list: List[str]) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_object_uuid(self, collection_class_id: str, tenant_id: str | None, graph_object_uuid: str) -> VitalVectorStatus:
        pass

    @abstractmethod
    def delete_object_uuid_list(self, collection_class_id: str, tenant_id: str | None, graph_object_uuid_list: List[str]) -> VitalVectorStatus:
        pass

    @abstractmethod
    def update_object(self, collection_class_id: str, tenant_id: str | None, graph_object) -> VitalVectorStatus:
        pass

    @abstractmethod
    def update_object_list(self, collection_class_id: str, tenant_id: str | None, graph_object_list: List) -> VitalVectorStatus:
        pass

    @abstractmethod
    def get_object_map_uri(self, collection_class_id: str, tenant_id: str | None, object_uri: str) -> dict | None:
        pass

    @abstractmethod
    def get_object_map_uri_list(self, collection_class_id: str, tenant_id: str | None, object_uri_list: str) -> List[dict]:
        pass

    @abstractmethod
    def get_object_map_uuid(self, collection_class_id: str, tenant_id: str | None, object_uuid: str) -> dict | None:
        pass

    @abstractmethod
    def get_object_map_uuid_list(self, collection_class_id: str, tenant_id: str | None, object_uuid_list: List[str]) -> List[dict]:
        pass

    @abstractmethod
    def index_batch(self, tenant_id: str | None, object_generator: GraphObjectGenerator,
                    *,
                    purge_first: bool = True,
                    graph_id: str | None = None,
                    account_id: str | None = None,
                    global_graph: bool = False,
                    batch_size: int = 10_000):
        # always scope object generator to a tenant or none if global
        pass

    @abstractmethod
    def index_batch_file(self, tenant_id: str | None, file_path: str,
                               *, purge_first: bool = True, batch_size: int = 10_000):
        pass

    @abstractmethod
    def index_multi_tenant_batch(self, object_generator: GraphObjectGenerator,
                         *, all_global: bool = False, purge_first: bool = True, batch_size: int = 10_000):

        # tenant determined by object values

        pass

    @abstractmethod
    def index_multi_tenant_batch_file(self, file_path: str,
                               *, all_global: bool = False, purge_first: bool = True, batch_size: int = 10_000):

        # tenant determined by object values

        pass


    @abstractmethod
    def query(self, query: VitalVectorQuery) -> VitalVectorQueryResult:
        pass
    
    @abstractmethod
    def metaql_select_query(self, *, graph_query: MetaQLSelectQuery,
                           namespace_list: List[Ontology] = None) -> VitalVectorResultList:
        pass

    @abstractmethod
    def metaql_graph_query(self, *, graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology] = None) -> VitalVectorResultList:
        pass
