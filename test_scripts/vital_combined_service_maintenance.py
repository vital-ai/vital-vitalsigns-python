from vital_ai_vitalsigns.vitalsigns import VitalSigns
import json
import uuid
from typing import List
import weaviate
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from weaviate.collections.classes.config import CollectionConfigSimple, PropertyConfig
from weaviate.config import AdditionalConfig, Timeout
from weaviate.connect import ConnectionParams


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def main():
    print('Vital Combined Service Maintenance')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

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

    try:

        client.connect()

        meta_info = client.get_meta()

        # print(meta_info)

        json_data = json.dumps(meta_info, indent=4)

        print(json_data)

        col_configs = client.collections.list_all()

        delete_collections = []

        # Print all collection names
        for name in col_configs:
            print(name)

            coll_config: CollectionConfigSimple = col_configs[name]

            coll_dict = coll_config.to_dict()

            coll_data = json.dumps(coll_dict, indent=4, cls=CustomEncoder)

            print(coll_data)

            # if "VITALTEST" in name:
            #    delete_collections.append(name)

        # Print one collection configuration
        # print(col_configs["MyCollection"])
        # print(col_configs["MyCollection"].properties)  # property schema
        # print(col_configs["MyCollection"].vectorizer_config)  # vectorizer configuration
        # print(col_configs["MyCollection"].vectorizer)  # vectorizer name

        for c in delete_collections:
            # print(f"Deleting collection {c}")
            # client.collections.delete(c)
            pass

    except Exception as e:
        print(f"Exception: {e}")

    finally:
        # client.close()
        pass

    client.close()


if __name__ == "__main__":
    main()



