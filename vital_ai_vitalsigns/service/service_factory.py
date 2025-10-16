import importlib
from typing import Optional, Any
from vital_ai_vitalsigns.config.vitalsigns_config import VitalSignsConfig, VitalServiceConfig


class ServiceFactory:
    """
    Factory class for dynamically creating database service instances
    based on configuration mappings.
    """
    
    @staticmethod
    def create_graph_service(
        service_config: VitalServiceConfig, 
        vitalsigns_config: VitalSignsConfig
    ) -> Optional[Any]:
        """
        Create a graph database service instance based on configuration.
        
        Args:
            service_config: The service configuration containing database_type
            vitalsigns_config: The full config containing implementation mappings
            
        Returns:
            Instance of the configured graph service class, or None if not found
        """
        if not service_config.graph_database:
            return None
            
        db_type = service_config.graph_database.database_type
        
        if not vitalsigns_config.database_implementations:
            raise ValueError("No database_implementations section found in configuration")
            
        graph_mappings = vitalsigns_config.database_implementations.graph_databases
        if not graph_mappings or db_type not in graph_mappings:
            raise ValueError(f"No implementation mapping found for graph database type: {db_type}")
            
        class_path = graph_mappings[db_type]
        return ServiceFactory._instantiate_class(
            class_path, 
            service_config.graph_database,
            base_uri=service_config.base_uri,
            namespace=service_config.namespace
        )
    
    @staticmethod
    def create_vector_service(
        service_config: VitalServiceConfig, 
        vitalsigns_config: VitalSignsConfig
    ) -> Optional[Any]:
        """
        Create a vector database service instance based on configuration.
        
        Args:
            service_config: The service configuration containing database_type
            vitalsigns_config: The full config containing implementation mappings
            
        Returns:
            Instance of the configured vector service class, or None if not found
        """
        if not service_config.vector_database:
            return None
            
        db_type = service_config.vector_database.vector_database_type
        
        if not vitalsigns_config.database_implementations:
            raise ValueError("No database_implementations section found in configuration")
            
        vector_mappings = vitalsigns_config.database_implementations.vector_databases
        if not vector_mappings or db_type not in vector_mappings:
            raise ValueError(f"No implementation mapping found for vector database type: {db_type}")
            
        class_path = vector_mappings[db_type]
        return ServiceFactory._instantiate_class(
            class_path, 
            service_config.vector_database,
            base_uri=service_config.base_uri,
            namespace=service_config.namespace
        )
    
    @staticmethod
    def _instantiate_class(class_path: str, config: Any, **kwargs) -> Any:
        """
        Dynamically import and instantiate a class from a fully qualified path.
        
        Args:
            class_path: Fully qualified class path (e.g., "package.module.ClassName")
            config: Configuration object to pass to the class constructor
            **kwargs: Additional keyword arguments to pass to the constructor
            
        Returns:
            Instance of the specified class
            
        Raises:
            ImportError: If the module or class cannot be imported
            Exception: If the class cannot be instantiated
        """
        try:
            # Split the path into module and class name
            module_path, class_name = class_path.rsplit('.', 1)
            
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the class from the module
            service_class = getattr(module, class_name)
            
            # Instantiate the class with the config and kwargs
            return service_class(config, **kwargs)
            
        except ImportError as e:
            raise ImportError(f"Could not import {class_path}: {e}")
        except AttributeError as e:
            raise ImportError(f"Class {class_name} not found in module {module_path}: {e}")
        except Exception as e:
            raise Exception(f"Could not instantiate {class_path}: {e}")


# Example usage function
def create_services_for_config(service_name: str, vitalsigns_config: VitalSignsConfig) -> tuple[Any, Any]:
    """
    Create both graph and vector services for a named service configuration.
    
    Args:
        service_name: Name of the service configuration to use
        vitalsigns_config: The full vitalsigns configuration
        
    Returns:
        Tuple of (graph_service, vector_service) - either may be None if not configured
    """
    # Find the service config by name
    service_config = None
    if vitalsigns_config.vitalservice_list:
        for svc in vitalsigns_config.vitalservice_list:
            if svc.name == service_name:
                service_config = svc
                break
    
    if not service_config:
        raise ValueError(f"Service configuration '{service_name}' not found")
    
    # Create services
    graph_service = ServiceFactory.create_graph_service(service_config, vitalsigns_config)
    vector_service = ServiceFactory.create_vector_service(service_config, vitalsigns_config)
    
    return graph_service, vector_service
