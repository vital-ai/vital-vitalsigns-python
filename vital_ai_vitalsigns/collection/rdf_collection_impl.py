from typing import List, TypeVar
from rdflib import Graph, URIRef, Dataset
from vital_ai_vitalsigns.impl.rdflib.rdflib_sparql_impl import RDFlibSparqlImpl
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.metaql_result import MetaQLResult
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.vital_name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery, SelectQuery as MetaQLSelectQuery

G = TypeVar('G', bound='GraphObject')


# TODO switch to using graph id in place of graph_uri to
# match service definition?

class RdfCollectionImpl(RDFlibSparqlImpl):
    def __init__(self, *, multigraph=False):
        super().__init__(multigraph=multigraph)

    def is_multigraph(self) -> bool:
        return self._multigraph

    def add_triples(self, nt_string: str, *, graph_uri: str = None):
        """
        Add multiple triples to the graph from an NT string.
        :param graph_uri:
        :param nt_string: Multiple triples in NT format.
        """
        self.graph.parse(data=nt_string, format="nt")

    def clear_graph(self):
        """
        Clear all triples from the graph.
        """
        if self._multigraph:
            self.graph = Dataset()
        else:
            self.graph = Graph()

    def query_graph(self, sparql_query: str, *, graph_uri: str = None):
        """
        Query the graph using a SPARQL query.
        :param graph_uri:
        :param sparql_query: The SPARQL query string.
        :return: The query results.
        """

        if self._multigraph:
            if graph_uri is not None:
                graph = self.graph.get_graph(URIRef(graph_uri))
                return graph.query(sparql_query)

        return self.graph.query(sparql_query)

    def delete_triples(self, subject_uri: str, *, graph_uri: str = None):
        """
        Delete all triples with the specified subject URI.
        :param graph_uri:
        :param subject_uri: The subject URI as a string.
        """

        subject = URIRef(subject_uri)

        if self._multigraph:
            if graph_uri is not None:
                graph = self.graph.get_graph(URIRef(graph_uri))
                graph.remove((subject, None, None))
                return

        self.graph.remove((subject, None, None))

    def export_ntriples(self, graph_uri: str, file_path: str, *,
                        overwrite=True) -> bool:

        return self._export_ntriples_impl(graph_uri=graph_uri, file_path=file_path, overwrite=overwrite)

    def import_ntriples(self, graph_uri: str, file_path: str) -> bool:

        return self._import_ntriples_impl(graph_uri=graph_uri, file_path=file_path)

    def list_graphs(self) -> List[VitalNameGraph]:

        return self._list_graphs_impl()

    def get_graph(self, graph_uri: str) -> VitalNameGraph:

        return self._get_graph_impl(graph_uri=graph_uri)

    def check_create_graph(self, graph_uri: str) -> bool:

        return self._check_create_graph_impl(graph_uri=graph_uri)

    def create_graph(self, graph_uri: str) -> bool:

        return self._create_graph_impl(graph_uri=graph_uri)

    def delete_graph(self, graph_uri: str) -> bool:

        return self._delete_graph_impl(graph_uri=graph_uri)

    def purge_graph(self, graph_uri: str) -> bool:

        return self._purge_graph_impl(graph_uri=graph_uri)

    def get_graph_all_objects(self, graph_uri: str, *, limit=100, offset=0, safety_check: bool = True,
                              ) -> ResultList:

        return self._get_graph_all_objects_impl(graph_uri=graph_uri, limit=limit, offset=offset, safety_check=safety_check)

    def insert_object(self, graph_uri: str, graph_object: G, *, safety_check: bool = True,
                      ) -> VitalGraphStatus:

        return self._insert_object_impl(graph_uri=graph_uri, graph_object=graph_object, safety_check=safety_check)

    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], *, safety_check: bool = True,
                           ) -> VitalGraphStatus:

        return self._insert_object_list_impl(graph_uri=graph_uri, graph_object_list=graph_object_list, safety_check=safety_check)

    def update_object(self, graph_object: G, *, graph_uri: str = None, upsert: bool = False, safety_check: bool = True,
                      ) -> VitalGraphStatus:

        return self._update_object_impl(graph_object=graph_object, graph_uri=graph_uri, upsert=upsert, safety_check=safety_check)

    def update_object_list(self, graph_object_list: List[G], *, graph_uri: str = None, upsert: bool = False,
                           safety_check: bool = True, vital_managed: bool = True) -> VitalGraphStatus:

        return self._update_object_list_impl(graph_object_list=graph_object_list, graph_uri=graph_uri, upsert=upsert, safety_check=safety_check)

    def get_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True,
                   vital_managed: bool = True) -> G:

        return self._get_object_impl(object_uri=object_uri, graph_uri=graph_uri, safety_check=safety_check)

    def get_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True,
                        vital_managed: bool = True) -> ResultList:

        return self._get_object_list_impl(object_uri_list=object_uri_list, graph_uri=graph_uri, safety_check=safety_check)

    def delete_object(self, object_uri: str, *, graph_uri: str = None, safety_check: bool = True,
                      vital_managed: bool = True) -> VitalGraphStatus:

        return self._delete_object_impl(object_uri=object_uri, graph_uri=graph_uri, safety_check=safety_check)

    def delete_object_list(self, object_uri_list: List[str], *, graph_uri: str = None, safety_check: bool = True,
                           vital_managed: bool = True) -> VitalGraphStatus:

        return self._delete_object_list_impl(object_uri_list=object_uri_list, graph_uri=graph_uri, safety_check=safety_check)

    def filter_query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit: int = 100, offset: int = 0,
                     resolve_objects: bool = True, safety_check: bool = True, vital_managed: bool = True) -> ResultList:

        return self._filter_query_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            uri_binding=uri_binding,
            limit=limit,
            offset=offset,
            resolve_objects=resolve_objects,
            safety_check=safety_check)

    def query(self, graph_uri: str, sparql_query: str, uri_binding='uri', *, limit=100, offset=0, resolve_objects=True,
              safety_check: bool = True, vital_managed=True) -> ResultList:

        return self._query_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            uri_binding=uri_binding,
            limit=limit,
            offset=offset,
            resolve_objects=resolve_objects,
            safety_check=safety_check)

    def query_construct(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                        binding_list: List[Binding], *, limit=100, offset=0, safety_check: bool = True,
                        vital_managed: bool = True) -> ResultList:

        return self._query_construct_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            namespace_list=namespace_list,
            binding_list=binding_list,
            limit=limit,
            offset=offset,
            safety_check=safety_check)

    def query_construct_solution(self, graph_uri: str, sparql_query: str, namespace_list: List[Ontology],
                                 binding_list: List[Binding], root_binding: str | None = None, *, limit=100, offset=0,
                                 safety_check: bool = True, vital_managed: bool = True) -> SolutionList:

        return self._query_construct_solution_impl(
            graph_uri=graph_uri,
            sparql_query=sparql_query,
            namespace_list=namespace_list,
            binding_list=binding_list,
            root_binding=root_binding,
            limit=limit,
            offset=offset,
            safety_check=safety_check)

    def metaql_select_query(self, *, namespace: str = None, select_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology]) -> MetaQLResult:
        pass

    def metaql_graph_query(self, *, namespace: str = None, graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology]) -> MetaQLResult:
        pass


