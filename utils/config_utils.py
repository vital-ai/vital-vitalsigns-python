import os
import yaml


class GraphDatabaseType:
    VIRTUOSO = "virtuoso"
    FUSEKI = "fuseki"


class VectorDatabaseType:
    WEAVIATE = "weaviate"
    VITAL_VECTORDB = "vital_vectordb"


class GraphDatabaseConfig:
    def __init__(self, username, password, endpoint, database_type):
        self.username = username
        self.password = password
        self.endpoint = endpoint
        if database_type not in [GraphDatabaseType.VIRTUOSO, GraphDatabaseType.FUSEKI]:
            raise ValueError(f"Invalid database type: {database_type}")
        self.database_type = database_type


class VectorDatabaseConfig:
    def __init__(self, endpoint, api_key, vector_database_type):
        self.endpoint = endpoint
        self.api_key = api_key
        if vector_database_type != VectorDatabaseType.WEAVIATE:
            raise ValueError(f"Invalid vector database type: {vector_database_type}")
        self.vector_database_type = vector_database_type


class VitalServiceConfig:
    def __init__(self, name, graph_database=None, vector_database=None):
        self.name = name
        self.graph_database = graph_database
        self.vector_database = vector_database
        if not self.graph_database and not self.vector_database:
            raise ValueError("At least one of graph_database or vector_database must be defined")


class VitalSignsConfig:
    def __int__(self):
        self.services = []


class ConfigUtils:

    @staticmethod
    def vitalsigns_load_config(file_path) -> VitalSignsConfig:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)

            vs_config = VitalSignsConfig()

            # vitalservice part
            services = []
            for service in config.get('vitalservice', []):
                name = service.get('name')
                graph_db = service.get('graph_database')
                vector_db = service.get('vector_database')

                graph_database = None
                if graph_db:
                    graph_database = GraphDatabaseConfig(
                        username=graph_db['username'],
                        password=graph_db['password'],
                        endpoint=graph_db['endpoint'],
                        database_type=graph_db['database_type']
                    )

                vector_database = None
                if vector_db:
                    vector_database = VectorDatabaseConfig(
                        endpoint=vector_db['endpoint'],
                        api_key=vector_db['api_key'],
                        vector_database_type=vector_db['vector_database_type']
                    )

                vital_service = VitalServiceConfig(
                    name=name,
                    graph_database=graph_database,
                    vector_database=vector_database
                )
                services.append(vital_service)

            vs_config.services = services

            return vs_config

    @staticmethod
    def load_config(config_file="../config/vitalsigns_config.yaml"):
        with open(config_file, "r") as config_stream:
            try:
                return yaml.safe_load(config_stream)
            except yaml.YAMLError as exc:
                print("failed to load config file")

    @staticmethod
    def find_project_root(starting_dir, project_dir_name="vital-vitalsigns-python"):
        current_dir = starting_dir
        while current_dir != os.path.dirname(current_dir):
            if project_dir_name in os.listdir(current_dir):
                return os.path.join(current_dir, project_dir_name)
            current_dir = os.path.dirname(current_dir)
        return None
