import os
from vital_ai_vitalsigns.utils.uri_generator import URIGenerator
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns_core.model.VitalServiceConfig import VitalServiceConfig


def main():

    print('Hello World')

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

    print(f"Current working directory: {os.getcwd()}")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    graph_list = vitalservice.list_graphs(account_id = "account1")

    for g in graph_list:
        print(f"Graph URI: {g.get_graph_uri()}")

    exit(0)

    account_id = "account1"

    graph_id = "graph-1"

    deleted = vitalservice.delete_graph(graph_id, account_id=account_id)

    print(f"Deleted Graph {graph_id}: {deleted}")

    created = vitalservice.create_graph(graph_id, account_id=account_id)

    print(f"Created Graph {graph_id}: {created}")

    service = VitalServiceConfig()
    service.URI = URIGenerator.generate_uri()
    service.appID = "app_id"

    insert_status = vitalservice.insert_object(graph_id, service, account_id=account_id)

    print(f"Insert Status: {insert_status.get_message()}")

    service.appID = "app_id_new"

    update_status = vitalservice.update_object(service, graph_id=graph_id, account_id=account_id)

    print(f"Update Status: {update_status.get_message()}")

    object_uri = service.URI

    object_get = vitalservice.get_object(object_uri, graph_id=graph_id, account_id=account_id)

    print(f"Get Object Status: {object_get.to_json()}")

    result_list = vitalservice.get_graph_all_objects(graph_id, account_id=account_id)

    print(f"Result Length: {len(result_list)}")

    for r in result_list:
        obj = r.graph_object
        print(obj.to_rdf())

    delete_status = vitalservice.delete_object(service.URI, graph_id=graph_id, account_id=account_id)

    print(f"Delete Status: {delete_status.get_message()}")

    purged = vitalservice.purge_graph(graph_id, account_id=account_id)

    print(f"Purged Graph {graph_id}: {purged}")

    result_list = vitalservice.get_graph_all_objects(graph_id, account_id=account_id)

    print(f"Result Length: {len(result_list)}")

    for r in result_list:
        obj = r.graph_object
        print(obj.to_rdf())

    # deleted = virtuoso_graph_service.delete_graph(graph_uri)

    # print(f"Deleted Graph {graph_uri}: {deleted}")


if __name__ == "__main__":
    main()
