import json
from typing import List
from vital_ai_vitalsigns.metaql.metaql_builder import MetaQLBuilder
from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.metaql.metaql_status import OK_STATUS_TYPE
from vital_ai_vitalsigns.metaql.query.query_builder import QueryBuilder, AndConstraintList, PropertyConstraint, \
    ConstraintType, ClassConstraint
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_metaql_impl import VirtuosoMetaQLImpl
from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName


class DictEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def main():

    print('Test MetaQL Select Builder')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vital_home = vs.get_vitalhome()

    print(f"VitalHome: {vital_home}")

    vs_config = vs.get_config()

    print(vs_config)

    graph_id = "account1"


    sq = (
        QueryBuilder.select_query()
        # .graph_uri("http://vital.ai/KGRAPH/account1/account1")
        .graph_id(graph_id)
        .constraint_list(
            AndConstraintList()
            .node_constraint(
                PropertyConstraint(
                    property=Property_hasName.get_uri(),
                    comparator=ConstraintType.STRING_CONTAINS,
                    value="John"
                )
            )
            .node_constraint(
                ClassConstraint(
                    clazz=VITAL_Node.get_class_uri()
                )
            )
        )
        .build()
    )

    print(sq)

    select_query_json = json.dumps(sq, indent=4)

    print(select_query_json)

    metaql_query_dict = json.loads(select_query_json)

    metaql_select_query = MetaQLParser.parse_metaql_dict(metaql_query_dict)

    print(metaql_select_query)

    namespace = "VITALTEST"

    ontology_list: List[Ontology] = []

    # add resolving graph objects true/false into query

    sparql_string = VirtuosoMetaQLImpl.generate_select_query_sparql(
        select_query=metaql_select_query,
        namespace_list=ontology_list
    )

    # compare sparql with groovy implementation

    print(f"Select Query SPARQL:\n{sparql_string}")

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

    virtuoso_graph_service = VirtuosoGraphService(
        base_uri="http://vital.ai",
        namespace="KGRAPH",
        username=virtuoso_username,
        password=virtuoso_password,
        endpoint=virtuoso_endpoint
    )

    graph_list = virtuoso_graph_service.list_graphs(account_id="account1")

    for g in graph_list:
        print(f"Graph URI: {g.get_graph_uri()}")

    metaql_result = virtuoso_graph_service.metaql_select_query(
        select_query=metaql_select_query,
        namespace_list=ontology_list,
        account_id="account1"
    )

    print(metaql_result)

    rl = metaql_result.get_result_list()

    result_list = []

    for r in rl:
        result_element = MetaQLBuilder.build_result_element(
            graph_object=r.graph_object,
            score=r.score
        )
        result_list.append(result_element)

    status = OK_STATUS_TYPE

    metaql_status = MetaQLBuilder.build_status(
        status_type=status
    )

    metaql_result_list = MetaQLBuilder.build_result_list(
        offset=metaql_result.get_offset(),
        limit=metaql_result.get_limit(),
        result_count=len(metaql_result.get_result_list()),
        total_result_count=metaql_result.get_total_result_count(),
        result_list=result_list,
    )

    metaql_response = MetaQLBuilder.build_response(
        result_status=metaql_status,
        result_list=metaql_result_list
    )

    print(metaql_response)

    metaql_response_json = json.dumps(metaql_response, cls=DictEncoder, indent=4)

    print(metaql_response_json)

    metaql_response_dict = json.loads(metaql_response_json)

    print(metaql_response_dict)

    metaql_response_parsed = MetaQLParser.parse_metaql_dict(metaql_response_dict)

    print(metaql_response_parsed)


if __name__ == "__main__":
    main()


