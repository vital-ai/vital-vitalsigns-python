import gzip
import json
import uuid
from typing import List
import weaviate
from com_vitalai_domain_wordnet.model.SynsetNode import SynsetNode
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from weaviate.config import AdditionalConfig, Timeout
from weaviate.connect import ConnectionParams
import weaviate.classes.config as wvcc
from weaviate.classes.query import Filter
import time


def main():

    print('Weaviate Wordnet Query')

    start_time = time.time()

    vs = VitalSigns()

    print("VitalSigns Initialized")

    elapsed_time = time.time() - start_time

    print(f"Initialization took {elapsed_time:.4f} seconds.")

    tenant_id = "wordnet-graph-1"
    graph_uri = "http://vital.ai/graph/wordnet-graph-1"

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
            timeout=Timeout(init=20, query=45, insert=120),
        ),
    )

    start_time = time.time()

    client.connect()

    elapsed_time = time.time() - start_time

    print(f"Connecting took {elapsed_time:.4f} seconds.")

    meta_info = client.get_meta()

    print(meta_info)

    col_configs = client.collections.list_all()

    # Print all collection names
    for name in col_configs:
        print(name)

    # Print one collection configuration
    # print(col_configs["MyCollection"])
    # print(col_configs["MyCollection"].properties)  # property schema
    # print(col_configs["MyCollection"].vectorizer_config)  # vectorizer configuration
    # print(col_configs["MyCollection"].vectorizer)  # vectorizer name


    # synset_node_collection = client.collections.get("SynsetNode")

    # print(f"Node collection Size: {len(synset_node_collection)}")

    # response = synset_node_collection.query.near_text(
    #    query="happy",
    #    limit=10
    # )

    # for obj in response.objects:
        # print(obj)
     #   pass

    """
    uri_value = "http://vital.ai/haley.ai/app/NounSynsetNode/1716488380173_691740102"

    response = synset_node_collection.query.fetch_objects(
        filters=Filter.by_property("uRI").equal(uri_value),
        limit=1
    )

    print(response)

    for obj in response.objects:
        go_uuid = obj.uuid
        print(go_uuid)

    """

    reference_list = [
        "edge_WordnetAlsoSee",
        "edge_WordnetAntonym",
        "edge_WordnetAttribute",
        "edge_WordnetCause",
        "edge_WordnetDerivationallyRelatedForm",
        "edge_WordnetDerivedFromAdjective",
        "edge_WordnetDomainOfSynset_Region",
        "edge_WordnetDomainOfSynset_Topic",
        "edge_WordnetDomainOfSynset_Usage",
        "edge_WordnetEntailment",
        "edge_WordnetHypernym",
        "edge_WordnetHyponym",
        "edge_WordnetInstanceHypernym",
        "edge_WordnetInstanceHyponym",
        "edge_WordnetMemberHolonym",
        "edge_WordnetMemberMeronym",
        "edge_WordnetMemberOfThisDomain_Region",
        "edge_WordnetMemberOfThisDomain_Topic",
        "edge_WordnetMemberOfThisDomain_Usage",
        "edge_WordnetPartHolonym",
        "edge_WordnetParticiple",
        "edge_WordnetPartMeronym",
        "edge_WordnetPertainym_PertainsToNouns",
        "edge_WordnetSimilarTo",
        "edge_WordnetSubstanceHolonym",
        "edge_WordnetSubstanceMeronym",
        "edge_WordnetVerbGroup"
    ]

    # Create the cross-reference fields part of the query
    fields = '\n'.join([f'{ref} {{\n  ... on SynsetNode {{\n    uRI\n    hasName\n    subclassURI\n  }}\n}}' for ref in reference_list])

    search_text = "horse"

    query = f"""
    {{
      Get {{
        SynsetNode(
          nearText: {{
            concepts: ["{search_text}"]
          }}
        ) {{
          uRI
          hasName
          hasGloss
          subclassURI
          {fields}
        }}
      }}
    }}
    """

    print(query)

    try:
        start_time = time.time()

        response = client.graphql_raw_query(query)

        # print(response)

        get_response = response.get

        nodes = get_response['SynsetNode']

        elapsed_time = time.time() - start_time

        print(f"Query took {elapsed_time:.4f} seconds.")

        print(f"Result Count: {len(nodes)}")

        for n in nodes:
            for key, value in n.items():
                if value:
                    print(f"{key}: {value}")
                    if isinstance(value, List):
                        for ref in value:
                            print(f"  ref: {key}")
                            print(f"  URI: {ref['uRI']}")
                            print(f"  hasName: {ref['hasName']}")
                            print(f"  subclassURI: {ref['subclassURI']}\n")

    except Exception as e:
        print(f"Exception: {e}")

    finally:
        # client.close()
        pass

    client.close()


if __name__ == "__main__":
    main()
