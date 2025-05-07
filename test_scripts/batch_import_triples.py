from vital_ai_vitalsigns.vitalsigns import VitalSigns
import gzip
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, POST, DIGEST

def send_sparql_update(sparql_endpoint, virtuoso_username, virtuoso_password, sparql_query):
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setMethod(POST)
    sparql.setQuery(sparql_query)
    sparql.setCredentials(virtuoso_username, virtuoso_password)
    sparql.setHTTPAuth(DIGEST)

    sparql.setReturnFormat("json")
    try:
        response = sparql.query().convert()
        return response
    except Exception as e:
        print(f"Error executing SPARQL query: {e}")
        print(sparql_query)
        raise


def read_nt_file_in_batches(file_path, batch_size=1000):

    graph = Graph()
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        batch = []
        for line in f:
            try:
                graph.parse(data=line, format="nt")
                for triple in graph:
                    batch.append(triple)
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                graph.remove((None, None, None))
            except Exception as e:
                print(f"Error parsing line: {e}")
        if batch:
            yield batch

def batch_insert_triples(graph_uri, file_path, batch_size=1000):

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

    vitalservice = vitalservice_manager.get_vitalservice("local_kgraph")

    graph_list = vitalservice.list_graphs(account_id="account1")

    for g in graph_list:
        print(f"Graph URI: {g.get_graph_uri()}")

    virtuoso_username = vitalservice.graph_service.username
    virtuoso_password = vitalservice.graph_service.password
    virtuoso_endpoint = vitalservice.graph_service.endpoint

    sparql_endpoint = f"{virtuoso_endpoint}/sparql-auth"

    for batch in read_nt_file_in_batches(file_path, batch_size):
        triples_str = "\n".join([format_triple(triple) for triple in batch])
        sparql_query = f"""
        INSERT DATA {{
            GRAPH <{graph_uri}> {{
                {triples_str}
            }}
        }}
        """

        send_sparql_update(sparql_endpoint, virtuoso_username, virtuoso_password, sparql_query)

        print(f"Inserted {len(batch)} triples")

def format_triple(triple):
    s, p, o = triple
    s = s.n3()  # Serializes URI or Literal to N-Triples format
    p = p.n3()
    o = o.n3()
    return f"{s} {p} {o} ."


def main():

    print('Batch Import Triples')

    graph_uri = "http://vital.ai/graph/wordnet-graph-1"

    file_path = "../test_data/wordnet-0.0.1.nt.gz"

    batch_insert_triples(graph_uri, file_path, batch_size=1000)


if __name__ == "__main__":
    main()
