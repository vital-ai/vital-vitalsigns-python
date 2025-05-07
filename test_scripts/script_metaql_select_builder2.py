import json
from typing import List

from ai_haley_kg_domain.model.KGEntity import KGEntity

from test_scripts.construct_query import ConstructQuery
from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.metaql.query.query_builder import QueryBuilder, AndConstraintList, PropertyConstraint, \
    ConstraintType, ClassConstraint
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_metaql_impl import VirtuosoMetaQLImpl
from vital_ai_vitalsigns.service.graph.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName


def generate_select_entity_query(search_string: str):

    namespace_list = get_default_namespace_list()

    binding_list = [
        Binding("?uri", "urn:hasUri"),
    ]

    entity_description_query = f"""
    {{
        ?uri a haley-ai-kg:KGEntity .
        ?uri haley-ai-kg:hasKGraphDescription ?description .
        ?description bif:contains "{search_string}" .
    }}
    """

    entity_name_query = f"""
    {{
        {{
            ?uri a haley-ai-kg:KGEntity .
        }}
        
        {{
            ?uri vital-core:hasName ?name .
            ?name bif:contains "{search_string}" .
        }}
    }}
    """

    root_binding = "?uri"

    construct_query = ConstructQuery(namespace_list, binding_list, entity_name_query, root_binding)

    return construct_query


def get_default_namespace_list():
    namespace_list = [
        Ontology("vital-core", "http://vital.ai/ontology/vital-core#"),
        Ontology("vital", "http://vital.ai/ontology/vital#"),
        Ontology("vital-aimp", "http://vital.ai/ontology/vital-aimp#"),
        Ontology("haley", "http://vital.ai/ontology/haley"),
        Ontology("haley-ai-question", "http://vital.ai/ontology/haley-ai-question#"),
        Ontology("haley-ai-kg", "http://vital.ai/ontology/haley-ai-kg#")
    ]

    return namespace_list


def main():

    print('Test MetaQL Select Builder')

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

    print(f"Virtuoso Endpoint: {virtuoso_endpoint}")

    virtuoso_graph_service = VirtuosoGraphService(
        base_uri="http://vital.ai",
        namespace="graph",
        username=virtuoso_username,
        password=virtuoso_password,
        endpoint=virtuoso_endpoint
    )

    wordnet_graph_uri = 'http://vital.ai/graph/wordnet-frames-graph-1'

    wordnet_graph_id = 'wordnet-frames-graph-1'


    sq = (
        QueryBuilder.select_query(
            limit=10, offset=0
        )
        .graph_uri(wordnet_graph_uri)
        .constraint_list(
            AndConstraintList()
            .node_constraint(
                PropertyConstraint(
                    property=Property_hasName.get_uri(),
                    comparator=ConstraintType.STRING_CONTAINS,
                    value="happy"
                )
            )
            .node_constraint(
                ClassConstraint(
                    clazz=KGEntity.get_class_uri()
                )
            )
        )
        .build()
    )

    print(sq)

    select_query_json = json.dumps(sq, indent=4)

    print(select_query_json)

    metaql_query_dict = json.loads(select_query_json)

    metaql_query = MetaQLParser.parse_metaql_dict(metaql_query_dict)

    print(metaql_query)

    namespace = "VITALTEST"

    ontology_list: List[Ontology] = []





    # add resolving graph objects true/false into query

    sparql_string = VirtuosoMetaQLImpl.generate_select_query_sparql(
        select_query=metaql_query,
        namespace_list=ontology_list
    )

    # compare sparql with groovy implementation

    print(f"Select Query SPARQL:\n{sparql_string}")

    search_string = "happy"

    construct_query = generate_select_entity_query(search_string)

    """
    result_list: ResultList = virtuoso_graph_service.query_construct(
        wordnet_graph_uri,
        construct_query.query,
        construct_query.namespace_list,
        construct_query.binding_list,
        limit=10, offset=0
    )

    print(result_list)

    for r in result_list:
        graph_object = r.graph_object
        print(graph_object.to_json())
    """

    solutions = virtuoso_graph_service.query_construct_solution(
        wordnet_graph_id,
        construct_query.query,
        construct_query.namespace_list,
        construct_query.binding_list,
        construct_query.root_binding,
        limit=10, offset=0)

    print(f"Wordnet Solution Count: {len(solutions.solution_list)}")

    for solution in solutions.solution_list:
        for binding, obj in solution.object_map.items():
            binding_uri = solution.uri_map[binding]
            print(f"Wordnet Solution Binding: {binding} : {binding_uri}")
            print(obj.to_rdf())


if __name__ == "__main__":
    main()


