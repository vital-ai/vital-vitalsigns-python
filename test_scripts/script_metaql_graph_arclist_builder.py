import json
from typing import List
from ai_haley_kg_domain.model.KGEntity import KGEntity
from ai_haley_kg_domain.model.KGFrame import KGFrame
from ai_haley_kg_domain.model.KGSlot import KGSlot
from ai_haley_kg_domain.model.properties.Property_hasEntitySlotValue import Property_hasEntitySlotValue
from ai_haley_kg_domain.model.properties.Property_hasKGSlotType import Property_hasKGSlotType
from ai_haley_kg_domain.model.properties.Property_hasKGraphDescription import Property_hasKGraphDescription

from test_scripts.construct_query import ConstructQuery
from vital_ai_vitalsigns.metaql.arc.metaql_arc import ARC_TRAVERSE_TYPE_PROPERTY
from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.metaql.query.query_builder import QueryBuilder, AndConstraintList, PropertyConstraint, \
    ConstraintType, ClassConstraint, Arc, OrConstraintList, NodeBind, EdgeBind, PathBind, PropertyPathList, \
    MetaQLPropertyPath, AndArcList, OrArcList
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.binding import Binding
from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_metaql_impl import VirtuosoMetaQLImpl
from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.properties.Property_hasName import Property_hasName


def generate_connecting_frame_query(entity_description: str):
    namespace_list = get_default_namespace_list()

    binding_list = [
        Binding("?entity", "urn:hasEntity"),
        Binding("?frame", "urn:hasFrame"),
        Binding("?sourceSlot", "urn:hasSourceSlot"),
        Binding("?destinationSlot", "urn:hasDestinationSlot"),
        Binding("?sourceSlotEntity", "urn:hasSourceSlotEntity"),
        Binding("?destinationSlotEntity", "urn:hasDestinationSlotEntity")
    ]

    # note: add select distinct for distinct solutions

    frame_query = f"""
        
        ?frame a haley-ai-kg:KGFrame .
        
        ?sourceEdge a haley-ai-kg:Edge_hasKGSlot .
        ?sourceEdge vital-core:hasEdgeSource ?frame .
        ?sourceEdge vital-core:hasEdgeDestination ?sourceSlot .
        
        ?sourceSlot a haley-ai-kg:KGEntitySlot .
        ?sourceSlot haley-ai-kg:hasEntitySlotValue ?sourceSlotEntity .
        ?sourceSlot haley-ai-kg:hasKGSlotType <urn:hasSourceEntity> .
        
        ?destinationEdge a haley-ai-kg:Edge_hasKGSlot .
        ?destinationEdge vital-core:hasEdgeSource ?frame .
        ?destinationEdge vital-core:hasEdgeDestination ?destinationSlot .
        
        ?destinationSlot a haley-ai-kg:KGEntitySlot .
        ?destinationSlot haley-ai-kg:hasEntitySlotValue ?destinationSlotEntity .
        ?destinationSlot haley-ai-kg:hasKGSlotType <urn:hasDestinationEntity> .
              
        ?sourceSlotEntity a haley-ai-kg:KGEntity .
        
        ?destinationSlotEntity a haley-ai-kg:KGEntity .

                
        {{
        
        
        {{
        ?sourceSlotEntity haley-ai-kg:hasKGraphDescription ?description1 .
        ?description1 bif:contains "happy" .
        }}
        UNION
        {{
        ?sourceSlotEntity vital-core:hasName ?name1 .
        ?name1 bif:contains "happy" .
        }}
        
        BIND(?sourceSlotEntity as ?entity)
        
        }}
        
        UNION
        
        {{
        

        {{
        ?destinationSlotEntity haley-ai-kg:hasKGraphDescription ?description2 .
        ?description2 bif:contains "happy" .
        }}
        UNION
        {{
        ?destinationSlotEntity vital-core:hasName ?name2 .
        ?name2 bif:contains "happy" .
        }}
        
        BIND(?destinationSlotEntity AS ?entity)
        
        }}

        
        
        """

    root_binding = "?frame"

    construct_query = ConstructQuery(namespace_list, binding_list, frame_query, root_binding)

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

    print('Test MetaQL Graph Builder')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vital_home = vs.get_vitalhome()

    print(f"VitalHome: {vital_home}")

    vs_config = vs.get_config()

    print(vs_config)

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


    print(f"Virtuoso Endpoint: {virtuoso_endpoint}")

    virtuoso_graph_service = VirtuosoGraphService(
        base_uri="http://vital.ai",
        namespace="graph",
        username=virtuoso_username,
        password=virtuoso_password,
        endpoint=virtuoso_endpoint
    )

    wordnet_graph_id = 'wordnet-frames-graph-1'

    wordnet_graph_uri = 'http://vital.ai/graph/wordnet-frames-graph-1'

    gq = (
        QueryBuilder.graph_query(
            offset=0,
            limit=100,
            resolve_objects=True
        )
        .graph_uri(wordnet_graph_uri)
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

    print(gq)

    graph_query_json = json.dumps(gq, indent=4)

    print(graph_query_json)

    metaql_query_dict = json.loads(graph_query_json)

    metaql_query = MetaQLParser.parse_metaql_dict(metaql_query_dict)

    print(metaql_query)

    namespace = "VITALTEST"

    ontology_list: List[Ontology] = []

    # add resolving graph objects true/false into query

    sparql_string = VirtuosoMetaQLImpl.generate_select_query_sparql(
        select_query=metaql_query,
        namespace_list=ontology_list
    )

    print(f"Graph Query SPARQL:\n{sparql_string}")

    search_string = "happy"

    construct_query = generate_connecting_frame_query(search_string)

    solutions = virtuoso_graph_service.query_construct_solution(
        wordnet_graph_id,
        construct_query.query,
        construct_query.namespace_list,
        construct_query.binding_list,
        construct_query.root_binding,
        limit=100, offset=0)

    print(f"Wordnet Solution Count: {len(solutions.solution_list)}")

    count = 0

    for solution in solutions.solution_list:
        count += 1
        print("-------------------------------------")
        print(f"Solution Count: {count}")
        print(f"Root Binding: {solution.root_binding}")
        print(f"Binding Map: {solution.uri_map}")
        for binding, obj in solution.object_map.items():
            binding_uri = solution.uri_map[binding]
            print(f"Wordnet Solution Binding: {binding} : {binding_uri}")
            print(obj.to_rdf())
        print("-------------------------------------")


if __name__ == "__main__":
    main()

