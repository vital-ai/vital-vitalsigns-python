import logging
import time

from vital_ai_vitalsigns.service.vitalservice_manager import VitalServiceManager
from vital_ai_vitalsigns.vitalsigns import VitalSigns

"""
graph_database:
    virtuoso_username: "marc"
    virtuoso_password: "mittens97"
    virtuoso_endpoint: "http://localhost:8890/"

vector_database:
    weaviate_user: ""
    weaviate_api_key: ""
    weaviate_endpoint: "localhost"
    weaviate_vector_endpoint: "localhost"
    weaviate_grpc_endpoint: "localhost"

"""


def main():

    logging.basicConfig(level=logging.INFO)

    # logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger("urllib3").setLevel(logging.DEBUG)

    print('Vitalservice Manager Test')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vitalhome = vs.get_vitalhome()

    print(f"vitalhome: {vitalhome}")

    config = vs.get_config()

    print(config)

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:

        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)

        print(vitalservice)

    vitalservice = vitalservice_manager.get_vitalservice("local_service")

    # initialize graph service
    # destroy graph service

    graph_service = vitalservice.graph_service

    vitalservice_name = vitalservice.get_vitalservice_name()

    print(f"vitalservice name: {vitalservice_name}")

    vitalservice_namespace = vitalservice.get_vitalservice_namespace()

    print(f"vitalservice namespace: {vitalservice_namespace}")


    exit(1)

    status = None

    status = graph_service.initialize_service(vitalservice_namespace)

    print(f"initialize status: {status}")

    new_graph_uri = f"urn:{vitalservice_namespace}_test1"

    ##############################
    status = graph_service.create_graph( new_graph_uri, namespace=vitalservice_namespace )
    print(f"create graph status: {status}")

    # time.sleep(0.1)

    status = graph_service.delete_graph( new_graph_uri, namespace=vitalservice_namespace )
    print(f"delete graph status: {status}")
    ##############################

    status = graph_service.destroy_service(vitalservice_namespace)

    print(f"destroy status: {status}")

    # initialize vector service
    # destroy vector service

    # initialize managed service
    # destroy managed service


    # import wordnet frame data into tenant (graph + vector)
    # using block file

    # test frame queries

    ######################################################

    graph_uri = 'http://vital.ai/graph/wordnet-graph-1'

    query = """
            SELECT DISTINCT ?uri WHERE {
                ?happyNode vital-core:hasName ?name .
                ?name bif:contains "happy"

                {
                    ?edge vital-core:hasEdgeSource ?happyNode .
                    ?edge vital-core:hasEdgeDestination ?uri .
                } UNION {
                    ?edge vital-core:hasEdgeDestination ?happyNode .
                    ?edge vital-core:hasEdgeSource ?uri .
                }
            }
        """

    # result_list = vitalservice.graph_service.query(graph_uri, query, limit=500, offset=0, resolve_objects=True)
    # print(f"Result Count: {len(result_list)}")

    # for result in result_list:
    #    go = result.graph_object
    #    print(go.to_rdf())


if __name__ == "__main__":
    main()

