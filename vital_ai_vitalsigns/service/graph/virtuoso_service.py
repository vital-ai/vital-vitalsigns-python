from typing import List, TypeVar, Tuple
import rdflib.plugins.sparql.aggregates
import requests
from SPARQLWrapper import SPARQLWrapper, DIGEST, JSON, POST
from rdflib import Graph, URIRef, BNode, Literal, RDF
from requests.auth import HTTPDigestAuth

from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution import Solution
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding, BindingValueType
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService
from vital_ai_vitalsigns.service.graph.name_graph import VitalNameGraph
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.service.graph.utils.virtuoso_utils import VirtuosoUtils
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.GraphMatch import GraphMatch
from vital_ai_vitalsigns_core.model.RDFStatement import RDFStatement
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment

G = TypeVar('G', bound='GraphObject')


class VirtuosoGraphService(VitalGraphService):

    def __init__(self, username: str | None = None, password: str | None = None, endpoint: str | None = None):
        self.username = username
        self.password = password
        self.endpoint = endpoint.rstrip('/')
        self.sparql_auth_endpoint = f"{self.endpoint}/sparql-auth"
        self.graph_crud_auth_endpoint = f"{self.endpoint}/sparql-graph-crud-auth"
        super().__init__()

    # keep cache of graphs/namespaces
    # which gets managed by background thread
    # could be at the service level, but that would mean
    # moving the graph existence checks to service level also

    def _find_graph(self, graph_uri: str, object_uri: str) -> bool:

        query = f"""
                ASK WHERE {{
                    GRAPH <{graph_uri}> {{
                        <{object_uri}> ?p ?o .
                    }}
                }}
            """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)
        result = sparql.query().convert()
        return result["boolean"]

    def _find_graph_uri_list(self, graph_uri: str, object_uri_list: List[str]) -> List[str]:

        # enforce maximum

        values_clause = " ".join(f"<{uri}>" for uri in object_uri_list)

        query = f"""
                SELECT ?s WHERE {{
                    GRAPH <{graph_uri}> {{
                        VALUES ?s {{ {values_clause} }}
                        ?s ?p ?o .
                    }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)

        results = sparql.query().convert()

        existing_uris = {result['s']['value'] for result in results['results']['bindings']}

        existing = [uri for uri in object_uri_list if uri in existing_uris]
        not_existing = [uri for uri in object_uri_list if uri not in existing_uris]

        return existing

    def _check_unique_subject(self, graph_uri, type_uri):

        query_count_subjects = f"""
            SELECT (COUNT(DISTINCT ?s) AS ?count) WHERE {{
                GRAPH <{graph_uri}> {{
                    ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{type_uri}> .
                }}
            }}
        """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query_count_subjects)
        sparql.setMethod('POST')
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        count = int(results['results']['bindings'][0]['count']['value'])

        if count == 1:
            return True
        elif count == 0:
            pass
        else:
            pass

        return False

    def list_graphs(self, vital_managed=True) -> List[VitalNameGraph]:

        # todo only vitalsegment ones

        query = """
            SELECT DISTINCT ?g WHERE { GRAPH ?g {?s ?p ?o} } ORDER BY ?g
        """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)

        results = sparql.query().convert()

        graph_uris = []

        for result in results["results"]["bindings"]:
            graph_uri = result["g"]["value"]
            graph_uris.append(graph_uri)

        name_graph_list = []

        for g_uri in graph_uris:
            name_graph = VitalNameGraph(g_uri)
            name_graph_list.append(name_graph)

        return name_graph_list

    def get_graph(self, graph_uri: str, vital_managed=True) -> VitalNameGraph:

        # todo vital segment ones

        query = f"""
                ASK WHERE {{
                    GRAPH <{graph_uri}> {{ ?s ?p ?o }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)

        result = sparql.query().convert()

        if result["boolean"]:
            return VitalNameGraph(graph_uri)
        else:
            raise ValueError(f"Graph with URI {graph_uri} does not exist.")

    # create graph
    # store name graph in vital service graph and in the graph itself
    # a graph needs to have some triples in it to exist

    def check_create_graph(self, graph_uri: str, vital_managed=True) -> bool:

        # TODO check if it contains vitalsegment

        query = f"""
                ASK WHERE {{
                    GRAPH <{graph_uri}> {{ ?s ?p ?o }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod('POST')
        sparql.setReturnFormat('json')

        result = sparql.query().convert()

        if result["boolean"]:
            return True

        vital_segment = VitalSegment()
        vital_segment.URI = URIGenerator.generate_uri()
        vital_segment.segmentID = graph_uri

        rdf_string = vital_segment.to_rdf()

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={graph_uri}"

        headers = {
            'Content-Type': 'application/rdf+xml'
        }

        response = requests.put(
            endpoint_url,
            data=rdf_string,
            headers=headers,
            auth=HTTPDigestAuth(self.username, self.password)
        )

        if response.status_code in [200, 201]:
            return True
        else:
            response.raise_for_status()

    def create_graph(self, graph_uri: str, vital_managed=True) -> bool:

        query = f"""
                ASK WHERE {{
                    GRAPH <{graph_uri}> {{ ?s ?p ?o }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod('POST')
        sparql.setReturnFormat('json')

        result = sparql.query().convert()

        if result["boolean"]:
            raise ValueError(f"Graph with URI {graph_uri} already exists.")

        vital_segment = VitalSegment()
        vital_segment.URI = URIGenerator.generate_uri()
        vital_segment.segmentID = graph_uri
        rdf_string = vital_segment.to_rdf()

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={graph_uri}"

        headers = {
            'Content-Type': 'application/n-triples'
        }

        response = requests.put(
            endpoint_url,
            data=rdf_string,
            headers=headers,
            auth=HTTPDigestAuth(self.username, self.password)
        )

        if response.status_code in [200, 201]:
            return True
        else:
            response.raise_for_status()

    # delete graph
    # delete graph itself plus record in vital service graph

    def delete_graph(self, graph_uri: str, vital_managed=True) -> bool:

        # todo check if contains vitalsegment

        query = f"""
                ASK WHERE {{
                    GRAPH <{graph_uri}> {{ ?s ?p ?o }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod('POST')
        sparql.setReturnFormat('json')

        result = sparql.query().convert()

        if not result["boolean"]:
            raise ValueError(f"Graph with URI {graph_uri} does not exist.")

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={graph_uri}"

        response = requests.delete(
            endpoint_url,
            auth=HTTPDigestAuth(self.username, self.password)
        )

        if response.status_code in [200, 204]:
            return True
        else:
            response.raise_for_status()

    # purge graph (delete all but name graph)

    def purge_graph(self, graph_uri: str, vital_managed=True) -> bool:

        vs = VitalSigns()

        segment_type_uri = "http://vital.ai/ontology/vital-core#VitalSegment"

        if not self._check_unique_subject(graph_uri, segment_type_uri):
            raise ValueError(f"Mismatch of segments within graph: {graph_uri}")

        query_vital_segments = f"""
                SELECT ?s ?p ?o WHERE {{
                    GRAPH <{graph_uri}> {{
                        ?s <{RDF.type}> <{segment_type_uri}> .
                        ?s ?p ?o .
                    }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query_vital_segments)
        sparql.setMethod('POST')
        sparql.setReturnFormat('json')

        results = sparql.query().convert()

        # print(results)

        if not results["results"]["bindings"]:
            raise ValueError(f"No VitalSegment triples found in graph {graph_uri}.")

        n_triples_string = ""

        for result in results["results"]["bindings"]:
            s = result["s"]["value"]
            p = result["p"]["value"]
            o = result["o"]["value"]
            o_type = result["o"]["type"]
            o_datatype = result["o"].get("datatype") if "datatype" in result["o"] else None
            o_lang = result["o"].get("xml:lang") if "xml:lang" in result["o"] else None

            n_triples_string += VirtuosoUtils.format_as_ntriples(s, p, o, o_type, o_datatype, o_lang)

        # print(n_triples_string)

        vital_segment = vs.from_rdf(n_triples_string)

        # print(vital_segment.to_rdf())

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={graph_uri}"

        headers = {
            'Content-Type': 'application/n-triples'
        }

        response = requests.put(
            endpoint_url,
            data=vital_segment.to_rdf(),
            headers=headers,
            auth=HTTPDigestAuth(self.username, self.password)
        )

        if response.status_code in [200, 201]:
            return True
        else:
            response.raise_for_status()

    # only use for small graphs
    def get_graph_all_objects(self, graph_uri: str, limit=100, offset=0, vital_managed=True) -> ResultList:

        vs = VitalSigns()

        # check if graph exists
        # throws exception if not exists
        name_graph = self.get_graph(graph_uri)

        # include limit, offset
        # sort by subject uri
        # count total unique subjects and throw exception if over some number?

        query = f"""
        CONSTRUCT {{
            ?s ?p ?o .
        }} 
        WHERE {{
            {{
                SELECT DISTINCT ?s WHERE {{
                        GRAPH <{graph_uri}> {{ ?s ?p ?o }}
                }}
                ORDER BY ?s
                LIMIT 100
                OFFSET 0
            }}
            GRAPH <{graph_uri}> {{
                ?s ?p ?o .
            }}
        }}
        """

        # print(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod('POST')
        sparql.setReturnFormat('rdf+xml')  # force getting graph back

        # converts to rdflib graph because of CONSTRUCT
        g = sparql.query().convert()

        subjects = sorted(set(g.subjects()))

        result_list = ResultList()

        for s in subjects:
            triples = g.triples((s, None, None))
            vitalsigns_object = vs.from_triples(triples)
            result_list.add_result(vitalsigns_object)

        return result_list

    # insert object into graph (scoped to vital service graph uri, which must exist)
    # insert object list into graph (scoped to vital service graph uri, which must exist)

    def insert_object(self, graph_uri: str, graph_object: G, vital_managed=True) -> VitalGraphStatus:

        # throws exception if not exists
        name_graph = self.get_graph(graph_uri)

        object_uri = str(graph_object.URI)

        if self._find_graph(graph_uri, object_uri):
            return VitalGraphStatus(-1, f"Failed to insert graph object.  The object URI already exists.")

        rdf_data = graph_object.to_rdf()

        query = f"""
                INSERT DATA {{
                    GRAPH <{graph_uri}> {{
                        {rdf_data}
                    }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)

        try:
            sparql.query()

            return VitalGraphStatus(0, "Graph object inserted successfully.")

        except Exception as e:
            return VitalGraphStatus(-1, f"Failed to insert graph object: {str(e)}")

    def insert_object_list(self, graph_uri: str, graph_object_list: List[G], vital_managed=True) -> VitalGraphStatus:

        # throws exception if not exists
        name_graph = self.get_graph(graph_uri)

        uri_list = []

        for g in graph_object_list:
            uri = str(g.URI)
            uri_list.append(uri)

        existing_object_uri_list = self._find_graph_uri_list(graph_uri, uri_list)

        if len(existing_object_uri_list) > 0:
            # todo return list of current uris
            return VitalGraphStatus(-1, f"Failed to insert graph objects.  One or more object uris already exists.")

        rdf_data_list = [graph_object.to_rdf() for graph_object in
                         graph_object_list]
        rdf_data = "\n".join(rdf_data_list)

        query = f"""
                INSERT DATA {{
                    GRAPH <{graph_uri}> {{
                        {rdf_data}
                    }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)
        sparql.setQuery(query)
        sparql.setMethod(POST)

        try:
            sparql.query()
            return VitalGraphStatus(0, "Graph objects inserted successfully.")
        except Exception as e:
            return VitalGraphStatus(-1, f"Failed to insert graph objects: {str(e)}")

    # update object into graph (scoped to vital service graph uri, which must exist)
    # delete old, replace with new

    # update object list into graph (scoped to vital service graph uri, which must exist)
    # delete old, replace with new

    def update_object(self, graph_object: G, graph_uri=None, vital_managed=True) -> VitalGraphStatus:

        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        object_uri = str(graph_object.URI)

        if not self._find_graph(graph_uri, object_uri):
            return VitalGraphStatus(-1, f"Failed to find graph object for update.")

        delete_query = f"""
                    DELETE WHERE {{
                        GRAPH <{graph_uri}> {{
                            <{object_uri}> ?p ?o .
                        }}
                    }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)
        sparql.setMethod(POST)

        sparql.setQuery(delete_query)

        try:
            sparql.query()
        except Exception as e:
            return VitalGraphStatus(-1, f"Error deleting object: {str(e)}")

        rdf_data = graph_object.to_rdf()

        insert_query = f"""
                    INSERT DATA {{
                        GRAPH <{graph_uri}> {{
                            {rdf_data}
                        }}
                    }}
                """

        sparql.setQuery(insert_query)

        try:
            sparql.query()
            return VitalGraphStatus(0, "Graph object updated successfully.")
        except Exception as e:
            return VitalGraphStatus(-1, f"Error inserting updated object: {str(e)}")

    def update_object_list(self, graph_object_list: List[G], graph_uri=None, vital_managed=True) -> VitalGraphStatus:

        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        # todo check if objects exist

        object_graph_map = {}

        for graph_object in graph_object_list:
            object_uri = graph_object.URI
            found = False

            if self._find_graph(graph_uri, object_uri):
                object_graph_map[object_uri] = graph_uri
                found = True

            if not found:
                return VitalGraphStatus(-1,
                                        f"Error: Object {object_uri} not found in provided graph.")

        for graph_object in graph_object_list:

            object_uri = graph_object.URI
            target_graph = object_graph_map[object_uri]

            delete_query = f"""
                DELETE WHERE {{
                    GRAPH <{target_graph}> {{
                        <{object_uri}> ?p ?o .
                    }}
                }}
            """

            sparql = SPARQLWrapper(self.sparql_auth_endpoint)
            sparql.setCredentials(self.username, self.password)
            sparql.setHTTPAuth(DIGEST)

            sparql.setQuery(delete_query)

            try:
                sparql.query()
            except Exception as e:
                return VitalGraphStatus(-1, f"Error deleting object {object_uri}: {str(e)}")

            rdf_data = graph_object.to_rdf()

            insert_query = f"""
                INSERT DATA {{
                    GRAPH <{target_graph}> {{
                        {rdf_data}
                    }}
                }}
            """

            sparql.setQuery(insert_query)

            try:
                sparql.query()
            except Exception as e:
                return VitalGraphStatus(-1, f"Error inserting updated object {object_uri}: {str(e)}")

        return VitalGraphStatus(0, "All graph objects updated successfully.")

    # get object (scoped to all vital service graphs)
    # get object (scoped to specific graph, or graph list)
    # get objects by uri list (scoped to all vital service graphs)
    # get objects by uri list (scoped to specific graph, or graph list)

    def get_object(self, object_uri: str, graph_uri=None, vital_managed=True) -> G:

        vs = VitalSigns()

        if graph_uri is None:
            raise ValueError("Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        target_graph = None

        if self._find_graph(graph_uri, object_uri):
            target_graph = graph_uri

        if not target_graph:
            # raise ValueError(f"Error: Object {object_uri} not found in any provided graphs.")
            return None

        query = f"""
                CONSTRUCT {{
                    <{object_uri}> ?p ?o .
                }} WHERE {{
                    GRAPH <{target_graph}> {{
                        <{object_uri}> ?p ?o .
                    }}
                }}
                """

        # print(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat('rdf+xml')  # force returning a graph

        try:
            graph = sparql.query().convert()
            # print(f"Triple Count: {len(graph)}")

            graph_object = vs.from_triples(graph.triples((None, None, None)))

            return graph_object

        except Exception as e:
            raise ValueError(f"Error retrieving object {object_uri}: {str(e)}")

    def get_object_list(self, object_uri_list: List[str], graph_uri=None, vital_managed=True) -> ResultList:

        # TODO do in bulk rather than one at a time

        vs = VitalSigns()

        if graph_uri is None:
            raise ValueError("Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        object_graph_map = {}

        for object_uri in object_uri_list:
            found = False
            if graph_uri:
                if self._find_graph(graph_uri, object_uri):
                    object_graph_map[object_uri] = graph_uri
                    found = True

            if not found:
                raise ValueError(f"Error: Object {object_uri} not found in any provided graphs.")

        results = []

        for object_uri in object_uri_list:
            target_graph = object_graph_map[object_uri]

            query = f"""
                    CONSTRUCT {{
                        <{object_uri}> ?p ?o .
                    }} WHERE {{
                        GRAPH <{target_graph}> {{
                            <{object_uri}> ?p ?o .
                        }}
                    }}
                    """

            sparql = SPARQLWrapper(self.sparql_auth_endpoint)
            sparql.setCredentials(self.username, self.password)
            sparql.setHTTPAuth(DIGEST)

            sparql.setQuery(query)
            sparql.setMethod(POST)
            sparql.setReturnFormat('rdf+xml')

            try:
                result = sparql.query().convert()

                graph_object = vs.from_triples(result.triples((None, None, None)))

                results.append(graph_object)

            except Exception as e:
                raise ValueError(f"Error retrieving object {object_uri}: {str(e)}")

        result_list = ResultList()

        for r in results:
            result_list.add_result(r)

        return result_list

    # delete uri (scoped to all vital service graphs)
    # delete uri list (scoped to all vital service graphs)
    # delete uri (scoped to graph or graph list)
    # delete uri list (scoped to graph or graph list)

    def delete_object(self, object_uri: str, graph_uri=None, vital_managed=True) -> VitalGraphStatus:

        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        target_graph = None

        if self._find_graph(graph_uri, object_uri):
            target_graph = graph_uri

        if not target_graph:
            return VitalGraphStatus(-1,
                                    f"Error: Object {object_uri} not found in the provided graph.")

        delete_query = f"""
                DELETE WHERE {{
                    GRAPH <{target_graph}> {{
                        <{object_uri}> ?p ?o .
                    }}
                }}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(delete_query)
        sparql.setMethod(POST)

        try:
            sparql.query()
            return VitalGraphStatus(0, "Graph object deleted successfully.")
        except Exception as e:
            return VitalGraphStatus(-1, f"Error deleting object {object_uri}: {str(e)}")

    def delete_object_list(self, object_uri_list: List[str], graph_uri=None, vital_managed=True) -> VitalGraphStatus:

        # todo do in bulk

        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        object_graph_map = {}

        for object_uri in object_uri_list:

            found = False

            if self._find_graph(graph_uri, object_uri):
                object_graph_map[object_uri] = graph_uri
                found = True

            if not found:
                return VitalGraphStatus(-1,
                                        f"Error: Object {object_uri} not found in any provided graphs.")

        # Delete each object
        for object_uri in object_uri_list:
            target_graph = object_graph_map[object_uri]

            delete_query = f"""
                        DELETE WHERE {{
                            GRAPH <{target_graph}> {{
                                <{object_uri}> ?p ?o .
                            }}
                        }}
                    """

            sparql = SPARQLWrapper(self.sparql_auth_endpoint)
            sparql.setCredentials(self.username, self.password)
            sparql.setHTTPAuth(DIGEST)

            sparql.setQuery(delete_query)
            sparql.setMethod(POST)

            try:
                sparql.query()
            except Exception as e:
                return VitalGraphStatus(-1, f"Error deleting object {object_uri}: {str(e)}")

        return VitalGraphStatus(0, "All graph objects deleted successfully.")

    # filter graph, this is meant to be optimized for case of a select
    # by a URI value associated with objects
    # the query must bind to the subject of the matching objects

    def filter_query(self, graph_uri: str, sparql_query: str,  uri_binding='uri', limit=100, offset=0, resolve_objects=True,
                     vital_managed=True) -> ResultList:

        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        query = f"""
                SELECT DISTINCT ?{uri_binding} WHERE {{
                    GRAPH <{graph_uri}> {{
                        {sparql_query}
                    }}
                }} ORDER BY ?{uri_binding}
                LIMIT {limit} OFFSET {offset}
                """

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)

        results = sparql.query().convert()

        object_uri_list = [result[uri_binding]["value"] for result in results["results"]["bindings"]]

        if not object_uri_list:
            return ResultList()

        if resolve_objects:
            return self.get_object_list(object_uri_list, graph_uri, vital_managed=vital_managed)
        else:
            result_list = ResultList()

            for uri in object_uri_list:
                # gm = GraphMatch()
                # gm.URI = URIGenerator.generate_uri()
                # gm[uri_binding] = uri
                # result_list.add_result(gm)

                rdf_triple = RDFStatement()
                rdf_triple.URI = URIGenerator.generate_uri()
                rdf_triple.rdfSubject = uri

                result_list.add_result(rdf_triple)

            return result_list

    # query graph, this is meant for a sparql query which binds to the
    # uris of matching objects

    # this only works with very flat queries without subqueries
    # because the top level query combines a uri or a set of top-level URIs
    # union-ed together, with each grouping contributing one uri
    # so a-->b-->c-->d would only be contributing one uri and not the
    # solution of a,b,c,d

    # if instead of a single binding value, the input included a list
    # the outer query could be a CONSTRUCT to construct
    # a triple for each member of the list, like
    # uri1 hasValue ?var1
    # some function could create random uri values within the database
    # or bnode values could be used like
    # _:bnode1 ex:hasValue ?value1
    # _:bnode1 should generate a unique value per invocation of construct

    # this would effectively have one triple per uri
    # which was the desired goal, such that a list will be produced
    # to get the objects corresponding to the uris

    # the previous/current way is to do two passes, one to get
    # the matching subjects, and then follow with resolving the objects

    # take parameter for namespaces
    # default can be derived from loaded ontologies

    def query(self, sparql_query: str, graph_uri: str, uri_binding='uri', limit=100, offset=0, resolve_objects=True, vital_managed=True) -> ResultList:

        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        query = f"""
                PREFIX vital-core: <http://vital.ai/ontology/vital-core#>
                PREFIX vital: <http://vital.ai/ontology/vital#>
                PREFIX vital-aimp: <http://vital.ai/ontology/vital-aimp#>
                PREFIX haley: <http://vital.ai/ontology/haley#>
                PREFIX haley-ai-question: <http://vital.ai/ontology/haley-ai-question#>
                PREFIX haley-ai-kg: <http://vital.ai/ontology/haley-ai-kg#>

                SELECT DISTINCT ?{uri_binding} WHERE {{
                    GRAPH <{graph_uri}> {{
                            {sparql_query}
                        }}
                    }} ORDER BY ?{uri_binding}
                    LIMIT {limit} OFFSET {offset}
            """

        # print(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)

        results = sparql.query().convert()

        object_uri_list = [result[uri_binding]["value"] for result in results["results"]["bindings"]]

        if not object_uri_list:
            return ResultList()

        # todo make resolve list efficient
        if resolve_objects:
            return self.get_object_list(object_uri_list, graph_uri, vital_managed=vital_managed)
        else:
            result_list = ResultList()

            for uri in object_uri_list:
                # gm = GraphMatch()
                # todo arbitrary key/values for GCO (parent of GraphMatch)
                # gm.URI = URIGenerator.generate_uri()
                # gm.uri_binding = uri
                # gm.ontologyIRI = uri
                # result_list.add_result(gm)

                rdf_triple = RDFStatement()
                rdf_triple.URI = URIGenerator.generate_uri()
                rdf_triple.rdfSubject = uri
                rdf_triple.rdfPredicate = ''
                rdf_triple.rdfObject = ''

                result_list.add_result(rdf_triple)

            return result_list

    # sparql query binding to variables with variable, property tuples
    # construct of bnode property variable triple for each bound value
    # constructed statements returned in RdfStatement object result list

    def query_construct(self,
                        graph_uri: str,
                        sparql_query: str,
                        namespace_list: List[Ontology],
                        binding_list: List[Binding],
                        limit=100, offset=0) -> ResultList:

        if graph_uri is None:
            result_list = ResultList()
            result_list.set_status(-1)
            result_list.set_message("Error: graph_uri is not set.")
            return result_list

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_uri)

        prefix_section = "\n".join([f"PREFIX {ns.prefix}: <{ns.ontology_iri}>" for ns in namespace_list])

        order_by_section = " ".join([binding.variable for binding in binding_list])

        construct_template = "\n".join([f"_:bnode1 <{binding.property_uri}> ?{binding.variable[1:]} ." for binding in binding_list])

        select_parts = []

        for binding in binding_list:
            variable = binding.variable
            if binding.optional:
                select_parts.append(f"(COALESCE({variable}, \"{binding.unbound_symbol}\") AS {variable})")
            else:
                select_parts.append(f"{variable}")

        select_clause = "SELECT " + ", ".join(select_parts)

        query = f"""
{prefix_section}
CONSTRUCT {{
{construct_template}
}}
WHERE {{
    GRAPH <{graph_uri}> {{
        {select_clause} WHERE 
        {{
        {sparql_query}
        }}
    }}
}}
ORDER BY {order_by_section}
LIMIT {limit}
OFFSET {offset}
"""

        # print(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)
        sparql.setQuery(query)
        sparql.setMethod(POST)

        sparql.setReturnFormat('rdf+xml')  # force getting graph back

        # converts to rdflib graph because of CONSTRUCT
        g = sparql.query().convert()

        # handle list split into solutions
        # subjects = sorted(set(g.subjects()))
        # for s in subjects:
        #    triples = g.triples((s, None, None))

        result_list = ResultList()

        triples = g.triples((None, None, None))

        # for result in results["results"]["bindings"]:

        for s, p, o in triples:

            rdf_triple = RDFStatement()
            rdf_triple.URI = URIGenerator.generate_uri()

            # rdf_triple.rdfSubject = result['s']["value"]
            # rdf_triple.rdfPredicate = result['p']["value"]
            # rdf_triple.rdfObject = result['o']["value"]

            rdf_triple.rdfSubject = str(s)  # blank node subject uri
            rdf_triple.rdfPredicate = str(p) # property from binding
            rdf_triple.rdfObject = str(o) # uri of matching object

            result_list.add_result(rdf_triple)

        return result_list

    # code for converting json result back into triples

    """
            for result in results["results"]["bindings"]:

                s = URIRef(result["s"]["value"])

                p = URIRef(result["p"]["value"])

                o = result["o"]["value"]

                o_type = result["o"]["type"]
                o_datatype = result["o"].get("datatype") if "datatype" in result["o"] else None
                o_lang = result["o"].get("xml:lang") if "xml:lang" in result["o"] else None

                if o_type == "uri":
                    o_uri = URIRef(o)
                elif o_type == "bnode":
                    o_uri = BNode(o)
                elif o_type == "literal" and o_datatype:
                    o_uri = Literal(o, datatype=URIRef(o_datatype))
                elif o_type == "literal" and o_lang:
                    o_uri = Literal(o, lang=o_lang)
                else:
                    o_uri = Literal(o)

                print(f"{s} {p} {o_uri}")

                g.add((s, p, o_uri))
    """

    def query_construct_solution(self,
                                 graph_uri: str,
                                 sparql_query: str,
                                 namespace_list: List[Ontology],
                                 binding_list: List[Binding],
                                 root_binding: str | None = None,
                                 limit=100, offset=0) -> SolutionList:

        # object cache to use during query
        # todo bulk retrieval of objects
        graph_collection = GraphCollection(use_rdfstore=False, use_vectordb=False)

        result_list = self.query_construct(
            graph_uri,
            sparql_query,
            namespace_list,
            binding_list,
            limit, offset)

        graph = Graph()

        for result in result_list:
            rs = result.graph_object
            if isinstance(rs, RDFStatement):
                s = rs.rdfSubject
                p = rs.rdfPredicate

                value_type = BindingValueType.URIREF

                for binding in binding_list:
                    if binding.property_uri == str(p):
                        value_type = binding.value_type
                        break

                o = rs.rdfObject
                if value_type == BindingValueType.URIREF:
                    graph.add((URIRef(str(s)), URIRef(str(p)), URIRef(str(o))))
                else:
                    graph.add((URIRef(str(s)), URIRef(str(p)), Literal(str(o))))

        solutions = []

        unique_subjects = set(graph.subjects())

        for subject in unique_subjects:

            uri_map = {}
            obj_map = {}

            # root_binding_uri = None
            root_binding_obj = None

            triples = set(graph.triples((subject, None, None)))

            for s, p, o in triples:

                matching_bindings = [binding for binding in binding_list if binding.property_uri == str(p)]

                if len(matching_bindings) == 1:

                    matching_binding = matching_bindings[0]

                    binding_var = matching_binding.variable
                    binding_value = o

                    uri_map[binding_var] = binding_value

                    if matching_binding.value_type == BindingValueType.URIREF:

                        # cache individual objects

                        cache_obj = graph_collection.get(str(o))

                        if cache_obj is None:
                            binding_obj = self.get_object(str(o), graph_uri=graph_uri)
                            graph_collection.add(binding_obj)
                        else:
                            binding_obj = cache_obj

                        obj_map[binding_var] = binding_obj

                        if binding_var == root_binding:
                            # root_binding_uri = binding_value
                            root_binding_obj = binding_obj

            solution = Solution(uri_map, obj_map, root_binding, root_binding_obj)
            solutions.append(solution)

        solution_list = SolutionList(solutions, limit, offset)

        return solution_list

