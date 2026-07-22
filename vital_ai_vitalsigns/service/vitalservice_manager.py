import logging
import threading

from vital_ai_vitalsigns.config.vitalsigns_config import VitalServiceConfig, VitalSignsConfig
from vital_ai_vitalsigns.service.vital_service import VitalService
from vital_ai_vitalsigns.service.service_factory import ServiceFactory

logger = logging.getLogger(__name__)


class VitalServiceManager:
    def __init__(self, *, config: list[VitalServiceConfig] = None, vitalsigns_config: VitalSignsConfig = None, config_file:str = None):
        self.config_file = config_file
        self.initialized = False
        self.vitalservice_config = config
        self.vitalsigns_config = vitalsigns_config
        self.services = {}
        # Guards initialization and the services map. Without it, concurrent
        # first access ran _initialize() twice, each building a full set of
        # VitalService objects -- each of which spawns a background thread.
        # Only one map survived; the other services' threads ran orphaned.
        self._init_lock = threading.RLock()

    def _ensure_initialized(self):
        if self.initialized:
            return
        with self._init_lock:
            if not self.initialized:
                self._initialize()

    @staticmethod
    def _stop_services(services):
        """Stop background threads on services being discarded.

        VitalService starts a background thread by default (synchronize_task=True).
        Dropping the services map without stopping them orphans one thread per
        service for the process lifetime.
        """
        for name, service in list((services or {}).items()):
            stop = getattr(service, 'stop', None)
            if stop is None:
                continue
            try:
                stop()
            except Exception as e:
                logger.warning("Failed to stop VitalService '%s': %s", name, e)

    def set_config(self, config_file: str):
        with self._init_lock:
            outgoing = self.services
            self.config_file = config_file
            self.initialized = False
            self.vitalservice_config = None
            self.services = {}

        self._stop_services(outgoing)

    def shutdown(self):
        """Stop every managed service. Safe to call repeatedly."""
        with self._init_lock:
            outgoing = self.services
            self.services = {}
            self.initialized = False

        self._stop_services(outgoing)

    def _initialize(self):
        # Retire any previous generation first, or their background threads leak.
        self._stop_services(self.services)

        # Build into a local map and publish it in one assignment. Assigning
        # self.services = {} up front left a window where a concurrent reader
        # saw an empty or half-populated map and raised KeyError for a service
        # that was configured correctly.
        services = {}

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
                    
                    services[vital_service.vitalservice_name] = vital_service
                    
                except Exception as e:
                    logger.warning("Failed to create service '%s': %s",
                                   service_config.name, e)
                    # Continue with other services even if one fails
                    continue

            self.services = services
            self.initialized = True
            return
        
        # Fallback to legacy vitalservice_config (list of VitalServiceConfig)
        if self.vitalservice_config:
            logger.warning(
                "Using legacy service configuration without database implementation "
                "mappings. Consider using VitalSignsConfig with a "
                "database_implementations section for full functionality.")
            
            # For backward compatibility, we could still try to create services
            # but without the implementation mappings, we can't use the factory
            # This would require falling back to hardcoded implementations
            self.services = services
            self.initialized = True
            return

        if self.config_file:
            # TODO: Load config from file and use ServiceFactory
            self.services = services
            self.initialized = True
            return

        self.services = services
        self.initialized = False

    def get_vitalservice_list(self):

        self._ensure_initialized()

        return self.services.keys()

    def get_vitalservice(self, vitalservice_name: str) -> VitalService:

        self._ensure_initialized()

        return self.services[vitalservice_name]

    # should only use config file to define vitalservices, but
    # for testing and other in-memory cases would be useful to define dynamically

    # todo confirm name unique, etc.

    def add_vitalservice(self, vitalservice_name: str, vitalservice: VitalService):
        self._ensure_initialized()

        with self._init_lock:
            self.services[vitalservice_name] = vitalservice

        return True

    def remove_vitalservice(self, vitalservice_name: str):

        self._ensure_initialized()

        with self._init_lock:
            removed = self.services.pop(vitalservice_name, None)

        if removed is None:
            return False

        self._stop_services({vitalservice_name: removed})
        return True




