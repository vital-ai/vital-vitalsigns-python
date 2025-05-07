import os
from typing import Optional, List
import yaml
from dataclasses import dataclass

# TODO use and enforce types
# potentially different types have different property sets

class GraphDatabaseType:
    VIRTUOSO = "virtuoso"
    FUSEKI = "fuseki"

class VectorDatabaseType:
    WEAVIATE = "weaviate"
    VITAL_VECTORDB = "vital_vectordb"

@dataclass
class EmbeddingModelConfig:
    id: str
    endpoint: str
    api_key: Optional[str] = None


@dataclass
class CollectionConfig:
    class_uri: str
    embedding_models: Optional[List[str]] = None


@dataclass
class VectorDatabaseConfig:
    vector_database_type: str
    endpoint: str
    vector_database_schema_list: Optional[list[str]]
    vector_endpoint: Optional[str] = None
    grpc_endpoint: Optional[str] = None
    api_key: Optional[str] = None
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
class VitalSignsConfig:
    vitalservice_list: Optional[List[VitalServiceConfig]] = None


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
        services = []
        for service_data in config_data['vitalservice']:
            graph_database = None
            vector_database = None

            if 'graph_database' in service_data:
                graph_database = GraphDatabaseConfig(**service_data['graph_database'])

            if 'vector_database' in service_data:
                vector_db_data = service_data['vector_database']
                embedding_models = [EmbeddingModelConfig(**model) for model in vector_db_data['embedding_models']]
                collections = None
                if 'collections' in vector_db_data:
                    collections = [
                        CollectionConfig(
                            class_uri=collection['class_uri'],
                            embedding_models=collection['embedding_models']
                        ) for collection in vector_db_data['collections']
                    ]
                vector_database = VectorDatabaseConfig(
                    endpoint=vector_db_data['endpoint'],
                    vector_endpoint=vector_db_data['vector_endpoint'],
                    grpc_endpoint=vector_db_data['grpc_endpoint'],

                    api_key=vector_db_data['api_key'],
                    vector_database_type=vector_db_data['vector_database_type'],
                    vector_database_schema_list=vector_db_data['vector_database_schema_list'],
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

        return VitalSignsConfig(vitalservice_list=services)


