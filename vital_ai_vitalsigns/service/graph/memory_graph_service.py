import os
from typing import List
from rdflib import Dataset, URIRef, Graph, Literal
from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.impl.rdflib.rdflib_sparql_impl import RDFlibSparqlImpl
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution import Solution
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding, BindingValueType
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService, G
from vital_ai_vitalsigns.service.graph.name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus
from vital_ai_vitalsigns.service.graph.graph_service_constants import VitalGraphServiceConstants
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.RDFStatement import RDFStatement
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment


class MemoryGraphService(VitalGraphService, RDFlibSparqlImpl):

    def __init__(self):

        super().__init__(multigraph=True)

        # init service graph, domain ontology graph

        # service_graph_uri_ref = URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI)

        service_graph = Graph(identifier=URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

        service_segment = VitalSegment()
        service_segment.URI = URIGenerator.generate_uri()
        service_segment.segmentID = VitalGraphServiceConstants.SERVICE_GRAPH_URI
        service_rdf_data = service_segment.to_rdf()

        ontology_segment = VitalSegment()
        ontology_segment.URI = URIGenerator.generate_uri()
        ontology_segment.segmentID = VitalGraphServiceConstants.SERVICE_GRAPH_URI
        ontology_rdf_data = ontology_segment.to_rdf()

        service_graph.parse(data=service_rdf_data, format="nt")
        service_graph.parse(data=ontology_rdf_data, format="nt")

        self.graph.add_graph(service_graph)

        # populate ontology graph
        # ontology_graph_uri_ref = URIRef(VitalGraphServiceConstants.ONTOLOGY_GRAPH_URI)

        ontology_graph = Graph(identifier=URIRef(VitalGraphServiceConstants.ONTOLOGY_GRAPH_URI))
        ontology_graph.parse(data=ontology_rdf_data, format="nt")

        self.graph.add_graph(ontology_graph)

    def start(self):
        pass

    def shutdown(self):
        pass

    def export_nquads(self):
        pass

    def import_nquads(self):
        pass

    def export_ntriples(self, graph_uri: str, file_path: str, *,
                        overwrite=True) -> bool:

        return self._export_ntriples_impl(graph_uri=graph_uri, file_path=file_path, overwrite=overwrite)

    def import_ntriples(self, graph_uri: str, file_path: str) -> bool:

        return self._import_ntriples_impl(graph_uri=graph_uri, file_path=file_path)

    def list_graphs(self, *, vital_managed=True) -> List[VitalNameGraph]:

        return self._list_graphs_impl()

    def get_graph(self, graph_uri: str, *, vital_managed=True) -> VitalNameGraph:

        return self._get_graph_impl(graph_uri=graph_uri)

    def check_create_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        return self._check_create_graph_impl(graph_uri=graph_uri)

    def create_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        return self._create_graph_impl(graph_uri=graph_uri)

    def delete_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        return self._delete_graph_impl(graph_uri=graph_uri)

    def purge_graph(self, graph_uri: str, *, vital_managed=True) -> bool:

        return self._purge_graph_impl(graph_uri=graph_uri)

    def get_graph_all_objects(self, graph_uri: str, *, limit=100, offset=0, safety_check: bool = True,
                              vital_managed=True) -> ResultList:

        return self._get_graph_all_objects_impl(graph_uri=graph_uri, limit=limit, offset=offset, safety_check=safety_check)

    def insert_object(self, graph_uri: str, graph_object: G, *, safety_check: bool = True,
                      vital_managed=True) -> VitalGraphStatus:

        return self._insert_object_impl(graph_uri=graph_uri, graph_object=graph_object, safety_check=safety_check)

    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], *, safety_check: bool = True,
                           vital_managed=True) -> VitalGraphStatus:

        return self._insert_object_list_impl(graph_uri=graph_uri, graph_object_list=graph_object_list, safety_check=safety_check)

    def update_object(self, graph_object: G, *, graph_uri: str = None, upsert: bool = False, safety_check: bool = True,
                      vital_managed: bool = True) -> VitalGraphStatus:

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
