from vital_ai_vitalsigns.vitalsigns import VitalSigns

def main():

    print('VitalService List Graph')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vs_config = vs.get_config()

    print(vs_config)

    # service_name = "local_kgraph"

    service_name = "local_kgraph_test"

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        # print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

    vitalservice = vitalservice_manager.get_vitalservice(service_name)

    print(f"VitalService Name: {service_name}")

    graph_list = vitalservice.list_graphs()

    graph_count = len(graph_list)

    print(f"Graph Count: {graph_count}")

    for g in graph_list:
        print(f"Graph URI: {g.get_graph_uri()}")

    account_graph_list = vitalservice.list_graphs(account_id="account1")

    account_graph_count = len(account_graph_list)

    print(f"Account Graph Count: {account_graph_count}")

    for g in account_graph_list:
        print(f"Account Graph URI: {g.get_graph_uri()}")


if __name__ == "__main__":
    main()

