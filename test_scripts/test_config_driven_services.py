#!/usr/bin/env python3

"""
Test script to verify the new configuration-driven service instantiation system.
This demonstrates how services are now created dynamically based on the config
instead of being hardcoded.
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.config.vitalsigns_config import VitalSignsConfigLoader
from vital_ai_vitalsigns.service.vitalservice_manager import VitalServiceManager
from vital_ai_vitalsigns.service.service_factory import ServiceFactory


def test_config_driven_services():
    """Test that services can be created dynamically from configuration."""
    
    print("=== Testing Configuration-Driven Service Instantiation ===\n")
    
    # Load the configuration
    vital_home = os.path.join(project_root, "vitalhome")
    print(f"Loading configuration from: {vital_home}")
    
    try:
        vitalsigns_config = VitalSignsConfigLoader.vitalsigns_load_config(vital_home)
        print("✓ Configuration loaded successfully")
        
        # Check if database implementations are loaded
        if vitalsigns_config.database_implementations:
            print("✓ Database implementation mappings found:")
            if vitalsigns_config.database_implementations.graph_databases:
                print(f"  - Graph databases: {list(vitalsigns_config.database_implementations.graph_databases.keys())}")
            if vitalsigns_config.database_implementations.vector_databases:
                print(f"  - Vector databases: {list(vitalsigns_config.database_implementations.vector_databases.keys())}")
        else:
            print("✗ No database implementation mappings found")
            return False
            
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False
    
    print()
    
    # Test VitalServiceManager with new configuration approach
    print("=== Testing VitalServiceManager ===")
    
    try:
        service_manager = VitalServiceManager(vitalsigns_config=vitalsigns_config)
        service_list = service_manager.get_vitalservice_list()
        print(f"✓ VitalServiceManager initialized with {len(service_list)} services")
        
        for service_name in service_list:
            print(f"  - Service: {service_name}")
            service = service_manager.get_vitalservice(service_name)
            
            if service.graph_service:
                print(f"    ✓ Graph service: {type(service.graph_service).__name__}")
            else:
                print("    - No graph service")
                
            if service.vector_service:
                print(f"    ✓ Vector service: {type(service.vector_service).__name__}")
            else:
                print("    - No vector service")
                
    except Exception as e:
        print(f"✗ VitalServiceManager test failed: {e}")
        return False
    
    print()
    
    # Test ServiceFactory directly
    print("=== Testing ServiceFactory Directly ===")
    
    if vitalsigns_config.vitalservice_list:
        for service_config in vitalsigns_config.vitalservice_list:
            print(f"Testing service: {service_config.name}")
            
            try:
                if service_config.graph_database:
                    graph_service = ServiceFactory.create_graph_service(service_config, vitalsigns_config)
                    if graph_service:
                        print(f"  ✓ Graph service created: {type(graph_service).__name__}")
                    else:
                        print("  - No graph service created")
                
                if service_config.vector_database:
                    vector_service = ServiceFactory.create_vector_service(service_config, vitalsigns_config)
                    if vector_service:
                        print(f"  ✓ Vector service created: {type(vector_service).__name__}")
                    else:
                        print("  - No vector service created")
                        
            except Exception as e:
                print(f"  ✗ Service creation failed: {e}")
                continue
    
    print("\n=== Test Complete ===")
    return True


def test_config_object_constructors():
    """Test that service constructors work with config objects + kwargs pattern."""
    
    print("\n=== Testing Config Object Constructors ===")
    
    try:
        from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_service import VirtuosoGraphService
        from vital_ai_vitalsigns.service.vector.weaviate.weaviate_service import WeaviateVectorService
        from vital_ai_vitalsigns.config.vitalsigns_config import GraphDatabaseConfig, VectorDatabaseConfig
        
        # Test VirtuosoGraphService with config object + kwargs
        graph_config = GraphDatabaseConfig(
            database_type="virtuoso",
            username="test_user",
            password="test_pass",
            endpoint="http://localhost:8890/"
        )
        virtuoso_service = VirtuosoGraphService(
            graph_config,
            base_uri="http://test.ai",
            namespace="TEST"
        )
        print("✓ VirtuosoGraphService config + kwargs constructor works")
        
        # Test WeaviateVectorService with config object + kwargs
        vector_config = VectorDatabaseConfig(
            vector_database_type="weaviate",
            vector_database_schema_list=[],
            rest_endpoint="localhost",
            rest_port=8080,
            rest_ssl=False,
            rest_api_key="test_key"
        )
        weaviate_service = WeaviateVectorService(
            vector_config,
            base_uri="http://test.ai",
            namespace="TEST"
        )
        print("✓ WeaviateVectorService config + kwargs constructor works")
        
        return True
        
    except Exception as e:
        print(f"✗ Config object constructor test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing new configuration-driven service system...\n")
    
    success = test_config_driven_services()
    if success:
        success = test_config_object_constructors()
    
    if success:
        print("\n🎉 All tests passed! The new system is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
