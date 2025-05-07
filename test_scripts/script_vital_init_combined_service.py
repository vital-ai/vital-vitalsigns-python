import yaml
from vital_ai_vitalsigns.vitalsigns import VitalSigns
import weaviate
from weaviate.collections.classes.config import Configure, Property, DataType, ReferenceProperty
from weaviate.classes.query import Filter
from weaviate.collections.classes.grpc import MetadataQuery
from weaviate.config import AdditionalConfig, Timeout
from weaviate.connect import ConnectionParams


def load_weaviate_schema():
    with open("../vector_schema/kgraph_weaviate_schema.yaml", "r") as config_stream:
        try:
            return yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

"""
  - name: KGEntity
    description: "Knowledge Graph Entity"
    class_uri: "http://vital.ai/ontology/haley-ai-kg#KGEntity"
    named_vectors:
      - name: value
    properties:
      - name: uri
        property_uri: "http://vital.ai/ontology/vital-core#URIProp"
        type: string
        description: "Unique identifier for the entity"
      - name: name
        property_uri: "http://vital.ai/ontology/vital-core#hasName"
        type: string
        named_vectors:
          - value
        description: "Name of the entity"
      - name: kGEntityType
        property_uri: "http://vital.ai/ontology/haley-ai-kg#hasKGEntityType"
        type: string
        description: "Type Identifier of the entity"
      - name: kGEntityTypeDescription
        property_uri: "http://vital.ai/ontology/haley-ai-kg#hasKGEntityTypeDescription"
        type: string
        named_vectors:
          - type
        description: "Type Description of the entity"
    cross_links:
      - name: edge_Edge_hasEntityKGFrame
        cross_link_type: Edge
        edge_name: Edge_hasEntityKGFrame
        edge_uri: "http://vital.ai/ontology/haley-ai-kg#Edge_hasEntityKGFrame"
        target_collection: KGFrame
        description: "Cross-link to KGFrame"

"""


def create_dict_with_keys(keys):
    return {key: [] for key in keys}


def append_to_key_list(d, key, value):
    if key in d:
        d[key].append(value)
    else:
        print(f"Key '{key}' not found in the dictionary")


def handle_collection(client, namespace, collection):

    collection_name = collection["name"]

    multi_prefix = "Multi"

    # multi-tenant
    # handle multiple vectors

    multi_tenant = collection["multi_tenant"]

    if multi_tenant:
        namespace_collection_name = f"{namespace}_{multi_prefix}_" + collection_name
    else:
        namespace_collection_name = f"{namespace}_" + collection_name

    description = collection["description"]
    class_uri = collection["class_uri"]
    named_vectors = collection["named_vectors"]

    named_vector_list = []
    for named_vector in named_vectors:
        name = named_vector["name"]
        named_vector_list.append(name)

    vector_dict = create_dict_with_keys(named_vector_list)

    cross_links = collection.get("cross_links", [])

    references = []

    for cross_link in cross_links:
        cross_link_name = cross_link["name"]
        cross_link_type = cross_link["cross_link_type"]
        cross_link_edge_name = cross_link["edge_name"]
        cross_link_edge_uri = cross_link["edge_uri"]
        cross_link_description = cross_link["description"]
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
            append_to_key_list(vector_dict, pnv, property_name)

        # datatypes

        data_type=None

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

    print(f"Collection Name: {namespace_collection_name}")

    vector_config_list = []

    for key in vector_dict.keys():

        prop_list = vector_dict[key]

        vector_config_list.append(Configure.NamedVectors.text2vec_transformers(
            name=key,
            source_properties=prop_list
        ))

    print(vector_config_list)

    print(f"Creating: {namespace_collection_name}")

    client.collections.create(
        name=namespace_collection_name,
        description=description,
        multi_tenancy_config=Configure.multi_tenancy(multi_tenant),
        vectorizer_config=vector_config_list,
        properties=property_list,
        references=references
    )


def main():

    print('Vital Init Combined Service')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    service_namespace = "VITALTEST"

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

    vitalservice = vitalservice_manager.get_vitalservice("local_kgraph")

    graph_list = vitalservice.list_graphs(account_id="account1")

    for g in graph_list:
        print(f"Graph URI: {g.get_namespace()}")

    weaviate_endpoint = vitalservice.vector_service.endpoint
    weaviate_grpc_endpoint = vitalservice.vector_service.grpc_endpoint
    weaviate_vector_endpoint = vitalservice.vector_service.vector_endpoint


    client = weaviate.WeaviateClient(
        connection_params=ConnectionParams.from_params(
            http_host=weaviate_endpoint,
            http_port=8080,
            http_secure=False,
            grpc_host=weaviate_grpc_endpoint,
            grpc_port=50051,
            grpc_secure=False,
        ),

        additional_config=AdditionalConfig(
            timeout=Timeout(init=2, query=45, insert=120),
        ),
    )

    client.connect()

    weaviate_schema = load_weaviate_schema()

    schema_name = weaviate_schema["name"]
    namespace = weaviate_schema["namespace"]

    print(f"Initializing Collection: {schema_name} : Namespace: {namespace}")

    collections = weaviate_schema["collections"]

    print(collections)

    for collection in collections:
        handle_collection(client, namespace, collection)

    client.close()

    # create service graph in virtuoso

    # init weaviate schema


if __name__ == "__main__":
    main()


