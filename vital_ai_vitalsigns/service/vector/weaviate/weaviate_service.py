import json
import logging
from typing import List
import weaviate
import yaml
from weaviate import WeaviateClient
from weaviate.collections.classes.config import ReferenceProperty, DataType, Property, Configure
from weaviate.config import AdditionalConfig, Timeout
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5
from vital_ai_vitalsigns.config.vitalsigns_config import EmbeddingModelConfig, CollectionConfig
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator
from vital_ai_vitalsigns.service.vector.vector_result import VitalVectorResult
from vital_ai_vitalsigns.service.vector.vector_result_list import VitalVectorResultList
from vital_ai_vitalsigns.service.vector.vector_service import VitalVectorService
from vital_ai_vitalsigns.service.vector.vector_status import VitalVectorStatus, VitalVectorStatusType
from vital_ai_vitalsigns.service.vector.weaviate.weaviate_result_list import WeaviateResultList
from vital_ai_vitalsigns.service.vector.weaviate.weaviate_vector_query import WeaviateVectorQuery
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery
import weaviate.classes.config as wvcc


# Note: this will expose creating collections based on passed in schema
# via WeaviateCollectionDefinition
# the schema will determine the content of the vectors

# requests will need to check if tenant exists for a collection, and if
# not, add it.  caching could help this

# TODO add tenant cache, have exceptions when tenant doesnt exist
# as tenants would infrequently get deleted


class WeaviateVectorService(VitalVectorService):

    def __init__(self,
                 endpoint: str | None = None,
                 grpc_endpoint : str | None = None,
                 vector_endpoint : str | None = None,
                 api_key : str | None = None,
                 schema_list : list[str] | None = None,
                 collections: List[CollectionConfig] | None  = None,
                 embedding_models: List[EmbeddingModelConfig] | None = None,
                 **kwargs):

        self.endpoint = endpoint
        self.grpc_endpoint = grpc_endpoint
        self.vector_endpoint = vector_endpoint
        self.api_key = api_key
        self.schema_list = schema_list
        self.collections = collections
        self.embedding_models = embedding_models

        self._client: WeaviateClient | None = None

        super().__init__(**kwargs)

    @staticmethod
    def _create_dict_with_keys(keys):
        return {key: [] for key in keys}

    @staticmethod
    def _append_to_key_list(d, key, value):
        if key in d:
            d[key].append(value)
        else:
            logging.info(f"Key '{key}' not found in the dictionary")

    # move this to when vitalservice inits
    @staticmethod
    def load_weaviate_schema(schema_path: str):
        with open(schema_path, "r") as config_stream:
            try:
                return yaml.safe_load(config_stream)
            except yaml.YAMLError as exc:
                logging.error(exc)


    def _create_collection(self, collection: dict) -> VitalVectorStatus :

        namespace = self.namespace

        client = self.get_client()

        collection_name = collection["name"]

        multi_prefix = "Multi"

        multi_tenant = collection["multi_tenant"]

        if multi_tenant:
            namespace_collection_name = f"{namespace}_{multi_prefix}_{collection_name}"
        else:
            namespace_collection_name = f"{namespace}_{collection_name}"

        description = collection["description"]
        class_uri = collection["class_uri"]
        named_vectors = collection["named_vectors"]

        named_vector_list = []

        for named_vector in named_vectors:
            name = named_vector["name"]
            named_vector_list.append(name)

        vector_dict = self._create_dict_with_keys(named_vector_list)

        cross_links = collection.get("cross_links", [])

        references = []

        for cross_link in cross_links:
            cross_link_name = cross_link["name"]


            cross_link_type = cross_link["cross_link_type"]

            # edge case or property case

            # cross_link_edge_name = cross_link["edge_name"]
            # cross_link_edge_uri = cross_link["edge_uri"]
            # property_name: hasEntitySlotValue
            # property_uri: "http://vital.ai/ontology/haley-ai-kg#hasEntitySlotValue"

            # cross_link_description = cross_link["description"]

            cross_link_target_collection = cross_link["target_collection"]

            ref_prop = ReferenceProperty(
                name=cross_link_name,
                target_collection=cross_link_target_collection
            )
            references.append(ref_prop)

        properties = collection["properties"]

        property_list = []

        for prop in properties:
            property_name = prop["name"]
            property_uri = prop["property_uri"]
            property_type = prop["type"]
            property_description = prop["description"]

            property_named_vectors = prop.get("named_vectors", [])

            for pnv in property_named_vectors:
                self._append_to_key_list(vector_dict, pnv, property_name)

            # datatypes

            data_type = None

            if property_type == "string":
                data_type = DataType.TEXT

            if property_type == "integer":
                data_type = DataType.INT

            if property_type == "boolean":
                data_type = DataType.BOOL

            if property_type == "date":
                data_type = DataType.DATE

            if property_type == "float":
                data_type = DataType.NUMBER

            p = Property(
                name=property_name,
                # dataType=data_type, # alias
                data_type=data_type,
                description=property_description
            )

            property_list.append(p)

        logging.info(f"Collection Name: {namespace_collection_name}")

        vector_config_list = []

        for key in vector_dict.keys():
            prop_list = vector_dict[key]

            vector_config_list.append(Configure.NamedVectors.text2vec_transformers(
                name=key,
                source_properties=prop_list
            ))

        logging.info(vector_config_list)

        logging.info(f"Creating Collection: {namespace_collection_name}")

        try:

            weaviate_collection = client.collections.create(
                name=namespace_collection_name,
                description=description,
                multi_tenancy_config=Configure.multi_tenancy(multi_tenant),
                vectorizer_config=vector_config_list,
                properties=property_list,
                references=references
            )

            vector_status = VitalVectorStatus()
            vector_status.status = VitalVectorStatusType.OK
            return vector_status

        except Exception as e:
            logging.error(e)

        vector_status = VitalVectorStatus()
        vector_status.status = VitalVectorStatusType.ERROR
        return vector_status

    def _remove_collection(self, collection: dict) -> VitalVectorStatus:

        namespace = self.namespace

        client = self.get_client()

        collection_name = collection["name"]

        multi_prefix = "Multi"

        multi_tenant = collection["multi_tenant"]

        namespace_collection_name = None

        if multi_tenant:
            namespace_collection_name = f"{namespace}_{multi_prefix}_{collection_name}"
        else:
            namespace_collection_name = f"{namespace}_{collection_name}"

        logging.info(f"Removing Collection: {namespace_collection_name}")

        try:
            client.collections.delete(namespace_collection_name)

            vector_status = VitalVectorStatus()
            vector_status.status = VitalVectorStatusType.OK
            return vector_status

        except Exception as e:
            logging.error(e)

        vector_status = VitalVectorStatus()
        vector_status.status = VitalVectorStatusType.ERROR
        return vector_status


    def init_client(self) -> WeaviateClient | None:

        try:

            print(f"Connecting to Endpoint: {self.endpoint}")
            print(f"Connecting to grpc Endpoint: {self.grpc_endpoint}")

            client = weaviate.WeaviateClient(
                connection_params=ConnectionParams.from_params(
                    http_host=self.endpoint,
                    http_port=8080,
                    http_secure=False,
                    grpc_host=self.grpc_endpoint,
                    grpc_port=50051,
                    grpc_secure=False,
                ),

                additional_config=AdditionalConfig(
                    timeout=Timeout(init=30, query=45, insert=120),
                ),
            )

            print(f"Client Connecting...")

            client.connect()

            meta_info = client.get_meta()

            print(meta_info)

            collections = client.collections.list_all()

            collection_count = len(collections)

            print(f"Collection Count: {collection_count}")

            for c_name in collections:
                print(f"{c_name}")
                c = client.collections.get(c_name)
                print(c.config.get())


            self._client = client

            return client

        except Exception as e:
            logging.info(e)

        print(f"Failed to init client to: {self.endpoint}")

        # failure
        self._client = None
        return None

    def destroy_client(self) -> bool:

        try:
            if self._client is not None:
                self._client.close()
                self._client = None
        except Exception as e:
            logging.info(e)
            return False

        return True

    def get_client(self) -> WeaviateClient:

        if self._client is None:
            client = self.init_client()
            return client

        if self._client.is_ready():
            return self._client

        # not ready, re-initialize
        client = self.init_client()
        return client

    def get_collection_identifiers(self) -> List[str]:

        client = self.get_client()

        collection_identifier_list = []

        if client:

            collections = client.collections.list_all()

            for collection_name in collections:
                # logging.info(f"\nCollection: {collection_name}")
                collection_identifier_list.append(collection_name)

        return collection_identifier_list

    def get_vector_collection(self, collection_id: str):
        # underlying vector collection with iterator returning dict
        pass

    def delete_vector_collection(self, collection_id: str):
        # underlying vector collection
        pass

    # mainly use for testing
    # move to internal function and remove from interface
    def init_vital_vector_collections(self):

        vs = VitalSigns()

        vital_home = vs.get_vitalhome()

        logging.info(self.collections)
        logging.info(self.embedding_models)

        for schema_file in self.schema_list:
            logging.info(f"Schema: {schema_file}")
            # loading schema
            # schemas will normally be loaded when
            # service is instantiated into a registry

            schema_path = f"{vital_home}/vital-config/vitalsigns/{schema_file}"

            schema = self.load_weaviate_schema(schema_path)

            collections = schema.get("collections", [])

            for collection in collections:

                collection_name = collection.get("name")
                logging.info(f"Collection: {collection_name}")

                vector_status = self._create_collection(collection)
                logging.info(f"Create Status for Collection: {collection_name}: {vector_status.status}")

    def remove_vital_vector_collections(self):

        vs = VitalSigns()

        vital_home = vs.get_vitalhome()

        logging.info(self.collections)
        logging.info(self.embedding_models)

        for schema_file in self.schema_list:
            logging.info(f"Schema: {schema_file}")
            # loading schema
            # schemas will normally be loaded when
            # service is instantiated into a registry

            schema_path = f"{vital_home}/vital-config/vitalsigns/{schema_file}"

            schema = self.load_weaviate_schema(schema_path)

            collections = schema.get("collections", [])

            for collection in collections:

                collection_name = collection.get("name")
                logging.info(f"Removing Collection: {collection_name}")

                vector_status = self._remove_collection(collection)
                logging.info(f"Remove Status for Collection: {collection_name}: {vector_status.status}")

    def init_vital_vector_service(self) -> VitalVectorStatus:

        client = self.get_client()

        service_graph_id = "SERVICE_GRAPH"

        namespace = self.namespace

        service_graph_collection_name = f"{namespace}_{service_graph_id}"

        # check for service graph collection

        # create service graph collection

        print(f"Creating Collection: {service_graph_collection_name}")

        logging.info(f"Creating Collection: {service_graph_collection_name}")

        description = "SERVICE_GRAPH"

        properties = [
            {"name": "serviceGraphNamespace", "type": "string", "description": "Service Graph Namespace"},
            {"name": "serviceGraphJSON", "type": "string", "description": "Service Graph JSON"}
        ]


        property_list = []

        for prop in properties:
            property_name = prop["name"]
            property_type = prop["type"]
            property_description = prop["description"]

            data_type = None

            if property_type == "string":
                data_type = DataType.TEXT

            if property_type == "integer":
                data_type = DataType.INT

            if property_type == "boolean":
                data_type = DataType.BOOL

            if property_type == "date":
                data_type = DataType.DATE

            if property_type == "float":
                data_type = DataType.NUMBER

            p = Property(
                name=property_name,
                data_type=data_type,
                description=property_description
            )

            property_list.append(p)


        print(property_list)

        serviceGraph = {
            "status": "ok"
        }

        serviceGraphJSON = json.dumps(serviceGraph, indent=4)

        try:

            service_graph_collection = client.collections.create(
                name=service_graph_collection_name,
                description=description,
                multi_tenancy_config=Configure.multi_tenancy(False),
                vectorizer_config=wvcc.Configure.Vectorizer.text2vec_transformers(),
                properties=property_list,
                references=[]
            )


            print(f"Created Collection: {service_graph_collection_name}")

            # insert object

            new_uuid = service_graph_collection.data.insert(
                properties={
                    "serviceGraphNamespace": namespace,
                    "serviceGraphJSON": serviceGraphJSON
                }
            )

            print(f"Created UUID: {new_uuid}")

            vector_status = VitalVectorStatus()
            vector_status.status = VitalVectorStatusType.OK
            return vector_status

        except Exception as e:
            print(e)
            logging.error(e)

        vector_status = VitalVectorStatus()
        vector_status.status = VitalVectorStatusType.ERROR
        return vector_status



    def destroy_vital_vector_service(self) -> VitalVectorStatus:

        client = self.get_client()

        service_graph_id = "SERVICE_GRAPH"

        namespace = self.namespace

        service_graph_collection_name = f"{namespace}_{service_graph_id}"

        # check for service graph collection

        # delete collections

        # remove service graph collection

        print(f"Destroying Collection: {service_graph_collection_name}")

        try:
            client.collections.delete(service_graph_collection_name)

            print(f"Deleted Collection: {service_graph_collection_name}")

            vector_status = VitalVectorStatus()
            vector_status.status = VitalVectorStatusType.OK
            return vector_status

        except Exception as e:
            logging.error(e)

        print(f"Failed to destroy Collection: {service_graph_collection_name}")

        vector_status = VitalVectorStatus()
        vector_status.status = VitalVectorStatusType.ERROR
        return vector_status


    def check_vital_collection(self, collection_class_id: str):
        pass

    def init_vital_collection(self, collection_class_id: str, delete_vital_collection=False):
        pass

    def add_vital_collection(self, collection_class_id: str) -> VitalVectorStatus:
        pass

    def delete_vital_collection(self, collection_class_id: str) -> VitalVectorStatus:
        pass

    def get_vital_collections(self) -> VitalVectorResult:
        pass

    def create_collection(self,
                          collection_class,
                          collection_schema=None,
                          vital_schema=False) -> VitalVectorStatus:

        # called by add_vital_collection
        pass

    def list_tenants(self, collection_class_id: str, *,
                     limit: int = 100, last_tenant_id: str | None = None) -> List[str]:
        pass

    def add_tenant(self, collection_class_id: str, tenant_id: str) -> VitalVectorStatus:
        pass

    def add_tenant_list(self, collection_class_id: str, tenant_id_list: List[str]) -> VitalVectorStatus:
        pass

    def delete_tenant(self, collection_class_id: str, tenant_id: str) -> VitalVectorStatus:
        pass

    def delete_tenant_list(self, collection_class_id: str, tenant_id_list: List[str]) -> VitalVectorStatus:
        pass

    def is_tenant(self, collection_class_id: str, tenant: str, use_tenant_cache=True) -> bool:
        pass

    def add_object(self, collection_class_id: str, tenant_id: str | None, graph_object) -> VitalVectorStatus:
        pass

    def add_object_list(self, collection_class_id: str, tenant_id: str | None,
                         graph_object_list: List) -> VitalVectorStatus:
        pass

    def delete_object(self, collection_class_id: str, tenant_id: str | None, graph_object) -> VitalVectorStatus:
        pass

    def delete_object_list(self, collection_class_id: str, tenant_id: str | None,
                            graph_object_list: List) -> VitalVectorStatus:
        pass

    def delete_object_uri(self, collection_class_id: str, tenant_id: str | None, graph_object_uri: str):
        pass

    def delete_object_uri_list(self, collection_class_id: str, tenant_id: str | None,
                                graph_object_uri_list: List[str]) -> VitalVectorStatus:
        pass

    def delete_object_uuid(self, collection_class_id: str, tenant_id: str | None,
                           graph_object_uuid: str) -> VitalVectorStatus:
        pass

    def delete_object_uuid_list(self, collection_class_id: str, tenant_id: str | None,
                                 graph_object_uuid_list: List[str]) -> VitalVectorStatus:
        pass

    def update_object(self, collection_class_id: str, tenant_id: str | None, graph_object) -> VitalVectorStatus:
        pass

    def update_object_list(self, collection_class_id: str, tenant_id: str | None,
                            graph_object_list: List) -> VitalVectorStatus:
        pass

    def get_object_map_uri(self, collection_class_id: str, tenant_id: str | None, object_uri: str) -> dict | None:
        pass

    def get_object_map_uri_list(self, collection_class_id: str, tenant_id: str | None, object_uri_list: str) -> List[dict]:
        pass

    def get_object_map_uuid(self, collection_class_id: str, tenant_id: str | None, object_uuid: str) -> dict | None:
        pass

    def get_object_map_uuid_list(self, collection_class_id: str, tenant_id: str | None, object_uuid_list: List[str]) -> List[dict]:
        pass

    def index_batch(self, tenant_id: str | None,
                    object_generator: GraphObjectGenerator,
                    *,
                    purge_first: bool = True,
                    graph_id: str | None = None,
                    account_id: str | None = None,
                    global_graph: bool = False,
                    batch_size: int = 10_000):
        # always scope object generator to a tenant or none if global

        namespace = self.namespace

        vs = VitalSigns()

        vital_home = vs.get_vitalhome()

        logging.info(self.collections)
        logging.info(self.embedding_models)

        schema_list = []

        # TODO get from registry

        for schema_file in self.schema_list:
            logging.info(f"Schema: {schema_file}")
            # loading schema
            # schemas will normally be loaded when
            # service is instantiated into a registry

            schema_path = f"{vital_home}/vital-config/vitalsigns/{schema_file}"

            schema = self.load_weaviate_schema(schema_path)

            schema_list.append(schema)

        for page_list in object_generator:
            for obj in page_list:
                go: GraphObject = obj

                logging.info(f"Graph Object: {go.to_json()}")

                clazz_uri = go.get_class_uri()

                for schema in schema_list:
                    collections = schema.get("collections", [])

                    for collection in collections:
                        class_uri = collection.get("class_uri")
                        collection_name = collection.get("name")

                        if clazz_uri == class_uri:
                            logging.info(f"Processing Class URI: {class_uri}")

                            multi_tenant = collection.get("multi_tenant")

                            if not multi_tenant:
                                namespace_collection_name = f"{namespace}_{collection_name}"
                            else:
                                namespace_collection_name = f"{namespace}_Multi_{collection_name}"

                            prop_map = {
                                "kGTenantIdentifier": tenant_id,
                                "accountID": account_id,
                                "knowledgeGraphID": graph_id
                            }

                            properties = collection.get("properties", [])

                            prop_list = go.keys()

                            for p in prop_list:
                                v = go.get_property_value(p).get_value()
                                logging.info(f"Property: {p} : {v}")

                                for col_prop in properties:
                                    col_prop_uri = col_prop.get("property_uri")
                                    if p == col_prop_uri:
                                        col_prop_name = col_prop.get("name")
                                        prop_map[col_prop_name] = v
                                        break

                            logging.info(prop_map)

                            filtered_map = {
                                key: value
                                for key, value in prop_map.items() if value is not None
                            }

                            logging.info(filtered_map)

                            uuid = generate_uuid5(filtered_map)

                            client = self.get_client()

                            if not multi_tenant:
                                logging.info(f"Getting Collection: {namespace_collection_name}")
                                index_collection = client.collections.get(namespace_collection_name)
                            else:
                                logging.info(f"Getting Collection: {namespace_collection_name} with Tenant: {tenant_id}")
                                index_collection = client.collections.get(namespace_collection_name).with_tenant(tenant_id)

                            insert_uuid = index_collection.data.insert(
                                properties=filtered_map,
                                uuid=uuid
                            )

                            logging.info(f"Inserted Object: {insert_uuid}")

    def index_batch_file(self, tenant_id: str | None, file_path: str,
                         *, purge_first: bool = True, batch_size: int = 10_000):
        pass

    def index_multi_tenant_batch(self, object_generator: GraphObjectGenerator,
                                 *, all_global: bool = False, purge_first: bool = True, batch_size: int = 10_000):

        # tenant determined by object values

        pass

    def index_multi_tenant_batch_file(self, file_path: str,
                                      *, all_global: bool = False, purge_first: bool = True,
                                      batch_size: int = 10_000):

        # tenant determined by object values

        pass

    def vector_query(self, *, weaviate_query: WeaviateVectorQuery) -> WeaviateResultList:
        pass

    def metaql_select_query(self, *, graph_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology] = None) -> VitalVectorResultList:
        pass

    def metaql_graph_query(self, *, graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology] = None) -> VitalVectorResultList:
        pass
