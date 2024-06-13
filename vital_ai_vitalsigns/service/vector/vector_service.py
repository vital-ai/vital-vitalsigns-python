from abc import abstractmethod
from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator


class VitalVectorService:
    def __init__(self):
        pass

    # todo have top-level namespace so multiple vital collections can co-exist
    # todo batch cases

    @abstractmethod
    def check_vital_collection(self, vital_managed=True):
        pass

    @abstractmethod
    def init_vital_collection(self, delete_vital_collection=False, vital_managed=True):
        pass

    @abstractmethod
    def add_vital_collection(self, vital_managed=True):
        pass

    @abstractmethod
    def delete_vital_collection(self, vital_managed=True):
        pass

    @abstractmethod
    def get_vital_collections(self, vital_managed=True):
        pass

    @abstractmethod
    def get_collections(self, vital_managed=True):
        pass

    @abstractmethod
    def create_collection(self,
                          collection_class,
                          collection_schema=None,
                          vital_managed=True,
                          vital_schema=False):
        pass

    @abstractmethod
    def delete_collection(self, vital_managed=True):
        pass

    @abstractmethod
    def list_tenants(self, collection_class, vital_managed=True):
        pass

    @abstractmethod
    def add_tenant(self, collection_class, tenant: str, vital_managed=True):
        pass

    @abstractmethod
    def delete_tenant(self, collection_class, tenant: str, vital_managed=True):
        pass

    @abstractmethod
    def is_tenant(self, collection_class, tenant: str, vital_managed=True, tenant_cache=True) -> bool:
        pass

    @abstractmethod
    def add_object(self, collection_class, tenant: str, graph_object, vital_managed=True):
        pass

    @abstractmethod
    def delete_object(self, collection_class, tenant: str, graph_object, vital_managed=True):
        pass

    @abstractmethod
    def update_object(self, collection_class, tenant: str, graph_object, vital_managed=True):
        pass

    @abstractmethod
    def get_object_map_uri(self, collection_class, tenant: str, object_uri: str, vital_managed=True):
        pass

    @abstractmethod
    def get_object_map_uuid(self, collection_class, tenant: str, object_uuid: str, vital_managed=True):
        pass

    @abstractmethod
    def index_collection(self, collection_class, tenant: str, object_generator: GraphObjectGenerator, vital_managed=True):
        pass



