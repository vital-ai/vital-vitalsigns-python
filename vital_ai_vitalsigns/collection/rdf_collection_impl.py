from rdflib import Graph, URIRef


class RdfCollectionImpl:
    def __init__(self):
        self.graph = Graph()

    def add_triples(self, nt_string: str):
        """
        Add multiple triples to the graph from an NT string.
        :param nt_string: Multiple triples in NT format.
        """
        self.graph.parse(data=nt_string, format="nt")

    def clear_graph(self):
        """
        Clear all triples from the graph.
        """
        self.graph = Graph()  # Reinitialize to clear

    def query_graph(self, sparql_query: str):
        """
        Query the graph using a SPARQL query.
        :param sparql_query: The SPARQL query string.
        :return: The query results.
        """
        return self.graph.query(sparql_query)

    def delete_triples(self, subject_uri: str):
        """
        Delete all triples with the specified subject URI.
        :param subject_uri: The subject URI as a string.
        """
        subject = URIRef(subject_uri)
        self.graph.remove((subject, None, None))
