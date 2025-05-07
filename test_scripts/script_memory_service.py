from rdflib import URIRef
from vital_ai_vitalsigns.service.graph.memory.memory_graph_service import MemoryGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.service.graph.graph_service_constants import VitalGraphServiceConstants


def main():

    print('Test Memory Service')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    memory_service = MemoryGraphService()

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    new_graph = "urn:new_graph"

    print(f"Creating new graph: {new_graph}")

    created = memory_service.create_graph(new_graph)

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    service_graph = memory_service.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

    for subject, predicate, obj in service_graph:
        print(f"Subject: {subject}, Predicate: {predicate}, Object: {obj}")

    print(f"Deleting new graph: {new_graph}")

    deleted = memory_service.delete_graph(new_graph)

    name_graph_list = memory_service.list_graphs()

    for ng in name_graph_list:
        print(f"Name Graph: {ng}")

    service_graph = memory_service.graph.get_graph(URIRef(VitalGraphServiceConstants.SERVICE_GRAPH_URI))

    for subject, predicate, obj in service_graph:
        print(f"Subject: {subject}, Predicate: {predicate}, Object: {obj}")


if __name__ == "__main__":
    main()
