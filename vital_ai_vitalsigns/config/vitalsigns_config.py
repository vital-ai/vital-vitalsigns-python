import os
from typing import Optional, List
import yaml
from dataclasses import dataclass

# TODO use and enforce types
# potentially different types have different property sets

class GraphDatabaseType:
    VIRTUOSO = "virtuoso"
    FUSEKI = "fuseki"
    VITALGRAPH = "vitalgraph"
    NEPTUNE = "neptune"
    ARANGODB = "arangodb"
    FUSEKI = "fuseki"
    QLEVER = "qlever"
    FUSEKI_MEMORY = "fuseki_memory"
    RDFLIB_MEMORY = "rdflib_memory"
    PYOXIGRAPH_MEMORY = "pyoxigraph_memory"
       
class VectorDatabaseType:
    WEAVIATE = "weaviate"
    VITALVECTORDB = "vitalvectordb"
    QDRANT_MEMORY = "qdrant_memory"

class EmbeddingModelType:
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    TEXT2VEC_TRANSFORMERS = "text2vec-transformers"

class EmbeddingModelOverflowPolicy:
    DEFAULT = "DEFAULT"
    TRUNCATE = "TRUNCATE"
    SLIDING_MEAN = "SLIDING_MEAN"
    SPLIT_MEAN = "SPLIT_MEAN"

# if vector embedding service exposed in weaviate api, then
# api key not need.  if vector is generated without using weaviate
# then api key would be needed

@dataclass
class EmbeddingModelConfig:
    id: str
    endpoint: str
    model_type: str
    api_key: Optional[str] = None
    overflow_policy: Optional[str] = "DEFAULT"
    max_tokens: Optional[int] = None

@dataclass
class CollectionConfig:
    class_uri: str
    embedding_models: Optional[List[str]] = None


@dataclass
class VectorDatabaseConfig:
    vector_database_type: str
    vector_database_schema_list: Optional[list[str]]
    rest_endpoint: Optional[str] = None
    rest_port: Optional[int] = None
    rest_ssl: Optional[bool] = True
    rest_api_key: Optional[str] = None
    grpc_endpoint: Optional[str] = None
    grpc_port: Optional[int] = 50051
    vector_endpoint: Optional[str] = None
    vector_port: Optional[int] = 8080
    vector_api_key: Optional[str] = None
    embedding_models: Optional[List[EmbeddingModelConfig]] = None
    collections: Optional[List[CollectionConfig]] = None


@dataclass
class GraphDatabaseConfig:
    database_type: str
    endpoint: str
    connection_type: Optional[str] = None
    server_name: Optional[str] = None
    server_user: Optional[str] = None
    server_dataset_dir: Optional[str] = None
    pem_path: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    apikey: Optional[str] = None


@dataclass
class VitalServiceConfig:
    name: str
    namespace: str
    base_uri: str
    graph_database: Optional[GraphDatabaseConfig] = None
    vector_database: Optional[VectorDatabaseConfig] = None


@dataclass
class ImplementationMappingConfig:
    graph_databases: Optional[dict[str, str]] = None
    vector_databases: Optional[dict[str, str]] = None


@dataclass
class VitalServiceSection:
    services: Optional[List[VitalServiceConfig]] = None
    implementation_mapping: Optional[ImplementationMappingConfig] = None


@dataclass
class VitalSignsConfig:
    vitalservice: Optional[VitalServiceSection] = None
    
    # Legacy property for backward compatibility
    @property
    def vitalservice_list(self) -> Optional[List[VitalServiceConfig]]:
        return self.vitalservice.services if self.vitalservice else None
    
    # Legacy property for backward compatibility  
    @property
    def database_implementations(self) -> Optional[ImplementationMappingConfig]:
        return self.vitalservice.implementation_mapping if self.vitalservice else None


# VitalSigns Config Path Components
vitalhome_config_dir = "vital-config"
vitalsigns_config_dir = "vitalsigns"
vitalsigns_config_filename = "vitalsigns_config.yaml"


class VitalSignsConfigLoader:
    @staticmethod
    def vitalsigns_load_config(vital_home: str) -> VitalSignsConfig:

        config_path = os.path.join(
            vital_home,
            vitalhome_config_dir,
            vitalsigns_config_dir,
            vitalsigns_config_filename
        )

        try:
            with open(config_path, 'r') as file:
                config_content = yaml.safe_load(file)
                # print(config_content)

            return VitalSignsConfigLoader._parse_config(config_content)
        except Exception as e:
            print(f"exception: {e}")
            return VitalSignsConfig()

    @staticmethod
    def parse_yaml_config(yaml_config: str) -> VitalSignsConfig:
        yaml_dict = yaml.safe_load(yaml_config)
        return VitalSignsConfigLoader._parse_config(yaml_dict)

    @staticmethod
    def _parse_config(config_data: dict) -> VitalSignsConfig:
        vitalservice_section = None
        
        if 'vitalservice' in config_data:
            vitalservice_data = config_data['vitalservice']
            
            # Parse services list
            services = []
            if 'services' in vitalservice_data:
                for service_data in vitalservice_data['services']:
                    graph_database = None
                    vector_database = None

                    if 'graph_database' in service_data:
                        graph_database = GraphDatabaseConfig(**service_data['graph_database'])

                    if 'vector_database' in service_data:
                        vector_db_data = service_data['vector_database']
                        embedding_models = [EmbeddingModelConfig(**model) for model in vector_db_data.get('embedding_models', [])]
                        collections = None
                        if 'collections' in vector_db_data:
                            collections = [
                                CollectionConfig(
                                    class_uri=collection['class_uri'],
                                    embedding_models=collection['embedding_models']
                                ) for collection in vector_db_data['collections']
                            ]
                        
                        # Handle defaults for new field structure
                        rest_ssl = vector_db_data.get('rest_ssl', True)
                        rest_port = vector_db_data.get('rest_port')
                        if rest_port is None:
                            rest_port = 443 if rest_ssl else 80
                        
                        vector_database = VectorDatabaseConfig(
                            vector_database_type=vector_db_data['vector_database_type'],
                            vector_database_schema_list=vector_db_data.get('vector_database_schema_list'),
                            rest_endpoint=vector_db_data.get('rest_endpoint'),
                            rest_port=rest_port,
                            rest_ssl=rest_ssl,
                            rest_api_key=vector_db_data.get('rest_api_key'),
                            grpc_endpoint=vector_db_data.get('grpc_endpoint'),
                            grpc_port=vector_db_data.get('grpc_port', 50051),
                            vector_endpoint=vector_db_data.get('vector_endpoint'),
                            vector_port=vector_db_data.get('vector_port', 8080),
                            vector_api_key=vector_db_data.get('vector_api_key'),
                            embedding_models=embedding_models,
                            collections=collections
                        )

                    services.append(VitalServiceConfig(
                        name=service_data['name'],
                        namespace=service_data['namespace'],
                        base_uri=service_data['base_uri'],
                        graph_database=graph_database,
                        vector_database=vector_database
                    ))
            
            # Parse implementation mapping section
            implementation_mapping = None
            if 'implementation_mapping' in vitalservice_data:
                impl_data = vitalservice_data['implementation_mapping']
                implementation_mapping = ImplementationMappingConfig(
                    graph_databases=impl_data.get('graph_databases', {}),
                    vector_databases=impl_data.get('vector_databases', {})
                )
            
            vitalservice_section = VitalServiceSection(
                services=services,
                implementation_mapping=implementation_mapping
            )

        return VitalSignsConfig(vitalservice=vitalservice_section)


