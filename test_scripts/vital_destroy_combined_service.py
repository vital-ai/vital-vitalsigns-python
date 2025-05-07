from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():
    print('Vital Destroy Combined Service')

    print("VitalSigns Initializing...")

    vs = VitalSigns()

    print("VitalSigns Initialized")

    service_namespace = "VITALTEST"


    # get schema
    # find classes prefixed with namespace
    # delete weaviate classes in the namespace

    # list virtuoso graphs from service graph
    # delete graphs in service
    # delete service graph



if __name__ == "__main__":
    main()

