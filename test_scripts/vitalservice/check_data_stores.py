from vital_ai_vitalsigns.vitalsigns import VitalSigns

def main():

    print('Check Data Stores')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vs_config = vs.get_config()

    print(vs_config)

    vitalservice_manager = vs.get_vitalservice_manager()

    vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

    for vitalservice_name in vitalservice_name_list:
        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
        print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")


if __name__ == "__main__":
    main()

