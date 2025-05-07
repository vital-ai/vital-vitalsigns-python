import time
from vital_ai_vitalsigns.service.graph.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns

def time_function(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        time_difference_ms = (end_time - start_time) * 1000
        print(f"The function '{func.__name__}' took {round(time_difference_ms)} ms.")
        return result
    return wrapper


def time_function_call(func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    time_difference_ms = (end_time - start_time) * 1000
    print(f"The function '{func.__name__}' took {round(time_difference_ms)} ms.")
    return result


def main():

    print('Test Wordnet SPARQL')

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
        print(f"Graph URI: {g.get_namespace()}")

    virtuoso_username = vitalservice.graph_service.username
    virtuoso_password = vitalservice.graph_service.password
    virtuoso_endpoint = vitalservice.graph_service.endpoint

    print(virtuoso_endpoint)

    virtuoso_graph_service = VirtuosoGraphService(
        username=virtuoso_username,
        password=virtuoso_password,
        endpoint=virtuoso_endpoint,
        base_uri="http://vital.ai",
        namespace="graph"
    )

    graph_uri = 'wordnet-graph-1'

    query_orig = """
PREFIX vital: <http://vital.ai/ontology/vital-core#>

SELECT ?connectedNode ?predicate ?object
WHERE {
    GRAPH <http://vital.ai/graph/wordnet-graph-1> {
        {
            SELECT DISTINCT ?connectedNode
            WHERE {
                ?happyNode vital:hasName ?name .
                FILTER(CONTAINS(LCASE(STR(?name)), "happy"))

                {
                    ?edge vital:hasEdgeSource ?happyNode .
                    ?edge vital:hasEdgeDestination ?connectedNode .
                } UNION {
                    ?edge vital:hasEdgeDestination ?happyNode .
                    ?edge vital:hasEdgeSource ?connectedNode .
                }
            }
        }

        ?connectedNode ?predicate ?object .
    }
}
ORDER BY ?connectedNode
    """

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

    # start_time = time.time()

    result_list = time_function_call(
        virtuoso_graph_service.query,
        graph_uri, query, limit=500, offset=0, resolve_objects=True)

    # end_time = time.time()

    print(f"Result Count: {len(result_list)}")

    for result in result_list:
        go = result.graph_object
        print(go.to_rdf())

    # object_uri = "http://vital.ai/haley.ai/app/AdjectiveSynsetNode/1716488384202_691800091"

    # obj = virtuoso_graph_service.get_object(object_uri, graph_uri=graph_uri)

    # print(obj.to_rdf())

    # time_difference_ms = (end_time - start_time) * 1000

    # print(f"The function call took {round(time_difference_ms)} ms.")


if __name__ == "__main__":
    main()

