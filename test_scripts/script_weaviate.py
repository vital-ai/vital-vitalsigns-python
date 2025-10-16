import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout
import weaviate.classes.config as wvcc
from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():

    print('Test Weaviate Client')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vital_home = vs.get_vitalhome()

    print(f"VitalHome: {vital_home}")

    vs_config = vs.get_config()

    print(vs_config)

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

    # vitalservice = vitalservice_manager.get_vitalservice("local_service")

    vitalservice = vitalservice_manager.get_vitalservice("local_kgraph_test")


    # assumes weaviate vector service type

    weaviate_endpoint = vitalservice.vector_service.endpoint
    weaviate_grpc_endpoint = vitalservice.vector_service.grpc_endpoint
    weaviate_vector_endpoint = vitalservice.vector_service.vector_endpoint

    print(f"Weaviate Endpoint: {weaviate_endpoint}")
    print(f"Weaviate GRPC Endpoint: {weaviate_grpc_endpoint}")

    client = weaviate.WeaviateClient(
        connection_params=ConnectionParams.from_params(
            http_host=weaviate_endpoint,
            http_port=8080,
            http_secure=False,
            grpc_host=weaviate_grpc_endpoint,
            grpc_port=50051,
            grpc_secure=False,
        ),

        # skip_init_checks=True,

        # auth_client_secret=weaviate.auth.AuthApiKey(weaviate_api_key),

        # Values in seconds
        additional_config=AdditionalConfig(
            timeout=Timeout(init=30, query=45, insert=120),
        ),
    )


    try:

        client.connect()

        meta_info = client.get_meta()

        print(meta_info)

        collections = client.collections.list_all()

        for c_name in collections:
            print(f"{c_name}")
            c = client.collections.get(c_name)
            print(c.config.get())


    except Exception as e:
        print(e)

    finally:
        client.close()

    # client.close()

    exit(0)

    try:

        try:
            articles = client.collections.get("TestArticle")
            articles_config = articles.config.get()
            if articles_config:
                print(articles_config)
                client.collections.delete("TestArticle")
        except:
            pass

        articles = client.collections.create(
            name="TestArticle",
            vectorizer_config=wvcc.Configure.Vectorizer.text2vec_transformers(),
            properties=[
                wvcc.Property(
                    name="title",
                    data_type=wvcc.DataType.TEXT
                )
            ]
        )

        new_uuid = articles.data.insert(
            properties={
                "title": "Zebras are great."
            }
        )

        new_uuid = articles.data.insert(
            properties={
                "title": "Cats are curious."
            }
        )

        response = articles.query.near_text(
            query="dogs",
            limit=10
        )

        for o in response.objects:
            print(o.properties)

        # articles = client.collections.get("TestArticle")

        articles_config = articles.config.get()

        print(articles_config)

        client.collections.delete("TestArticle")

    finally:
        client.close()


if __name__ == "__main__":
    main()
