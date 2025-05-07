import json
import requests
import weaviate
import yaml
from ai_haley_kg_domain.model.KGEntity import KGEntity
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from weaviate.collections.classes.grpc import MetadataQuery, TargetVectors
from weaviate.collections.classes.tenants import Tenant
from weaviate.config import AdditionalConfig, Timeout
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5


def load_weaviate_schema():
    with open("../vector_schema/kgraph_weaviate_schema.yaml", "r") as config_stream:
        try:
            return yaml.safe_load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)


def insert_objects(weaviate_schema, client, tenant_name, graph_object_list):

    # first find edges in list and generate list for cross-refs
    # if endpoints are on the list then can use those URI/uuids
    # otherwise will need to get from db to determine uuids

    namespace = weaviate_schema['namespace']

    collections = weaviate_schema["collections"]

    for go in graph_object_list:

        go_class_uri = go.get_class_uri()

        for collection in collections:

            collection_name = collection["name"]

            namespace_collection_name = f"{namespace}_Multi_{collection_name}"

            class_uri = collection["class_uri"]

            if class_uri == go_class_uri:

                print(f"Class URI: {go_class_uri}")

                print(collection)

                properties = collection["properties"]

                print(go.to_json())

                insert_obj_dict = {}

                for go_prop_uri, go_prop_value in go.items():
                    for p in properties:
                        property_uri = p["property_uri"]
                        if property_uri == go_prop_uri:
                            print(f"{go_prop_uri}: {go_prop_value}")

                            prop_name = p["name"]

                            # so far handle string values
                            insert_obj_dict[prop_name] = str(go_prop_value)

                print(f"Object To Insert: {insert_obj_dict}")

                uuid = generate_uuid5(insert_obj_dict)

                tenant_collection = client.collections.get(namespace_collection_name).with_tenant(tenant_name)

                insert_uuid = tenant_collection.data.insert(
                    properties=insert_obj_dict,
                    uuid=uuid
                )

                print(f"Inserted Object: {insert_uuid}")


def main():
    print('Vital Combined Service Test')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    # service graph for virtuoso to go into:
    # SERVICE_GRAPH_URI = "urn:SERVICE_GRAPH" + '_' + namespace

    # like:
    # urn:SERVICE_GRAPH_VITALTEST
    # vital segment to have
    # graph uri in segment_id, which determines namespace
    # and vitalservice name in name property for human friendly name
    # constants are currently used in the memory vitalservice impl

    service_namespace = "VITALTEST"

    # initially separately test weaviate with KG classes and vector queries

    # collection naming convention:

    # namespace (all caps, alpha only)
    # _ (underscore)
    # Multi (if multi-tenant)
    # _ (underscore, if Multi)
    # Collection name, starting with uppercase

    # example:
    # VITALTEST_Multi_KGFrame
    # and
    # VITALTEST_KGDocument

    # get instance of combined service

    # consider a new account by uri

    # check if graph/tenants exist
    # should be no

    # add graph to virtuoso for account
    # add tenant to weaviate classes for account

    # check if graph/tenant exists
    # should be yes

    # insert data into combined service
    # should insert into weaviate and virtuoso

    # get from combined service
    # should get from virtuoso

    # graph query from combined service
    # should go to virtuoso
    # resolve objects true/false

    # vector query from combined service
    # should go to weaviate
    # resolved objects true/false, should resolve from virtuoso

    # vector/graph query from combined service
    # should go to weaviate and use cross-references
    # resolve objects true/false, should resolve from virtuoso

    # delete account
    # should remove tenant from weaviate classes
    # should delete graph from virtuoso and reference from service graph

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

    vitalservice = vitalservice_manager.get_vitalservice("local_kgraph")

    graph_list = vitalservice.list_graphs(account_id="account1")

    for g in graph_list:
        print(f"Graph URI: {g.get_graph_uri()}")

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
            timeout=Timeout(init=20, query=45, insert=120),
        ),
    )

    client.connect()

    weaviate_schema = load_weaviate_schema()

    schema_name = weaviate_schema["name"]

    namespace = weaviate_schema["namespace"]

    collection_list = weaviate_schema["collections"]

    collection_name_list = []

    for collection in collection_list:
        collection_name = collection["name"]
        collection_name_list.append(collection_name)

    for collection_name in collection_name_list:
        print(collection_name)

    client.close()
    exit(1)

    kgentity_collection_name = namespace + "_Multi_" + "KGEntity"

    kgentity_collection = client.collections.get(kgentity_collection_name)

    tenant_name = "account123"

    tenant_obj = kgentity_collection.tenants.get_by_name(tenant_name)

    print(f"Before: {tenant_obj}")

    if not tenant_obj:
        kgentity_collection.tenants.create(
            tenants=[
                Tenant(name=tenant_name),

            ]
        )

    tenant_obj = kgentity_collection.tenants.get_by_name(tenant_name)

    print(f"After: {tenant_obj}")

    tenants = kgentity_collection.tenants.get()

    for name, object in tenants.items():
        print(f"Tenant: {name} : {object}")

    kgentity = KGEntity()
    kgentity.URI = URIGenerator.generate_uri()

    kgentity.name = "John Smith"
    kgentity.kGraphDescription = "Friendly person from New Jersey"
    kgentity.kGEntityType = "urn:Person"
    kgentity.kGEntityTypeDescription = "Person"

    graph_object_list = [
        kgentity
    ]

    tenant_kgentity_collection = kgentity_collection.with_tenant(tenant_name)

    # insert_objects(weaviate_schema, client, tenant_name, graph_object_list)

    # test queries with:
    # entity --> frame --> slot paths
    # person --> personal info --> phone number

    # test wordnet data with:
    # frame --> slot --> entity (near vector X )
    # frame --> slot --> entity ( filter URI )

    # iterate over all objects in tenant

    # If using named vectors, you can specify ones to include e.g. ['title', 'body'], or True to include all
    for item in tenant_kgentity_collection.iterator(
            include_vector=True
    ):
        print(item.properties)
        print(item.vector)

    # do search of inserted data

    response = tenant_kgentity_collection.query.near_text(
        query="Chemistry",
        limit=100,
        target_vector=["value"],
        return_metadata=MetadataQuery(distance=True)
    )

    for o in response.objects:
        print(o.properties)
        print(o.metadata.distance)

    url = "http://localhost:9090/vectors"

    headers = {
        "Content-Type": "application/json"
    }

    value_data = {
        "text": "Friendly person from New Jersey",
    }

    type_data = {
        "text": "Human"
    }

    response = requests.post(url, headers=headers, data=json.dumps(value_data))

    if response.status_code == 200:
        result = response.json()

        text = result.get("text")
        value_vector = result.get("vector", [])

    response = requests.post(url, headers=headers, data=json.dumps(type_data))

    if response.status_code == 200:
        result = response.json()

        text = result.get("text")
        type_vector = result.get("vector", [])

    print(f"Type Vector: {type_vector}")
    print(f"Value Vector: {value_vector}")

    response = tenant_kgentity_collection.query.near_vector(

        near_vector={
            "type": type_vector,
            "value": value_vector,
        },

        limit=100,
        target_vector=TargetVectors.manual_weights(
            {
                "type": 10,
                "value": 10
            }),
        return_metadata=MetadataQuery(distance=True)
    )

    for o in response.objects:
        print(o.properties)
        print(o.metadata.distance)

    # delete all inserted objects by iterating through collection

    client.close()


if __name__ == "__main__":
    main()


