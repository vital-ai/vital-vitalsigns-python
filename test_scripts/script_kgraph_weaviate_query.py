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

def main():

    print('KGraph Weaviate Query Test')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    client = weaviate.WeaviateClient(
        connection_params=ConnectionParams.from_params(
            http_host="localhost",
            http_port=8080,
            http_secure=False,
            grpc_host="localhost",
            grpc_port=50051,
            grpc_secure=False
        ),
        additional_config=AdditionalConfig(
            timeout=Timeout(init=20, query=45, insert=120),
        )
    )

    client.connect()

    namespace = "KGRAPH"

    class_name = "KGAgent"

    kg_agent_collection_name = f"{namespace}_{class_name}"

    kg_agent_collection = client.collections.get(kg_agent_collection_name)

    # tenants = kg_agent_collection.tenants.get()
    # for name, object in tenants.items():
    #    print(f"Tenant: {name} : {object}")

    for item in kg_agent_collection.iterator(include_vector=True):
        print(item.properties)
        print(item.vector)

    url = "http://localhost:9090/vectors"

    headers = {
        "Content-Type": "application/json"
    }

    value_data = {
        "text": "shoes"
    }

    value_vector = None

    response = requests.post(url, headers=headers, data=json.dumps(value_data))

    if response.status_code == 200:

        result = response.json()

        text = result.get("text")

        value_vector = result.get("vector", [])

        print(f"Value Vector: {value_vector}")

    response = kg_agent_collection.query.near_vector(

        # can use multi-vector
        near_vector={
            "value": value_vector,
        },

        limit=100,
        # can use multi-vector scaling
        target_vector=TargetVectors.manual_weights(
            {
                "value": 10
            }),
        return_metadata=MetadataQuery(distance=True)
    )

    for o in response.objects:
        print(o.properties)
        print(o.metadata.distance)

    # client.collections.delete(kg_agent_collection_name)

    client.close()

if __name__ == "__main__":
    main()


