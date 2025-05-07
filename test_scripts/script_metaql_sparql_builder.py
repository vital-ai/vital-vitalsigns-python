import json
from ai_haley_kg_domain.model.KGEntity import KGEntity
from ai_haley_kg_domain.model.KGFrame import KGFrame
from ai_haley_kg_domain.model.KGSlot import KGSlot
from ai_haley_kg_domain.model.properties.Property_hasEntitySlotValue import Property_hasEntitySlotValue
from ai_haley_kg_domain.model.properties.Property_hasKGSlotType import Property_hasKGSlotType
from ai_haley_kg_domain.model.properties.Property_hasKGraphDescription import Property_hasKGraphDescription
from vital_ai_vitalsigns.metaql.arc.metaql_arc import ARC_TRAVERSE_TYPE_PROPERTY
from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.metaql.query.query_builder import QueryBuilder, AndConstraintList, PropertyConstraint, \
    ConstraintType, ClassConstraint, Arc, OrConstraintList, NodeBind, EdgeBind, PathBind, PropertyPathList, \
    MetaQLPropertyPath, AndArcList, OrArcList, SolutionBind
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.service.metaql.metaql_sparql_builder import MetaQLSparqlBuilder
from vital_ai_vitalsigns.service.metaql.metaql_sparql_impl import MetaQLSparqlImpl
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName

def main():

    print('Test MetaQL SPARQL Builder')

    print("Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vital_home = vs.get_vitalhome()

    print(f"VitalHome: {vital_home}")

    vs_config = vs.get_config()

    print(vs_config)

    # wordnet_graph_uri = 'http://vital.ai/graph/wordnet-frames-graph-1'

    base_uri = "http://vital.ai"
    namespace = "graph"

    wordnet_graph_uri = "wordnet-frames-graph-1"

    gq = (
        QueryBuilder.graph_query(
            offset=0,
            limit=10,
            resolve_objects=True
        )
        .graph_id(wordnet_graph_uri)
        .arc(
            Arc()
            .node_bind(NodeBind(name="frame"))
            .constraint_list(
                AndConstraintList()
                .node_constraint(
                    ClassConstraint(
                        clazz=KGFrame.get_class_uri()
                    )
                )
            )
            .arc_list(
                OrArcList()
                .arc_list(
                    AndArcList()
                    .arc(
                        Arc()
                        .node_bind(NodeBind(name="source_slot"))
                        .edge_bind(EdgeBind(name="source_slot_edge"))
                        .constraint_list(
                            AndConstraintList()
                            .node_constraint(
                                PropertyConstraint(
                                    property=Property_hasKGSlotType.get_uri(),
                                    comparator=ConstraintType.EQUAL_TO,
                                    value="urn:hasSourceEntity"
                                )
                            )
                            .node_constraint(
                                ClassConstraint(
                                    clazz=KGSlot.get_class_uri(),
                                    include_subclasses=True
                                )
                            )
                        )
                        .arc(
                            Arc(arc_traverse_type=ARC_TRAVERSE_TYPE_PROPERTY)
                            .solution_bind(SolutionBind(name="entity"))
                            .node_bind(NodeBind(name="source_entity"))  # source_entity
                            .path_bind(PathBind(name="source_entity_path"))
                            .property_path_list(
                                PropertyPathList()
                                .property_path(
                                    MetaQLPropertyPath(
                                        property_uri=Property_hasEntitySlotValue.get_uri()
                                    )
                                )
                            )
                            .constraint_list(
                                OrConstraintList()
                                .node_constraint(
                                    PropertyConstraint(
                                        property=Property_hasKGraphDescription.get_uri(),
                                        comparator=ConstraintType.STRING_CONTAINS,
                                        value="happy"
                                    )
                                )
                                .node_constraint(
                                    PropertyConstraint(
                                        property=Property_hasName.get_uri(),
                                        comparator=ConstraintType.STRING_CONTAINS,
                                        value="happy"
                                    )
                                )
                            )
                            .constraint_list(
                                AndConstraintList()
                                .node_constraint(
                                    ClassConstraint(
                                        clazz=KGEntity.get_class_uri()
                                    )
                                )
                            )
                        )
                    )
                    .arc(
                        Arc()
                        .node_bind(NodeBind(name="destination_slot"))
                        .edge_bind(EdgeBind(name="destination_slot_edge"))
                        .constraint_list(
                            AndConstraintList()
                            .node_constraint(
                                PropertyConstraint(
                                    property=Property_hasKGSlotType.get_uri(),
                                    comparator=ConstraintType.EQUAL_TO,
                                    value="urn:hasDestinationEntity"
                                )
                            )
                            .node_constraint(
                                ClassConstraint(
                                    clazz=KGSlot.get_class_uri(),
                                    include_subclasses=True
                                )
                            )
                        )
                        .arc(
                            Arc(arc_traverse_type=ARC_TRAVERSE_TYPE_PROPERTY)
                            .node_bind(NodeBind(name="destination_entity"))
                            .path_bind(PathBind(name="destination_entity_path"))
                            .property_path_list(
                                PropertyPathList()
                                .property_path(
                                    MetaQLPropertyPath(
                                        property_uri=Property_hasEntitySlotValue.get_uri()
                                    )
                                )
                            )
                            .constraint_list(
                                AndConstraintList()
                                .node_constraint(
                                    ClassConstraint(
                                        clazz=KGEntity.get_class_uri()
                                    )
                                )
                            )
                        )
                    )
                )
                .arc_list(
                    AndArcList()
                    .arc(
                        Arc()
                        .node_bind(NodeBind(name="source_slot"))
                        .edge_bind(EdgeBind(name="source_slot_edge"))
                        .constraint_list(
                            AndConstraintList()
                            .node_constraint(
                                PropertyConstraint(
                                    property=Property_hasKGSlotType.get_uri(),
                                    comparator=ConstraintType.EQUAL_TO,
                                    value="urn:hasSourceEntity"
                                )
                            )
                            .node_constraint(
                                ClassConstraint(
                                    clazz=KGSlot.get_class_uri(),
                                    include_subclasses=True
                                )
                            )
                        )
                        .arc(
                            Arc(arc_traverse_type=ARC_TRAVERSE_TYPE_PROPERTY)
                            .node_bind(NodeBind(name="source_entity"))
                            .path_bind(PathBind(name="source_entity_path"))
                            .property_path_list(
                                PropertyPathList()
                                .property_path(
                                    MetaQLPropertyPath(
                                        property_uri=Property_hasEntitySlotValue.get_uri()
                                    )
                                )
                            )
                            .constraint_list(
                                AndConstraintList()
                                .node_constraint(
                                    ClassConstraint(
                                        clazz=KGEntity.get_class_uri()
                                    )
                                )
                            )
                        )
                    )
                    .arc(
                        Arc()
                        .node_bind(NodeBind(name="destination_slot"))
                        .edge_bind(EdgeBind(name="destination_slot_edge"))
                        .constraint_list(
                            AndConstraintList()
                            .node_constraint(
                                PropertyConstraint(
                                    property=Property_hasKGSlotType.get_uri(),
                                    comparator=ConstraintType.EQUAL_TO,
                                    value="urn:hasDestinationEntity"
                                )
                            )
                            .node_constraint(
                                ClassConstraint(
                                    clazz=KGSlot.get_class_uri(),
                                    include_subclasses=True
                                )
                            )
                        )
                        .arc(
                            Arc(arc_traverse_type=ARC_TRAVERSE_TYPE_PROPERTY)
                            .solution_bind(SolutionBind(name="entity"))
                            .node_bind(NodeBind(name="destination_entity"))  # destination_entity
                            .path_bind(PathBind(name="destination_entity_path"))
                            .property_path_list(
                                PropertyPathList()
                                .property_path(
                                    MetaQLPropertyPath(
                                        property_uri=Property_hasEntitySlotValue.get_uri()
                                    )
                                )
                            )
                            .constraint_list(
                                OrConstraintList()
                                .node_constraint(
                                    PropertyConstraint(
                                        property=Property_hasKGraphDescription.get_uri(),
                                        comparator=ConstraintType.STRING_CONTAINS,
                                        value="happy"
                                    )
                                )
                                .node_constraint(
                                    PropertyConstraint(
                                        property=Property_hasName.get_uri(),
                                        comparator=ConstraintType.STRING_CONTAINS,
                                        value="happy"
                                    )
                                )
                            )
                            .constraint_list(
                                AndConstraintList()
                                .node_constraint(
                                    ClassConstraint(
                                        clazz=KGEntity.get_class_uri()
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        .build()
    )

    # print(gq)

    graph_query_json = json.dumps(gq, indent=4)

    # before parsing
    # print("Before Parsing:")
    # print(graph_query_json)

    metaql_query_dict = json.loads(graph_query_json)

    metaql_query = MetaQLParser.parse_metaql_dict(metaql_query_dict)

    # print(metaql_query)

    graph_query_json = json.dumps(metaql_query, indent=4)

    # after parsing
    # print("After Parsing:")
    # print(graph_query_json)

    # return

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

    sparql_builder = MetaQLSparqlBuilder()

    # parsed query
    sparql_impl: MetaQLSparqlImpl = sparql_builder.build_sparql(metaql_query, base_uri=base_uri, namespace=namespace)

    # original built query
    # sparql_impl: MetaQLSparqlImpl = sparql_builder.build_sparql(gq)

    limit = sparql_impl.get_limit()

    offset = sparql_impl.get_offset()

    graph_id = sparql_impl.get_graph_id_list()[0]

    print(f"SPARQL: Graph ID: {graph_id}")

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

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

    vitalservice = vitalservice_manager.get_vitalservice("local_kgraph")

    graph_list = vitalservice.list_graphs(account_id="account1")

    for g in graph_list:
        print(g)
        print(f"Graph URI: {g.get_graph_uri()}")

    virtuoso_username = vitalservice.graph_service.username
    virtuoso_password = vitalservice.graph_service.password
    virtuoso_endpoint = vitalservice.graph_service.endpoint

    print(f"Virtuoso Endpoint: {virtuoso_endpoint}")

    virtuoso_graph_service = VirtuosoGraphService(
        base_uri=base_uri,
        namespace=namespace,
        username=virtuoso_username,
        password=virtuoso_password,
        endpoint=virtuoso_endpoint
    )

    # print(f"Query string:\n---------\n{query_string}\n---------")

    solutions = virtuoso_graph_service.query_construct_solution(
        graph_id,
        query_string,
        namespace_list,
        binding_list,
        root_binding,
        limit=limit, offset=offset)

    print(f"Solution Count: {len(solutions.solution_list)}")

    count = 0

    for solution in solutions.solution_list:
        count += 1
        print("-------------------------------------")
        print(f"Solution Count: {count}")
        print(f"Root Binding: {solution.root_binding}")
        print(f"Binding Map: {solution.uri_map}")
        for binding, obj in solution.object_map.items():
            binding_uri = solution.uri_map[binding]
            print(f"Solution Binding: {binding} : {binding_uri}")
            print(obj.to_rdf())
        print("-------------------------------------")

    # ont_list = vs.get_ontology_manager().get_ontology_list()

    # for ont in ont_list:
    #    print(f"Ontology: {ont.prefix} {ont.ontology_iri}")

    iri_list = vs.get_ontology_manager().get_ontology_iri_list()

    ont_prefix_map = {}

    for iri in iri_list:
        # print(f"IRI: {iri}")

        ont = vs.get_ontology_manager().get_vitalsigns_ontology(iri)
        ns_map = ont._namespace_map

        for k in ns_map.keys():
            if k:  # skip empty string
                v = ns_map[k]
                if v:  # all should have a value
                    # print(f"Namespace {k}: {v}")
                    # ont_prefix_map[k] = v
                    pass

    for iri in iri_list:

        if iri.startswith("http://vital.ai/ontology/"):

            prefix = iri[len("http://vital.ai/ontology/"):]

            prefix = prefix.removesuffix("#")

            # print(f"Vital Prefix: {prefix} IRI: {iri}")

            ont_prefix_map[prefix] = iri

    for k in ont_prefix_map.keys():
        # print(f"Ont Prefix: {k} IRI: {ont_prefix_map[k]}")
        pass


if __name__ == "__main__":
    main()

