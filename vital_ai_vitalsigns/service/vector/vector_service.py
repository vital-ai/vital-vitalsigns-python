from abc import abstractmethod
from typing import List

from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator


class VitalVectorService:
    def __init__(self):
        pass

    # todo have top-level namespace so multiple vital collections can co-exist
    # todo batch cases

    @abstractmethod
    def get_collection_identifiers(self) -> List[str]:
        pass

    @abstractmethod
    def get_collections(self):
        pass

    @abstractmethod
    def initialize_vector_service(self):
        pass

    @abstractmethod
    def destroy_vector_service(self):
        pass

    @abstractmethod
    def check_vital_collection(self):
        pass

    @abstractmethod
    def init_vital_collection(self, delete_vital_collection=False):
        pass

    @abstractmethod
    def add_vital_collection(self):
        pass

    @abstractmethod
    def delete_vital_collection(self):
        pass

    @abstractmethod
    def get_vital_collections(self):
        pass

    @abstractmethod
    def create_collection(self,
                          collection_class,
                          collection_schema=None,
                          vital_schema=False):
        pass

    @abstractmethod
    def delete_collection(self):
        pass

    @abstractmethod
    def list_tenants(self, collection_class):
        pass

    @abstractmethod
    def add_tenant(self, collection_class, tenant: str):
        pass

    @abstractmethod
    def delete_tenant(self, collection_class, tenant: str):
        pass

    @abstractmethod
    def is_tenant(self, collection_class, tenant: str, tenant_cache=True) -> bool:
        pass

    @abstractmethod
    def add_object(self, collection_class, tenant: str, graph_object):
        pass

    @abstractmethod
    def delete_object(self, collection_class, tenant: str, graph_object):
        pass

    @abstractmethod
    def update_object(self, collection_class, tenant: str, graph_object):
        pass

    @abstractmethod
    def get_object_map_uri(self, collection_class, tenant: str, object_uri: str):
        pass

    @abstractmethod
    def get_object_map_uuid(self, collection_class, tenant: str, object_uuid: str):
        pass

    @abstractmethod
    def index_collection(self, collection_class, tenant: str, object_generator: GraphObjectGenerator):
        pass
