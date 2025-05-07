from ai_haley_kg_domain.model.Edge_hasInteractionKGFrame import Edge_hasInteractionKGFrame
from ai_haley_kg_domain.model.Edge_hasKGSlot import Edge_hasKGSlot
from ai_haley_kg_domain.model.KGFrame import KGFrame
from ai_haley_kg_domain.model.KGInteraction import KGInteraction
from ai_haley_kg_domain.model.KGTextSlot import KGTextSlot
from vital_ai_vitalsigns.ontology.ontology import Ontology
from vital_ai_vitalsigns.service.graph.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
import gzip
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, POST, DIGEST
from vital_ai_vitalsigns.service.graph.binding import Binding


def get_sample_frame():

    interaction = KGInteraction()
    interaction.URI = URIGenerator.generate_uri()
    interaction.name = "KGInteraction 1"

    frame_1 = KGFrame()
    frame_1.URI = URIGenerator.generate_uri()
    frame_1.kGFrameType = "urn:person_frametype"
    frame_1.kGFrameTypeDescription = "Person"

    frame_edge_1 = Edge_hasInteractionKGFrame()
    frame_edge_1.URI = URIGenerator.generate_uri()
    frame_edge_1.edgeSource = interaction.URI
    frame_edge_1.edgeDestination = frame_1.URI

    slot_1 = KGTextSlot()
    slot_1.URI = URIGenerator.generate_uri()
    slot_1.kGSlotType = "urn:firstname_slottype"
    slot_1.kGSlotTypeDescription = "First Name"
    slot_1.textSlotValue = "Jane"

    slot_edge_1 = Edge_hasKGSlot()
    slot_edge_1.URI = URIGenerator.generate_uri()
    slot_edge_1.edgeSource = frame_1.URI
    slot_edge_1.edgeDestination = slot_1.URI

    graph_object_list = [
        interaction,
        frame_1, frame_edge_1,
        slot_1, slot_edge_1
    ]

    return graph_object_list


def main():

    print('Graph Test')

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
        print(f"Graph URI: {g.get_namespace()}")

    virtuoso_username = vitalservice.graph_service.username
    virtuoso_password = vitalservice.graph_service.password
    virtuoso_endpoint = vitalservice.graph_service.endpoint


    graph_id = "kgframe-test-1"

    graph_uri = "http://vital.ai/graph/kgframe-test-1"

    vital_graph_service = VirtuosoGraphService(
        base_uri="http://vital.ai",
        namespace="graph",
        username=virtuoso_username,
        password=virtuoso_password,
        endpoint=virtuoso_endpoint
    )

    graph_list = vital_graph_service.list_graphs()

    for graph in graph_list:
        print(graph.get_graph_uri())

    # created = vital_graph_service.create_graph(graph_uri)
    # print(created)

    # exit(0)

    # purged = vital_graph_service.purge_graph(graph_uri)
    # print(f"Purged: {purged}")

    """

    graph_object_list = get_sample_frame()

    for g in graph_object_list:
        print(g.to_rdf())
        status = vital_graph_service.insert_object(graph_uri, g)
        print(status.get_status())

    # status = vital_graph_service.insert_object_list(graph_uri, graph_object_list)
    # print(status.get_status())

    """

    frame = None

    frame_uri = None

    result_list = vital_graph_service.get_graph_all_objects(graph_id)

    for r in result_list:

        go = r.graph_object

        print(r.graph_object.to_rdf())

        if isinstance(go, KGFrame):
            frame = go
            frame_uri = go.URI

    print(f"frame_uri: {frame_uri}")

    namespace_list = [
        Ontology("vital-core", "http://vital.ai/ontology/vital-core#"),
        Ontology("vital", "http://vital.ai/ontology/vital#"),
        Ontology("vital-aimp", "http://vital.ai/ontology/vital-aimp#"),
        Ontology("haley", "http://vital.ai/ontology/haley"),
        Ontology("haley-ai-question", "http://vital.ai/ontology/haley-ai-question#"),
        Ontology("haley-ai-kg", "http://vital.ai/ontology/haley-ai-kg#")
    ]

    binding_list = [
        Binding("?frame", "urn:hasFrame"),
        Binding("?slotEdge", "urn:hasSlotEdge"),
        Binding("?slot", "urn:hasSlot", True, "UNK"),
        Binding("?otherSlot", "urn:hasOtherSlot", True, "UNK")
    ]

    frame_query = f"""
    
    {{
        # virtuoso gets confused if the VALUES group is not in the same
        # grouping as it is used
        
        VALUES ?slotDataType {{
            haley-ai-kg:KGSlot
            haley-ai-kg:KGAudioSlot
            haley-ai-kg:KGBooleanSlot
            haley-ai-kg:KGChoiceOptionSlot
            haley-ai-kg:KGChoiceSlot
            haley-ai-kg:KGCodeSlot
            haley-ai-kg:KGCurrencySlot
            haley-ai-kg:KGDateTimeSlot
            haley-ai-kg:KGDoubleSlot
            haley-ai-kg:KGEntitySlot
            haley-ai-kg:KGFileUploadSlot
            haley-ai-kg:KGGeoLocationSlot
            haley-ai-kg:KGImageSlot
            haley-ai-kg:KGIntegerSlot
            haley-ai-kg:KGJSONSlot
            haley-ai-kg:KGLongSlot
            haley-ai-kg:KGLongTextSlot
            haley-ai-kg:KGMultiChoiceOptionSlot
            haley-ai-kg:KGMultiChoiceSlot
            haley-ai-kg:KGMultiTaxonomyOptionSlot
            haley-ai-kg:KGMultiTaxonomySlot
            haley-ai-kg:KGPropertySlot
            haley-ai-kg:KGRunSlot
            haley-ai-kg:KGTaxonomyOptionSlot
            haley-ai-kg:KGTaxonomySlot
            haley-ai-kg:KGTextSlot
            haley-ai-kg:KGURISlot
            haley-ai-kg:KGVideoSlot
        }}
        
        ?frame rdf:type haley-ai-kg:KGFrame .

        ?slotEdge vital-core:hasEdgeSource ?frame .
        ?slotEdge vital-core:hasEdgeDestination ?slot .
        ?slotEdge rdf:type haley-ai-kg:Edge_hasKGSlot .

        # if slotDataType is moved outside of the group
        # then this must be the last part of the group
        # so that it is right before the filter
        # otherwise virtuoso has a syntax error
        
        ?slot rdf:type ?slotType .

        OPTIONAL {{
            ?slotEdge vital-core:hasEdgeDestination ?otherSlot .
            ?otherSlot rdf:type haley-ai-kg:KGMultiTaxonomySlot .
        }}
    }}
    
    FILTER(?slotType IN (?slotDataType))
"""

    # handling optional
    # SELECT ?name (COALESCE(?email, "No email") AS ?email)
    # always put a value in the construct ?

    result_list = vital_graph_service.query_construct(
        graph_id, frame_query, namespace_list, binding_list, limit=500, offset=0)

    print(f"Result Count: {len(result_list)}")

    frame_uri_list = []

    for result in result_list:
        go = result.graph_object
        print(go.to_rdf())

    exit(0)


    # has frame query
    query = f"""
    
    SELECT DISTINCT ?uri WHERE {{
    GRAPH <http://vital.ai/graph/kgframe-test-1> {{
        VALUES ?subject {{ <{frame_uri}> }}
        
        {{
            # Ensure there's a triple pattern here
            ?subject rdf:type ?type .
            BIND(?subject AS ?uri)
        }} UNION {{
            ?subject haley-ai-kg:Edge_hasKGSlot ?slot .
            ?slot rdf:type ?slotType .
            VALUES ?slotType {{
                haley-ai-kg:KGSlot
                haley-ai-kg:KGAudioSlot
                haley-ai-kg:KGBooleanSlot
                haley-ai-kg:KGChoiceOptionSlot
                haley-ai-kg:KGChoiceSlot
                haley-ai-kg:KGCodeSlot
                haley-ai-kg:KGCurrencySlot
                haley-ai-kg:KGDateTimeSlot
                haley-ai-kg:KGDoubleSlot
                haley-ai-kg:KGEntitySlot
                haley-ai-kg:KGFileUploadSlot
                haley-ai-kg:KGGeoLocationSlot
                haley-ai-kg:KGImageSlot
                haley-ai-kg:KGIntegerSlot
                haley-ai-kg:KGJSONSlot
                haley-ai-kg:KGLongSlot
                haley-ai-kg:KGLongTextSlot
                haley-ai-kg:KGMultiChoiceOptionSlot
                haley-ai-kg:KGMultiChoiceSlot
                haley-ai-kg:KGMultiTaxonomyOptionSlot
                haley-ai-kg:KGMultiTaxonomySlot
                haley-ai-kg:KGPropertySlot
                haley-ai-kg:KGRunSlot
                haley-ai-kg:KGTaxonomyOptionSlot
                haley-ai-kg:KGTaxonomySlot
                haley-ai-kg:KGTextSlot
                haley-ai-kg:KGURISlot
                haley-ai-kg:KGVideoSlot
            }}
            BIND(?slot AS ?uri)
        }} UNION {{
            ?edge vital-core:hasEdgeSource ?subject .
            ?edge vital-core:hasEdgeDestination ?slot .
            BIND(?edge AS ?uri)
        }} UNION {{
            ?edge vital-core:hasEdgeDestination ?subject .
            ?edge vital-core:hasEdgeSource ?slot .
            BIND(?edge AS ?uri)
        }}
    }}
}}
ORDER BY ?uri
LIMIT 500 OFFSET 0
    """

    """
    result_list = vital_graph_service.query(
        query, graph_uri, limit=500, offset=0, resolve_objects=True)

    print(f"Result Count: {len(result_list)}")

    frame_uri_list = []

    for result in result_list:
        go = result.graph_object
        print(go.to_rdf())

    """

    print(frame.to_json())

    frame_get = vital_graph_service.get_object(frame_uri, graph_uri)

    print(frame.to_json())

    obj_get = vital_graph_service.get_object("urn:not_a_uri", graph_uri)

    print(f"Empty Object: {obj_get}")

    frame_get.name = "Updated Frame Name"

    try:
        insert_status = vital_graph_service.insert_object(graph_uri, frame_get)
        print(f"Insert Status: {insert_status.message}")

    except Exception as e:
        print(f"Insert Exception: {e}")

    update_status = vital_graph_service.update_object(frame_get, graph_uri)
    print(f"Update Status: {update_status.get_status()}")

    frame_get2 = vital_graph_service.get_object(frame_uri, graph_uri)

    print(frame_get2.to_json())

    # for g in graph_object_list:
    #    status = vital_graph_service.delete_object(str(g.URI), graph_uri)
    #    print(status.get_status())

    delete_list = []
    for g in graph_object_list:
        delete_uri = str(g.URI)
        delete_list.append(delete_uri)

    status = vital_graph_service.delete_object_list(delete_list, graph_uri)
    print(status.get_status())

    result_list = vital_graph_service.get_graph_all_objects(graph_uri)

    for r in result_list:
        go = r.graph_object
        print(go.to_rdf())


if __name__ == "__main__":
    main()


