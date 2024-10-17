from vital_ai_vitalsigns.config.vitalsigns_config import VitalServiceConfig
from vital_ai_vitalsigns.service.vital_service import VitalService


class VitalServiceManager:
    def __init__(self, *, config: list[VitalServiceConfig] = None, config_file:str = None):
        self.config_file = config_file
        self.initialized = False
        self.vitalservice_config = config
        self.services = {}

    def set_config(self, config_file: str):
        self.config_file = config_file
        self.initialized = False
        self.vitalservice_config = None
        self.services = {}

    def _initialize(self):

        from vital_ai_vitalsigns.service.graph.virtuoso_service import VirtuosoGraphService
        from vital_ai_vitalsigns.service.vector.weaviate.weaviate_service import WeaviateVectorService

        self.initialized = False
        self.services = {}

        if self.vitalservice_config:

            for config in self.vitalservice_config:

                vitalservice_name = config.name
                vitalservice_namespace = config.namespace
                vitalservice_graph_db = config.graph_database
                vitalservice_vector_db = config.vector_database

                graph_service = None
                vector_service = None

                if vitalservice_graph_db:
                    username = vitalservice_graph_db.username
                    password = vitalservice_graph_db.password
                    endpoint = vitalservice_graph_db.endpoint

                    graph_service = VirtuosoGraphService(
                        username=username,
                        password=password,
                        endpoint=endpoint,
                        namespace=vitalservice_namespace
                    )

                if vitalservice_vector_db:

                    endpoint = vitalservice_vector_db.endpoint
                    grpc_endpoint = vitalservice_vector_db.grpc_endpoint
                    vector_endpoint = vitalservice_vector_db.vector_endpoint
                    api_key = vitalservice_vector_db.api_key
                    schema_list = vitalservice_vector_db.vector_database_schema_list

                    vector_service = WeaviateVectorService()

                vital_service = VitalService(
                    vitalservice_name=vitalservice_name,
                    vitalservice_namespace=vitalservice_namespace,
                    graph_service=graph_service,
                    vector_service=vector_service)

                self.services[vital_service.vitalservice_name] = vital_service

            self.initialized = True

            return

        if self.config_file:

            self.services = {}
            self.initialized = True
            return

        self.initialized = False

    def get_vitalservice_list(self):

        if self.initialized is False:
            self._initialize()

        return self.services.keys()

    def get_vitalservice(self, vitalservice_name: str) -> VitalService:

        if self.initialized is False:
            self._initialize()

        return self.services[vitalservice_name]

    # should only use config file to define vitalservices, but
    # for testing and other in-memory cases would be useful to define dynamically

    # todo confirm name unique, etc.

    def add_vitalservice(self, vitalservice_name: str, vitalservice: VitalService):
        if self.initialized is False:
            self._initialize()

        self.services[vitalservice_name] = vitalservice

        return True

    def remove_vitalservice(self, vitalservice_name: str):

        if self.initialized is False:
            self._initialize()

        del self.services[vitalservice_name]

        return True




