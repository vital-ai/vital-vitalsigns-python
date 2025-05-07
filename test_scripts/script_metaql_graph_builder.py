import json
from typing import List

from vital_ai_vitalsigns.metaql.metaql_builder import MetaQLBuilder
from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.metaql.metaql_status import OK_STATUS_TYPE
from vital_ai_vitalsigns.metaql.query.query_builder import QueryBuilder, Arc, AndConstraintList, PropertyConstraint, \
    ConstraintType, ClassConstraint, OrConstraintList, PropertyPathList, AndArcList, MetaQLPropertyPath, NodeBind, \
    EdgeBind, PathBind, SolutionBind
from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.metaql.metaql_sparql_builder import MetaQLSparqlBuilder
from vital_ai_vitalsigns.service.metaql.metaql_sparql_impl import MetaQLSparqlImpl
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName


class DictEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def main():

    print('Test MetaQL Graph Builder')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vital_home = vs.get_vitalhome()

    print(f"VitalHome: {vital_home}")

    vs_config = vs.get_config()

    print(vs_config)

    # bindings were added to this to avoid an error for the missing bindings
    # this is query for fictional data

    gq = (
        QueryBuilder.graph_query(
            limit=100,
            offset=0,
            resolve_objects=True
        )
        .graph_id("urn:123")
        .arc(
            Arc()
            .node_bind(NodeBind(name="node1"))
            .edge_bind(EdgeBind(name="edge1"))
            .path_bind(PathBind(name="path1"))
            .solution_bind(SolutionBind(name="solution1"))
            .constraint_list(
                OrConstraintList()
                .node_constraint(
                    PropertyConstraint(
                        property=Property_hasName.get_uri(),
                        comparator=ConstraintType.STRING_CONTAINS,
                        value="Alfred"
                    )
                )
                .node_constraint(
                    ClassConstraint(
                        clazz=VITAL_Node.get_class_uri()
                    )
                )
            )

            .arc(
                Arc()
                .node_bind(NodeBind(name="node2"))
                .edge_bind(EdgeBind(name="edge2"))
                .path_bind(PathBind(name="path2"))
                .constraint_list(
                    AndConstraintList()
                    .node_constraint(
                        PropertyConstraint(
                            property=Property_hasName.get_uri(),
                            comparator=ConstraintType.STRING_CONTAINS,
                            value="Betty"
                        )
                    )
                    .edge_constraint(
                        ClassConstraint(
                            clazz=VITAL_Edge.get_class_uri()
                        )
                    )
                )
                .property_path_list(
                    PropertyPathList()
                    .property_path(
                        MetaQLPropertyPath(
                            property_uri=Property_hasName.get_uri(),
                        )
                    )
                )
                .arc_list(
                    AndArcList()
                    .arc(
                        Arc()
                        .node_bind(NodeBind(name="node2"))
                        .edge_bind(EdgeBind(name="edge2"))
                        .path_bind(PathBind(name="path2"))
                        .constraint_list(
                            AndConstraintList()
                            .node_constraint(
                                PropertyConstraint(
                                    property=Property_hasName.get_uri(),
                                    comparator=ConstraintType.STRING_CONTAINS,
                                    value="David"
                                )
                            )
                            .node_constraint(
                                ClassConstraint(
                                    clazz=VITAL_Node.get_class_uri()
                                )
                            )
                        )
                    )
                    .arc_list(
                        AndArcList()
                        .arc(
                            Arc()
                            .node_bind(NodeBind(name="node3"))
                            .edge_bind(EdgeBind(name="edge3"))
                            .path_bind(PathBind(name="path3"))
                            .constraint_list(
                                AndConstraintList()
                                .node_constraint(
                                    PropertyConstraint(
                                        property=Property_hasName.get_uri(),
                                        comparator=ConstraintType.STRING_CONTAINS,
                                        value="Edgar"
                                    )
                                )
                                .node_constraint(
                                    ClassConstraint(
                                        clazz=VITAL_Node.get_class_uri()
                                    )
                                )
                            )
                        )
                    )
                )
                .arc(
                    Arc()
                    .node_bind(NodeBind(name="node2"))
                    .edge_bind(EdgeBind(name="edge2"))
                    .path_bind(PathBind(name="path2"))
                    .constraint_list(
                        AndConstraintList()
                        .node_constraint(
                            PropertyConstraint(
                                property=Property_hasName.get_uri(),
                                comparator=ConstraintType.STRING_CONTAINS,
                                value="Charles"
                            )
                        )
                        .node_constraint(
                            ClassConstraint(
                                clazz=VITAL_Node.get_class_uri()
                            )
                        )
                    )

                )
            )
        )
        .build()
    )

    print(gq)

    graph_query_json = json.dumps(gq, indent=4)

    print(graph_query_json)

    metaql_query_dict = json.loads(graph_query_json)

    metaql_graph_query = MetaQLParser.parse_metaql_dict(metaql_query_dict)

    # print(metaql_graph_query)

    graph_query_json = json.dumps(metaql_graph_query, indent=4)

    print(graph_query_json)

    # exit(0)

    # namespace = "VITALTEST"

    ontology_list: List[Ontology] = []

    namespace_list = [
        Ontology("owl", "http://www.w3.org/2002/07/owl#"),
        Ontology("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        Ontology("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
    ]

    iri_list = vs.get_ontology_manager().get_ontology_iri_list()

    ont_prefix_map = {}

    for iri in iri_list:

        if iri.startswith("http://vital.ai/ontology/"):
            prefix = iri[len("http://vital.ai/ontology/"):]

            prefix = prefix.removesuffix("#")

            # print(f"Vital Prefix: {prefix} IRI: {iri}")

            ont_prefix_map[prefix] = iri

    for k in ont_prefix_map.keys():
        # print(f"Ont Prefix: {k} IRI: {ont_prefix_map[k]}")
        ont = Ontology(k, ont_prefix_map[k])
        namespace_list.append(ont)


    # add resolving graph objects true/false into query

    # sparql_string = VirtuosoMetaQLImpl.generate_graph_query_sparql(
    #    namespace=namespace,
    #    graph_query=metaql_graph_query,
    #    namespace_list=ontology_list
    #)

    # print(f"Graph Query SPARQL:\n{sparql_string}")

    sparql_builder = MetaQLSparqlBuilder()

    sparql_impl: MetaQLSparqlImpl = sparql_builder.build_sparql(metaql_graph_query,
                                                                base_uri="http://vital.ai",
                                                                namespace="graph")

    print(sparql_impl)


    # exit(0)

    limit = sparql_impl.get_limit()

    offset = sparql_impl.get_offset()

    graph_uri = sparql_impl.get_graph_uri_list()[0]

    # graph_id = sparql_impl.get_graph_id_list()[0]


    resolve_objects = sparql_impl.get_resolve_objects()

    binding_list = []

    for binding in sparql_impl.get_binding_list():
        b = Binding(f"?{binding}", f"urn:{binding}")
        binding_list.append(b)

    root_binding = f"?{sparql_impl.get_root_binding()}"

    term_list = "\n".join(sparql_impl.get_arc_constraint_list())

    bind_constraint_list = "\n".join(sparql_impl.get_bind_constraint_list())

    query_string = f"""
    {term_list}

    {bind_constraint_list}
    """

    print(query_string)

    # exit(0)

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice in vitalservice_list:
        print(f"vitalservice: {vitalservice}")

    vitalservice = vitalservice_manager.get_vitalservice("local_kgraph")

    virtuoso_graph_service = vitalservice.graph_service

    graph_list = virtuoso_graph_service.list_graphs(
        account_id="account1"
    )

    for g in graph_list:
        print(f"Graph URI: {g.get_graph_uri()}")



    exit(0)


    metaql_result = virtuoso_graph_service.metaql_graph_query(
        graph_query=metaql_graph_query,
        namespace_list=ontology_list
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

    metaql_result_list = MetaQLBuilder.build_result_list(
        offset=metaql_result.get_offset(),
        limit=metaql_result.get_limit(),
        result_count=len(metaql_result.get_result_list()),
        total_result_count=metaql_result.get_total_result_count(),
        binding_list=metaql_result.get_binding_list(),
        result_list=result_list,
        result_object_list=metaql_result.get_result_object_list(),
    )

    status = OK_STATUS_TYPE

    metaql_status = MetaQLBuilder.build_status(
        status_type=status
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

    metaql_result_list = metaql_response_parsed['result_list']

    binding_list = metaql_result_list['binding_list']

    print(binding_list)

    result_object_list = metaql_result_list['result_object_list']

    object_map = {}

    for go in result_object_list:
        print(f"Object: {go.to_json()}")
        uri = str(go.URI)
        object_map[uri] = go

    result_list = metaql_result_list['result_list']

    for re in result_list:
        print(f"ResultElement: {re}")
        go = re["graph_object"]
        print(go.to_json())
        for b in binding_list:
            b_uri = str(go[b])
            print(f"Binding: {b} : {object_map[b_uri].to_json()}")


if __name__ == "__main__":
    main()


