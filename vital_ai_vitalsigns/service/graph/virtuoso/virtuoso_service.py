import logging
import time
from typing import List, TypeVar
import pyodbc
import rdflib.plugins.sparql.aggregates
import requests
from SPARQLWrapper import SPARQLWrapper, DIGEST, JSON, POST
from rdflib import Graph, URIRef, Literal
from requests.adapters import HTTPAdapter
from requests.auth import HTTPDigestAuth
from requests.exceptions import ChunkedEncodingError
from urllib3 import Retry
from urllib3.exceptions import ProtocolError
from vital_ai_vitalsigns.metaql.arc.metaql_arc import ArcRoot
from vital_ai_vitalsigns.metaql.query.query_builder import QueryBuilder, AndConstraintList, ClassConstraint
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.metaql_result import MetaQLResult
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.query.solution import Solution
from vital_ai_vitalsigns.query.solution_list import SolutionList
from vital_ai_vitalsigns.service.graph.binding import Binding, BindingValueType
from vital_ai_vitalsigns.service.graph.graph_object_generator import GraphObjectGenerator
from vital_ai_vitalsigns.service.graph.graph_service import VitalGraphService
from vital_ai_vitalsigns.service.graph.graph_service_constants import VitalGraphServiceConstants
from vital_ai_vitalsigns.service.graph.graph_service_status import GraphServiceStatus, GraphServiceStatusType
from vital_ai_vitalsigns.service.vital_name_graph import VitalNameGraph
from vital_ai_vitalsigns.service.graph.utils.virtuoso_utils import VirtuosoUtils
from vital_ai_vitalsigns.service.graph.vital_graph_status import VitalGraphStatus
from vital_ai_vitalsigns.service.metaql.metaql_sparql_builder import MetaQLSparqlBuilder
from vital_ai_vitalsigns.service.metaql.metaql_sparql_impl import MetaQLSparqlImpl
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.config.vitalsigns_config import GraphDatabaseConfig
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.GraphMatch import GraphMatch
from vital_ai_vitalsigns_core.model.RDFStatement import RDFStatement
from vital_ai_vitalsigns_core.model.VitalSegment import VitalSegment
from vital_ai_vitalsigns.metaql.metaql_query import SelectQuery as MetaQLSelectQuery
from vital_ai_vitalsigns.metaql.metaql_query import GraphQuery as MetaQLGraphQuery

G = TypeVar('G', bound='GraphObject')


class CustomHTTPDigestAuth(HTTPDigestAuth):
    def handle_401(self, r, **kwargs):
        # Close the connection when a 401 Unauthorized is encountered
        # try to avoid the issue with chunked transfer exception
        logging.info(f"HTTPDigestAuth for {r.url}")

        r.request.headers['Connection'] = 'close'

        if hasattr(r.raw, 'release_conn'):
            logging.info(f"Releasing connection for {r.url}")
            r.raw.release_conn()

        return super().handle_401(r, **kwargs)


class CustomHTTPAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        try:
            logging.info(f"Adapter Sending request to {request.url}")
            return super().send(request, **kwargs)
        # except (ChunkedEncodingError, ProtocolError) as e:
        except Exception as e:
            logging.info(f"Error: {e}, retrying...")
            raise


class VirtuosoGraphService(VitalGraphService):

    def __init__(self, config: GraphDatabaseConfig, **kwargs):
        # Extract configuration values from the database config
        self.username = config.username
        self.password = config.password
        self.endpoint = config.endpoint.rstrip('/') if config.endpoint else None
        self.server_name = config.server_name
        self.server_user = config.server_user
        self.server_dataset_dir = config.server_dataset_dir
        self.pem_path = config.pem_path

        if self.endpoint:
            self.sparql_auth_endpoint = f"{self.endpoint}/sparql-auth"
            self.graph_crud_auth_endpoint = f"{self.endpoint}/sparql-graph-crud-auth"
        else:
            self.sparql_auth_endpoint = None
            self.graph_crud_auth_endpoint = None
            
        super().__init__(config, **kwargs)

    # keep cache of graphs/namespaces
    # which gets managed by background thread?
    # could be at the service level, but that would mean
    # moving the graph existence checks to service level also
    # this would account for other processes adding/removing graphs

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

    def _get_graph_internal(self, graph_uri: str) -> VitalSegment | None:

        base_uri = self.base_uri
        namespace = self.namespace

        logging.info(f"Getting graph: {graph_uri}")

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

            sq = (
                QueryBuilder.select_query()
                .graph_uri(graph_uri)
                .constraint_list(
                    AndConstraintList()
                    .node_constraint(
                        ClassConstraint(
                            clazz=VitalSegment.get_class_uri()
                        )
                    )
                )
                .build()
            )

            metaql_result = self.metaql_select_query(
                select_query=sq
            )

            rl = metaql_result.get_result_list()

            result_list = []

            for r in rl:
                graph_object=r.graph_object
                score=r.score
                result_list.append(graph_object)

            if len(result_list) == 1:
                return result_list[0]

            return None

        else:
            # raise ValueError(f"Graph with URI {graph_uri} does not exist.")
            return None

    def service_status(self) -> GraphServiceStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        # check if connection is active
        status_type = GraphServiceStatusType.CONNECTION_ERROR

        service_graph_uri = f"{base_uri}/{namespace}/{VitalGraphServiceConstants.SERVICE_GRAPH_ID}"

        vital_segment = self._get_graph_internal(service_graph_uri)

        # check if initialized

        if vital_segment is None:
            status_type = GraphServiceStatusType.UNINITIALIZED
            status = GraphServiceStatus(status_type, "Uninitialized")
            return status

        status_type = GraphServiceStatusType.READY

        status = GraphServiceStatus(status_type)

        return status

    def service_info(self) -> dict:

        base_uri = self.base_uri
        namespace = self.namespace

        service_info = {}

        return service_info

    def list_graph_uris(self, *,
                    safety_check: bool = True) -> List[str]:

        base_uri = self.base_uri
        namespace = self.namespace

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

        graph_uri_list = []

        for result in results["results"]["bindings"]:
            graph_uri = result["g"]["value"]
            graph_uri_list.append(graph_uri)

        return graph_uri_list

    def is_graph_global(self, graph_id: str, *,
                        account_id: str|None = None) -> bool:

        base_uri = self.base_uri
        namespace = self.namespace

        service_graph_uri = f"{base_uri}/{namespace}/{VitalGraphServiceConstants.SERVICE_GRAPH_ID}"

        query = f"""

                   SELECT ?global WHERE {{

                   GRAPH ?g {{
                        ?s <http://vital.ai/ontology/vital-core#hasSegmentNamespace> "{namespace}"^^xsd:string .
                        ?s <http://vital.ai/ontology/vital-core#hasSegmentID> "{graph_id}"^^xsd:string .
                        ?s <http://vital.ai/ontology/vital-core#isSegmentGlobal> ?global .
                        
                        ?s <http://vital.ai/ontology/vital-core#vitaltype> <http://vital.ai/ontology/vital-core#VitalSegment> .
                        ?s ?p ?o .
                   }}
                   FILTER(?g != <{service_graph_uri}>)
                   }}
                   ORDER BY ?global
               """

        # logging.info(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)

        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            is_global = result["global"]["value"]
            if is_global:
                return True

        return False


    # TODO return value for initialized vs error
    def initialize_service(self) -> bool:

        base_uri = self.base_uri
        namespace = self.namespace

        logging.info(f"initializing graph service with namespace: {namespace}")
        logging.info(f"initializing graph service with base uri: {base_uri}")

        target_graph_uri = f"{base_uri}/{namespace}/{VitalGraphServiceConstants.SERVICE_GRAPH_ID}"

        logging.info(f"target graph uri: {target_graph_uri}")

        # check for service graph
        # if found, return false

        query = f"""
                ASK WHERE {{
                    GRAPH <{target_graph_uri}> {{ ?s ?p ?o }}
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
            logging.info(f"target graph uri exists: {target_graph_uri}")
            return False

        # check for graphs that include the namespace
        # if found, return false

        prefix = f"{base_uri}/{namespace}"

        graph_uri_list = self.list_graph_uris()

        for graph_uri in graph_uri_list:
            graph_uri = str(graph_uri)

            if graph_uri.startswith(prefix):
                logging.info(f"graph uri with prefix {prefix} exists: {graph_uri}")
                return False

        # create service graph, insert vitalsegment

        # this segment represents the service graph
        vital_segment = VitalSegment()
        vital_segment.URI = URIGenerator.generate_uri()

        # re-arrange these?  add properties?
        # store base_uri?

        vital_segment.name = VitalGraphServiceConstants.SERVICE_GRAPH_ID

        # use this to find segments within a namespace
        vital_segment.segmentNamespace = namespace

        # each graph sets its own value for this
        vital_segment.segmentGraphURI = target_graph_uri

        vital_segment.segmentID = VitalGraphServiceConstants.SERVICE_GRAPH_ID
        vital_segment.segmentTenantID = None
        vital_segment.segmentGlobal = False

        # add json for index state
        vital_segment.segmentStateJSON = "[]"

        rdf_string = vital_segment.to_rdf()

        logging.info(f"{rdf_string}")

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={target_graph_uri}"

        headers = {
            'Content-Type': 'application/n-triples',
            'Content-Length': str(len(rdf_string)),
            'Connection': 'close'
        }

        response = requests.put(
            endpoint_url,
            data=rdf_string,
            headers=headers,
            auth=HTTPDigestAuth(self.username, self.password)
        )

        if response.status_code in [200, 201]:
            logging.info(f"target graph uri initialized: {target_graph_uri}")
            return True
        else:
            logging.info(f"target graph uri failed to initialize: {target_graph_uri}")
            return False

    def destroy_service(self) -> bool:

        base_uri = self.base_uri
        namespace = self.namespace

        logging.info(f"destroying graph service: {namespace}")

        # check for service graph
        # if not found, return false

        target_graph_uri = f"{base_uri}/{namespace}/{VitalGraphServiceConstants.SERVICE_GRAPH_ID}"

        logging.info(f"target graph uri: {target_graph_uri}")

        try:
            query = f"""
                    ASK WHERE {{
                        GRAPH <{target_graph_uri}> {{ ?s ?p ?o }}
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
                logging.info(f"target graph uri does not exist: {target_graph_uri}")
                return False

        except Exception as e:
            logging.error(f"exception checking target graph uri {target_graph_uri}: {e}")
            return False

        # find graphs that include namespace
        # TODO check that these graphs are in the service graph
        # query via segment objects

        prefix = f"{base_uri}/{namespace}"

        # TODO this will return only graphs within this service
        # once query updated
        name_graph_list = self.list_graphs()

        graph_to_delete_list = []

        for name_graph in name_graph_list:
            graph_uri = str(name_graph.get_graph_uri())

            if graph_uri.startswith(prefix) and graph_uri != target_graph_uri:
                logging.info(f"graph uri with prefix {prefix} exists: {graph_uri}")
                graph_to_delete_list.append(name_graph)

        # remove graphs with namespace
        for name_graph in graph_to_delete_list:
            graph_uri = str(name_graph.get_graph_uri())
            try:
                graph_id = name_graph.get_graph_id()
                global_graph = name_graph.is_global()
                delete_status = self.delete_graph(graph_id, global_graph=global_graph)
                logging.info(f"status of deleting graph uri {graph_uri}: {delete_status}")
            except Exception as e:
                logging.error(f"error deleting graph uri {graph_uri}: {e}")

        # remove service graph
        try:
            delete_status = self.delete_graph(VitalGraphServiceConstants.SERVICE_GRAPH_ID)
            logging.info(f"status of deleting service graph uri {target_graph_uri}: {delete_status}")
        except Exception as e:
            logging.error(f"error deleting graph uri {target_graph_uri}: {e}")

        return True

    def list_graphs(self, *,
                    account_id: str | None = None,
                    include_global: bool = True,
                    include_private: bool = True,
                    safety_check: bool = True) -> List[VitalNameGraph]:

        base_uri = self.base_uri
        namespace = self.namespace

        service_graph_uri = f"{base_uri}/{namespace}/{VitalGraphServiceConstants.SERVICE_GRAPH_ID}"

        # SELECT DISTINCT ?g WHERE { GRAPH ?g {?s ?p ?o} } ORDER BY ?g

        # TODO
        # include_global: bool = True,
        # include_private: bool = True,

        account_id_term = ""

        if account_id:
            account_id_term = f"?s <http://vital.ai/ontology/vital-core#hasSegmentTenantID> \"{account_id}\"^^xsd:string ."
        else:
            account_id_term = """
            FILTER NOT EXISTS {
                ?s <http://vital.ai/ontology/vital-core#hasSegmentTenantID> ?value .
            }"""

        query = f"""
            
            SELECT DISTINCT ?graphID, ?graphGlobal WHERE {{
            
            GRAPH ?g {{
                ?s <http://vital.ai/ontology/vital-core#hasSegmentNamespace> "{namespace}"^^xsd:string .
                ?s <http://vital.ai/ontology/vital-core#hasSegmentID> ?graphID .
                ?s <http://vital.ai/ontology/vital-core#isSegmentGlobal> ?graphGlobal .

                {account_id_term}

                ?s <http://vital.ai/ontology/vital-core#vitaltype> <http://vital.ai/ontology/vital-core#VitalSegment> .
            }}
            FILTER(?g != <{service_graph_uri}>)
            }}
            ORDER BY ?graphID
        """

        # logging.info(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)

        results = sparql.query().convert()

        name_graph_list = []

        for result in results["results"]["bindings"]:
            graph_id = result["graphID"]["value"]
            graph_global = result["graphGlobal"]["value"]

            g_uri = self.get_graph_uri(graph_id=graph_id,
                                       account_id=account_id,
                                       is_global=graph_global)

            name_graph = VitalNameGraph(g_uri, graph_id=graph_id, is_global=graph_global)


            name_graph_list.append(name_graph)

        return name_graph_list

    def get_graph(self, graph_id: str, *,
                  global_graph: bool = False,
                  account_id: str | None = None,
                  safety_check: bool = True) -> VitalNameGraph:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

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
            return VitalNameGraph(graph_uri,
                                  graph_id=graph_id,
                                  account_id=account_id,
                                  is_global=global_graph)
        else:
            raise ValueError(f"Graph with URI {graph_uri} does not exist.")

    # create graph
    # store name graph in vital service graph and in the graph itself
    # a graph needs to have some triples in it to exist

    def check_create_graph(self, graph_id: str, *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           safety_check: bool = True) -> bool:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

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
        vital_segment.name = graph_id

        vital_segment.segmentNamespace = namespace

        vital_segment.segmentID = graph_id
        vital_segment.segmentTenantID = account_id

        vital_segment.segmentGraphURI = graph_uri

        vital_segment.segmentGlobal = global_graph

        rdf_string = vital_segment.to_rdf()

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={graph_uri}"

        headers = {
            'Content-Type': 'application/rdf+xml',
            'Content-Length': str(len(rdf_string)),
            'Connection': 'close'
        }

        response = requests.put(
            endpoint_url,
            data=rdf_string,
            headers=headers,
            auth=HTTPDigestAuth(self.username, self.password)
        )

        if response.status_code not in [200, 201]:
            response.raise_for_status()

        return True

    # there is an occasional error with connections,
    # which seems to have something to do with the initial 401 auth failure and
    # subsequent auth with digest.
    # setting headers seems to help
    # trying to explicitly close the initial 401 connection
    # so that a new connection is made
    # there may be some race condition, which running locally may
    # cause to happen more frequently.

    def send_with_retries(
            self,
            method,
            url,
            data=None,
            headers=None,
            auth=None,
            timeout=(10, 30),
            max_retries=5
    ):
        """
        Sends a request with retries on network-related errors.

        :param method: HTTP method, e.g., 'PUT', 'POST'
        :param url: URL to send the request to
        :param data: Data to be sent in the request
        :param headers: Headers for the request
        :param auth: Authentication information
        :param timeout: Tuple of (connect timeout, read timeout)
        :param max_retries: Maximum number of retries on failure
        :return: Response object or None if final attempt fails
        """

        # Create session and mount the custom adapter with retry strategy
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,  # Retry up to max_retries times
            backoff_factor=1,  # Backoff time (1 second)
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=[method.upper()],  # Retry for specified method
        )
        adapter = CustomHTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Retry loop for handling connection errors manually
        for attempt in range(max_retries):
            try:

                logging.info(f"Attempt: {url} {attempt + 1}/{max_retries}")

                response = session.request(
                    method=method,
                    url=url,
                    data=data,
                    headers=headers,
                    auth=auth,
                    timeout=timeout
                )

                return response

            except (ChunkedEncodingError, ProtocolError, ConnectionError) as e:
                logging.warning(f"Retry attempt {attempt + 1} failed with error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Optional: Add backoff between retries
                else:
                    logging.error(f"Final failure after {max_retries} attempts: {e}")
                    return None  # Return None if all retries fail
            except Exception as e:
                logging.error(f"Unhandled error: {e}")
                return None

    def create_graph(self, graph_id: str, *,
                     global_graph: bool = False,
                     account_id: str | None = None,
                     safety_check: bool = True) -> bool:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        query = f"""
                ASK WHERE {{
                    GRAPH <{graph_uri}> {{ ?s ?p ?o }}
                }}
                """

        sparql.setQuery(query)
        sparql.setMethod('POST')
        sparql.setReturnFormat('json')

        result = sparql.query().convert()

        if result["boolean"]:
            raise ValueError(f"Graph with URI {graph_uri} already exists.")

        vital_segment = VitalSegment()
        vital_segment.URI = URIGenerator.generate_uri()

        vital_segment.name = graph_id
        vital_segment.segmentNamespace = namespace
        vital_segment.segmentID = graph_id
        vital_segment.segmentTenantID = account_id

        vital_segment.segmentGlobal = global_graph

        vital_segment.segmentGraphURI = graph_uri

        rdf_string = vital_segment.to_rdf()

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={graph_uri}"

        headers = {
            'Content-Type': 'application/n-triples',
            'Content-Length': str(len(rdf_string)),
            'Connection': 'close'
        }

        response = self.send_with_retries(
            method="PUT",
            url=endpoint_url,
            data=rdf_string,
            headers=headers,
            auth= CustomHTTPDigestAuth(self.username, self.password),
            timeout=(10, 30),
            max_retries=3
        )

        if response:
            logging.info(response.status_code)
            logging.info(response.text)
        else:
            logging.info("Request failed after retries.")

        return True

    # delete graph
    # delete graph itself plus segment record

    def delete_graph(self, graph_id: str, *,
                     global_graph: bool = False,
                     account_id: str | None = None,
                     safety_check: bool = True) -> bool:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

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

        if response.status_code not in [200, 204]:
            response.raise_for_status()

        return True

    # purge graph (delete all but name graph)

    def purge_graph(self, graph_id: str, *,
                    global_graph: bool = False,
                    account_id: str | None = None,
                    safety_check: bool = True) -> bool:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        vs = VitalSigns()

        segment_type_uri = "http://vital.ai/ontology/vital-core#VitalSegment"

        if not self._check_unique_subject(graph_uri, segment_type_uri):
            raise ValueError(f"Mismatch of segments within graph: {graph_uri}")

        query_vital_segments = f"""
                SELECT ?s ?p ?o WHERE {{
                    GRAPH <{graph_uri}> {{
                        ?s <http://vital.ai/ontology/vital-core#vitaltype> <{segment_type_uri}> .
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

        # logging.info(results)

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

        # logging.info(n_triples_string)

        vital_segment = vs.from_rdf(n_triples_string)

        # logging.info(vital_segment.to_rdf())

        endpoint_url = f"{self.graph_crud_auth_endpoint}?graph-uri={graph_uri}"

        rdf_string = vital_segment.to_rdf()

        headers = {
            'Content-Type': 'application/n-triples',
            'Content-Length': str(len(rdf_string)),
            'Connection': 'close'
        }

        # put replaces graph with new data (thus deleting existing graph)
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

    def get_graph_all_objects(self,
                              graph_id: str, *,
                              limit: int = 100,
                              offset: int = 0,
                              global_graph: bool = False,
                              account_id: str | None = None,
                              safety_check: bool = True) -> ResultList:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        vs = VitalSigns()

        # check if graph exists
        # throws exception if not exists
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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
                LIMIT {limit}
                OFFSET {offset}
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

    def insert_object(self, graph_id: str, graph_object: G, *,
                      global_graph: bool = False,
                      account_id: str | None = None,
                      safety_check: bool = True) -> VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # throws exception if not exists
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

    def insert_object_list(self, graph_id: str, graph_object_list: List[G], *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           safety_check: bool = True) -> VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # throws exception if not exists
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

    def update_object(self, graph_object: G, *,
                      graph_id: str = None,
                      upsert: bool = False,
                      global_graph: bool = False,
                      account_id: str | None = None,
                      safety_check: bool = True) -> VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )
        if graph_uri is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

    def update_object_list(self, graph_object_list: List[G], *,
                           graph_id: str = None,
                           upsert: bool = False,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           safety_check: bool = True) -> VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        if graph_id is None:
            return VitalGraphStatus(-1, "Error: graph_id is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )


        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

    def get_object(self, object_uri: str, *,
                   graph_id: str = None,
                   global_graph: bool = False,
                   account_id: str | None = None,
                   safety_check: bool = True) -> G:

        base_uri = self.base_uri
        namespace = self.namespace

        vs = VitalSigns()

        if graph_id is None:
            raise ValueError("Error: graph_uri is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

        # logging.info(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat('rdf+xml')  # force returning a graph

        try:
            graph = sparql.query().convert()
            # logging.info(f"Triple Count: {len(graph)}")

            graph_object = vs.from_triples(graph.triples((None, None, None)))

            return graph_object

        except Exception as e:
            raise ValueError(f"Error retrieving object {object_uri}: {str(e)}")

    def get_object_list(self, object_uri_list: List[str], *,
                        graph_id: str = None,
                        global_graph: bool = False,
                        account_id: str | None = None,
                        safety_check: bool = True) -> ResultList:

        base_uri = self.base_uri
        namespace = self.namespace

        # TODO do in bulk rather than one at a time

        vs = VitalSigns()

        if graph_id is None:
            raise ValueError("Error: graph_uri is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

    def get_object_list_bulk(self, object_uri_list: List[str], *,
                             graph_id: str = None,
                             global_graph: bool = False,
                             account_id: str | None = None,
                             safety_check: bool = True) -> ResultList:

        base_uri = self.base_uri
        namespace = self.namespace

        vs = VitalSigns()

        if graph_id is None:
            raise ValueError("Error: graph_uri is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

        values_clause = " ".join(f"<{uri}>" for uri in object_uri_list)

        results = []

        query = f"""
                SELECT ?s ?p ?o WHERE {{
            GRAPH <{graph_uri}> {{
                VALUES ?s {{ {values_clause} }}
                ?s ?p ?o .
            }}
        }}
        """

        # logging.info(query)

        sparql = SPARQLWrapper(self.sparql_auth_endpoint)
        sparql.setCredentials(self.username, self.password)
        sparql.setHTTPAuth(DIGEST)

        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat('json')

        try:
            result = sparql.query().convert()
            graph = rdflib.Graph()

            for result in result['results']['bindings']:
                s = rdflib.URIRef(result['s']['value'])
                p = rdflib.URIRef(result['p']['value'])
                o = rdflib.URIRef(result['o']['value']) if result['o']['type'] == 'uri' else rdflib.Literal(
                    result['o']['value'])
                graph.add((s, p, o))

            unique_subjects = set(graph.subjects())

            for subject_uri in unique_subjects:

                graph_object = vs.from_triples(graph.triples((URIRef(subject_uri), None, None)))

                results.append(graph_object)

        except Exception as e:
            raise ValueError(f"Error retrieving object list: {str(e)}")

        result_list = ResultList()

        for r in results:
            result_list.add_result(r)

        return result_list

    # delete uri (scoped to all vital service graphs)
    # delete uri list (scoped to all vital service graphs)
    # delete uri (scoped to graph or graph list)
    # delete uri list (scoped to graph or graph list)

    def delete_object(self, object_uri: str, *,
                      graph_id: str = None,
                      global_graph: bool = False,
                      account_id: str | None = None,
                      safety_check: bool = True) -> VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        if graph_id is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

    def delete_object_list(self, object_uri_list: List[str], *,
                           graph_id: str = None,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           safety_check: bool = True) -> VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        # todo do in bulk

        if graph_id is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

    def filter_query(self, graph_id: str, sparql_query: str,  uri_binding='uri', *,
                     limit=100,
                     offset=0,
                     resolve_objects=True,
                     global_graph: bool = False,
                     account_id: str | None = None,
                     safety_check: bool = True) -> ResultList | VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        if graph_id is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )


        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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
            return self.get_object_list(object_uri_list, graph_id=graph_id)
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

    def query(self, graph_id: str, sparql_query: str, uri_binding='uri', *,
              limit=100,
              offset=0,
              resolve_objects=True,
              global_graph: bool = False,
              account_id: str | None = None,
              safety_check: bool = True) -> ResultList | VitalGraphStatus:

        base_uri = self.base_uri
        namespace = self.namespace

        if graph_id is None:
            return VitalGraphStatus(-1, "Error: graph_uri is not set.")

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )
        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

        logging.info(query)

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
            return self.get_object_list(object_uri_list, graph_id=graph_id)
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
                        graph_id: str,
                        sparql_query: str,
                        namespace_list: List[Ontology],
                        binding_list: List[Binding], *,
                        limit=100, offset=0,
                        global_graph: bool = False,
                        account_id: str | None = None,
                        safety_check: bool = True) -> ResultList:

        base_uri = self.base_uri
        namespace = self.namespace

        if graph_id is None:
            result_list = ResultList()
            result_list.set_status(-1)
            result_list.set_message("Error: graph_uri is not set.")
            return result_list

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # exception if graph doesn't exist
        name_graph = self.get_graph(graph_id,
                                    account_id=account_id,
                                    global_graph=global_graph)

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

        print(f"SPARQL Query:\n{query}\n")

        logging.info(query)

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
            rdf_triple.rdfPredicate = str(p)  # property from binding
            rdf_triple.rdfObject = str(o)  # uri of matching object

            result_list.add_result(rdf_triple)

        return result_list

    def query_construct_solution(self,
                                 graph_id: str,
                                 sparql_query: str,
                                 namespace_list: List[Ontology],
                                 binding_list: List[Binding],
                                 root_binding: str | None = None, *,
                                 limit=100,
                                 offset=0,
                                 global_graph: bool = False,
                                 account_id: str | None = None,
                                 resolve_objects: bool = True,
                                 safety_check: bool = True) -> SolutionList:

        base_uri = self.base_uri
        namespace = self.namespace

        graph_uri = self.get_graph_uri(
            graph_id=graph_id,
            account_id=account_id,
            is_global=global_graph
        )

        # object cache to use during query
        # added bulk retrieval of objects
        # graph_collection = GraphCollection(use_rdfstore=False, use_vectordb=False)

        graph_map: dict = {}

        result_list = self.query_construct(
            graph_id,
            sparql_query,
            namespace_list,
            binding_list,
            global_graph=global_graph,
            account_id=account_id,
            limit=limit, offset=offset)

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

        unique_objects = set(graph.objects())

        uri_objects = {o for o in unique_objects if isinstance(o, URIRef)}

        retrieve_list: List[str] = []

        for obj_uri in uri_objects:
            object_uri_str = str(obj_uri)
            # print(f"object uri: {object_uri_str}")
            retrieve_list.append(object_uri_str)

        # print(f"Bulk Retrieving URIs length: {len(retrieve_list)}")

        total_objects = len(retrieve_list)

        start_index = 0

        chunk_size = 1_000

        while start_index < total_objects:
            end_index = min(start_index + chunk_size, total_objects)
            chunk = retrieve_list[start_index:end_index]

            # print(f"Bulk Retrieving URIs Chunk length: {len(chunk)}")

            result_list = self.get_object_list_bulk(chunk,
                                                    graph_id=graph_id,
                                                    account_id=account_id,
                                                    global_graph=global_graph)

            for re in result_list:
                graph_object = re.graph_object
                # graph_collection.add(graph_object)
                graph_map[str(graph_object.URI)] = graph_object

            start_index += chunk_size

        # print(f"Bulk Retrieving URIs Complete length: {len(retrieve_list)}")

        # is necessary?
        # does construct create duplicates?
        unique_triples = set(graph.triples((None, None, None)))

        unique_graph = Graph()

        for triple in unique_triples:
            unique_graph.add(triple)

        unique_subjects = set(unique_graph.subjects())

        solution_count = 0

        for subject in unique_subjects:

            uri_map = {}
            obj_map = {}

            # root_binding_uri = None
            root_binding_obj = None

            # created unique set of all triples instead
            # triples = set(graph.triples((subject, None, None)))

            triples = unique_graph.triples((subject, None, None))

            for s, p, o in triples:

                matching_bindings = [binding for binding in binding_list if binding.property_uri == str(p)]

                if len(matching_bindings) == 1:

                    matching_binding = matching_bindings[0]

                    binding_var = matching_binding.variable

                    binding_value = o

                    # set to string instead of Node
                    uri_map[binding_var] = str(binding_value)

                    if matching_binding.value_type == BindingValueType.URIREF:

                        # cache individual objects
                        # should already be cached

                        # cache_obj = graph_collection.get(str(o))

                        cache_obj = graph_map[str(o)]

                        if cache_obj is None:

                            # print(f"Retrieving cache miss: {str(o)}")

                            binding_obj = self.get_object(str(o), graph_id=graph_id)
                            # graph_collection.add(binding_obj)
                            graph_map[str(o)] = binding_obj

                        else:
                            binding_obj = cache_obj

                        obj_map[binding_var] = binding_obj

                        if binding_var == root_binding:
                            # root_binding_uri = binding_value
                            root_binding_obj = binding_obj

            solution_count += 1
            # print(f"Adding Solution: {solution_count}")
            solution = Solution(uri_map, obj_map, root_binding, root_binding_obj)

            solutions.append(solution)

        solution_list = SolutionList(solutions, limit, offset)

        # logging.info(f"Completed Solutions: {solution_count}")

        return solution_list

    def metaql_select_query(self, *,
                            select_query: MetaQLSelectQuery,
                            namespace_list: List[Ontology] = None,
                            account_id: str|None = None, is_global: bool = False) -> MetaQLResult:

        base_uri = self.base_uri
        namespace = self.namespace

        namespace_list = [
            Ontology("vital-core", "http://vital.ai/ontology/vital-core#"),
            Ontology("vital", "http://vital.ai/ontology/vital#"),
            Ontology("vital-aimp", "http://vital.ai/ontology/vital-aimp#"),
            Ontology("haley", "http://vital.ai/ontology/haley"),
            Ontology("haley-ai-question", "http://vital.ai/ontology/haley-ai-question#"),
            Ontology("haley-ai-kg", "http://vital.ai/ontology/haley-ai-kg#")
        ]

        sparql_impl = MetaQLSparqlImpl()

        graph_uri_list = select_query.get('graph_uri_list', [])

        graph_id_list = select_query.get('graph_id_list', [])


        offset = select_query.get('offset', 0)
        limit = select_query.get('limit', 10)

        arc: ArcRoot = select_query.get('arc', None)

        if arc is None:
            # error
            metaql_result = MetaQLResult()
            return metaql_result

        constraint_list_list = arc.get('constraint_list_list', [])

        term_count = 0

        for cl in constraint_list_list:

            constraint_list = cl.get('constraint_list', [])

            for constraint in constraint_list:

                logging.info(f"Constraint: {constraint}")

                term_count += 1

                metaql_class = constraint.get('metaql_class')

                if metaql_class == 'NodeConstraint':
                    class_uri = constraint.get('class_uri')

                    constraint_str = f" ?uri a <{class_uri}> ."
                    sparql_impl.add_arc_constraint(constraint_str)

                if metaql_class == 'StringPropertyConstraint':

                    property_uri = constraint.get('property_uri')
                    string_value = constraint.get('string_value')

                    constraint_str = f"""
                    ?uri <{property_uri}> ?term_{term_count} .
                    ?term_{term_count} bif:contains "{string_value}" .
                    """

                    sparql_impl.add_arc_constraint(constraint_str)

        binding_list = [
            Binding("?uri", "urn:hasUri"),
        ]

        constraint_list_str = ""

        # for an OR list these would be UNION-ed together
        for c in sparql_impl.get_arc_constraint_list():

            constraint_list_str += f"""
            {{
                {c}
            }}
            """

        query_str = f"""
        {{
            {constraint_list_str}
        }}
        """

        root_binding = "?uri"

        logging.info(query_str)

        # graph_uri = graph_uri_list[0]

        # TODO handle list instead of single graph_id

        graph_id = graph_id_list[0]

        # name_graph = self.get_name_graph(graph_uri)

        # graph_id = name_graph.get_graph_id()

        # account_id = name_graph.get_account_id()

        # is_global = name_graph.is_global()

        solutions = self.query_construct_solution(
            graph_id,
            query_str,
            namespace_list,
            binding_list,
            root_binding,
            account_id=account_id,
            global_graph=is_global,
            limit=limit, offset=offset)

        # logging.info(f"Solution Count: {len(solutions.solution_list)}")

        rl = ResultList()

        for solution in solutions.solution_list:
            for binding, obj in solution.object_map.items():
                binding_uri = solution.uri_map[binding]
                # print(f"Solution Binding: {binding} : {binding_uri}")
                # print(obj.to_rdf())
                rl.add_result(obj, 1.0)

        total_result_count = len(rl)

        metaql_result = MetaQLResult(
            offset=offset,
            limit=limit,
            total_result_count=total_result_count,
            result_list=rl
        )

        return metaql_result

    def metaql_graph_query(self, *,
                           graph_query: MetaQLGraphQuery,
                           namespace_list: List[Ontology] = None,
                           account_id: str|None = None, is_global: bool = False) -> MetaQLResult:

        base_uri = self.base_uri
        namespace = self.namespace

        sparql_builder = MetaQLSparqlBuilder()

        sparql_impl: MetaQLSparqlImpl = sparql_builder.build_sparql(graph_query)

        limit = sparql_impl.get_limit()

        offset = sparql_impl.get_offset()

        # graph_uri = sparql_impl.get_graph_uri_list()[0]

        # TODO handle list instead of single graph_id

        graph_id = sparql_impl.get_graph_id_list()[0]


        # name_graph = self.get_name_graph(graph_uri)

        # graph_id = name_graph.get_graph_id()

        # account_id = name_graph.get_account_id()

        # is_global = name_graph.is_global()

        resolve_objects = sparql_impl.get_resolve_objects()

        binding_string_list = []

        binding_list = []

        for binding in sparql_impl.get_binding_list():
            b = Binding(f"?{binding}", f"urn:{binding}")
            binding_string_list.append(binding)
            binding_list.append(b)

        root_binding = f"?{sparql_impl.get_root_binding()}"

        term_list = "\n".join(sparql_impl.get_arc_constraint_list())

        bind_constraint_list = "\n".join(sparql_impl.get_bind_constraint_list())

        query_string = f"""
        {term_list}

        {bind_constraint_list}
        """

        solutions = self.query_construct_solution(
            graph_id,
            query_string,
            namespace_list,
            binding_list,
            root_binding,
            account_id=account_id,
            global_graph=is_global,
            limit=limit, offset=offset)

        logging.info(f"Solution Count: {len(solutions.solution_list)}")

        count = 0

        result_object_map = {}

        result_object_list = []

        rl = ResultList()

        for solution in solutions.solution_list:
            count += 1

            gm = GraphMatch()
            gm.URI = URIGenerator.generate_uri()

            logging.info("-------------------------------------")
            logging.info(f"Solution Count: {count}")
            logging.info(f"Root Binding: {solution.root_binding}")
            logging.info(f"Binding Map: {solution.uri_map}")
            for binding, obj in solution.object_map.items():
                binding_uri = solution.uri_map[binding]
                logging.info(f"Solution Binding: {binding} : {binding_uri}")
                logging.info(obj.to_rdf())
                result_object_map[str(obj.URI)] = obj

                prop_string = binding

                if prop_string.startswith("?"):
                    prop_string = prop_string[1:]

                gm.set_property(prop_string, str(binding_uri))

            logging.info("-------------------------------------")

            rl.add_result(gm, 1.0)

        for v in  result_object_map.values():
            result_object_list.append(v)

        metaql_result = MetaQLResult(
            offset=offset,
            limit=limit,
            total_result_count=count,
            binding_list=binding_string_list,
            result_list=rl,
            result_object_list=result_object_list
        )

        return metaql_result

    def trigger_bulk_import(self, graph_uri, file_name):
        """
        Trigger a bulk import in Virtuoso.

        :param graph_uri: The target graph URI for the import.
        :param file_name: The name of the file in the upload directory.
        """

        # TODO get config
        endpoint = "localhost"
        user = "dba"
        password = "dba"

        # delete from DB.DBA.load_list;
        # select * from DB.DBA.load_list;
        # ld_dir ( '/Users/hadfield/Desktop/IMDBData', '*.nt', 'http://vital.ai/graph/imdb-movie-graph-1');
        # rdf_loader_run();
        # DB.DBA.VT_INC_INDEX_DB_DBA_RDF_OBJ();

        connection = pyodbc.connect(
            f'DRIVER=/Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/Contents/MacOS/virtodbcu_r.so;wideAsUTF16=Y;HOST={endpoint};UID={user};PWD={password}')

        file_dir = "/Users/hadfield/Desktop/"

        file_path = f"/Users/hadfield/Desktop/{file_name}"

        try:
            cursor = connection.cursor()

            # query = f"""
            #        INSERT INTO DB.DBA.LOAD_LIST (ll_file, ll_graph, ll_state)
            #        VALUES ('{file_path}', '{graph_uri}', 0)
            #"""

            query = "delete from DB.DBA.load_list"
            cursor.execute(query)
            connection.commit()

            query = f"ld_dir ( '{file_dir}', '{file_name}', '{graph_uri}')"
            cursor.execute(query)
            connection.commit()

            query = "rdf_loader_run()"
            cursor.execute(query)
            connection.commit()

            query = "DB.DBA.VT_INC_INDEX_DB_DBA_RDF_OBJ()"
            cursor.execute(query)
            connection.commit()

            print(f"File '{file_name}' imported into graph '{graph_uri}'.")
            return True
        except Exception as e:
            print(f"Error during bulk import: {e}")
            return False

    def check_import_status_for_file(self, file_name):
        """
        Check the status of a specific file being imported in Virtuoso.

        :param file_name: The name of the file to check.
        :return: A dictionary containing the status of the specified file or None if not found.
        """

        # TODO get config

        endpoint = "localhost"
        user = "dba"
        password = "dba"

        connection = pyodbc.connect(
            f'DRIVER=/Library/ODBC/OpenLink Virtuoso ODBC Driver (Unicode).bundle/Contents/MacOS/virtodbcu_r.so;wideAsUTF16=Y;HOST={endpoint};UID={user};PWD={password}')

        file_path = f"/Users/hadfield/Desktop//{file_name}"

        try:
            cursor = connection.cursor()

            query = f"""SELECT ll_file, ll_graph, ll_state, ll_error
                        FROM DB.DBA.LOAD_LIST
                        WHERE ll_file = '{file_path}'
                    """

            print(query)

            # Query the LOAD_LIST table for the file
            cursor.execute(query)

            results = []
            for row in cursor.fetchall():
                print(row)
                results.append({
                    "file": row.ll_file,
                    "graph": row.ll_graph,
                    "state": row.ll_state,
                    "error": row.ll_error
                })

            print(results)

            return results
        except Exception as e:
            print(f"Error checking import status: {e}")
            return []

    #################################################
    # Import Functions

    def import_graph_batch(self, graph_id: str, object_generator: GraphObjectGenerator,
                           *,
                           global_graph: bool = False,
                           account_id: str | None = None,
                           purge_first: bool = True, batch_size: int = 10_000):
        pass

    def import_graph_batch_file(self, graph_id: str, file_path: str,
                                *,
                                global_graph: bool = False,
                                account_id: str | None = None,
                                purge_first: bool = True, batch_size: int = 10_000):
        pass

    def import_multi_graph_batch(self, object_generator: GraphObjectGenerator,
                                 *,
                                 purge_first: bool = True,
                                 use_account_id: bool = True,
                                 batch_size: int = 10_000):
        pass

    def import_multi_graph_batch_file(self, file_path: str,
                                     *,
                                     purge_first: bool = True,
                                     use_account_id: bool = True,
                                     batch_size: int = 10_000):
        pass



