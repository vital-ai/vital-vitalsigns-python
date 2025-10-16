from vital_ai_vitalsigns.vitalsigns import VitalSigns

def main():

    print('VitalService Destroy Service')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vs_config = vs.get_config()

    print(vs_config)

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

    service_name = "local_kgraph_test"

    # check current state
    # destroy

    vitalservice = vitalservice_manager.get_vitalservice(service_name)

    destroy_status = vitalservice.destroy_service()

    print(f"{service_name}: Destroy Status: {destroy_status}")


if __name__ == "__main__":
    main()

