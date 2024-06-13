from utils.config_utils import ConfigUtils
from vital_ai_vitalsigns.service.graph.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.service.vital_service import VitalService
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.VitalServiceConfig import VitalServiceConfig


def main():

    print('Hello World')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    config = ConfigUtils.load_config()

    virtuoso_username = config['graph_database']['virtuoso_username']
    virtuoso_password = config['graph_database']['virtuoso_password']
    virtuoso_endpoint = config['graph_database']['virtuoso_endpoint']

    virtuoso_graph_service = VirtuosoGraphService(
        username=virtuoso_username,
        password=virtuoso_password,
        endpoint=virtuoso_endpoint
    )

    graph_list = virtuoso_graph_service.list_graphs()

    for g in graph_list:
        print(f"Graph URI: {g.get_graph_uri()}")

    # vital_service = VitalService(graph_service=virtuoso_graph_service)

    graph_uri = "urn:graph-1"

    deleted = virtuoso_graph_service.delete_graph(graph_uri)

    print(f"Deleted Graph {graph_uri}: {deleted}")

    created = virtuoso_graph_service.create_graph(graph_uri)

    print(f"Created Graph {graph_uri}: {created}")

    service = VitalServiceConfig()
    service.URI = URIGenerator.generate_uri()
    service.appID = "app_id"

    insert_status = virtuoso_graph_service.insert_object(graph_uri, service)

    print(f"Insert Status: {insert_status.get_message()}")

    service.appID = "app_id_new"

    update_status = virtuoso_graph_service.update_object(service, graph_uri=graph_uri)

    print(f"Update Status: {update_status.get_message()}")

    object_uri = service.URI

    object_get = virtuoso_graph_service.get_object(object_uri, graph_uri=graph_uri)

    print(f"Get Object Status: {object_get.to_json()}")

    result_list = virtuoso_graph_service.get_graph_all_objects(graph_uri)

    print(f"Result Length: {len(result_list)}")

    for r in result_list:
        obj = r.graph_object
        print(obj.to_rdf())

    delete_status = virtuoso_graph_service.delete_object(service.URI, graph_uri=graph_uri)

    print(f"Delete Status: {delete_status.get_message()}")

    purged = virtuoso_graph_service.purge_graph(graph_uri)

    print(f"Purged Graph {graph_uri}: {purged}")

    result_list = virtuoso_graph_service.get_graph_all_objects(graph_uri)

    print(f"Result Length: {len(result_list)}")

    for r in result_list:
        obj = r.graph_object
        print(obj.to_rdf())

    # deleted = virtuoso_graph_service.delete_graph(graph_uri)

    # print(f"Deleted Graph {graph_uri}: {deleted}")


if __name__ == "__main__":
    main()
