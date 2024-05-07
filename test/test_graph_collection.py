from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.embedding.embedding_model import EmbeddingModel
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName


def main():
    print('Hello World')

    embedder = EmbeddingModel()

    vs = VitalSigns()
    vs.put_embedding_model(embedder.get_model_id(), embedder)

    graph = GraphCollection()

    class_uri = VITAL_Node().get_class_uri()

    property_uris = [Property_hasName.get_uri()]

    graph.set_vector_properties(class_uri, property_uris)

    node1 = VITAL_Node()
    node1.URI = 'uri:node1'
    node1.name = 'Omelet'

    node2 = VITAL_Node()
    node2.URI = 'uri:node2'
    node2.name = 'Pork Chop'

    node3 = VITAL_Node()
    node3.URI = 'uri:node3'
    node3.name = 'Coffee'

    node4 = VITAL_Node()
    node4.URI = 'uri:node4'
    node4.name = 'Orange Juice'

    node5 = VITAL_Node()
    node5.URI = 'uri:node5'
    node5.name = 'Spaghetti'

    graph.add_objects([node1, node2, node3, node4, node5])

    node = graph.get('uri:node2')

    print('Look up Node: ' + str(node.name))

    # query = 'pig'
    # query = 'apple'
    # query = 'noodles'
    # query = 'tea'
    query = 'frittata'

    print('Search for: ' + query)

    results = graph.search(query)

    if results is not None:
        re = results[0]
        obj = re.graph_object
        score = re.score
        print('Top Result for: ' + query + ': ' + str(obj.name) + " (" + str(score) + ")")
        print(obj.to_json())
        print(obj.to_rdf())
    else:
        print('No results')

    # for r in results:
    #    print(r)

    sparql_results = graph.sparql_query("SELECT ?s ?p ?o WHERE { ?s ?p ?o } ORDER BY ?s ?p")

    sparql_result_count = len(sparql_results)
    print('Sparql Result Count: ' + str(sparql_result_count))

    for row in sparql_results:
        print(f"Subject: {row['s']}, Property: {row['p']}, Object: {row['o']}")


if __name__ == "__main__":
    main()
