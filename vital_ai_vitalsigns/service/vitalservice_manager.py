from vital_ai_vitalsigns.config.vitalsigns_config import VitalServiceConfig, VitalSignsConfig
from vital_ai_vitalsigns.service.vital_service import VitalService
from vital_ai_vitalsigns.service.service_factory import ServiceFactory


class VitalServiceManager:
    def __init__(self, *, config: list[VitalServiceConfig] = None, vitalsigns_config: VitalSignsConfig = None, config_file:str = None):
        self.config_file = config_file
        self.initialized = False
        self.vitalservice_config = config
        self.vitalsigns_config = vitalsigns_config
        self.services = {}

    def set_config(self, config_file: str):
        self.config_file = config_file
        self.initialized = False
        self.vitalservice_config = None
        self.services = {}

    def _initialize(self):
        self.initialized = False
        self.services = {}

        # Use vitalsigns_config if available (preferred method)
        if self.vitalsigns_config and self.vitalsigns_config.vitalservice_list:
            for service_config in self.vitalsigns_config.vitalservice_list:
                try:
                    # Use ServiceFactory to create services dynamically based on config
                    graph_service = None
                    vector_service = None
                    
                    if service_config.graph_database:
                        graph_service = ServiceFactory.create_graph_service(service_config, self.vitalsigns_config)
                    
                    if service_config.vector_database:
                        vector_service = ServiceFactory.create_vector_service(service_config, self.vitalsigns_config)
                    
                    vital_service = VitalService(
                        vitalservice_name=service_config.name,
                        vitalservice_namespace=service_config.namespace,
                        vitalservice_base_uri=service_config.base_uri,
                        graph_service=graph_service,
                        vector_service=vector_service
                    )
                    
                    self.services[vital_service.vitalservice_name] = vital_service
                    
                except Exception as e:
                    print(f"Warning: Failed to create service '{service_config.name}': {e}")
                    # Continue with other services even if one fails
                    continue
            
            self.initialized = True
            return
        
        # Fallback to legacy vitalservice_config (list of VitalServiceConfig)
        if self.vitalservice_config:
            print("Warning: Using legacy service configuration without database implementation mappings")
            print("Consider using VitalSignsConfig with database_implementations section for full functionality")
            
            # For backward compatibility, we could still try to create services
            # but without the implementation mappings, we can't use the factory
            # This would require falling back to hardcoded implementations
            self.initialized = True
            return

        if self.config_file:
            # TODO: Load config from file and use ServiceFactory
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




